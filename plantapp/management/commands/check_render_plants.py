from django.core.management.base import BaseCommand
from plantapp.models import Plant


class Command(BaseCommand):
    help = "Kiểm tra danh sách cây trong cơ sở dữ liệu"

    def handle(self, *args, **options):
        plants = Plant.objects.order_by("name").values_list(
            "name", flat=True
        )

        self.stdout.write("=== DANH SACH CAY ===")
        for name in plants:
            self.stdout.write(str(name))

        self.stdout.write(
            f"Tong so cay: {Plant.objects.count()}"
        )