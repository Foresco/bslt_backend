from django.apps import AppConfig


class PriceConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'  # Тип ключевых полей по умолчанию
    name = 'jsonserv.supply'
    verbose_name = 'Закупки и поставки'