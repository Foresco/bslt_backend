# Модуль с полезным фукнционалом для обмена
import logging
import json
from datetime import datetime as dt
import os.path
from django.db.models.fields.related import ForeignKey, ManyToManyField  # Класс для определения внешних ключей
from django.conf import settings  # для обращения к настройкам

from jsonserv.core.models import Entity, UserSession as usr_sess # Для доступа к сессиям
from jsonserv.exchange.models import ExchangeSession, ExternalID
from jsonserv.core.models_dispatcher import ModelsDispatcher


# Порядок использования:
# Наполняем промежуточный массив с помощью add_to_load
# Готовим данные к импорту
# Выполняем импорт процедурой import_loaded
class DataImporter:
    """Класс с функционалом импорта из списков словарей со свойствами"""
    # Предназначенные для импорта элементы предварительно загружаются в массив для упорядоченного импорта
    items_to_import = dict()  # Экземпляры для импорта
    imported_ids = dict()  # Импортированные идентификаторы и сопоставленные им внутренные идентификаторы
    ModelsDispatcher = ModelsDispatcher()
    exclude_props = ('id', )  # Имена полей, исключаемые из передаваемого на импорт массива
    # Дополнительные поля, их нет в моделях, но их нужно обработать
    extra_fields = ('src', 'archive_id', 'watermark_date')
    # Например, исходное расположение файла src
    # Указатель файлового архива archive
    # Дата для вставки в метку watermark_date
    json_file_name = ''  # Имя файла для сохранения данных
    session_id = 1  # Идентификатор сессии, выполняющей запись данных
    partner = None  # Партнер источник данных
    exchange_session = None  # Сессия обмена данными

    def clear(self):
        """Очистка накопленных массивов"""
        self.items_to_import = dict()
        self.imported_ids = dict()

    def __init__(self):
        # Инициализация логирования
        # Уникальное имя на основе даты и времени
        date_time = dt.now().strftime("%Y%m%d-%H%M%S")
        log_file_name = date_time + '.log'

        log_target_dir = getattr(settings, 'LOG_DIR', 'jsonserv/logs')
        log_file_name = os.path.join(log_target_dir, log_file_name)
        # Используется при генерации json-файлов
        self.json_target_dir = getattr(settings, 'TEMP_DIR', 'temp')

        logging.basicConfig(level=logging.INFO,
                            handlers=[logging.FileHandler(log_file_name, 'w', 'utf-8')],
                            format='%(asctime)s %(levelname)-8s %(message)s',
                            datefmt='%y-%m-%d %H:%M',
                            )
        logging.info('Начало импорта')

        # Инициализация сессии обмена
        self.exchange_session = ExchangeSession(partner=self.partner, direction='I', exchange_datetime=dt.now().date())
        self.exchange_session.save()

    def set_session_id(self, session_id):
        self.session_id = session_id
        logging.info(f'Идентификатор сессии {self.session_id}')

    def set_session(self):
        self.session = usr_sess.get_session_by_id(self.session_id)

    def is_in_loaded(self, exter_id):
        return exter_id in self.items_to_import

    def add_to_load(self, exter):
        """Предварительное наполнение массива элементами для импорта с контролем уникальности"""
        if 'id' in exter:  # Если в массиве есть id
            if not self.is_in_loaded(exter['id']):  # Ранее добавленные пропускаем
                self.items_to_import[exter['id']] = exter  # В словарь предназаняенных для импорта
            return 0
        else:
            logging.error('Объект {} не имеет атрибута id'.format(exter))
            return 1  # Ошибка - нет идентификатора

    def save_external_id(self, exter_id, internal):
        """Запись информации о внешнем идентификаторе в базу данных"""
        # Проверка принадлежности объекта с потомкам Entity
        # Пока идентификаторы сохраняются только для них
        if isinstance(internal, Entity):
            obj, created = ExternalID.objects.get_or_create(
                internal=internal,
                partner=self.partner,
                external_id=exter_id,
                defaults=dict(
                    internal=internal,
                    partner=self.partner,
                    external_id=exter_id,
                    exchange_session=self.exchange_session
                )
            )

    def add_to_imported(self, exter_id, internal):
        """Фиксация импортированных в массиве импортированных"""
        self.imported_ids[exter_id] = internal
        self.save_external_id(exter_id, internal)

    def get_from_external(self, ext_id):
        internal_object = ExternalID.objects.filter(
            partner=self.partner, external_id=ext_id, internal__dlt_sess=0
        ).first()
        if internal_object:  # Такой объект найден
            return internal_object.internal.get_inheritor()  # Получаем наследника Entity
        return None

    def is_in_imported(self, ext_id):
        if ext_id in self.imported_ids:
            return True
        # Пробуем найти по идентификатору
        internal = self.get_from_external(ext_id)
        if internal:
            # Добавляем полученный id в словарь импортированных
            logging.info(f'{internal} Найден по внешней ссылке {ext_id}. Взят.')
            self.imported_ids[ext_id] = internal
            return True
        return False

    def get_imported(self, ext_id):
        return self.imported_ids[ext_id]

    def get_loaded(self, ext_id):
        if ext_id in self.items_to_import:
            return self.items_to_import[ext_id]
        else:
            logging.error(f'Объекта нет среди импортированных. Ссылка {ext_id}')
            return None

    def get_item_ref_or_import(self, ext_id):
        """Получение идентификатора в БД ранее импортированного объекта"""
        if not self.is_in_imported(ext_id):
            item_dict = self.get_loaded(ext_id)  # Получаем словарь со свойствами
            if item_dict:
                # Импортируем объект
                result = self.import_item_from_dict(item_dict)
                # Добавляем полученный id в словарь импортированных
                self.add_to_imported(ext_id, result)
            else:
                # Ссылка была ошибочной
                logging.error(f'Свойства объекта не найдены. Ссылка {ext_id}')
                return None
        # Возвращаем id в базе данных
        return self.get_imported(ext_id)

    def prepare_item_dict(self, model_ref, prop_dict):
        """Преобразование и подготовка словаря свойств экземпляра сущности"""
        # Перебор всех свойств класса, замена ссылок на ссылки из базы данных
        fields = model_ref._meta.get_fields() # fields  # получение полей класса
        prepared_props = dict()  # Словарь с результатами подготовки
        many_to_many_links = list()  # Список связей многие-ко-многим (у импортируемого объекта)
        # Перебираем все поля модели-получателя
        for f in fields:
            prop_name = f.name
            if prop_name in self.exclude_props:  # Исключаемые свойства пропускаем
                continue
            # Если данное свойство передано в массиве
            if prop_name in prop_dict:
                if isinstance(f, ForeignKey):  # Если это поле-ссылка
                    if prop_dict[prop_name]:  # Если свойство заполнено (иначе ничего не делаем)
                        # Получаем по ней ссылку на сам объект
                        # Если его нет среди импортированных он будет предварительно импортирован
                        value = self.get_item_ref_or_import(prop_dict[prop_name])
                    else:
                        continue
                elif isinstance(f, ManyToManyField):  # Если это поле-ссылка многие-ко-многим
                    if prop_dict[prop_name]:  # Если свойство заполнено (иначе ничего не делаем)
                        # Получаем по ней ссылку на сам объект
                        # Если его нет среди импортированных он будет предварительно импортирован
                        value = self.get_item_ref_or_import(prop_dict[prop_name])
                        # Добавляем в отельный список связей многие-ко-многим
                        many_to_many_links.append(dict(name=prop_name, value=value))
                        continue  # В словарь значений эти поля не добавляем, они идут отдельным атрибутом
                    else:
                        continue
                else:
                    value = prop_dict[prop_name]
                prepared_props[prop_name] = value
                # TODO: Сделать контроль наличия обязательных свойств (использовать механизмы модели)
            elif prop_name == 'crtd_sess':
                # Добавление идентификатора сессии
                prepared_props['crtd_sess'] = self.session
        if many_to_many_links:
            # Если были сформированы связи многие-ко-многим
            prepared_props['many_to_many_links'] = many_to_many_links
        # Обработка дополнительных полей
        for extra_field in self.extra_fields:
            if extra_field in prop_dict:
                prepared_props[extra_field] = prop_dict[extra_field]
        # print(prepared_props)
        return prepared_props

    def create_many_to_many(self, item, many_to_many_links):
        """Создание связей многие-ко-многим для указанного объекта"""
        while len(many_to_many_links) > 0:
            lnk = many_to_many_links.pop()
            ref = getattr(item, lnk['name'], None)
            if ref:
                ref.add(lnk['value'])  # Добавляем связь
            else:
                logging.error('Связь {} у объекта не найдена'.format(lnk['name']))

    def import_item_from_dict(self, item_dict, update_exist=False):
        """Создание экземпляра сущности на основе словаря со свойствами"""
        # Определяем название соответствующей модели
        target_model_name = item_dict['model']
        # Получаем модель по названию
        try:
            target_model = ModelsDispatcher.get_entity_class_by_entity_name(target_model_name)
        except Exception as e:
            logging.error(e)
            return
        # Готовим массив свойств
        prepared_props = self.prepare_item_dict(target_model, item_dict)
        many_to_many_links = prepared_props.pop('many_to_many_links', '')  # Предварительно вырезаем из словаря
        # Создаем новый объект в базе данных
        # get_or_create_item ДОЛЖЕН БЫТЬ У КАЖДОЙ МОДЕЛИ!!!
        # print(target_model_name)
        # print(prepared_props)
        new_item, created = target_model.get_or_create_item(prepared_props)
        message = 'создан' if created else 'найден'
        logging.info(f'{new_item} {message}')
        if new_item and update_exist and not created:
            # Если указана необходимость обновления и объект существовал
            if not target_model_name == 'SystemUser':  # SystemUser не обновляем - стирается пароль
                target_model.objects.filter(pk=new_item.pk).update(**prepared_props)
                logging.info(f'{new_item} свойства обновлены')
        # Создание связей многие-ко-многим
        if many_to_many_links:
            self.create_many_to_many(new_item, many_to_many_links)
        return new_item

    def import_loaded(self):
        """Создание экземпляров на основе загруженного массива"""
        logging.info('Начало загрузки данных в базу')
        for ext_id in self.items_to_import:
            # если есть среди импортированных идем дальше
            if self.is_in_imported(ext_id):
                continue
            item_dict = self.get_loaded(ext_id)  # Получаем словарь со свойствами
            # импортируем из словаря
            result = self.import_item_from_dict(item_dict)
            if result:
                # Добавляем полученный id в словарь импортированных
                self.add_to_imported(ext_id, result)

    def dump_loaded(self, file_name=''):
        """Сохранение загруженного массива в json-файл"""
        if not file_name:
            # Имя файла для сохранения данных
            date_time = dt.now().strftime("%Y%m%d-%H%M%S")
            file_name = date_time + '.json'
            file_name = os.path.join(self.json_target_dir, file_name)
        with open(file_name, 'w', encoding='utf-8') as json_file:
            json.dump(self.items_to_import, json_file)

    @staticmethod
    def write_to_log(message_type, message_text):
        """Запись в лог извне"""
        if message_type == 'info':
            logging.info(message_text)
        if message_type == 'error':
            logging.error(message_text)
        if message_type == 'warning':
            logging.warning(message_text)


class DataExporter:

    def __init__(model_name):
        pass
