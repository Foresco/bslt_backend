from django.apps import AppConfig


class BasaltalegasyConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'  # Тип ключевых полей по умолчанию
    name = 'jsonserv.basaltalegasy'
    verbose_name = 'Наследуемые данные'
