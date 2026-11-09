# Выгрузка массива с данными
from zipfile import ZipFile
import os
import logging

from jsonserv.core.report import BaseReportClass
from jsonserv.core.fileutils import get_temp_file_path, get_import_file_path, handle_uploaded_file
from jsonserv.exchange.exchange_utils import DataImporter  # Класс импорта данных


logger = logging.getLogger('import')


class ReportClass(BaseReportClass):
    file_name_txt = "import.txt"  # Имя файла с результатом всегда одинаковое
    file_name_json_path = get_temp_file_path(file_name_txt)  # Путь к файлу с результатом всегда одинаковый

    def __init__(self, request):
        self.importer = DataImporter()  # Создаем класс импорта
        self.session_id = request.session.get('user_session_id', 1) # Идентификатор сессии
        super().__init__(request)

    def prepare_report_file(self):
        """Основной метод формирования файла-отчета"""
        # Получаем файл, переданный в форме
        file_name = ''
        imp_file = self.request.data.get('file', None)  # Получаем переданный файл
        if imp_file:
            file_name = imp_file.name  # Получаем имя переданного файл

        if file_name:
            src = get_temp_file_path(file_name)  # Каталог и имя для временного сохранения файла
            # перенос файла во временный каталог
            if handle_uploaded_file(imp_file, src):
                logger.info('Перенос файла во временное хранилище осуществлен')
                # Проверяем, что это zip-архив
                name, ext = os.path.splitext(file_name)
                if ext == '.zip':
                    # Распаковываем файл во временный каталог
                    with ZipFile(src, 'r') as zip_ref:
                        zip_ref.extractall(get_import_file_path(''))  # В каталог import
                    logger.info('Распаковка архива выполнена')
                    # Находим файл export.json# Открываем основной файл json
                    main_file_path = get_import_file_path('export.json')
                    if os.path.exists(main_file_path):  # Нужный файл существует
                        # Устанавливаем сессию для класса импорта
                        self.importer.set_session_id(self.session_id)
                        self.importer.set_session()
                        # Устанавливаем основной каталог
                        self.importer.set_src_dir(get_import_file_path(''))
                        # Загружаем данные из основного файла json
                        self.importer.import_file_content(main_file_path)
                    else:
                        logger.error('Переданный архив не содержит основной файл export.json')
                else:
                    logger.error(f'Переданный файл не является архивом {ext}')

            else:
                logger.error('Перенос файла '+self.request.data['filename']+' во временное хранилище не осуществлен')
        else:
            logger.error('Файл для импорта не передан')

        # Возвращаем результат работы
        return logging.getLoggerClass().root.handlers[0].baseFilename  # ReportClass.file_name_txt





