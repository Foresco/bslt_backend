# Команда импорта данных из каталога с gtc-пакетом
from django.core.management.base import BaseCommand

from jsonserv.exchange.exchange_utils import DataImporter  # Класс импорта данных
from jsonserv.toolover.gtc.package_reader import PackageReader  # Класс чтения gtc-пакета


class Command(BaseCommand):
    help = 'Import tool data from gtc-packege'

    def __init__(self):
        self.importer = DataImporter()  # Создаем класс импорта
        self.prepare = False  # Признак, что не нужно загружать данные, а только подготовить массивы
        self.package_reader = None  # Просто инициализируем
        super().__init__()

    def add_arguments(self, parser):
        # Идентификатор сессии
        parser.add_argument('session_id', type=int, help='Import session identifier')
        # Имя каталога с пакетом для импорта
        parser.add_argument('dir_name', type=str, nargs='?', default='package',
                            help='Name source gtc-package directory')
        parser.add_argument('--prepare', action='store_true', help='Признак подготовки данных без импорта')

    def data_section_load(self, reader):
        """Универсальный загрузчик раздела данных
        reader - функция подготовки данных"""
        for package_data in reader(): # Чтение данных
            self.importer.clear()  # Очистка данных с предыдущего шага
            # Передача данных в импортер
            for node in package_data:
                result = self.importer.add_to_load(node)
                if result:  # Если при добавление была ошибка
                    print('Ошибка добавления в массив для импорта')
                    break

            if self.prepare:  # Если в парамтерах запуска указано --prepare
                # Сохраняем подготовленный массив в файл
                self.package_reader.dump_loaded()
            else:
                # Импортируем загруженный массив
                self.importer.import_loaded()

    def handle(self, *args, **options):
        self.importer.write_to_log('info', 'Определяем идентификатор сессии')
        session_id = options['session_id']
        self.prepare = options['prepare']
        if not session_id:
            self.importer.write_to_log('error', 'Не указан идентификатор сессии')
            return
        else:
            self.importer.set_session_id(session_id)
            self.importer.set_session()

        self.importer.write_to_log('info', 'Открываем файл с данными для импорта')
        dir_name = options['dir_name']
        if not dir_name:
            self.importer.write_to_log('error', 'Не указан каталог с данными для импорта')
            return

        self.importer.write_to_log('info', 'Импорт данных из каталога ' + dir_name)
        self.package_reader = PackageReader(dir_name)

        # Регистрация загружаемого пакета
        # TODO: Проверка, что пакет еще не загружался
        self.data_section_load(self.package_reader.package_meta_data_read)

        # Импорт классов
        self.data_section_load(self.package_reader.tool_classes_read)

        # Импорт ассортимента
        self.data_section_load(self.package_reader.package_assortment_read)
