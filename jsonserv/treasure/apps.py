from django.apps import AppConfig


class TreasureConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'  # Тип ключевых полей по умолчанию
    name = 'jsonserv.treasure'
    verbose_name = 'Учет драгоценных металлов'
