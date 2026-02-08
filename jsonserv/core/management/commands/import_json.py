# Команда импорта данных из json-файла

import json
import os.path

from django.core.management.base import BaseCommand

from jsonserv.exchange.exchange_utils import DataImporter  # Класс импорта данных
from jsonserv.exchange.models import ExternalPartner


class Command(BaseCommand):
    help = 'Import data from file in json format'

    def __init__(self):
        self.importer = DataImporter()  # Создаем класс импорта
        super().__init__()

    def add_arguments(self, parser):
        # Идентификатор сессии
        parser.add_argument('session_id', type=int, help='Идентификатор сессии')
        # Идентификатор партнера
        parser.add_argument('partner_id', type=int, nargs='?', help='Идентификатор партнера-источника данных')
        # Имя файла для импорта
        parser.add_argument('filename', type=str, nargs='?', default='strings.json',
                            help='Имя json-файла с данными для импорта')

    def handle(self, *args, **options):
        self.importer.write_to_log('info', 'Определяем идентификатор сессии')
        # print('handle')
        # print(options)
        session_id = options['session_id']
        if not session_id:
            self.importer.write_to_log('error', 'Не указан идентификатор сессии')
            return
        else:
            self.importer.set_session_id(session_id)
            self.importer.set_session()

        partner_id = options['partner_id']
        if partner_id:
            self.importer.partner = ExternalPartner.objects.get(pk=partner_id)

        self.importer.write_to_log('info', 'Открываем файл с данными для импорта')
        filename = options['filename']
        if not filename:
            self.importer.write_to_log('error', 'Не указан файл с данными для импорта')
            return

        # Открытие файла
        if not os.path.isabs(filename):  # Если путь не абсолютный
            filename = os.path.join('jsonserv', filename)
        self.importer.write_to_log('info', 'Импорт данных из файла ' + filename)

        if not os.path.isfile(filename):
            self.importer.write_to_log('info', 'Не найден файл ' + filename)
            print('Не найден файл', filename)
            return

        # TODO: Убрать отсюда загрузку содержимого файла
        with open(filename, encoding='utf-8') as json_data:
            nodes = json.load(json_data)
            # Перенос объектов для импорта во внутренний словарь
            for node in nodes:
                self.importer.add_to_load(node)

        # Импортируем загруженный массив
        self.importer.import_loaded()
