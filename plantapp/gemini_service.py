
import io
import json
import time

from django.conf import settings
from google import genai
from google.genai import types, errors
from PIL import Image, ImageOps


# Thu nhỏ ảnh để giảm dung lượng gửi lên Gemini.
def optimize_image(image_bytes):
    with Image.open(io.BytesIO(image_bytes)) as image:
        image = ImageOps.exif_transpose(image)
        image.thumbnail((1280, 1280))

        if image.mode not in ("RGB", "L"):
            if "A" in image.getbands():
                rgba = image.convert("RGBA")
                background = Image.new("RGB", rgba.size, "white")
                background.paste(
                    rgba,
                    mask=rgba.getchannel("A"),
                )
                image = background
            else:
                image = image.convert("RGB")

        if image.mode == "L":
            image = image.convert("RGB")

        output = io.BytesIO()
        image.save(
            output,
            format="JPEG",
            quality=80,
            optimize=True,
        )
        return output.getvalue(), "image/jpeg"


# Chỉ nhận diện trong 10 lớp cây được hỗ trợ.
ALLOWED_CLASSES = {
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


def call_gemini_with_retry(client, model, prompt, image_bytes, mime_type):
    """Thử tối đa 3 lần khi API gặp lỗi tạm thời."""

    for attempt in range(3):
        try:
            return client.models.generate_content(
                model=model,
                contents=[
                    prompt,
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=mime_type,
                    ),
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0,
                ),
            )

        except (errors.ServerError, errors.ClientError) as exc:
            status_code = (
                getattr(exc, "code", None)
                or getattr(exc, "status_code", None)
            )

            # Chỉ thử lại với lỗi có khả năng tạm thời.
            if status_code not in (429, 500, 502, 503, 504):
                raise

            # Đã hết số lần thử thì trả lỗi về cho phần xử lý bên ngoài.
            if attempt == 2:
                raise

            # Chờ 2 giây, sau đó 4 giây trước lần thử tiếp theo.
            time.sleep(2 ** (attempt + 1))

    raise RuntimeError("Không thể kết nối Gemini sau nhiều lần thử.")


def recognize_with_gemini(image_bytes, mime_type):
    api_key = getattr(settings, "GEMINI_API_KEY", None)

    if not api_key:
        raise RuntimeError("Chưa cấu hình GEMINI_API_KEY.")

    allowed_mime_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if mime_type not in allowed_mime_types:
        raise ValueError(
            "Ảnh không được hỗ trợ. Vui lòng dùng JPG, PNG hoặc WEBP."
        )

    image_bytes, mime_type = optimize_image(image_bytes)

    class_list = "\n".join(
        f"- {key}: {name}"
        for key, name in ALLOWED_CLASSES.items()
    )

    prompt = f"""
Bạn là hệ thống nhận diện thực vật qua hình ảnh.

Hãy chọn đúng một lớp trong danh sách sau:
{class_list}

Nếu không đủ căn cứ để nhận diện, hãy trả về class_key là "unknown".
Không được tự tạo lớp mới.

Chỉ trả về JSON hợp lệ theo cấu trúc:
{{
    "class_key": "một khóa trong danh sách hoặc unknown",
    "reason": "giải thích ngắn gọn bằng tiếng Việt"
}}
"""

    client = genai.Client(api_key=api_key)
    model = getattr(
        settings,
        "GEMINI_MODEL",
        "gemini-3.8-flash",
    )

    response = call_gemini_with_retry(
        client=client,
        model=model,
        prompt=prompt,
        image_bytes=image_bytes,
        mime_type=mime_type,
    )

    response_text = response.text

    if not response_text:
        raise RuntimeError("Gemini không trả về kết quả nhận diện.")

    try:
        result = json.loads(response_text)
    except (json.JSONDecodeError, TypeError) as exc:
        raise RuntimeError(
            "Gemini trả về dữ liệu không hợp lệ."
        ) from exc

    if not isinstance(result, dict):
        raise RuntimeError("Kết quả Gemini không đúng định dạng JSON.")

    class_key = result.get("class_key")
    reason = str(result.get("reason", ""))

    if class_key == "unknown":
        return None, reason

    if class_key not in ALLOWED_CLASSES:
        raise RuntimeError("Gemini trả về lớp cây không được hỗ trợ.")

    return ALLOWED_CLASSES[class_key], reason
