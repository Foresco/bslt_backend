# Генератор обработки объектов конструкции для ЗАО СММ
from copy import copy
from jsonserv.core.generator import Generator
from jsonserv.pdm.models import Classification, PartObject


class GeneratorExt(Generator):
    """Расширенный класс для использования в коде"""

    def __init__(self):
        """Отключаем родительский инициализатор
        там есть лишнее (создание генератора)"""
        pass

    def process_before(self, itm):
        """Обработка экземпляра объекта до сохранения"""
        if itm.code and str(itm.code).endswith('СБ') and itm.part_type_id == 'document':
            # Установка классификацонной группы для сборочных чертежей
            # Проверка, что классификационная группа не указана
            if not itm.group_id:
                # Получение нужной классификационной группы
                cl_group = Classification.objects.filter(code='Сборочный чертеж').first()
                if cl_group:
                    itm.group = cl_group
                    if not itm.edt_sess:
                        # Если изменение идет после создания, то надо указать edt_sess иначе ошибка
                        itm.edt_sess = itm.crtd_sess_id 

    def process_after(self, itm):
        """Обработка экземпляра объекта после сохранения"""
        if itm.code and str(itm.code).endswith('СБ') and itm.part_type_id == 'document':
            # Запись форматов от родительского объекта
            if not itm.object_formats.all(): # Проверка, что у объекта нет форматов
                # Определение родительского объекта как обозначение без СБ
                parent_itm = PartObject.objects.filter(part_type='assembly', code=itm.code[:-2]).first()
                if parent_itm:  # Получение форматов родительского объекта
                    parent_formats = parent_itm.object_formats.all()
                    if parent_formats:  # Если нашлись форматы
                        # Копируем их для текущего объекта
                        for f in parent_formats:
                            new_f = copy(f)  # Создание новой связи
                            new_f.pk, new_f.id = None, None  # Убираем идентификаторы, чтобы создался новый объект
                            # Указываем ссылку на новый объект
                            new_f.part_object = itm
                            new_f.crtd_sess_id = itm.edt_sess if itm.edt_sess else itm.crtd_sess_id
                            new_f.save()
