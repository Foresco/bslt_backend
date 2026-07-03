# Команда Наследование данных из другой Базальты
import json
from django.core.management.base import BaseCommand

from jsonserv.exchange.exchange_utils import ModelsDispatcher


class Command(BaseCommand):
    help = 'Export data from Basalta database'

    def __init__(self):
        self.item_id = 1  # Идентификатор выгружаемого объекта
        self.model_name = 'PartLink'  # Имя выгружаемой модели
        self.output_file = 'temp/aaa.json'
        super().__init__()

    def add_arguments(self, parser):
        # Обязательные аргументы
        parser.add_argument('model_name', type=str, help='Наименование модели')
        parser.add_argument('item_id', type=int, help='Идентификатор объекта')

    def handle(self, *args, **options):
        self.item_id = options['item_id']
        self.model_name = options['model_name']

        # Получаем класс модели
        if self.model_name:
            instance = ModelsDispatcher.get_entity_class_by_entity_name(self.model_name)  # Получаем модель
        # Получаем экземпляр модели
        item = instance.objects.get(pk=self.item_id)
        # Вызываем метод экспорта
        json_arr = json.dumps(item.to_json())
        # Сохраняем результат в файл
        with open(self.output_file, 'w') as f:
            print(self.output_file)
            f.write(json_arr)
