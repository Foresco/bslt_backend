# Команда экспорта данных в json-файл

import os.path
import json

from django.core.management.base import BaseCommand
from django.conf import settings  # для обращения к настройкам

from jsonserv.exchange.serializers import get_model_serializer
from jsonserv.exchange.exchange_utils import ModelsDispatcher


class Command(BaseCommand):
    help = 'Export data to file in json format'

    def add_arguments(self, parser):
        # Имя модели для экспорта
        parser.add_argument('model', type=str, nargs='?', help='Имя модели для экспорта')

    def handle(self, *args, **options):
        model_name = options['model']
        # Определение файла для записи
        temp_dir = getattr(settings, 'TEMP_DIR', '')
        file_name = os.path.join(temp_dir, model_name + '.json')

        # Получаем модель по названию
        try:
            source_model = ModelsDispatcher.get_entity_class_by_entity_name(model_name)
        except Exception as e:
            print(e)
            # TODO: Сделать нормальную обработку исключения
            return
        serializer = get_model_serializer(source_model)

        # queryset = source_model.objects.all()
        queryset = source_model.objects.filter(pk__in=(306, 748636, 748637, 748638)) # Только указанные объекты
        serializer = serializer(queryset, many=True)

        # Добавление имени модели к каждому элементу массива
        def model_add(item):
            item['model'] = model_name
            return item

        result_data = [model_add(v) for v in serializer.data]

        with open(file_name, 'w', encoding='utf-8') as json_file:
            json.dump(result_data, json_file)
