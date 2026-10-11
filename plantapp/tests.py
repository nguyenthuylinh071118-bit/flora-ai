from django.shortcuts import render
from .ai_service import recognize_and_get_plant


def home(request):
    plant = None
    error = None

    if request.method == "POST":
        image_file = request.FILES.get("image")

        if image_file:
            plant = recognize_and_get_plant(image_file)

            if plant is None:
                error = "Không nhận diện được loài cây hoặc chưa có thông tin trong cơ sở dữ liệu."
        else:
            error = "Vui lòng chọn một hình ảnh."

    return render(
        request,
        "plantapp/home.html",
        {
            "plant": plant,
            "error": error,
        },
    )