# Команда Наследование данных из сторонней базы данных
from datetime import datetime
from django.core.management.base import BaseCommand
from jsonserv.basaltalegasy.models import Exporter  # Класс экспорта моделей источника
from jsonserv.exchange.exchange_utils import DataImporter  # Класс импорта данных
# from jsonserv.exchange.models import ExternalPartner, ExchangeSession, ExternalID  # Для фиксации соответствтий
from django.core.paginator import Paginator

# В параметрах команды указывается имя наследуемой базы, например  basaltalegasy
# Это каталог в каталоге basaltalegasy (потом можно будет перенести)
# Также в параметрах передается имя сторонней базы, с которой будет устанавливаться соответствие объектов
# Если оно не передано, то соответствие не устанавливается
# Параметр Идентификатор сессии


class Command(BaseCommand):
    help = 'Import data from legacy database'

    def __init__(self):
        self.importer = DataImporter()  # Создаем класс импорта
        self.exporter = Exporter()  # Создаем класс экспорта
        self.page_size = 1000  # Количество объектов в одном
        self.page_number = 1  # Счетчик экспортированных массивов
        self.only_page_number = 0  # Номер единственного, предназначенного для импорта пакета
        self.start_number = 1  # Номер начального пакета
        self.model_name = ''  # Имя выгружаемой модели
        self.check_only = False
        super().__init__()

    def add_arguments(self, parser):
        # Обязательные аргументы
        # Идентификатор сессии
        parser.add_argument('session_id', type=int, help='Идентификатор сессии')
        # Именованные (дополнительные) аргументы
        # parser.add_argument('--source', action='store', default='basaltalegasy', nargs='?',
        #                     help='Имя базы данных-источника')
        # parser.add_argument('--save_links', action='store_true', default=False,
        #                     help='Создавать связи с исходной базой-источником')
        parser.add_argument('--check_only', action='store_true', default=False,
                            help='Не выполнять импорт, только проверить выгрузку')
        parser.add_argument('--package', action='store', type=int, nargs='?', default=0,
                            help='Номер импортируемого пакета')
        parser.add_argument('--from', action='store', type=int, nargs='?', default=1,
                            help='Начальный номер импортируемого пакета')

    def handle(self, *args, **options):
        # Параметр ExternalPartner берем из параметров запуска команды
        # print(options)
        session_id = options['session_id']
        if not session_id:
            self.importer.write_to_log('error', 'Не указан идентификатор сессии')
            return
        else:
            self.importer.set_session_id(session_id)
            self.importer.set_session()
        self.only_page_number = options['package']
        self.start_number = options['from']
        self.check_only = options['check_only']
        entities = self.exporter.list_to_export()  # Список экспортируемых сущностей
        self.importer.write_to_log('info', 'Готовим данные для импорта')
        # Перебор всех сущностей в списке
        for entity in entities:
            self.model_name = entity._meta.verbose_name.title()
            self.importer.write_to_log('info', 'Готовим ' + self.model_name)
            self.export_entity_items(entity, options)

    def import_page(self, paginator):
        """Импорт указанной страницы исходного массива"""
        print(f'Пакет {self.page_number} из {paginator.num_pages} начало {datetime.now().strftime("%H:%M:%S")}')
        self.importer.clear()  # Очистка внутреннх массивов от ранее импортированных данных
        # Перенос (экспорт) всех сущностей во временный массив для импорта
        page = paginator.get_page(self.page_number)
        for entity_item in page:
            # Получаем свойства объекта из исходной модели
            list_to_import = entity_item.to_dict()  # В общем случае результат - список описаний нескольких объектов
            if list_to_import:
                for item in list_to_import:  # Перебираем весь список
                    result = self.importer.add_to_load(item)
        if not self.check_only:
            # Импортируем загруженный массив
            self.importer.import_loaded()
            # if options['save_links']:
            #     # Записываем соответствие ссылок
            #     self.importer.set_external_links()
        else:
            # Сохраняем массив в файл
            self.importer.dump_loaded()

    def export_entity_items(self, entity, options):
        print(entity._meta.verbose_name.title())
        paginator = Paginator(entity.objects.all(), self.page_size)  # Длинные массивы дробятся на части
        pages_count = paginator.num_pages
        if self.only_page_number:  # Если указан единственный пакет для импорта
            self.page_number = self.only_page_number
            self.import_page(paginator)
        else:
            for self.page_number in range(self.start_number, pages_count+1):
                self.import_page(paginator)
