# Отчет Свойства объекта справочника
from jsonserv.core.report import BaseReportClass
from jsonserv.core.views import type_fields
from jsonserv.core.models_dispatcher import ModelsDispatcher
from jsonserv.pdm.serializers import PartObjectSerializerDetailed


class ReportClass(BaseReportClass):

    def __init__(self, request):
        super().__init__(request)
        self.file_name = "Свойства объекта.xls"
        self.gen_code_file_name()  # Генерируем отчету имя на основе обозначения объекта

        # Встроенные форматы ячеек
        self.norma_style = self.get_cell_style()
        self.norma_style.num_format_str = '# ##0.000'

        # 1000 единиц здесь = 3,715 в Excel
        
        self.columns = {
            'Свойство': {
                'field': 'prop_name',
                'width': 10000
            },
            'Значение': {
                'field': 'prop_value',
                'width': 8000
            }            
        }

        self.headers = []

    def gen_file_name(self):
        self.gen_code_file_name()

    def get_report_rows(self):
        """Получение данных для строк отчета"""
        # Переопределяем метод родительского класса
        # Получаем набор полей
        type_key = self.request.GET.get('type_key', '')
        sub_type_key = self.request.GET.get('sub_type_key', '')
        props = type_fields(type_key, sub_type_key)
        # Получаем свойства объекта
        model_class = ModelsDispatcher.get_entity_class_by_entity_name(type_key)
        object_id = self.request.GET.get('object_id', 0)
        values = model_class.objects.get(pk=object_id)
        serializer = PartObjectSerializerDetailed(values)
        # print(props)
        # print(serializer.data)
        result = list()
        # Формируем результирующий список
        for p in props:
            t = p['type']  # Тип свойства
            n = p['name']  # Наименование свойств
            v = serializer.data[n]
            if t == 'Link':
                if v:
                    v = v['value']
            elif t == 'List':
                if v:
                    lv = p['data']
                    v = list(filter(lambda x: (x['value'] == v), lv))[0]['text']
            elif t == 'CheckBox':
                v = "Да" if v else "Нет"
            elif t in ['EntityLabel', 'Ref']:  # Такие поля пока не выводим
                continue
            l = dict(prop_name=p['label'], prop_value=v)
            result.append(l)
        return result
