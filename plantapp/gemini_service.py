import json

from django.conf import settings
from google import genai
from google.genai import types


# Gemini chỉ được chọn trong 10 lớp cây đã quy định.
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


def recognize_with_gemini(image_bytes, mime_type):
    api_key = getattr(settings, "GEMINI_API_KEY", None)

    if not api_key:
        raise RuntimeError("Chưa cấu hình GEMINI_API_KEY trong file .env.")

    allowed_mime_types = {"image/jpeg", "image/png", "image/webp"}
    if mime_type not in allowed_mime_types:
        raise ValueError("Ảnh không được hỗ trợ. Vui lòng dùng JPG, PNG hoặc WEBP.")

    class_list = "\n".join(
        f"- {key}: {name}" for key, name in ALLOWED_CLASSES.items()
    )

    prompt = f'''
Bạn là hệ thống nhận diện thực vật qua hình ảnh.

Hãy phân tích hình ảnh và chọn đúng một lớp trong danh sách:
{class_list}

Nếu không đủ căn cứ để xác định cây thuộc một trong các lớp trên,
hãy trả về class_key là "unknown".
Không được tự tạo lớp mới.
Chỉ trả về JSON hợp lệ theo định dạng:
{{
  "class_key": "một khóa trong danh sách hoặc unknown",
  "reason": "giải thích ngắn gọn bằng tiếng Việt"
}}
'''

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
        contents=[
            prompt,
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0,
        ),
    )

    response_text = response.text
    if not response_text:
        raise RuntimeError("Gemini không trả về kết quả nhận diện.")

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Gemini trả về dữ liệu không hợp lệ.") from exc

    class_key = result.get("class_key")
    reason = str(result.get("reason", ""))

    if class_key == "unknown":
        return None, reason
    if class_key not in ALLOWED_CLASSES:
        raise RuntimeError("Gemini trả về lớp cây không được hỗ trợ.")

    return ALLOWED_CLASSES[class_key], reason
