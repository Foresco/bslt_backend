# Базовый класс генератора обозначений
from jsonserv.core.models import GenerateNumber


class Generator:
    """Класс генератора по умолчанию
    реализует базовую функциональность генерации"""

    def __init__(self, params=dict()):
        """Установка значений для фильтрации"""
        # Извлечение значения генератора
        self.item, created = GenerateNumber.get_or_create_item(params)

    def get_current_value(self):
        """Получение текущего значения генератора"""
        return self.item.get_current_number()

    def set_new_value(self, new_value):
        """Установка нового значения генератора"""
        self.item.current_number = new_value
        self.item.save()

    def process_before(self, itm):
        """Обработка экземпляра объекта до сохранения
        по умолчанию не обрабатывается
        в дочерних классах может быть изменено"""
        pass
    
    def process_after(self, itm):
        """Обработка экземпляра объекта после сохранения
        по умолчанию не обрабатывается
        в дочерних классах может быть изменено"""
        # ВНИМАНИЕ! В методе не должно быть действий, редактирующих сам объект
        pass
