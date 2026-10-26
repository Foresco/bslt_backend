# Выгрузка массива с данными об объекте
import logging
import json
from zipfile import ZipFile
from jsonserv.core.fileutils import get_report_template_path, get_temp_file_path, prepare_filename
from jsonserv.core.report import BaseReportClass
from jsonserv.pdm.models import PartObject


class ReportClass(BaseReportClass):
    file_name_json = "export.json"  # Имя файла с данными всегда одинаковое
    file_name_json_path = get_temp_file_path(file_name_json)  # Имя файла с данными всегда одинаковое

    def prepare_report_file(self):
            """Основной метод формирования файла-отчета"""
            row_id = self.request.GET.get('id', 0)  # Получаем идентификатор объекта из параметров
            if row_id:
                obj = PartObject.objects.get(pk=row_id)
                if obj:
                     # Имя итогового файла                     
                     zip_file_name = get_temp_file_path(f"{prepare_filename(obj.code)}.zip")
                     #  Формируем json-массив с данными
                     all_item_ids = list()  # Список для сбора выгруженных id
                     obj_json = obj.to_json(all_item_ids)
                     #  Выбираей из найденных объектов ссылки на файлы
                     files_to_export = dict()
                     for i in obj_json:
                         if (i['model'] == 'DigitalFile'):
                             files_to_export[i['src']] = i['file_path']   
                     # Записываем массов в файл
                     with open(ReportClass.file_name_json_path, 'w', encoding='utf-8') as json_file:
                          json.dump(obj_json, json_file)
                     #  Упаковываем файл в архив
                     zip_obj = ZipFile(zip_file_name, 'w')
                     zip_obj.write(ReportClass.file_name_json_path, ReportClass.file_name_json)
                     # Добавляем ссылки на все найденные файлы
                     for key in files_to_export.keys():
                          zip_obj.write(files_to_export[key], key)
                     zip_obj.close()

            # Возвращаем результат работы
            return zip_file_name
