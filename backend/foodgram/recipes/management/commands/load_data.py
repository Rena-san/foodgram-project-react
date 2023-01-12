import json

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient

FILE_PATH = '/data/ingredients.json'
DIR_PATH = settings.BASE_DIR


class Command(BaseCommand):
    def handle(self, *args, **options):
        with open((DIR_PATH + FILE_PATH), encoding='utf-8') as f:
            data = json.load(f)

            for item in data:
                Ingredient.objects.create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
            self.stdout.write(self.style.SUCCESS('Ингрeдиенты загружены!'))
