# Отчет по заданиям работникам
import xlwt

from jsonserv.core.fileutils import get_mime_type, get_temp_file_path
from jsonserv.core.report import BaseReportClass
from jsonserv.manufacture.models import WorkerReportConsist


class ReportClass(BaseReportClass):
    filename = "workertaskreport.xls"

    def export_users_xls(self):
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Отчет по заданиям')
        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = ['Дата', 'Смена', 'Оператор', 'Деталь', 'Операция', 'Количество', 'Брак', 'Время', 'Наладка',
                   'Комментарий']

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)

        font_style = xlwt.XFStyle()

        rows = WorkerReportConsist.objects.all().values_list(
            'report_date',
            'work_shift__list_value',
            'task_link__worker__user_name',
            'task_link__prod_order_link__child__code',
            'task_link__tp_row__operation__operation_name',
            'quantity',
            'bad_quantity',
            'work_time',
            'aux_time',
            'comment'
        )
        for row in rows:
            row_num += 1
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)

        # Сохраняем сформированный файл
        file_name = get_temp_file_path(self.filename)
        wb.save(file_name)
        return file_name

    def prepare_report_file(self):
        """Основной метод формирования файла-отчета"""
        # Формируем файл
        file_name = self.export_users_xls()
        # Возвращаем результат работы
        return file_name
