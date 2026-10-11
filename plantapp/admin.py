from django.contrib import admin
from .models import Plant, PlantComparison, QuizQuestion


@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "scientific_name",
        "family",
        "genus",
        "harmful",
        "created_at",
    )

    search_fields = (
        "name",
        "scientific_name",
        "family",
        "genus",
    )

    list_filter = (
        "harmful",
        "created_at",
    )

    fieldsets = (
        (
            "🌱 Thông tin cơ bản",
            {
                "fields": (
                    "name",
                    "scientific_name",
                    "image",
                )
            }
        ),

        (
            "🔬 Phân loại thực vật",
            {
                "fields": (
                    "phylum",
                    "class_name",
                    "order",
                    "family",
                    "genus",
                    "species",
                )
            }
        ),

        (
            "🌿 Đặc điểm hình thái",
            {
                "fields": (
                    "description",
                    "characteristics",
                    "identification_clues",
                    "stem",
                    "root",
                    "leaf",
                    "flower",
                    "fruit",
                    "seed",
                    "flower_formula",
                )
            }
        ),

        (
            "🌍 Sinh thái",
            {
                "fields": (
                    "habitat",
                    "distribution",
                    "role",
                )
            }
        ),

        (
            "💡 Giá trị và tác động",
            {
                "fields": (
                    "uses",
                    "harmful",
                )
            }
        ),

        (
            "📅 Thời gian",
            {
                "fields": (
                    "created_at",
                )
            }
        ),
    )

    readonly_fields = (
        "created_at",
    )


@admin.register(PlantComparison)
class PlantComparisonAdmin(admin.ModelAdmin):

    list_display = (
        "plant",
        "compared_plant",
        "created_at",
    )

    search_fields = (
        "plant__name",
        "compared_plant__name",
        "differences",
    )


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):

    list_display = (
        "plant",
        "question",
        "correct_answer",
        "created_at",
    )

    search_fields = (
        "plant__name",
        "question",
    )

    list_filter = (
        "correct_answer",
        "created_at",
    )