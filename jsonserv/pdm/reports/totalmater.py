# Отчет Сводная ведомость материалов
from jsonserv.core.report import BaseReportClass
from jsonserv.core.fileutils import get_sql_file_path


class ReportClass(BaseReportClass):

    def __init__(self, request):
        super().__init__(request)
        self.file_name = "Сводная ведомость материалов.xls"
        self.gen_code_file_name()  # Генерируем отчету имя на основе обозначения объекта

        # Встроенные форматы ячеек
        self.norma_style = self.get_cell_style()
        self.norma_style.num_format_str = '# ##0.000'

        # 1000 единиц здесь = 3,715 в Excel
        
        self.columns = {
            '№ пп': {
                'field': 'row_counter',
                'width': 958
            },
            'Группа': {
                'field': 'group_code',
                'width': 1943
            },
            'Код материала': {
                'field': 'nom_code',
                'width': 3558
            },
            'Замена 1': {
                'field': 'repl_1',
                'width': 2931
            },
            'Замена 2': {
                'field': 'repl_2',
                'width': 2872
            },
            'Материал': {
                'field': 'mater_code',
                'width': 18064
            },
            'Норма': {
                'field': 'norm',
                'width': 2931,
                'cell_style': self.norma_style  # Особый стиль ячейки
            },
            'ЕИ': {
                'field': 'ei',
                'width': 1556
            },
        }

        self.headers = [
            {
                0: 'Изделие',
                3: self.part_object.code
            },
            {
                0: 'Количество',
                3: self.params.get('quantity', 1)
            },
        ]

        # Готовим параметры sql-запроса, передавая значения по умолчанию
        self.prepare_sql_params({"object_id": 1, "quantity": 1, 'group_id': ''})

        self.sql_file = get_sql_file_path('pdm', 'total_mater.sql')

    def gen_file_name(self):
        self.gen_code_file_name()

