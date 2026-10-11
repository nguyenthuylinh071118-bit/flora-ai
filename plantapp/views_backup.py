from django.shortcuts import render

from .ai_service import recognize_plant
from .models import Plant, PlantComparison, QuizQuestion


def home(request):

    plant = None
    error = None

    comparisons = []
    quiz_questions = []

    ai_name = None


    if request.method == "POST":

        image_file = request.FILES.get("image")


        if image_file:

            try:

                ai_name = recognize_plant(
                    image_file
                )


                if ai_name:

                    try:

                        plant = Plant.objects.get(
                            name=ai_name
                        )


                        comparisons = (
                            PlantComparison.objects
                            .filter(plant=plant)
                            .select_related(
                                "compared_plant"
                            )
                        )


                        quiz_questions = (
                            QuizQuestion.objects
                            .filter(plant=plant)
                        )


                    except Plant.DoesNotExist:

                        error = (
                            f"AI nhận diện được {ai_name}, "
                            "nhưng cây này chưa có "
                            "trong cơ sở dữ liệu."
                        )


                else:

                    error = (
                        "Không thể xác định loài cây "
                        "từ hình ảnh."
                    )


            except Exception as e:

                error_message = str(e)


                if (
                    "429" in error_message
                    or
                    "RESOURCE_EXHAUSTED"
                    in error_message
                ):

                    error = (
                        "⚠️ Hệ thống AI đã hết lượt "
                        "nhận diện trong thời gian hiện tại. "
                        "Vui lòng thử lại sau khi hạn mức "
                        "được khôi phục."
                    )


                elif (
                    "503" in error_message
                    or
                    "UNAVAILABLE"
                    in error_message
                ):

                    error = (
                        "⚠️ Hệ thống AI đang quá tải "
                        "tạm thời. Vui lòng thử lại "
                        "sau ít phút."
                    )


                else:

                    error = (
                        "❌ Đã xảy ra lỗi khi nhận diện "
                        "hình ảnh. Vui lòng thử lại."
                    )


        else:

            error = (
                "Vui lòng chọn một hình ảnh."
            )


    return render(

        request,

        "plantapp/home.html",

        {
            "plant": plant,

            "ai_name": ai_name,

            "comparisons": comparisons,

            "quiz_questions": quiz_questions,

            "error": error,
        }
    )