# Преобразование предварительно разобранных данных текстового файла в формате STEP (*.p21)
# в массив для последующего импорта

import json
from copy import copy

from .p21parser import P21Parser


class P21Builder:
    tool_item_extra_data = dict()  # Внешние данные об инстурменте
    result_data = list()  # Список с результатами
    ids = list()  # Список с идентификаторами выгруженных объектов
    item_map = dict()  # Словарь для перевода идентифкаторов ITEM_VERSION и ITEM_DEFINITION
    # к идентификатору ITEM
    # исходные массивы с данными для разбора
    header = dict()
    data_lines = dict()  # Строки из раздела DATA
    patterns = dict()
    # Данные из одних элементов, нужные другим
    article = ''

    def __init__(self):
        # В данном словаре указаны все обработчики для всех вариантов параметров
        # Сюда добавляются обработчики для новых вариантов
        # TODO: Переделать на getattr
        self.pattern_processors = {
            'ITEM': self.item,
            'ITEM_VERSION': self.item_version,
            'ITEM_DEFINITION': self.item_definition,
            'SPECIFIC_ITEM_CLASSIFICATION': self.specific_item_classification,
            'PERSON_ORGANIZATION_ASSIGNMENT':  self.person_organization_assignment,
            'PROPERTY_VALUE_ASSOCIATION': self.property_value_association,
            'LANGUAGE': self.language,
            'CLASSIFICATION_ASSOCIATION': self.classification_association
            # 'PLIB_CLASS_REFERENCE': self.plib_class_reference,
            # 'PLIB_PROPERTY_REFERENCE': self.plib_property_reference
        }
        self.parser = P21Parser(self.pattern_processors.keys())  # Класс для парсинга файла

    # Доступ к методам и свойствам парсера
    def file_name_set(self, file_name):
        """Установка имени исходного файла с данными"""
        self.parser.file_name_set(file_name)

    def error_check(self):
        return self.parser.is_error

    def data_clear(self):
        """Очистка результирующих данных"""
        self.tool_item_extra_data = dict()  # Внешние данные об инстурменте
        self.result_data = list()  # Список с результатами
        self.ids = list()  # Список с идентификаторами выгруженных объектов
        self.item_map = dict()  # Словарь для перевода идентифкаторов ITEM_VERSION и ITEM_DEFINITION
        self.article = ''

    def file_parse(self):
        self.parser.data_clear()  # Предварительно очищаем результаты парсинга
        # Передаем структуры данных для заполнения
        self.header, self.data_lines, self.patterns = self.parser.file_parse()

    def error_message_get(self):
        return self.parser.error_message

    def parsed_to_file_save(self):
        self.parser.to_file_save()

    def extra_data_put(self, tool_item):
        """Добавление дополнительных данных об инструменте в массив"""
        self.tool_item_extra_data = tool_item

    def string_value_get(self, id):
        """Получение данных из узлов типа MULTI_LANGUAGE_STRING"""
        value_id = self.data_lines[id]['primary_language_string']
        return  self.data_lines[value_id]['contents']
        # TODO: Сделать получение extra_language_strings

    def add_value_to_node(self, node_id, value_name, value):
        """Добавление атрибута к ранее подготовленному узлу"""
        trg = [line for line in self.lines if line['id'] == node_id]
        if trg:
            trg[0][value_name] = value
        else:
            print(f'Ошибка поиска элемента с id = {node_id}')


    def tool_object_add(self, id, obj_id):
        """Добавление в массив информации об инструменте"""
        self.type_key_add('tool')  # Добавляем описание типа Инструмент
        line = self.data_lines[id]
        tool_object = dict(model='ToolObject', id=obj_id, type_key='tool')
        tool_object['code'] = self.string_value_get(line['name'])
        tool_object['description'] = self.string_value_get(line['description'])
        self.result_data.append(tool_object)
        self.ids.append(obj_id)
        self.article = tool_object['code']  # Артикул для поставок

    def item(self, id):
        """Добавление в массив информации об инструменте-продукте поставщика"""
        line = self.data_lines[id]
        obj_id = f'tobj.{id}'
        self.tool_object_add(id, obj_id)  # Добавялем объект справочника Инструмент
        tool_product = dict(model='ToolProduct', id=id, product_id=line['id'], tool_object=obj_id)
        tool_product['name'] = self.string_value_get(line['name'])
        tool_product['description'] = self.string_value_get(line['description'])
        # Остальные параметры берутся из полученных ранее значений
        for prop_name in self.tool_item_extra_data:
            tool_product[prop_name] = self.tool_item_extra_data[prop_name]
        self.result_data.append(tool_product)
        self.ids.append(id)

    def item_version(self, id):
        line = self.data_lines[id]
        self.item_map[id] = line['associated_item']

    def item_definition(self, id):
        line = self.data_lines[id]
        self.item_map[id] = self.item_map.get(line['associated_item_version'])

    def specific_item_classification(self, id):
        """Добавление спецификационной классификации"""
        line = self.data_lines[id]
        # Сначала добавляем сам спецификацонный класс
        if line['classification_name'] not in self.ids:
            sp_class = dict(model='SpecificClass', id=line['classification_name'], list_value=line['classification_name'])
            self.result_data.append(sp_class)
            self.ids.append(line['classification_name'])
        for specific_item in line['associated_item']:
            link_id = f"{line['classification_name']}.{specific_item}"  # Синтетический ключ
            sp_classification = dict(model='SpecificClassification', id=link_id,
                                     specific_class=line['classification_name'],
                                     tool_product=specific_item)
            self.result_data.append(copy(sp_classification))
            self.ids.append(id)

    def type_key_add(self, type_key):
        """Добавление описания типа сущности"""
        if type_key not in self.ids:
            e_type = dict(model='EntityType', id=type_key, type_key=type_key)
            self.result_data.append(e_type)
            self.ids.append(type_key)

    def place_add(self, id):
        """Добавление организации-поставщика"""
        if id not in self.ids:
            self.type_key_add('place')  # Добавляем описание типа Производственные подразделения
            line = self.data_lines[id]
            place = dict(model='Place', id=id, type_key='place',
                         code=line['organization_name'],
                         place_code=line['id'],
                         sitelink=line['visitor_address'])
            self.result_data.append(place)
            self.ids.append(id)

    def person_organization_assignment(self, id):
        """Добавление добавление поставки"""
        line = self.data_lines[id]
        # Сначала добавляем организацию
        self.place_add(line['associated_organization'])
        for supplied_entity in line['is_applied_to']:
            supply = dict(model='Price', id=id, supplier=line['associated_organization'],
                          supplied_entity=supplied_entity, article=self.article)
            self.result_data.append(copy(supply))
            self.ids.append(id)

    def property_add(self, property_name, pattern):
        """Добавление свойства"""
        if property_name not in self.ids:
            property = dict(model='Property', id=property_name, property_name=property_name.capitalaze())
            if pattern == 'NUMERICAL_VALUE':
                property['property_type']='F'
            elif pattern == 'STRING_VALUE':
                property['property_type'] = 'T'
            else:
                property['property_type'] = 'C'
            self.result_data.append(property)
            self.ids.append(property_name)

    def external_library_add(self, id):
        """Добавление описания внешней библиотеки"""
        if id not in self.ids:
            line = self.data_lines[id]
            external_library = dict(model='ExternalLibrary', external_id=line['external_id'],
                                    library_type=line['library_type'])
            if line['description']:
                description = self.string_value_get(line['description'])
                external_library['description'] = description
            self.result_data.append(external_library)
            self.ids.append(line['external_id'])

    # def plib_property_add(self):
    #
    #
    # def plib_class_add(self):


    def property_source_add(self, id, property):
        property_reference = self.data_lines[id]
        if property_reference['pattern'] == 'PLIB_PROPERTY_REFERENCE':
            # Добавление описаний PLIB
            # PLIB_PROPERTY_REFERENCE
            if id not in self.ids:
                plib_property = dict(model='PlibProperty', id=id, code=property_reference['code'],
                                     name_scope=property_reference['name_scope'],
                                     version=property_reference['version'],
                                     property=property)
                self.result_data.append(plib_property)
                self.ids.append(id)
            # PLIB_CLASS_REFERENCE
            if property_reference['name_scope'] not in self.ids:
                plib_class_reference = self.data_lines[property_reference['name_scope']]
                plib_class = dict(model='PlibClass', id=property_reference['name_scope'],
                                  code=plib_class_reference['code'],
                                  supplier_bsu=plib_class_reference['supplier_bsu'],
                                  version=plib_class_reference['version'])
                self.result_data.append(plib_class)
                self.ids.append(property_reference['name_scope'])
        elif property_reference['pattern'] == 'EXTERNAL_LIBRARY_REFERENCE':
            self.external_library_reference(property, property_reference)

    def unit_add(self, id):
        if id not in self.ids:
            line = self.data_lines[id]
            measure_unit = dict(model='MeasureUnit', id=id, unit_name=line['unit name'],
                                short_name=line['unit name'],
                                unit_code=line['unit name'])
            self.result_data.append(measure_unit)
            self.ids.append(id)

    def prop_unit_add(self, property, unit):
        self.unit_add(unit)  # Сначала добавим саму ЕИ
        link_id = f'{property}.{unit}'  # Синтетический ключ, другого нет
        if link_id not in self.ids:
            property_unit = dict(model='PropertyUnit', id=link_id, property=property, measure_unit=unit)
            self.result_data.append(property_unit)
            self.ids.append(link_id)



    def property_value_association(self, id):
        """Добавление значения свойства"""
        line = self.data_lines[id]
        property_value_representation = self.data_lines[line['describing_property_value']]

        property_item = self.data_lines[property_value_representation['definition']]
        value_item = self.data_lines[property_value_representation['value']]

        self.property_add(value_item['value_name'], value_item['pattern'])  # Добавление свойства
        self.property_source_add(property_item['property_source'], value_item['value_name'])  # Добавление описаний связки P-LIB
        if 'unit' in property_item:  # ЕИ указаны не всегда
            for unit_item in property_item['unit']:
                 self.prop_unit_add(value_item['value_name'], unit_item)
        # Теперь само значение свойства
        prop_value = dict(model='PropertyValue', id=id, entity='tobj.'+self.item_map.get(line['described_element']),
                          property=value_item['value_name'])

        if value_item['pattern'] == 'NUMERICAL_VALUE':
            prop_value['value_min'] = value_item['value_component']
            if 'unit_component' in value_item:
                prop_value['unit'] = value_item['unit_component']
        elif value_item['pattern'] == 'STRING_VALUE':
            prop_value['value'] =  self.string_value_get(value_item['value_specification'])

        self.result_data.append(prop_value)
        self.ids.append(id)

    def language(self, id):
        """Добавление в массив информации о языке"""
        line = self.data_lines[id]
        language = dict(model='Language', id=id, value_code=line['language_code'], list_value=line['language_code'])
        self.result_data.append(language)
        self.ids.append(id)

    def plib_class_add(self, code):
        """Добавление в массив ссылки на plib-класс"""
        if code not in self.ids:
            plib_class = dict(model='PlibClass', id=code, code=code)
            self.result_data.append(plib_class)
            self.ids.append(code)

    def plib_class_reference(self, item_id, id):
        """Добавление в массив ссылки на plib-класс"""
        line = self.data_lines[id]
        self.plib_class_add(line['code'])  # Добавляем сам plib-класс
        link_id = f"v{line['code']}"  # Идентификатор связи
        if link_id not in self.ids:
            vendor_plib_class = dict(model='VendorPlibClass', id=link_id, plib_class=line['code'],
                                     tool_product=item_id, supplier_bsu=line['supplier_bsu'],
                                     version=line['version'])
            self.result_data.append(vendor_plib_class)
            self.ids.append(link_id)

    def external_library_reference(self, ref_id, library_node):
        """Добавление в массив ссылки на внешнюю библиотеку"""
        link_id = f"{ref_id}v{library_node['external_id']}"  # Идентификатор связи
        if link_id not in self.ids:
            library_reference = dict(model='ExternalLibraryReference', id=link_id, external_id=library_node['external_id'],
                                     reference=ref_id, library_type=library_node['library_type']
                                     )
            if 'description' in library_node:
                library_reference['description'] = self.string_value_get(library_node['description'])

            self.result_data.append(library_reference)
            self.ids.append(link_id)

    def plib_property_reference(self, id):
        """Добавление в массив информации о plib-свойстве"""
        print('plib_property_reference', id)
        pass

    def classification_association(self, id):
        """Установка классификационных связей"""
        line = self.data_lines[id]
        assc = self.data_lines[line['associated_classification']]
        if assc['pattern'] == 'GENERAL_CLASSIFICATION':
            cl_id = assc['classification_source']
            item = self.data_lines[line['classified_element']]
            if item['pattern'] == 'ITEM_DEFINITION':
                # Переход к непосредственно объекту
                item_id = self.item_map[line['classified_element']]
            else:
                item_id = line['classified_element']
            cl_line = self.data_lines[cl_id]
            if cl_line['pattern'] == 'PLIB_CLASS_REFERENCE':
                # Добавление связи с классом
                self.plib_class_reference(item_id, cl_id)
            elif cl_line['pattern'] == 'EXTERNAL_LIBRARY_REFERENCE':
                # Добавление связи с внешней библиотекой
                self.external_library_reference(item_id, cl_line)
            else:
                print('Необработанный случай 2!')
                print(cl_line)
        else:  # Вдруг что-то еще?
            print('Необработанный случай 1!')
            print(assc)

    def data_build(self):
        """Построение массива для последующего импорта"""
        # Перебираем self.pattern_processors
        for pattern_name in self.pattern_processors:
            for item in self.patterns[pattern_name]:
                self.pattern_processors[pattern_name](item)

    def result_get(self):
        """Возвращает результаты парсинга"""
        return self.result_data

    def to_file_save(self):
        """Сохранение массива в json-файл"""
        with open('data.json', 'w', encoding='utf-8') as json_file:
            json.dump(self.result_data, json_file, ensure_ascii=False)
