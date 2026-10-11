from io import BytesIO
import time

from PIL import Image
from google import genai
from google.genai import types
from django.conf import settings

from .models import Plant


PLANT_LIST = [
    "Lan Mokara",
    "Hoa layon",
    "Vông mồng gà",
    "Cây muồng trâu",
    "Hoa bông trang",
    "Cây phượng",
    "Cây bưởi",
    "Cây chuối",
    "Hoa hồng",
    "Hoa sen",
]


def recognize_plant(image_file):

    total_start = time.time()

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY
    )

    # =========================
    # 1. ĐỌC VÀ TỐI ƯU ẢNH
    # =========================

    image_start = time.time()

    original_bytes = image_file.read()

    try:
        image = Image.open(
            BytesIO(original_bytes)
        )

        max_size = 1280

        image.thumbnail(
            (max_size, max_size),
            Image.Resampling.LANCZOS
        )

        if image.mode != "RGB":
            image = image.convert("RGB")

        output = BytesIO()

        image.save(
            output,
            format="JPEG",
            quality=85,
            optimize=True
        )

        image_bytes = output.getvalue()

    except Exception:
        image_bytes = original_bytes

    image_time = time.time() - image_start

    print(
        f"[GEMINI] Thời gian xử lý ảnh: "
        f"{image_time:.2f} giây"
    )

    print(
        f"[GEMINI] Kích thước ảnh gửi: "
        f"{len(image_bytes) / 1024:.1f} KB"
    )

    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type="image/jpeg",
    )

    prompt = f"""
Bạn là chuyên gia nhận diện thực vật từ hình ảnh.

Hãy quan sát toàn bộ hình ảnh và xác định chính xác loài thực vật.

Chỉ được chọn MỘT tên trong danh sách:

{", ".join(PLANT_LIST)}

Gợi ý nhận diện:
- Lan Mokara: hoa lan đặc trưng
- Hoa layon: hoa nhiều cánh đặc trưng
- Vông mồng gà: hoa dạng mào gà
- Cây muồng trâu: lá kép đặc trưng
- Hoa bông trang: cụm hoa nhỏ mọc thành đầu
- Cây phượng: lá kép lông chim, hoa phượng
- Cây bưởi: lá đơn, hoa trắng, quả bưởi
- Cây chuối: lá rất lớn, dài, gân song song
- Hoa hồng: nhiều cánh xếp lớp, thân thường có gai
- Hoa sen: lá tròn lớn, cây thủy sinh, hoa sen nhiều cánh

Chỉ trả về đúng một tên trong danh sách.
Nếu không xác định được, trả về KHONG_XAC_DINH.
Không giải thích.
Không trả về thông tin khác.
"""

    # =========================
    # 2. GỌI GEMINI
    # =========================

    gemini_start = time.time()

    max_retries = 2

    for attempt in range(max_retries):

        try:

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=[
                    image_part,
                    prompt,
                ],
            )

            break

        except Exception as e:

            if (
                "503" in str(e)
                and attempt < max_retries - 1
            ):

                wait_time = 3

                print(
                    "Gemini đang bận. "
                    f"Thử lại sau {wait_time} giây..."
                )

                time.sleep(wait_time)

            else:
                raise

    gemini_time = time.time() - gemini_start

    print(
        f"[GEMINI] Thời gian gọi API: "
        f"{gemini_time:.2f} giây"
    )

    # =========================
    # 3. KẾT QUẢ
    # =========================

    result = response.text.strip()

    total_time = time.time() - total_start

    print(
        f"[GEMINI] Tổng thời gian: "
        f"{total_time:.2f} giây"
    )

    print(
        f"[GEMINI] Kết quả: {result}"
    )

    if result not in PLANT_LIST:
        return None

    return result


def recognize_and_get_plant(image_file):

    plant_name = recognize_plant(
        image_file
    )

    if not plant_name:
        return None

    try:

        return Plant.objects.get(
            name=plant_name
        )

    except Plant.DoesNotExist:

        return None