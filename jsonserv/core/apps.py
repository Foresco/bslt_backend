from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'  # Тип ключевых полей по умолчанию
    name = 'jsonserv.core'
    verbose_name = 'Основные данные'
