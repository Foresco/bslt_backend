# Генератор обозначений для производственных заказов
from datetime import datetime
from jsonserv.core.generator import Generator


class GeneratorExt(Generator):
    """Расширенный класс для использования в коде"""

    def __init__(self):
        """Установка значений для фильтрации"""
        gen_params = dict() # Параметры работы генератора
        gen_params['generator_name'] = 'prodorder'  # Название генератора
        now = datetime.now()
        year = now.year
        gen_params['div'] = year  # Раздел генерации
        super().__init__(gen_params)

    def gen_new_code(self):
        number_item = self.get_current_value() + 1
        self.set_new_value(number_item)
        now = datetime.now()
        year = now.year
        # Преобразуем в формат 0023/22
        return '{}/{}'.format(str(number_item).zfill(4), str(year)[-2:])

    def process_before(self, itm):
        """Обработка экземпляра объекта до сохранения"""
        # if not itm.code:  # Обозначение генерируем только если оно не указано
        itm.code = self.gen_new_code()  # Генерируем обозначение
