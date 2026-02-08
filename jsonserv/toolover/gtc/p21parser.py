# Разбор текстового файла в формате STEP (*.p21)

import os.path
import re
import json
from ast import literal_eval  # Преборазование строки с unicode-escape в нормальную строку

from .schema_dictionary import schema_dictionary  # Свойства вариантов экземпляров


class P21Parser:

    def __init__(self, useful_patterns):
        self.useful_patterns = useful_patterns  # Паттерны, которые нужно отслеживать
        self.schema_dictionary = schema_dictionary
        self.file_name = ''
        self.error_message = ''  # Текст ошибки
        self.is_error = False
        self.reader = None
        self.line = ''
        # Результрующие массив с собранными данными
        self.header = dict()  # Информация из заголовка файла
        self.items = dict()  # Найденные в файле экземпляры данных
        self.patterns = dict()  # Экземпляры данных по основным паттернам

    def file_name_set(self, file_name):
        """Установка имени исходного файла с данными"""
        # Проверка существования
        if os.path.exists(file_name):
            if os.path.isfile(file_name):
                # Проверка расширения
                ext = os.path.splitext(file_name)[-1].lower()
                if ext == '.p21':
                    self.file_name = file_name
                else:
                    self.trace_error('Source file is not p21 ({})'.format(ext))
            else:
                self.trace_error('Source path is not file')
        else:
            self.trace_error('Source p21 file does not exists')

    def error_check(self):
        return self.is_error

    def error_message_get(self):
        return self.error_message

    def trace_error(self, error_message):
        self.is_error = True
        self.error_message = error_message

    def data_clear(self):
        """Очистка результирующих данных"""
        self.header = dict()
        self.items = dict()  # Найденные в файле экземпляры данных
        self.patterns = dict()  # Экземпляры данных по паттернам

    def name_get(self, value=''):
        """Получение имени (текста до первого пробела)"""
        str = value if value else self.line
        space_pos = str.find(" ")
        if space_pos == -1:  # Если пробела не найдено
            return str
        else:
            return str[:space_pos]  # Текст до пробела

    def inter_quotes_get(self, value=''):
        """Получение значения между кавчками"""
        str = value if value else self.line
        fnd = re.search(r".*\'(.*?)\'.*", str)
        return fnd.group(1) if fnd else ''

    def move_next(self):
        """Итератор по строкам файла"""
        # Перемещается на следующую строчку
        # считывает ее значение в буфер
        self.line = self.reader.readline().strip()
        # Пропуск пустых строк
        while self.line == '':
            self.line = self.reader.readline().strip()

    # Процедуры обработки секций
    def header_parse(self):
        """Обработка заголовочной секции HEADER"""
        while self.line != 'ENDSEC;':  # Признак окончания секции
            sub_sec_name = self.name_get()
            if sub_sec_name == 'FILE_DESCRIPTION':
                self.file_description_parse()
            elif sub_sec_name == 'FILE_NAME':
                self.file_name_parse()
            elif sub_sec_name == 'FILE_SCHEMA':
                self.file_schema_parse()
            self.move_next()

    def file_description_parse(self):
        """Обработка раздела FILE_DESCRIPTION"""
        self.header['file_description'] = dict()
        self.move_next()
        self.header['file_description']['description'] = self.inter_quotes_get()  # LIST[1: ?] OF STRING(256)
        self.move_next()
        self.header['file_description']['implementation_level'] = self.inter_quotes_get()  #  STRING(256)

    def file_name_parse(self):
        """Обработка заголовочной секции FILE_NAME"""
        self.header['file_name'] = dict()
        # TODO: Переделать в цикл по массиву из настроек
        self.move_next()
        self.header['file_name']['name'] = self.inter_quotes_get()  #  STRING (256);
        self.move_next()
        self.header['file_name']['time_stamp'] = self.inter_quotes_get()  #  time_stamp_text;
        self.move_next()
        self.header['file_name']['author'] = self.inter_quotes_get()  #  LIST [1 : ?] OF STRING (256);
        self.move_next()
        self.header['file_name']['organization'] = self.inter_quotes_get()  #  LIST [1 : ?] OF STRING (256);
        self.move_next()
        self.header['file_name']['preprocessor_version'] = self.inter_quotes_get()  #  STRING (256);
        self.move_next()
        self.header['file_name']['originating_system'] = self.inter_quotes_get()  #  STRING (256);
        self.move_next()
        self.header['file_name']['authorization'] = self.inter_quotes_get()  #  STRING (256);

    def file_schema_parse(self):
        """Обработка заголовочной секции FILE_SCHEMA"""
        self.header['file_schema'] = self.inter_quotes_get()

    def pattern_get(self, item_type):
        """Получение паттерна для парсинга строки значений"""
        return self.schema_dictionary.get(item_type, '')

    @staticmethod
    def item_value_parse(pattern, value_str):
        """
        Универсальная фукнция разбора экземпляра
        pattern - шаблон разбора (список)
        pattern_name - имя шблона, для включения в массив
        value_str - разбираемая строка значений
        """
        def decode_str_value(value):
            """Декодирование текстового значения"""
            lGrs = re.findall(r'\\X2\\[A-Z0-9]+\\X0\\', value)
            for lGr in lGrs:
                lGr4 = re.findall(r'.{4}', lGr)
                sJr = '\\u' + '\\u'.join(lGr4[1:-1])
                value = value.replace(lGr, sJr)
            value = value.replace('\X\\', r'\x')
            return literal_eval("'%s'" % value)

        def value_prepare(value):
            """Очистка и подготовка значений свойств экземпляров"""
            empty_values = ('$', )  # Список занчений, которые символизируют пустоту
            clr_value = value.strip(" '")
            if clr_value in empty_values:
                return ''
            if clr_value.startswith('#'):  # Это ссылочный идентификатор
                return clr_value
            else:
                if clr_value and clr_value.startswith('(') and clr_value.endswith(')'):  # В скобках списки, их надо разбивать
                    clr_value = clr_value.strip('()')
                    if clr_value:
                        clr_value = clr_value.split(',')
                    return clr_value # Списки не декодируем
                return decode_str_value(clr_value)

        def value_split(value):
            """Разбиение строки со списком значений на список"""
            # TODO: Передалать на регулярные выражения
            result = list()
            cur_value = ''
            list_loading = False
            split_symbol = ','  # Символ, по которому осуществляется разбиение
            for symbol in value:
                if symbol == ',' and not list_loading:  # Закончилось значение и не грузится список в скобках
                    result.append(cur_value.strip())
                    cur_value = ''
                    continue
                if symbol == '(':  # Если начался список в скобках, то начинаем его разбор
                    list_loading = True
                cur_value += symbol
                if symbol == ')' and list_loading:  # Список закончился
                    list_loading = False
            result.append(cur_value.strip())  # Добавление крайнего значения
            return result

        vls = value_split(value_str[1:-2])  # Убираем крайние скобки и ; разбиваем на список значений .split(',')
        cnt = 0
        result = dict()
        for itm in pattern:
            vl = value_prepare(vls[cnt])
            if vl:  # Отображаем только имеющие значение параметры
                result[itm] = vl
            cnt += 1
        return result

    def to_patterns_add(self, pattern, item_id):
        # Отбирать только нужные паттерны (остальные будут в items)
        if pattern in self.useful_patterns:
            if pattern not in self.patterns:
                self.patterns[pattern] = list()
            self.patterns[pattern].append(item_id)

    def exemplar_parse(self):
        """Парсинг экземпляра объекта"""
        # Проверка наличия #
        if self.line[0] != '#':
            print(self.line)
            self.trace_error('Line does not contain item')
            return
        # Выделение идентификатора
        item_id = self.name_get()
        value_pos = len(item_id) + 3  # 3 - " = "
        item_type = self.name_get(self.line[value_pos:])
        pattern = self.pattern_get(item_type)
        if pattern:
            value_pos += len(item_type) + 1  # Пробел
            item = self.item_value_parse(pattern, self.line[value_pos:])
            self.to_patterns_add(item_type, item_id)
            item['pattern'] = item_type  # TODO: Убрать после окончания отладки
            self.items[item_id] = item
        else:
            self.items[item_id] = self.line[value_pos:]
        # Определение типа

    def data_parse(self):
        """Обработка заголовочной секции DATA"""
        # Если структура обмена содержит только одну секцию данных,
        # тогда список параметров (РАRAMETER_LIST) может быть опущен.
        self.move_next()
        while self.line != 'ENDSEC;':  # Признак окончания секции
            self.exemplar_parse()
            self.move_next()

    def to_file_save(self):
        """Сохранение массива в json-файл"""
        # Сборка дерева данных
        result_data = dict(header = self.header,
                           data = self.items,
                           patterns = self.patterns)
        with open('result_new.json', 'w', encoding='utf-8') as json_file:
            json.dump(result_data, json_file)

    def file_parse(self):
        """Главная процедура парсинга файла"""
        with open(self.file_name, 'rt', encoding='utf-8') as self.reader:
            self.move_next()
            if self.line != 'ISO-10303-21;':
                self.trace_error('Source file does not contain ISO-10303-21 data')
                return
            self.move_next()
            while self.line != 'END-ISO-10303-21;':  # Признак окончания данных в файле
                if self.line == 'HEADER;':
                    self.header_parse()
                elif self.line == 'DATA;':
                    self.data_parse()
                self.move_next()
        # Передаем результаты парсинга обратно TODO: Переделать на структуры
        return self.header, self.items, self.patterns


