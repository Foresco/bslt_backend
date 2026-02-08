# Модуль формирования отчета Паспорт
from datetime import datetime
from docxtpl import DocxTemplate

from jsonserv.core.fileutils import get_report_template_path, get_temp_file_path, prepare_filename
from jsonserv.core.report import BaseReportClass
from jsonserv.manufacture.models import Shipment


class ReportClass(BaseReportClass):
    template_name = "passport1.docx"

    def prepare_report_file(self):
        """Основной метод формирования файла-отчета"""
        row_id = self.request.GET.get('id', 0)  # Получаем идентификатор строки из параметров
        if row_id:
            row = Shipment.objects.filter(pk=row_id).values(
                'prod_order_link__child__code',
                'prod_order_link__child__partobject__title',
                'prod_order_link__parent__prodorder__enterprise',
                'quantity'
            ).first()
            # Данные для заполнения шаблона
            context = {
                'code': row['prod_order_link__child__code'],
                'title': row['prod_order_link__child__partobject__title'],
                'quantity': round(row['quantity']),
                'year': datetime.today().year
            }
            if row['prod_order_link__parent__prodorder__enterprise'] and row[
                'prod_order_link__parent__prodorder__enterprise'] > 1:
                # Для других юрлиц другие наклейки на основе их идентификатора
                self.template_name = f"passport{row['prod_order_link__parent__prodorder__enterprise']}.docx"
            # Имя формируемого файла
            file_name = get_temp_file_path(f"Паспорт {prepare_filename(row['prod_order_link__child__code'])}.docx")
        else:
            # Формируем пустографку
            context = {'code': "", 'title': '', 'quantity': ""}
            file_name = get_temp_file_path("passport.docx")
        # Получаем шаблон
        doc = DocxTemplate(get_report_template_path('manufacture', self.template_name))
        # Заполняем шаблон
        doc.render(context)
        # Сохраняем
        doc.save(file_name)
        # Возвращаем результат работы
        return file_name
