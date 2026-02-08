# Классы для чтения содержимого пакета и преобразования данных в json
import sys
import os.path
from copy import copy
import lxml.etree as lxmllib # Библиотека для работы с xml
import json

from django.conf import settings  # для обращения к настройкам
from jsonserv.toolover.gtc.p21builder import P21Builder  # Построитель массивов импорта из файлов формата *.p21


class PackageReader:
    """Базовый класс для всех парсеров"""
    def __init__(self, dir_name=''):
        self.dir_name = dir_name # Каталог расположения пакета
        self.error_message = ''  # Текст ошибки
        self.is_error = False
        self.result_data = dict()
        self.json_file_name = 'data.json'  # Дайл для сохранения результатов чтения
        self.temp_dir = getattr(settings, 'TEMP_DIR', 'temp')

    def dump_loaded(self):
        """Сохранение массива в json-файл во временный каталог"""
        json_file_name = os.path.join(self.temp_dir, self.json_file_name)
        with open(json_file_name, 'w', encoding='utf-8') as json_file:
            json.dump(self.result_data, json_file)

    def open_and_parse(self, file_name):
        try:
            tree = lxmllib.parse(os.path.join(self.dir_name, file_name))
            return tree
        except:
            self.error_message = f'Ошибка открытия xml-файла с данными {file_name}'
            self.is_error = True
            return None

    @staticmethod
    def lang_value_get(xml_node, value_lang):
        """Получение строки на нужном языке из узла language"""
        if xml_node[0].text == value_lang:
            return xml_node[1].text
        return None

    @staticmethod
    def slash_remove(value):
        """Удаление лидирующего обратного слеша, который мешает использовать os.path.join"""
        return value.strip('/') if value else value

    @staticmethod
    def str_lang_value_get(xml_node, value_lang):
        """Получение строки на нужном языке из узла string_with_language"""
        for lng in xml_node.iterfind("string_with_language"):
            # print(lng[0].text)
            if lng[0].text == value_lang:
                return lng[1].text
        return None

    def package_meta_data_read(self):
        """Чтение свойств GTC-пакета из файла package_meta_data.xml"""
        self.json_file_name = 'package_meta_data.json'  # Имя файла для сохранения результатов в случае, если не будет импорта
        is_done = False  # Переменная для имитации итератора
        if not is_done:
            file_name = 'package_meta_data.xml'
            file_counter = 1  # Счетчик файлов для уникальной идентификации

            tree = self.open_and_parse(file_name)
            if self.is_error:
                print(self.error_message)
                sys.exit(1)
            # Получение корневого элемента
            root_node = tree.getroot()
            self.result_data = list()
            item = dict()
            file_item = dict()
            item['model'] = 'GtcPackage'  # Модель для хранения свойств пакетов
            file_item['model'] = 'GraphicFile'  # Модель для хранения свойств Графических файлов
            # Перебор элементов корневого уровня
            for xml_node in root_node:
                node_name = xml_node.tag
                if node_name == 'gtc_package_id':
                    item['id'] = xml_node.text  # id - необходимый атрибут
                if node_name == 'logo_url':
                    if xml_node.text:
                        # Добавляем описание графического файла логотипа
                        file_item['id'] = 'gf' + str(file_counter)
                        file_item['file_name'] = os.path.join(self.dir_name, self.slash_remove(xml_node.text))
                        self.result_data.append(file_item)
                        item['logo'] = file_item['id']
                        file_counter += 1
                    else:
                        item['logo'] = ''
                    continue
                if node_name == 'language':
                    item['short_description'] = self.lang_value_get(xml_node, 'eng')

                # Во всех остальных случаях просто переносим содержимое узла
                item[node_name] = xml_node.text

            self.result_data.append(item)
            yield self.result_data
            is_done = True  # Прерываем итератор

    def tool_classes_read(self):
        """Чтение иерархии классов из файла gtc_class_hierarchy_vendor.xml"""
        self.json_file_name = 'tool_classes.json'  # Имя файла для сохранения результатов
        is_done = False  # Переменная для имитации итератора
        if not is_done:
            file_name = 'gtc_class_hierarchy_vendor.xml'
            file_counter = 1  # Счетчик файлов для уникальной идентификации
            tree = self.open_and_parse(file_name)
            if self.is_error:
                print(self.error_message)
                sys.exit(1)
            # Получение корневого элемента
            root_node = tree.getroot()
            self.result_data = list()
            item = dict()
            item['model'] = 'ToolClass'  # Модель для хранения свойств классов инструмента
            file_item = dict()
            file_item['model'] = 'GraphicFile'  # Модель для хранения свойств Графических файлов
            # Перебор элементов корневого уровня
            for class_node in root_node:
                for xml_node in class_node:
                    node_name = xml_node.tag
                    if node_name == 'id':
                        item['class_id'] = xml_node.text  # class_id - имя атрибута в модели
                    if node_name == 'parent_id':
                        item['parent'] = xml_node.text
                        continue
                    if node_name == 'node_name':
                        item['class_name'] = self.str_lang_value_get(xml_node, 'eng')
                        continue
                    if node_name == 'preferred_name':
                        item[node_name] = self.str_lang_value_get(xml_node, 'eng')
                        continue
                    if node_name == 'document_list':
                        for doc in xml_node.iterfind("document"):
                            file_item['id'] = 'gf' + str(file_counter)
                            file_counter += 1
                            for gf_param in doc:
                                if gf_param.tag == 'usage':
                                    usage = gf_param.text
                                    if usage == 'class_icon':
                                        item['icon'] = file_item['id']
                                    elif usage == 'class_drawing':
                                        item['drawing'] = file_item['id']
                                if gf_param.tag == 'location':
                                    if gf_param.text.startswith('http'):
                                        file_item['file_name'] = gf_param.text
                                    else:
                                        file_item['file_name'] = os.path.join(self.dir_name,
                                                                              self.slash_remove(gf_param.text))
                            self.result_data.append(copy(file_item))
                        continue
                        # TODO: Сделать импорт всех иконок и документов
                    # Во всех остальных случаях просто переносим содержимое узла
                    item[node_name] = xml_node.text
                self.result_data.append(copy(item))

            yield self.result_data
            is_done = True  # Прерываем итератор

    def package_assortment_read(self):
        """Чтение ассортимента пакета из файла package_assortment.xml"""
        def tool_class_node_gen(class_id):
            """Формирование узла с описанием класса инструмента"""
            if class_id not in extra_ids:
                self.result_data.append(dict(model='ToolClass', id=class_id, class_id=class_id))
                extra_ids.append(class_id)

        builder = P21Builder()  # Построитель массива для импорта на основе данных из *.p21-файла

        file_name = 'package_assortment.xml'
        tree = self.open_and_parse(file_name)
        if self.is_error:
            print(self.error_message)
            sys.exit(1)
        # Получение корневого элемента
        root_node = tree.getroot()
        # Перебор элементов пакета
        for tool_node in root_node:
            self.result_data = list()
            extra_ids = list()  # Список идентификаторов уже описанных дополнительных сущностей
            # Свойства продукции их ветки пакета
            tool_item = dict()
            tool_item['model'] = 'ToolProduct'
            for xml_node in tool_node:
                node_name = xml_node.tag
                if node_name == 'p21_file_name':
                    continue
                elif node_name == 'p21_file_url':
                    self.json_file_name = os.path.split(xml_node.text)[1].replace('.p21', '.json')  # На случай сохранения результата
                    p21_file_name = os.path.join(self.dir_name, self.slash_remove(xml_node.text))
                    continue
                elif node_name == 'gtc_generic_class_id':
                    tool_class_node_gen(xml_node.text)  # Добавляем описание класса в массив
                    tool_item['generic_class'] = xml_node.text
                    continue
                elif node_name == 'gtc_vendor_class_id':
                    tool_class_node_gen(xml_node.text)  # Добавляем описание класса в массив
                    tool_item['gtc_vendor_class'] = xml_node.text
                    continue
                elif node_name == 'unit_system':
                    if xml_node.text not in extra_ids:
                        # Добавляем описание системы измерения
                        self.result_data.append(dict(model='MeasureSystem', id=xml_node.text, list_value=xml_node.text))
                # Во всех остальных случаях просто переносим содержимое узла
                tool_item[node_name] = xml_node.text

            # self.result_data.append(copy(item))
            # передаем имя файла с проверкой ошибок
            # print(p21_file_name)
            # Временно! Грузим только один файл
            # if p21_file_name != r'D:/temp/gtc/Demo_Catalog\product_data_files/5961364.p21':
            #     continue
            builder.data_clear() # Предварительная очистка данных
            builder.file_name_set(p21_file_name)
            if builder.error_check():
                print(builder.error_message_get())
                sys.exit(1)
            builder.extra_data_put(tool_item)  # Передаем дополнительне сведенья, полученные из xml
            # запускаем парсинг
            builder.file_parse()
            if builder.error_check():
                print(builder.error_message_get())
            # Запись результатов парсинга
            # builder.parsed_to_file_save()
            # Построение массива
            builder.data_build()
            # Запись данных в файл
            # builder.to_file_save()
            self.result_data += builder.result_get()  # Добавляем в список результаты разбора
            # Сохраняем разобранный массив
            # self.to_file_save()
            yield self.result_data
