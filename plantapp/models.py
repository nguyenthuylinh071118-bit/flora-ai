from django.db import models


class Plant(models.Model):

    name = models.CharField(
        "Tên cây",
        max_length=200,
        unique=True
    )

    scientific_name = models.CharField(
        "Tên khoa học",
        max_length=200,
        blank=True
    )

    phylum = models.CharField(
        "Ngành",
        max_length=200,
        blank=True
    )

    class_name = models.CharField(
        "Lớp",
        max_length=200,
        blank=True
    )

    order = models.CharField(
        "Bộ",
        max_length=200,
        blank=True
    )

    family = models.CharField(
        "Họ",
        max_length=200,
        blank=True
    )

    genus = models.CharField(
        "Chi",
        max_length=200,
        blank=True
    )

    species = models.CharField(
        "Loài",
        max_length=200,
        blank=True
    )

    description = models.TextField(
        "Mô tả chung",
        blank=True
    )

    characteristics = models.TextField(
        "Đặc điểm",
        blank=True
    )
    identification_clues = models.TextField(
    "Dấu hiệu nhận diện",
    blank=True
    )

    stem = models.TextField(
        "Thân",
        blank=True
    )

    root = models.TextField(
        "Rễ",
        blank=True
    )

    leaf = models.TextField(
        "Lá",
        blank=True
    )

    flower = models.TextField(
        "Hoa",
        blank=True
    )

    fruit = models.TextField(
        "Quả",
        blank=True
    )

    seed = models.TextField(
        "Hạt",
        blank=True
    )

    flower_formula = models.TextField(
        "Công thức hoa",
        blank=True
    )

    habitat = models.TextField(
        "Môi trường sống",
        blank=True
    )

    distribution = models.TextField(
        "Phân bố",
        blank=True
    )

    role = models.TextField(
        "Vai trò",
        blank=True
    )

    uses = models.TextField(
        "Công dụng",
        blank=True
    )

    harmful = models.BooleanField(
        "Gây hại",
        default=False
    )

    image = models.ImageField(
        "Hình ảnh",
        upload_to="plants/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        "Ngày thêm",
        auto_now_add=True
    )

    def __str__(self):
        return self.name


class PlantComparison(models.Model):

    plant = models.ForeignKey(
        Plant,
        on_delete=models.CASCADE,
        related_name="comparisons",
        verbose_name="Cây chính"
    )

    compared_plant = models.ForeignKey(
        Plant,
        on_delete=models.CASCADE,
        related_name="compared_with",
        verbose_name="Cây dễ nhầm"
    )

    differences = models.TextField(
        "Đặc điểm phân biệt",
        blank=True
    )

    created_at = models.DateTimeField(
        "Ngày thêm",
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Loài dễ nhầm"
        verbose_name_plural = "Loài dễ nhầm"

    def __str__(self):
        return f"{self.plant.name} - {self.compared_plant.name}"


class QuizQuestion(models.Model):

    plant = models.ForeignKey(
        Plant,
        on_delete=models.CASCADE,
        related_name="quiz_questions",
        verbose_name="Cây"
    )

    question = models.TextField(
        "Câu hỏi"
    )

    option_a = models.CharField(
        "Đáp án A",
        max_length=500
    )

    option_b = models.CharField(
        "Đáp án B",
        max_length=500
    )

    option_c = models.CharField(
        "Đáp án C",
        max_length=500
    )

    option_d = models.CharField(
        "Đáp án D",
        max_length=500
    )

    correct_answer = models.CharField(
        "Đáp án đúng",
        max_length=1
    )

    explanation = models.TextField(
        "Giải thích đáp án",
        blank=True
    )

    created_at = models.DateTimeField(
        "Ngày thêm",
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Câu hỏi kiểm tra"
        verbose_name_plural = "Câu hỏi kiểm tra"

    def __str__(self):
        return self.question

class DailyRecognitionQuota(models.Model):
    """Hạn mức nhận diện dùng chung cho toàn website."""

    day = models.DateField("Ngày áp dụng", unique=True)
    used = models.PositiveIntegerField(
        "Số lượt đã sử dụng",
        default=0,
    )

    LIMIT = 1500

    class Meta:
        verbose_name = "Hạn mức nhận diện theo ngày"
        verbose_name_plural = "Hạn mức nhận diện theo ngày"

    def __str__(self):
        return f"{self.day}: {self.used}/{self.LIMIT}"