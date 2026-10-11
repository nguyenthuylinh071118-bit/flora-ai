
import logging

from django.shortcuts import render
from django.utils import timezone
from django.db import transaction
from django.db.models import F

from .gemini_service import ALLOWED_CLASSES, recognize_with_gemini
from .local_model_service import recognize_with_local_model
from .models import (
    Plant,
    PlantComparison,
    QuizQuestion,
    DailyRecognitionQuota,
)

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.50
MAX_IMAGE_SIZE = 10 * 1024 * 1024

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


def use_daily_quota():
    """Dành một lượt trong hạn mức gọi Gemini mỗi ngày."""
    today = timezone.localdate()

    with transaction.atomic():
        DailyRecognitionQuota.objects.get_or_create(
            day=today,
            defaults={"used": 0},
        )

        updated = (
            DailyRecognitionQuota.objects
            .filter(
                day=today,
                used__lt=DailyRecognitionQuota.LIMIT,
            )
            .update(used=F("used") + 1)
        )

        return updated > 0


def attach_plant_information(ai_name):
    """Tìm thông tin cây trong cơ sở dữ liệu Flora AI."""
    if not ai_name:
        return None, [], []

    aliases = {
        "bong_trang": "Hoa bông trang",
        "cay_buoi": "Cây bưởi",
        "cay_chuoi": "Cây chuối",
        "cay_phuong": "Cây phượng",
        "hoa_hong": "Hoa hồng",
        "hoa_layon": "Hoa layon",
        "hoa_sen": "Hoa sen",
        "lan_mokara": "Lan Mokara",
        "muong_trau": "Cây muồng trâu",
        "vong_mong_ga": "Vông mồng gà",
    }

    search_name = aliases.get(
        ai_name.strip().lower(),
        ai_name.strip(),
    )

    plant = Plant.objects.filter(
        name__iexact=search_name
    ).first()

    if plant is None:
        return None, [], []

    comparisons = list(
        PlantComparison.objects
        .filter(plant=plant)
        .select_related("compared_plant")
    )

    quiz_questions = list(
        QuizQuestion.objects.filter(plant=plant)
    )

    return plant, comparisons, quiz_questions

def home(request):
    plant = None
    error = None
    ai_name = None
    ai_reason = None
    comparisons = []
    quiz_questions = []

    if request.method == "POST":
        image_file = request.FILES.get("image")

        if not image_file:
            error = "Vui lòng chọn một hình ảnh."

        elif image_file.size > MAX_IMAGE_SIZE:
            error = "Ảnh quá lớn. Vui lòng chọn ảnh không quá 10 MB."

        elif image_file.content_type not in ALLOWED_MIME_TYPES:
            error = "Vui lòng sử dụng ảnh JPG, PNG hoặc WEBP."

        else:
            image_bytes = image_file.read()
            class_key = None
            confidence = None
            local_name = None

            # Bước 1: Chạy mô hình đã huấn luyện trước.
            try:
                class_key, confidence = recognize_with_local_model(
                    image_bytes
                )
                local_name = ALLOWED_CLASSES.get(class_key)

                if local_name is None:
                    raise ValueError(
                        f"Lớp cây không được hỗ trợ: {class_key}"
                    )

            except Exception:
                logger.exception("Lỗi mô hình nhận diện cục bộ")
                error = (
                    "Không thể chạy mô hình nhận diện cục bộ. "
                    "Hãy kiểm tra file mô hình và thử lại."
                )

            # Bước 2: Nếu confidence đủ cao, dùng kết quả cục bộ.
            if local_name is not None and confidence is not None:
                if confidence >= CONFIDENCE_THRESHOLD:
                    ai_name = local_name
                    ai_reason = (
                        "Nhận diện bằng EfficientNet-B0 đã huấn luyện. "
                        f"Confidence: {confidence:.1%}. "
                        "Đây là điểm tin cậy của mô hình, "
                        "không bảo đảm kết quả luôn chính xác."
                    )

                else:
                    # Bước 3: Confidence thấp thì thử Gemini.
                    try:
                        quota_available = use_daily_quota()
                    except Exception:
                        logger.exception(
                            "Không kiểm tra được hạn mức Gemini"
                        )
                        quota_available = False

                    if not quota_available:
                        ai_name = local_name
                        ai_reason = (
                            "Gemini hiện không khả dụng hoặc hạn mức "
                            "đã hết. Hệ thống dùng dự đoán của "
                            "EfficientNet-B0 với confidence "
                            f"{confidence:.1%}. Kết quả chưa được "
                            "xác minh; vui lòng kiểm tra lại."
                        )

                    else:
                        try:
                            gemini_name, gemini_reason = (
                                recognize_with_gemini(
                                    image_bytes,
                                    image_file.content_type,
                                )
                            )

                            if gemini_name:
                                ai_name = gemini_name
                                ai_reason = (
                                    "Gemini được dùng để xác minh vì "
                                    "confidence của mô hình cục bộ "
                                    f"là {confidence:.1%}. "
                                    f"{gemini_reason or ''}"
                                )
                            else:
                                ai_name = local_name
                                ai_reason = (
                                    "Gemini chưa xác định được cây. "
                                    f"EfficientNet-B0 dự đoán {local_name} "
                                    f"với confidence {confidence:.1%}. "
                                    f"{gemini_reason or ''} "
                                    "Kết quả chưa được xác minh."
                                )

                        except Exception as exc:
                            logger.exception(
                                "Gemini thất bại; dùng kết quả cục bộ"
                            )
                            message = str(exc).upper()

                            if (
                                "429" in message
                                or "RESOURCE_EXHAUSTED" in message
                                or "QUOTA" in message
                            ):
                                fallback_note = (
                                    "Gemini đã chạm giới hạn yêu cầu "
                                    "hoặc hạn mức API."
                                )
                            elif (
                                "503" in message
                                or "UNAVAILABLE" in message
                            ):
                                fallback_note = (
                                    "Gemini đang tạm thời không khả dụng."
                                )
                            else:
                                fallback_note = (
                                    "Không thể xác minh bằng Gemini."
                                )

                            ai_name = local_name
                            ai_reason = (
                                f"{fallback_note} "
                                "Hệ thống đã chuyển về mô hình "
                                "EfficientNet-B0 đã huấn luyện. "
                                f"Confidence: {confidence:.1%}. "
                                "Kết quả chưa được xác minh; "
                                "vui lòng kiểm tra lại."
                            )

                # Bước 4: Tải thông tin cây trong cơ sở dữ liệu.
                if ai_name:
                    try:
                        (
                            plant,
                            comparisons,
                            quiz_questions,
                        ) = attach_plant_information(ai_name)

                        if plant is None:
                            ai_reason = (
                                f"{ai_reason or ''} "
                                "Cây này chưa có bản ghi khớp trong "
                                "cơ sở dữ liệu Flora AI."
                            )

                    except Exception:
                        logger.exception(
                            "Lỗi truy xuất thông tin cây"
                        )
                        error = (
                            "Đã nhận diện được tên cây nhưng chưa thể "
                            "tải thông tin chi tiết. Vui lòng thử lại."
                        )

    return render(
        request,
        "plantapp/home.html",
        {
            "plant": plant,
            "ai_name": ai_name,
            "ai_reason": ai_reason,
            "comparisons": comparisons,
            "quiz_questions": quiz_questions,
            "error": error,
        },
    )
