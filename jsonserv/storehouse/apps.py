from django.apps import AppConfig


class StorehouseConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'  # Тип ключевых полей по умолчанию
    name = 'jsonserv.storehouse'
    verbose_name = 'Управление складом'
