# Модуль формирования отчета *Выгрузка файлов*
from os.path import join
import xlwt
from zipfile import ZipFile
import logging

from jsonserv.core.fileutils import get_sql_file_path, get_temp_file_path
from jsonserv.core.dbutils import execute_sql_from_file
from jsonserv.core.report import BaseReportClass
from jsonserv.core.models import Entity, UserSession
from jsonserv.pdm.models import PartObject
from jsonserv.docarchive.models import FileArchive
from jsonserv.docarchive.pdfutils import insert_text_to_pdf

logger = logging.getLogger('basalta')


class ReportClass(BaseReportClass):
    doc_types = {
        't1': '2',
        't2': '3',
        't3': '5',
        't4': '6',
        't5': '5',
        't6': '7'
    }

    def __init__(self, request):
        self.object_code = ''  # Обозначение объекта
        super().__init__(request)

    def prepare_params(self):
        """Подготовка параметров для запроса"""
        self.params['object_id'] = self.request.GET.get('object_id', 0)  # Идентификатор объекта
        if not self.params['object_id']:
            return
        # Определение обозначения объекта
        obj = PartObject.objects.get(pk=self.params['object_id'])
        self.object_code = obj.key_code  # Обозначение объекта
        dt = list()
        for key in self.doc_types:
            if self.request.GET.get(key, 'false') in ('true', 'True'):
                dt.append(self.doc_types[key])

        self.params['doc_types'] = ', '.join(dt)  # Типы документов, включаемые в отчет
        if self.request.GET.get('t10', False):  # Извещения
            self.params['notices'] = 1
        else:
            self.params['notices'] = 0
        self.params['archive'] = self.request.GET.get('archive', 1)  # Идентификатор архива
        # Информация о метке
        if self.request.GET.get('watermark', 'false') in ('true', 'True'):
            self.params['watermark'] = True
            self.params['stamp_date'] = self.request.GET.get('stamp_date', '')
            self.params['order_code'] = self.request.GET.get('order_code', '')
            if self.params['order_code']:
                a = Entity.objects.get(pk=self.params['order_code'])
                self.params['order_code'] = a.code

    def prepare_files(self):
        """Формирование списка файлов"""
        # Определение адреса архива
        logger.info(f'self.params["archive"] = {self.params["archive"]}')
        archive = FileArchive.objects.get(pk=self.params['archive'])
        core_directory = archive.core_directory
        logger.info(f'core_directory = {core_directory}')
        # Получение списка файлов
        sql_file = get_sql_file_path('docarchive', 'report_files.sql')
        rows = execute_sql_from_file(sql_file, self.params)
        files = dict()
        for row in rows:
            # Если указана вставка метки и это pdf
            if self.params.get("watermark", False) and row[0][-4:].lower() == '.pdf':
                inv_number = row[2]
                inv_date = row[3]
                wm_text = f"Инвентарный № {inv_number}; " if inv_number else ''
                wm_text += f"Дата присвоения и.н.: {inv_date}; " if inv_number else ''
                user_session_id = self.request.session.get('user_session_id', 0)
                user_session = UserSession.objects.get(pk=user_session_id)
                wm_text += f"Номер заказа: {self.params['order_code']}; Дата выдачи: {self.params['stamp_date']}; "
                wm_text += f"Архивариус: {user_session.user_profile_user_name}"
                # Формирование файла с меткой
                result_file = insert_text_to_pdf(join(core_directory, row[1], row[0]), wm_text, 3, 25)
                logger.info(f'В массив добавляем элемент {row[0]}: {result_file}')
                files[row[0]] = result_file
            else:
                files[row[0]] = join(core_directory, row[1], row[0])

        return files

    def prepare_specf(self, specif_file_name):
        """Формирование спецификации"""
        logger.info('Создание книги спецификации')
        # Создание книги
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Спецификация')
        row_num = 0

        # Стиль ячейки
        cell_style = xlwt.XFStyle()
        # Шрифт
        cell_style.font.bold = True
        # Границы
        # borders = xlwt.Borders()
        cell_style.borders.left = 1
        cell_style.borders.right = 1
        cell_style.borders.top = 1
        cell_style.borders.bottom = 1

        columns = {
            'Обозначение': 'object_code',
            'Наименование': 'object_name',
            'Количество': 'o_quant',
            'Вес (ориентировочно), кг': 'weight',
            'Материал': 'mater_code',
            'Группа': 'group_name',
            'Версия документа': 'version_num',
            'Номер извещения': 'notice_num',
            'Дата проведения извещения': 'notice_date',
            'Тип Изменения': 'change_type',
            'Номер изменения': 'change_num',
            'Обозначение файла чертежа': 'doc_code',
            'Примечание': 'remark',
            'Тип документа': 'doc_type'
        }

        # Заполнение шапки отчета
        col_num = 0
        logger.info('Заполнение шапки отчета спецификации')
        for key in columns:
            ws.write(row_num, col_num, key, cell_style)
            col_num += 1

        # Остальные строки
        cell_style.font.bold = False

        # Получение списка объектов файлов
        logger.info('Получение списка объектов файлов')
        sql_file = get_sql_file_path('docarchive', 'report_files_objects.sql')
        rows = execute_sql_from_file(sql_file, self.params)
        for row in rows:
            row_num += 1
            col_num = 0
            for key in columns:
                ws.write(row_num, col_num, row[col_num], cell_style)
                col_num += 1
        # Сохраняем сформированный файл
        spec_file = get_temp_file_path(specif_file_name)
        logger.info(f'Сохраняем сформированный файл спецификации {spec_file}')
        wb.save(spec_file)
        return spec_file

    def prepare_report_file(self):
        self.prepare_params()  # Получение параметров отчета
        files_list = self.prepare_files()  # Формируем список файлов

        files_list[f'{self.object_code}.xls'] = self.prepare_specf(f'{self.object_code}.xls')  # Формируем спецификацию

        # Формирование zip-архива
        zip_path = get_temp_file_path(f'{self.object_code}.zip')  # Расположение файла-архива
        zip_obj = ZipFile(zip_path, 'w')
        for file_name in files_list:
            zip_obj.write(files_list[file_name], file_name)  # Добавляем собранные файлы
        zip_obj.close()

        # Возвращаем результат работы
        return zip_path
