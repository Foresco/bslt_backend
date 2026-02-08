# Дополнительные утилиты конвертации данных
# Словарь соответствий идентификаторов массивов и классов
dims = {
    1: 'partobject',
    2: 'classification'
}


part_types = {
    1:  'document',
    2:  'complex',
    3:  'assembly',
    4:  'detail',
    5:  'standart',
    6:  'other',
    7:  'material',
    8:  'complect',
    9:  'sortament',
    10: 'exemplar',
    12: 'rigging',
    13: 'tool',
    14: 'equipment',
    15: 'tare',
    16: 'device',
    21: 'letter'
}


def part_type_chg(type_id, unit_id):
    return dict(part_type=part_types[int(type_id)])


def str_val_chg(fld):
    def str_val_named_chg(str_value, unit_id):
        a = dict()
        a[fld] = str_value
        return a
    return str_val_named_chg


def int_val_chg(fld):
    def int_val_named_chg(int_value, unit_id):
        a = dict()
        a[fld] = str(int_value)
        return a
    return int_val_named_chg


def float_val_chg(fld):
    def float_val_named_chg(float_value, unit_id):
        a = dict()
        a[fld] = str(float_value)
        return a
    return float_val_named_chg


def bool_val_chg(fld):
    def bool_val_named_chg(bool_value, unit_id):
        a = dict()
        a[fld] = bool_value == 1
        return a
    return bool_val_named_chg


# Словарь соответсвий параметров
params = {
    1:  part_type_chg, # Тип
    2: str_val_chg('code'),  #Обозначение
    3: str_val_chg('title'),  # Наименование
    # 4 Документ
    # 5 Формат
    6: str_val_chg('abbr'),  # Кратко
    7: bool_val_chg('is_top'),  # Готовое изделие
    8: str_val_chg('nom_code'),  #  Номенклатурный код
    9: int_val_chg('source'),  # Источник поступления
    # 10 Группа
    # 11 Единица измерения
    12: float_val_chg('weight'),  #  Чистый вес
    13: int_val_chg('preference'),  #  Предпочтительность
    # 14 Иллюстрация
    15: str_val_chg('title'),  # Примечание
    16: int_val_chg('state'),  #  Состояние
    # 22 Материал
    # 42 Толщина (диаметр)
    # 74 Сортамент
    # 75 Высота (ширина)
    # 76 Толщина стенки
    # 77 Типоразмер
    # 106 Литера
    # 124 Единица измерения размера
    166: str_val_chg('surface')  # Параметры обработки
}

# Словарь соответствий единиц измерения
units= {
    1: 'шт.'
}


# Функция формирования строки изменений
def get_change(param_id, param_value, unit_id):
    if param_id in params:
        func = params[param_id]
        return func(param_value, unit_id)
    return None