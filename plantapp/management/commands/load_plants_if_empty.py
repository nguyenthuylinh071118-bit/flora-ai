from django.core.management import call_command
from django.core.management.base import BaseCommand
from plantapp.models import Plant


class Command(BaseCommand):
    help = "Nap du lieu cay tu fixture neu co so du lieu chua co cay nao"

    def handle(self, *args, **options):
        count = Plant.objects.count()

        if count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"Da co {count} ban ghi cay; bo qua nap fixture."
                )
            )
            return

        call_command("loaddata", "plants")
        self.stdout.write(
            self.style.SUCCESS("Da nap fixture du lieu cay thanh cong.")
        )
