# Команда импорта данных в RawRows

import os.path
import json
from datetime import datetime

from django.core.management.base import BaseCommand
from django.conf import settings  # для обращения к настройкам

from jsonserv.exchange.sources.sources import SourceExcelx

from jsonserv.exchange.exchange_utils import DataImporter  # Класс импорта данных

from jsonserv.mdm.models import RawProperty


class Command(BaseCommand):
    help = 'Import data into raw rows'

    def __init__(self):
        self.importer = DataImporter()  # Создаем класс импорта
        self.row_number = 0  # Счетчик экспортированных строк
        self.start_number = 1  # Номер начальной строки
        self.package_size = 1000  # Размер загружаемого пакета в строках
        self.package_number = 1  # Номер загружаемого пакета
        self.check_only = False
        self.settings_file = ''  # Имя файла настроек
        self.source_file = ''  # Имя файла с исходными данными
        self.sheet_name = ''  # Имя листа с исходными данными
        self.fields = dict()  # Словарь для трансляции основных полей
        self.exclude = list()  # Список исключаемых полей
        self.filter = dict() # Словарь полей для фильтрации
        self.prop_fields = RawProperty.get_field_ids()  # Словарь для трансляции дополнительных полей

        super().__init__()

    def add_arguments(self, parser):
        # Обязательные аргументы
        parser.add_argument('session_id', type=int, help='Идентификатор сессии')
        parser.add_argument('settings_file', type=str, help='Имя файла с json-настройками импорта')
        # Именованные (дополнительные) аргументы
        parser.add_argument('--check_only', action='store_true', default=False,
                            help='Не выполнять импорт, только проверить выгрузку')
        parser.add_argument('--from', action='store', type=int, default=1,
                            help='Начальный номер импортируемой строки (с учетом строки-шапки)')

    def load_options(self, options):
        """Загрузка параметров команды"""
        session_id = options['session_id']
        if not session_id:
            self.importer.write_to_log('error', 'В параметрах запуска не указан идентификатор сессии')
            return False
        else:
            self.importer.set_session_id(session_id)
            self.importer.set_session()
        self.settings_file = options['settings_file']
        if not self.settings_file:
            self.importer.write_to_log('error', 'В параметрах запуска не указан файл настроек')
            return False
        # Указываем точное расположение файла
        self.settings_file = os.path.join(getattr(settings, 'BASE_DIR', ''), 'jsonserv', 'mdm', 'imp_settings', self.settings_file)
        self.start_number = options['from']
        self.check_only = options['check_only']
        return True

    def load_settings(self):
        """Загрузка настроек из файла и проверка"""
        self.importer.write_to_log('info', f'Загружаем настройки из файла {self.settings_file}')
        with open(self.settings_file, encoding='utf-8') as json_data:
            dct = json.load(json_data)
            self.source_file = dct.get('source_file', '')
            if not self.source_file:
                self.importer.write_to_log('error', 'В файле настроек не указано имя файла с данными (source_file)')
                return False
            # Формируем полный путь
            self.source_file = os.path.join(getattr(settings, 'TEMP_DIR', ''), self.source_file)
            self.sheet_name = dct.get('sheet_name', '')
            if not self.sheet_name:
                self.importer.write_to_log('error', 'В файле настроек не указано имя листа с данными (sheet_name)')
                return False
            self.fields = dct.get('fields', '')
            if not self.fields:
                self.importer.write_to_log('error', 'В файле настроек не указан словарь с ключевыми полями (fields)')
                return False
            self.exclude = dct.get('exclude', list())
            self.filter = dct.get('filter', dict())
            return True

    def check_row(self, row):
        for key in self.filter:
            if row[key] == self.filter[key]:
                # Если значение фильтрации совпало
                return False
        return True

    def prepare_dict(self, row, row_num):
        """Подготовка словаря для загрузки на основе строки"""
        dct = dict(model='RawRow', id=row_num)
        prop_dct = dict()

        for key in row:
            if row[key]:
                if key in self.fields: # Если это основное поле из настроек
                    # Заполняем обязательные поля на основе описания из настроек
                    dct[self.fields[key]] = row[key]
                elif key in self.exclude: # Если это поле исключается
                    continue
                else:
                    # Заполняем дополнительные поля
                    prop_dct[self.prop_fields[key]] = row[key]
        if prop_dct:
            dct['properties'] = prop_dct
        return [dct, ]

    def print_package(self):
        """Отображение сообщения о формируемом пакете"""
        print(f'Пакет {self.package_number} начало {datetime.now().strftime("%H:%M:%S")}')

    def handle(self, *args, **options):
        # print(options)
        self.importer.write_to_log('info', 'Разбираем параметры запуска')
        if not self.load_options(options):
            return
        self.importer.write_to_log('info', 'Загружаем настройки из файла')
        if not self.load_settings():
            return
        self.importer.write_to_log('info', 'Открываем файл с исходными данными')
        reader = SourceExcelx(file_name=self.source_file, sheet_name=self.sheet_name)
        reader.open()  # Открываем источник

        self.importer.write_to_log('info', 'Готовим данные для импорта')
        row_num = 0
        processed_row_num = 0
        package_row = 0
        self.print_package()
        # Перебираем строки в открывшемся файле
        for row in reader.row_get():
            row_num += 1
            if row_num <= self.start_number:
                continue  # Первую строку пропускаем (Там заголовок) или если в параметрах указано больше
            if self.check_row(row):  # Проверяем выполнение условий импорта
                # Формируем словарь со свойствами
                list_to_import = self.prepare_dict(row, row_num)
                processed_row_num += 1
                package_row += 1
            else:
                continue
            if list_to_import:
                for item in list_to_import:  # Перебираем весь список
                    result = self.importer.add_to_load(item)
            if package_row == self.package_size:
                # Если набрался пакет
                self.import_package()
                package_row = 0  # Обнуляем счетчик пакетов
                self.print_package()
        # Загружаем данные в базу
        self.import_package()
        print(f'Обработано строк {processed_row_num} ({row_num - 1})')
        reader.close()  # Закрываем источник

    def import_package(self):
        """Импорт пакета"""
        if self.importer.items_to_import:
            if not self.check_only:
                # Импортируем загруженный массив
                self.importer.import_loaded()
            else:
                # Сохраняем массив в файл
                self.importer.dump_loaded()
            self.package_number += 1

        self.importer.clear()  # Очистка внутренних массивов от ранее импортированных данных
