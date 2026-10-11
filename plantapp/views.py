import logging
from django.shortcuts import render
from django.utils import timezone
from django.db import transaction
from django.db.models import F

from .gemini_service import recognize_with_gemini
from .models import (
    Plant,
    PlantComparison,
    QuizQuestion,
    DailyRecognitionQuota,
)


def use_daily_quota():
    """Dành một lượt nhận diện trong hạn mức chung mỗi ngày."""
    today = timezone.localdate()

    with transaction.atomic():
        quota, _ = DailyRecognitionQuota.objects.get_or_create(
            day=today,
            defaults={"used": 0},
        )

        updated = (
            DailyRecognitionQuota.objects
            .filter(day=today, used__lt=DailyRecognitionQuota.LIMIT)
            .update(used=F("used") + 1)
        )

        if updated == 0:
            return False

    return True


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

        elif image_file.size > 10 * 1024 * 1024:
            error = "Ảnh quá lớn. Vui lòng chọn ảnh không quá 10 MB."

        elif image_file.content_type not in {
            "image/jpeg",
            "image/png",
            "image/webp",
        }:
            error = "Vui lòng sử dụng ảnh JPG, PNG hoặc WEBP."

        elif not use_daily_quota():
            error = (
                "Hệ thống đã đạt giới hạn 1.500 lượt nhận diện "
                "trong hôm nay. Vui lòng thử lại vào ngày mai."
            )

        else:
            try:
                image_bytes = image_file.read()

                ai_name, ai_reason = recognize_with_gemini(
                    image_bytes,
                    image_file.content_type,
                )

                if not ai_name:
                    error = (
                        "Chưa thể xác định cây thuộc danh sách hỗ trợ. "
                        + (ai_reason or "Vui lòng thử ảnh rõ hơn.")
                    )
                else:
                    try:
                        plant = Plant.objects.get(name=ai_name)

                        comparisons = (
                            PlantComparison.objects
                            .filter(plant=plant)
                            .select_related("compared_plant")
                        )

                        quiz_questions = QuizQuestion.objects.filter(
                            plant=plant
                        )

                    except Plant.DoesNotExist:
                        error = (
                            f"Gemini nhận diện được {ai_name}, nhưng "
                            "cây này chưa có trong cơ sở dữ liệu."
                        )

            except ValueError as exc:
                error = str(exc)

            except Exception as exc:
    logger.exception("Lỗi khi nhận diện ảnh bằng Gemini")
    message = str(exc).upper()

                if "429" in message or "RESOURCE_EXHAUSTED" in message:
                    error = (
                        "Dịch vụ Gemini đang giới hạn yêu cầu. "
                        "Vui lòng thử lại sau."
                    )
                elif "503" in message or "UNAVAILABLE" in message:
                    error = (
                        "Dịch vụ AI đang bận. Vui lòng thử lại sau ít phút."
                    )
                else:
                    error = (
                        "Đã xảy ra lỗi khi nhận diện ảnh. "
                        "Vui lòng kiểm tra cấu hình Gemini và thử lại."
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
