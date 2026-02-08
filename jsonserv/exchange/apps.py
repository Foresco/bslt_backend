from django.apps import AppConfig


class ExchangeConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'  # Тип ключевых полей по умолчанию
    name = 'jsonserv.exchange'
    verbose_name = 'Поддержка обменов данными'
