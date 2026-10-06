# Функциональность для экспорта данных
import json
from django.db import models
from jsonserv.core.models_dispatcher import ModelsDispatcher


class JsonExport:
    """Класс с функциональностью экспорта в JSON"""
    # Поля, исключаемые из экспорта
    exclude_fields = ('id',
    'crtd_sess', 'edt_sess', 'dlt_sess', 'link_ptr', 'link_class', 'entity_ptr', 'view_right', 'edit_right',
    'value_right', 'rating')

    def __init__(self):
        # TODO: сделать свойством класса
        self.md = ModelsDispatcher()  # Диспетчер, для поиска моделей по наименованию

    def get_real_entity_item(self, itm):
        # TODO: Сделать методом класса
        # Определяем модель типа объекта т.к. она скорее всего не Entity
        # а PartObject или что-то еще
        source_model = self.md.get_entity_class_by_entity_name(itm.type_key.pk)
        return source_model.objects.get(pk=itm.pk)

    def ref_get(self):
        """Формирование ссылки на объект"""
        return f'{self.__class__.__name__}.{self.pk}'

    def children_for_export_get(self):
        """Получение списка связанных потомков"""
        yield from ()  # По умолчанию пустой итератор

    def to_json(self, all_item_ids):
        """Метод выгрузки данных в JSON
        all_item_ids - list()  # Собранный список уникальных идентификаторов объектов"""
        # Добавляем идентификатор id, он формируется по особому алгоритму для каждой модели
        ref_id = self.ref_get()
        if ref_id in all_item_ids:
            # Если объект с таким идентификатором ранее выгружался
            return None  # Останавливаемся и ничего не выгружаем
        # Добавляем идентификатор в список экспортированных
        all_item_ids.append(ref_id)
        all_items = list()  # Собранный список объектов
        item_data = dict()  # Данные об объекте
        item_data['id'] = ref_id
        # Перебираем все поля модели
        for field in self._meta.fields:
            field_name = field.name
            # print(field_name)
            if field_name in JsonExport.exclude_fields:
                # Поля из списка исключений пропускаем
                continue

            if field_name == 'code':
                print(getattr(self, field_name))
            if isinstance(field, models.ForeignKey):
                # Если это ссылка на объект, то записываем ссылку
                f_obj = getattr(self, field_name)
                if f_obj is not None:
                    if f_obj.__class__.__name__ == 'Entity':
                        f_obj = self.get_real_entity_item(f_obj)
                    # Записываем ссылку
                    item_data[field_name] = f_obj.ref_get()
                    # Добавляем описание в массив
                    descr_arr = f_obj.to_json(all_item_ids)
                    if descr_arr:
                        # Если что-то было получено
                        all_items += descr_arr
            else:
                # Просто значение
                attr_value = getattr(self, field_name)
                if attr_value:  # Записываем только если есть значение
                    item_data[field_name] = attr_value
        # Добавляем название модели
        item_data['model'] = self.__class__.__name__
        all_items.append(item_data)  # Добавляем сам объект в список
        # Добавление связей с потомками и описаний потомков
        # У каждого класса должен быть метод, возвращающий связаные с ним экземпляры
        for child_link in self.children_for_export_get():
            # Добавляем связь в массив
            all_items += child_link.to_json(all_item_ids)
        return all_items
