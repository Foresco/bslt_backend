import xlwt
from jsonserv.core.dbutils import execute_sql_from_file
from jsonserv.core.fileutils import get_temp_file_path, prepare_filename
from jsonserv.pdm.models import PartObject


class BaseReportClass:
    """Базовый класс формирования отчета"""

    @staticmethod
    def get_cell_style():
        cell_style = xlwt.XFStyle()
        cell_style.borders.left = 1
        cell_style.borders.right = 1
        cell_style.borders.top = 1
        cell_style.borders.bottom = 1
        return cell_style

    @staticmethod
    def excel_width(width):
        # 1000 единиц здесь = 3,715 в Excel
        return width

    def prepare_sql_params(self, params):
        """Подготовка параметров sql-запроса"""
        for key in params:
            self.params[key] = self.request.GET.get(key, params[key])

    def __init__(self, request):
        self.request = request
        self.row_num, self.col_num = 0, 0
        self.file_name = ''  # Имя сформированного файла
        self.params = dict()  # Параметры запроса
        self.sql_file = ''  # Файл с SQL-запросом
        self.ws = None  # Лист с отчетом
        self.headers = dict()  # Массив с заголовком отчета
        self.columns = dict()  # Массив с описание колонок таблицы
        self.cell_style = self.get_cell_style()
        self.part_object = None  # Объект, на который формируется отчет
        self.print_header = True  # Признак необходимости вывода заголовка
        self.print_table_header = True  # Признак необходимости вывода заголовка таблицы

    def get_report_part_object(self):
        """Получение объекта, на который формируется отчет"""
        self.part_object = PartObject.objects.get(pk=self.request.GET.get('object_id', 0))

    def gen_code_file_name(self):
        """Генерация имени файла отчета с указанием обозначения объекта"""
        if not self.part_object:  # Если объект не получен ранее - получаем
            self.get_report_part_object()
        code = self.part_object.code
        self.file_name = prepare_filename(f'{code} {self.file_name}') # Убираем недопустимые символы

    def gen_file_name(self):
        """Генерация имени файла отчета
        Заглушка, в дочерних классах может быть переопределена"""
        pass

    def fill_report_header(self):
        """Заполнение заголовка отчета"""
        font_style = xlwt.XFStyle()

        for row in self.headers:
            for c in row:
                self.ws.write(self.row_num, c, row[c], font_style)
            self.row_num += 1

    def fill_table_header(self):
        """Заполнение заголовка таблицы"""
        head_cell_style = self.get_cell_style()
        head_cell_style.font.bold = True

        for col in self.columns:
            self.ws.write(self.row_num, self.col_num, col, head_cell_style)
            self.col_num += 1
        self.row_num += 1

    def set_columns_width(self):
        """Установка ширины столбцов таблицы"""
        col_num = 0
        for col in self.columns:
            self.ws.col(col_num).width = self.columns[col]['width']
            col_num += 1

    def get_report_rows(self):
        """Получение данных для строк отчета"""
        # По умолчанию выполняем запрос в базу данных
        # В дочерних классах можно переопределить
        # TODO: Обернуть защитой от ошибок
        return execute_sql_from_file(self.sql_file, self.params, True)

    def fill_report_file(self):
        """Подготовка файла отчета"""
        wb = xlwt.Workbook(encoding='utf-8')
        self.ws = wb.add_sheet('Отчет')

        # Заполняем заголовок отчета
        if self.print_header:
            self.fill_report_header()

        # Заполняем заголовок таблицы
        if self.print_table_header:
            self.row_num += 1
            self.fill_table_header()

        # Получаем строки для отчета
        rows = self.get_report_rows()
        row_counter = 1  # Счетчик строк
        
        # print('self.row_num =', self.row_num)
        for row in rows:
            self.col_num = 0

            for col in self.columns:
                col_def = self.columns[col]
                if col_def['field'] == 'row_counter':
                    # Счетчик строк
                    self.ws.write(self.row_num, self.col_num,
                                  row_counter, self.cell_style)
                    row_counter += 1
                else:
                    self.ws.write(self.row_num, self.col_num, row[col_def['field']], col_def.get(
                        'cell_style', self.cell_style))
                self.col_num += 1
            self.row_num += 1

        # Устанавливаем ширины колонок таблицы
        self.set_columns_width()

        # Сохраняем сформированный файл
        file_name = get_temp_file_path(self.file_name)
        wb.save(file_name)
        return file_name

    def prepare_report_file(self):
        """Основной метод формирования отчета
        должен быть у каждого потомка
        должен возвращать file_name
        где result_file_name - полный путь к сформированному файлу (название файла на латинице)
        """
        result_file_name = self.fill_report_file()  # Формируем файл
        return result_file_name  # Возвращаем результат работы
