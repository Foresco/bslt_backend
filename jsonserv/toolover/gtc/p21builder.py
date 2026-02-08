# Преобразование предварительно разобранных данных текстового файла в формате STEP (*.p21)
# в массив для последующего импорта

import json
from copy import copy

from .p21parser import P21Parser


class P21Builder:

    def get_processor(self, pattern_name):
        """Получение обработчика в соответствтии с именем паттерна строки"""
        processor = getattr(self, pattern_name.lower(), '')  # TODO: попробовать запоминать в словарь
        if not processor:
            print(f'Не найден обработчик для паттерна {pattern_name}')
            exit(1)
        return processor

    def process_line(self, id):
        """Обработка строки данных
        id - идентификатор строки"""
        # print(id)
        line = self.data_lines[id]  # Получаем строку
        pattern_name = line['pattern']
        processor = self.get_processor(pattern_name)  # Получаем соответсвующий паттерну обработчик
        return processor(line, id)

    def get_pattern(self, id):
        """Получения паттерна строки по идентификатору id"""
        return self.data_lines[id]['pattern']

    def data_clear(self):
        """Очистка результирующих данных"""
        self.tool_item_extra_data = dict()  # Внешние данные об инстурменте
        self.result_data = list()  # Список с результатами
        self.ids = list()  # Список с идентификаторами выгруженных объектов
        self.article = ''
        self.properties = dict()
        self.property_sources = list()  # Список со ссылками на источники свойств
        self.id_links = dict()  # Связи идентификаторов для перехода
        self.property_classes = dict()  # Словарь со ссылками на PLib-классы Plib-свойств

    def __init__(self):
        # В данном словаре указаны все паттерны, от которых начинается построение массива
        self.main_patterns = (
            'SPECIFIC_ITEM_CLASSIFICATION',
            'PERSON_ORGANIZATION_ASSIGNMENT',
            'PROPERTY_VALUE_ASSOCIATION',
            'PROPERTY_VALUE_REPRESENTATION_RELATIONSHIP',
            # 'LANGUAGE',
            'CLASSIFICATION_ASSOCIATION',
            'DOCUMENT_ASSIGNMENT',
            'DIGITAL_DOCUMENT',
            'EFFECTIVITY_ASSIGNMENT',
            'ALIAS_IDENTIFICATION'
        )

        self.parser = P21Parser(self.main_patterns)  # Класс для парсинга файла
        self.data_clear()  # Начальная инициализация переменных

    # Доступ к методам и свойствам парсера
    def file_name_set(self, file_name):
        """Установка имени исходного файла с данными"""
        self.parser.file_name_set(file_name)

    def error_check(self):
        return self.parser.is_error

    def file_parse(self):
        self.parser.data_clear()  # Предварительно очищаем результаты парсинга
        # Получаем распарсенные данные
        # Информация из заголовка файла, Все строки данных, Строки данных по основным паттернам
        self.header, self.data_lines, self.main = self.parser.file_parse()

    def error_message_get(self):
        return self.parser.error_message

    def parsed_to_file_save(self):
        self.parser.to_file_save()

    def extra_data_put(self, tool_item):
        """Добавление дополнительных данных об инструменте в массив"""
        self.tool_item_extra_data = tool_item

    def result_get(self):
        """Возвращает результаты парсинга"""
        return self.result_data

    def to_file_save(self):
        """Сохранение массива в json-файл"""
        # print(self.result_data)
        with open('data.json', 'w', encoding='utf-8') as json_file:
            json.dump(self.result_data, json_file, ensure_ascii=False)

    def data_build(self):
        """Построение массива для последующего импорта"""
        # Перебираем все основеные шаблоны из результатов парсинга
        # в них идентификаторы строк общего массива self.data_lines
        for pattern_name in self.main:
            for line_id in self.main[pattern_name]:
                self.process_line(line_id)
        # По окончании обработки массива добавляем в него собранные свойства инструмента
        self.upload_properies()

    # --- Вспомогательные функции для обработчиков паттернов ---

    def put_to_result(self, node, id):
        """Добавление в результирующий массив новых данных"""
        self.result_data.append(node)
        self.ids.append(id)

    def type_key_add(self, type_key):
        """Добавление узла с описанием типа сущности"""
        # TODO: Переименовать в entity_type_add
        if type_key not in self.ids:
            e_type = dict(model='EntityType', id=type_key, type_key=type_key)
            self.put_to_result(e_type, type_key)

    def add_value_to_node(self, node_id, value_name, value):
        """Добавление атрибута к ранее подготовленному узлу"""
        trg = [line for line in self.result_data if line['id'] == node_id]
        if trg:
            trg[0][value_name] = value
        else:
            print(f'Ошибка поиска элемента с id = {node_id}')

    # def tool_object_add(self, id, obj_id):
    #     """Добавление в массив информации об инструменте"""
    #     Пока не используется
    #     self.type_key_add('toolobject')  # Добавляем описание типа Инструмент
    #     line = self.data_lines[id]
    #     tool_object = dict(model='ToolObject', id=obj_id, type_key='toolobject')
    #     tool_object['code'] = self.process_line(line['name'])
    #     tool_object['description'] = self.process_line(line['description'])
    #     self.put_to_result(tool_object, obj_id)
    #     self.article = tool_object['code']  # Артикул для поставок

    def unit_add(self, id):
        if id not in self.ids:
            line = self.data_lines[id]
            measure_unit = dict(model='MeasureUnit', id=id, unit_name=line['unit name'],
                                short_name=line['unit name'],
                                unit_code=line['unit name'])
            self.put_to_result(measure_unit, id)

    def prop_unit_add(self, property, unit):
        self.unit_add(unit)  # Сначала добавим саму ЕИ
        link_id = f'{property}{unit}'  # Синтетический ключ, другого нет
        if link_id not in self.ids:
            property_unit = dict(model='PropertyUnit', id=link_id, property=property, measure_unit=unit)
            self.put_to_result(property_unit, link_id)

    def property_add(self, id, property_name, property_type):
        """Добавление свойства"""
        if id not in self.ids:
            property = dict(model='Property', id=id, property_name=property_name.capitalize(),
                            property_type=property_type)
            self.put_to_result(property, id)

    def upload_properies(self):
        """Выгрузка свойств и их источников, накопленных ранее"""
        # print(self.properties)
        # print(self.property_sources)
        prop_counts = dict()
        prop_numbers = dict()
        added_keys = list()  # Список ключей уже добавленных свойств

        def get_prop_number(prop_name, value_check):
            """Получение номера свойства (для повторов свойств)"""
            if prop_name not in prop_counts:
                prop_counts[prop_name] = 0
            if value_check not in prop_numbers:
                prop_counts[prop_name] += 1
                prop_numbers[value_check] = prop_counts[prop_name]
            return prop_numbers[value_check]

        # Перебираем собранные свойства
        for value_id in self.properties:
            # Добавляем само свойство
            self.property_add(self.properties[value_id]['prop_id'],
                              self.properties[value_id]['name'],
                              self.properties[value_id]['type'])
            # Добавляем значение свойства
            node = dict(model='PropertyValue', id=value_id)
            node['entity'] = self.properties[value_id]['item']
            node['property'] = self.properties[value_id]['prop_id']
            value_check = ''  # На всякий случай
            if 'value' in self.properties[value_id]:
                node['value'] = self.properties[value_id]['value']
                value_check = self.properties[value_id]['value']
            elif 'value_min' in self.properties[value_id]:
                node['value_min'] = self.properties[value_id]['value_min']
                value_check = self.properties[value_id]['value_min']
                if 'unit' in self.properties[value_id]:
                    node['unit'] = self.properties[value_id]['unit']

            node['value_number'] = get_prop_number(self.properties[value_id]['name'], value_check)
            self.put_to_result(node, value_id)

        # Перебираем собранные ссылки на источники свойств
        for line in self.property_sources:
            node = dict(model='PropertySource', id=line['id'])
            # TODO: собирать строки в массив уже сразу с нужными свойствами
            if 'external_library_reference' in line:
                key_id = line['property'] + line['external_library_reference']  # Контрольный ключ
                node['external_library_reference'] = line['external_library_reference']
            elif 'plib_property' in line:
                key_id = line['property'] + line['plib_property']  # Контрольный ключ
                node['plib_property'] = line['plib_property']
            else:
                print('Не найдена ссылка на источник', line)
                continue
            if key_id not in added_keys:
                node['property'] = line['property']
                self.put_to_result(node, line['id'])
                added_keys.append(key_id)
                if 'units' in line:  # Если переданы единицы измерения
                    for unit in line['units']:
                        self.prop_unit_add(line['property'], unit)

    # --- Обработчики паттернов ---

    def string_with_language(self, line, id):
        return line['contents']

    def multi_language_string(self, line, id):
        """Получение данных из узлов типа MULTI_LANGUAGE_STRING"""
        return self.process_line(line['primary_language_string'])
        # TODO: Сделать получение extra_language_strings

    def item(self, line, id):
        """Добавление в массив информации об инструменте-продукте поставщика"""
        if id not in (self.ids):
            # obj_id = f'{id}tlobj'  # Искусственный ключ (КОРРЕКТИРОВАТЬ В ДВУХ МЕСТАХ)
            self.type_key_add('toolproduct')  # Добавляем описание типа Инструмент
            tool_product = dict(model='ToolProduct', id=id, type_key='toolproduct', product_id=line['id'])
            tool_product['code'] = self.process_line(line['name'])
            tool_product['description'] = self.process_line(line['description'])

            # Остальные параметры берутся из полученных ранее значений
            for prop_name in self.tool_item_extra_data:
                tool_product[prop_name] = self.tool_item_extra_data[prop_name]
            self.put_to_result(tool_product, id)
            self.article = line['id']  # Артикул для поставок
        return id

    def item_version(self, line, id):
        return self.process_line(line['associated_item'])

    def item_definition(self, line, id):
        return self.process_line(line['associated_item_version'])

    def specific_item_classification(self, line, id):
        """Добавление спецификационной классификации"""
        # Сначала добавляем сам спецификацонный класс
        if line['classification_name'] not in self.ids:
            sp_class = dict(model='SpecificClass', id=line['classification_name'],
                            list_value=line['classification_name'])
            self.put_to_result(sp_class, line['classification_name'])

        # Далее устанавливаем связи
        for associated_item in line['associated_items']:  # Там список связанных item'ов
            specific_item = self.process_line(associated_item)
            link_id = f"{id}{specific_item}"  # Синтетический ключ
            sp_classification = dict(model='SpecificClassification', id=link_id,
                                     specific_class=line['classification_name'],
                                     tool_product=specific_item)
            self.put_to_result(copy(sp_classification), link_id)

    def organization(self, line, id):
        """Добавление организации-поставщика"""
        if id not in self.ids:
            self.type_key_add('place')  # Добавляем описание типа Производственные подразделения
            place = dict(model='Place', id=id, type_key='place',
                         code=line['organization_name'],
                         place_code=line['id'],
                         sitelink=line['visitor_address'])
            self.put_to_result(place, id)
        return id

    def person_organization_assignment(self, line, id):
        """Добавление поставщика и поставки"""
        # Сначала добавляем организацию-поставщика
        supplier = self.process_line(line['associated_organization'])

        for applied_to in line['is_applied_to']:  # Пееребираем перечень поставляемых позиций
            supplied_entity = self.process_line(applied_to)
            # supplied_entity = f'{supplied_entity}tlobj'  # Искусственный ключ (КОРРЕКТИРОВАТЬ В ДВУХ МЕСТАХ)
            supply = dict(model='Price', id=id, supplier=supplier, supplied_entity=supplied_entity)
            # Если ранее был счита аритикул
            if self.article:
                supply['article'] = self.article
            self.put_to_result(copy(supply), id)

    def document(self, line, id):
        """Формирование информации о файле документа"""
        self.type_key_add('archdocument')# Добавляем тип сущности Архивный документ
        doc = dict(model='Document', id=id, type_key='archdocument')
        doc['code'] = line['document_id']
        doc['doc_type'] = self.process_line(line['description'])
        doc['description'] = self.process_line(line['name'])
        self.put_to_result(doc, id)
        return id

    def document_version(self, line, id):
        """Формирование информации о версии документа в архиве"""
        if id not in self.ids:
            dv = dict(model='DocumentVersion', id=id)
            dv['document'] = self.process_line(line['assigned_document'])
            dv['description'] = self.process_line(line['description'])
            dv['version_num'] = line['id']
            self.put_to_result(dv, id)
        return id

    def document_assignment(self, line, id):
        """Связывание документа и инстурмента"""
        edv = dict(model='EntityDocumentVersion', id=id)
        edv['entity'] = self.process_line(line['is_assigned_to'])
        edv['document_version'] = self.process_line(line['assigned_document'])
        edv['document_role'] = line['role']
        self.put_to_result(edv, id)

    def document_location_property(self, line, id):
        return line['location_name']

    def external_file_id_and_location(self, line, id):
        location = self.process_line(line['location'])
        return location + line['external_id']

    def document_format_property(self, line, id):
        return line['data_format'], line['character_code']

    def digital_file(self, line, id):
        # dfl = list()
        # # locations = self.process_line(line['external_id_and_location'])
        # for location in line['external_id_and_location']:
        #     loc = self.process_line(location)
        #     df = dict()
        #     file_location = self.process_line(location)
        #     df['file_location'] = file_location
        #     df['file_format'] = line['file_format']
        #     df['file_id'] = line['file_id']
        #     dfl.append(df)
        return line

    def digital_document(self, line, id):
        """Описание цифрового документа"""
        def put_file_to_res(file_id, file_path):
            """Служебная функция добавления файла"""
            df = dict(model='DigitalFile', id=file_id)
            df['document_version'] = document_version
            df['file_name'] = file_path
            df['data_format'] = file_format
            df['character_code'] = character_code
            df['file_number'] = file_number
            self.put_to_result(df, file_id)

        document_version = self.process_line(line['associated_document_version'])
        for df in line['file']:
            digital_file = self.process_line(df)
            file_number = digital_file['file_id']
            file_format, character_code = self.process_line(digital_file['file_format'])
            for loc in digital_file['external_id_and_location']:
                file_path = self.process_line(loc)
                put_file_to_res(loc, file_path)

    def date_time(self, line, id):
        return f'{line["date"]}T{line["time"]}'

    def effectivity(self, line, id):
        return self.process_line(line['start_definition'])

    def effectivity_assignment(self, line, id):
        # print(line)
        ea = dict(model='Effectivity', id=id)
        ea['tool_product'] = self.process_line(line['effective_element'])
        if line['effectivity_indication'] == '.F.':
            ea['indicator'] = False
        else:
            ea['indicator'] = True
        ea['role'] = line['role']
        ea['limit'] = self.process_line(line['assigned_effictivity'])
        self.put_to_result(ea, id)

    def alias_identification(self, line, id):
        alias = dict(model='ToolProductAlias', id=id)
        alias['alias'] = line['alias_id']
        alias['supplier'] = self.process_line(line['alias_scope'])
        alias['alias_name'] = self.process_line(line['description'])
        alias['tool_product'] = self.process_line(line['is_applied_to'])
        self.put_to_result(alias, id)

    def external_library_reference(self, line, id):
        # Добавление описания внешней библиотеки
        # print(line)
        if id not in self.ids:
            external_library = dict(model='ExternalLibrary', id=id, external_id=line['external_id'],
                                    library_type=line['library_type'])
            if 'description' in line:
                external_library['description'] = self.process_line(line['description'])
            self.put_to_result(external_library, id)

        return id, 'external_library_reference'  # Возвращаем и идентификатор и тип

    def plib_class_reference(self, line, id):
        code = line['code']
        if code not in self.ids:
            plib_class = dict(model='PlibClass', id=id, code=code)
            self.put_to_result(plib_class, code)

        return id, 'plib_class_reference'  # Возвращаем и идентификатор и тип

    def plib_property_reference(self, line, id):
        """Описание PLib-свойства """
        cls, cls_type = self.process_line(line['name_scope'])  # Получение ссылки на PLib-класс
        # Описание самого PLib-свойства
        plib_property = dict(model='PlibProperty', id=id, code=line['code'])
        # print(id, self.property_classes)
        if cls_type == 'plib_class_reference':
            # Установка связи с классом
            link_id = f'{cls}{id}'
            vendor_plib_property = dict(model='VendorPlibProperty', id=link_id, plib_property=id,
                                        name_scope=cls, version=line['version'])
            self.put_to_result(vendor_plib_property, link_id)

        self.put_to_result(plib_property, id)
        return id, 'plib_property_reference'

    def numerical_value(self, line, id):
        """Разбор числового значения свойства"""
        property = dict()
        property['name'] = line['value_name']
        property['type'] = 'F'
        property['value_min'] = line['value_component']
        if 'unit_component' in line:
            # Если есть ссылка на единицу измерения - добавляем
            property['unit'] = self.process_line(line['unit_component'])
        return property

    def string_value(self, line, id):
        """Разбор текстового значения свойства"""
        property = dict()
        property['name'] = line['value_name']
        property['type'] = 'S'
        property['value'] = self.process_line(line['value_specification'])
        return property

    def unit(self, line, id):
        """Добавление единицы измерения"""
        if id not in self.ids:
            measure_unit = dict(model='MeasureUnit', id=id, unit_name=line['unit name'],
                                short_name=line['unit name'],
                                unit_code=line['unit name'])
            self.put_to_result(measure_unit, id)
        return id

    def property(self, line, id):
        """Обработка свойств свойства"""
        src, src_type = self.process_line(line['property_source'])
        property_source = dict(id=id)

        if src_type == 'plib_property_reference':
            property_source['plib_property'] = src
        elif src_type == 'external_library_reference':
            property_source['external_library_reference'] = src
        else:
            print(f'Неизветсный тип свойства {src_type}')

        # TODO: Делать что-то с этими ЕИ
        if 'unit' in line:  # ЕИ указаны не всегда
            units = list()
            for unit_item in line['unit']:
                 units.append(self.process_line(unit_item))
            property_source['units'] = units

        return property_source

    def property_value_representation(self, line, id):
        """Определение значения свойства"""
        property_value = self.process_line(line['value'])  # Свойство
        property_value['prop_id'] = id

        # Ссылка на источник свойства
        property_source = self.process_line(line['definition'])
        property_source['property'] = id
        property_source['id'] = line['value']
        property_source['src'] = 'property_value_representation'
        self.property_sources.append(property_source)

        return property_value

    def property_value_association(self, line, id):
        """Добавление значения свойства"""
        item = self.process_line(line['described_element'])  # Объект, для которого указано свойство
        property_value = self.process_line(line['describing_property_value'])  # Свойство и его значение
        # Добавление в свойство ссылки на объект
        property_value['item'] = item
        # Добавление свойства в массив для последующей выгрузки
        self.properties[id] = property_value
        self.id_links[line['describing_property_value']] = id  # Для дальнейшего сопоставления

    def property_value_representation_relationship(self, line, id):
        """Добавление взаимосвязей свойств"""
        # print(self.id_links)
        related = self.id_links[line['related']]
        relating = line['relating']
        property_value = self.process_line(relating)
        property_value['item'] = self.properties[related]['item']  # Берем от родительского
        # Добавление свойства в массив для последующей выгрузки
        prop_value_id = related + id  # Т.к. нет связанной PROPERTY_VALUE_ASSOCIATION
        self.properties[prop_value_id] = property_value
        link = dict(model='PropertyValueRelation', id=id)
        link['parent_value'] = related
        link['child_value'] = prop_value_id
        link['link_type'] = line['relation_type']
        if 'description' in line:
            link['description'] = self.process_line(line['description'])
        self.put_to_result(link, id)

    def general_classification(self, line, id):
        # Получаем источник классификации и ее тип
        src, src_type = self.process_line(line['classification_source'])
        return src, src_type

    def classification_association(self, line, id):
        """Установка классификационных признаков"""
        # print(line)
        obj_id = line['classified_element']
        obj = self.process_line(obj_id)
        obj_pattern = self.get_pattern(obj_id)
        # print(obj)
        cl, cl_type = self.process_line(line['associated_classification'])
        # print(cl_type)
        if cl_type == 'plib_class_reference':
            if obj_pattern == 'ITEM_DEFINITION':
                # Определяем свойства классифицироующей связи
                class_line = self.data_lines[cl]
                # Создание связи с PLib-классом
                link_id = f"{obj}{cl}"  # Идентификатор связи
                vendor_plib_class = dict(model='VendorPlibClass', id=link_id, plib_class=cl,
                                         tool_product=obj, supplier_bsu=class_line['supplier_bsu'],
                                         version=class_line['version'])
                self.put_to_result(vendor_plib_class, link_id)
            else:
                # Ссылка на PLib-класс у свойства
                self.property_classes[obj_id] = cl

        elif cl_type == 'external_library_reference':
            if obj_pattern == 'ITEM_DEFINITION':
                # Указание свойства external_library_reference
                self.add_value_to_node(obj, 'external_library_reference', cl)
            # else: # Пока отключим, так как назначение не очевидно
                # self.property_sources.append(dict(id=id, property=obj_id, external_library_reference=cl))
        else:
            print(f'Неизвестный тип классификации {cl_type}')
