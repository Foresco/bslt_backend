from django.apps import AppConfig


class TooloverConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'  # Тип ключевых полей по умолчанию
    name = 'jsonserv.toolover'
    verbose_name = 'Инструментооборот'
