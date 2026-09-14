# Функциональность для экспорта данных
import json
from django.db import models
from jsonserv.core.models_dispatcher import ModelsDispatcher

def get_real_entity_item(itm):
    # Определяем модель типа объекта т.к. она скорее всего не Entity
    # а PartObject или что-то еще
    source_model = ModelsDispatcher.get_entity_class_by_entity_name(itm.type_key.pk)
    return source_model.objects.get(pk=itm.pk)


class JsonExport:
    """Класс с функциональностью экспорта в JSON"""
    # Поля, исключаемые из экспорта
    exclude_fields = ('crtd_sess', 'edt_sess', 'dlt_sess', 'link_ptr', 'link_class')

    def ref_get(self):
        """Формирование ссылки на объект"""
        return f'{self.__class__.__name__}.{self.pk}'

    def to_json(self):
        """Метод выгрузки данных в JSON"""
        all_items = list()  # Собранный список объектов
        item_data = dict() # Данные об объекте
        for field in self._meta.fields:
            field_name = field.name
            if field_name in JsonExport.exclude_fields:
                # Поля из списка исключений пропускаем
                continue
            if field_name == 'id':
                # Идентификатор записываем по-другому
                item_data[field_name] = self.ref_get()
                continue
            if field_name == 'code':
                print(getattr(self, field_name))
            if isinstance(field, models.ForeignKey):
                # Если это ссылка на объект, то записываем ссылку
                # print(field_name)
                f_obj = getattr(self, field_name)
                if f_obj is not None:
                    # print(field_name)
                    if f_obj.__class__.__name__ == 'Entity':
                        f_obj = get_real_entity_item(f_obj)
                    # Записываем ссылку
                    item_data[field_name] = f_obj.ref_get()
                    print(item_data[field_name])
                    # Добавляем описание в массив
                    all_items += f_obj.to_json()
            else:
                # Просто значение
                item_data[field_name] = getattr(self, field_name)
        # Добавляем название модели
        item_data['model'] = self.__class__.__name__
        all_items.append(item_data)  # Добавляем сам объект в список
        return all_items
