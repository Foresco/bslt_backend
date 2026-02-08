# Отчет Матрица прав пользователей
from jsonserv.core.report import BaseReportClass
from jsonserv.core.fileutils import get_sql_file_path


class ReportClass(BaseReportClass):

    def __init__(self, request):
        super().__init__(request)
        self.file_name = "Материца прав доступа.xls"

        # 1000 единиц здесь = 3,715 в Excel
        
        self.columns = {
            'Логин': {
                'field': 'username',
                'width': 3000
            },
            'Фамилия': {
                'field': 'last_name',
                'width': 4500
            },
            'Имя': {
                'field': 'first_name',
                'width': 3500
            },
            'Группа пользователей': {
                'field': 'group_name',
                'width': 5000
            },
            'Описание права': {
                'field': 'right_name',
                'width': 8500
            },
            'Код права': {
                'field': 'codename',
                'width': 5500
            }
        }

        # Готовим параметры sql-запроса, передавая значения по умолчанию
        # self.prepare_sql_params({"object_id": 1, "quantity": 1, 'group_id': ''})

        self.sql_file = get_sql_file_path('core', 'rights_matrix.sql')
