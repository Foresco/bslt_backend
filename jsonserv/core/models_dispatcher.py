# Класс для поиска модели по имени
import logging
from django.apps import apps


# Класс сбора названий всех доступных моделей
class ModelsDispatcher:
    # Реализован по паттерну Singleton - создается только один экземпляр класса
    __instance = None  # Ссылка на единственный экземпляр

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(ModelsDispatcher, cls).__new__(cls)
        return cls.__instance

    # Список приложений, исключаемых из обработки
    exclude_apps = ('admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles', 'corsheaders',
                   'rest_framework', 'django_filters', 'django_extensions', 'basaltalegasy', 'vw')
    entities_classes = dict()   # Словарь для хранения всех классов моделей
    # entities_fields = dict()    # Словарь для хранения всех обязательных свойств сущностей
    required_fields = dict()    # Словарь для хранения обязательных полей сущностей
    track_link_classes = list()  # Список моделей, хранящих связи для отслеживания при замене
    same_link_classes = list()  # Список моделей, хранящих связи для отслеживания при создании подобного

    def __init__(self):
        # При инициализации класса переносим все модели из приложений в единые массив
        if not self.entities_classes:
            for app in apps.get_app_configs():
                if app.label in ModelsDispatcher.exclude_apps:  # Обрабатываем не все
                    continue
                for model in app.get_models():
                    k = model.__name__.lower()
                    ModelsDispatcher.entities_classes[k] = model
                    # Запись обязательных свойств в список и массив
                    # TODO: сделать точнее и гибче (get_required)
                    ModelsDispatcher.required_fields[k] = ('id', 'model')
                    if hasattr(model, 'BasaltaProps'):
                        if getattr(model.BasaltaProps, 'track_links', False):
                            ModelsDispatcher.track_link_classes.append(model)
                        if getattr(model.BasaltaProps, 'same_links', False):
                            ModelsDispatcher.same_link_classes.append(model)

    @staticmethod
    def get_entity_class_by_entity_name(entity_name):
        """Получение класса сущности по имени"""
        try:
            # Имя приводится к нижнему регистру для единообразия
            return ModelsDispatcher.entities_classes[entity_name.lower()]
        except KeyError as e:
            logging.error('Среди моделей не найдена '+entity_name)
            raise

    @staticmethod
    def get_required(entity):
        """Получение списка обязательных полей"""
        # fields = model_class._meta.fields  # получение полей класса
        pass

    @staticmethod
    def check_required(entity_name, props_list):
        """Проверка наличия обязательных свойств в переданном списке"""
        return all(elem in props_list for elem in ModelsDispatcher.required_fields[entity_name])
