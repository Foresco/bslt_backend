# Отчет Сводная подетальная ведомость материалов
from jsonserv.core.report import BaseReportClass
from jsonserv.core.fileutils import get_sql_file_path


class ReportClass(BaseReportClass):

    def __init__(self, request):
        super().__init__(request)
        self.file_name = "Сводная подетальная ведомость материалов.xls"
        self.gen_code_file_name()  # Генерируем отчету имя на основе обозначения объекта

        # Встроенные форматы ячеек
        self.norma_style = self.get_cell_style()
        self.norma_style.num_format_str = '# ##0.000'

        # 1000 единиц здесь = 3,715 в Excel
        
        self.columns = {
            '№ пп': {
                'field': 'row_counter',
                'width': 837
            },
            'Группа': {
                'field': 'group_code',
                'width': 1973
            },
            'ДСЕ': {
                'field': 'code',
                'width': 4874
            },
            'Кол-во': {
                'field': 'parent_quantity',
                'width': 1316
            },
            'Код материала': {
                'field': 'nom_code',
                'width': 3528
            },
            'Замена 1': {
                'field': 'repl_1',
                'width': 3170
            },
            'Замена 2': {
                'field': 'repl_2',
                'width': 3049
            },
            'Материал': {
                'field': 'mater_code',
                'width': 13639
            },
            'Норма': {
                'field': 'norm',
                'width': 2481,
                'cell_style': self.norma_style  # Особый стиль ячейки
            },
            'ЕИ': {
                'field': 'ei',
                'width': 958
            },
            'Цех': {
                'field': 'place_code',
                'width': 6102
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
        self.prepare_sql_params({"object_id": 1844, "quantity": 1})

        self.sql_file = get_sql_file_path('pdm', 'total_mater_det.sql')
