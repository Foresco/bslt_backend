# Выгрузка массива с данными
from zipfile import ZipFile
import logging

from jsonserv.core.report import BaseReportClass
from jsonserv.core.fileutils import get_temp_file_path, prepare_filename, handle_uploaded_file
from jsonserv.exchange.exchange_utils import DataImporter  # Класс импорта данных


logger = logging.getLogger('basalta')


class ReportClass(BaseReportClass):
    file_name_txt = "import.txt"  # Имя файла с результатом всегда одинаковое
    file_name_json_path = get_temp_file_path(file_name_txt)  # Путь к файлу с результатом всегда одинаковый

    def __init__(self):
        self.importer = DataImporter()  # Создаем класс импорта
        super().__init__()


    def prepare_report_file(self):
        """Основной метод формирования файла-отчета"""
        # Получаем файл, переданный в форме
        file_name = self.request.GET.get('file_name', None)  # Получаем переданный файл

        # Если это файл и zip-файл
        if file_name:
            src = get_temp_file_path(file_name)  # Каталог и имя для временного сохранения файла
            # перенос файла во временный каталог
            if handle_uploaded_file(self.request.data['file'], src):
                logger.info('Перенос файла во временное хранилище осуществлен')
                # Распаковываем файл во временный каталог
                pass
                # Открываем основной файл json


                #
        # СОхраняем лог обработки в файл

        # Возвращаем результат работы
        return ReportClass.file_name_txt





