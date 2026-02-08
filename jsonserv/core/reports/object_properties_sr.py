# Отчет Свойства объекта справочника
# Вариант Светлана-Рентген
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
            'Значение': {
                'field': 'prop_value',
                'width': 18000
            }            
        }

        self.headers = []
        self.print_table_header = False  # Заголовок таблицы не выводим

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
        only_fileds = ('code', 'nom_code', 'unit')  # Свойства, которые будут выводиться
        # print(props)
        # print(serializer.data)
        result = list()
        # Формируем результирующий набор
        res_dict = dict()
        for p in props:
            t = p['type']  # Тип свойства
            n = p['name']  # Наименование свойства
            if n not in only_fileds:
                # Выводим тольк ограниченный набор свойств
                continue
            v = serializer.data[n]
            if t == 'Link':
                if v:
                    v = v['value']
            elif t == 'List':
                if v:
                    lv = p['data']
                    v = list(filter(lambda x: (x['value'] == v), lv))[0]['text']
            res_dict[n] = v
            
            
        l = dict(prop_value=res_dict['nom_code'])
        result.append(l)
        l = dict(prop_value=res_dict['code'] + '           ' + res_dict['unit'])
        result.append(l)
        return result
