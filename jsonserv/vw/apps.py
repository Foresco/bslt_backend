from django.apps import AppConfig


class VwConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'  # Тип ключевых полей по умолчанию
    name = 'jsonserv.vw'
    verbose_name = 'Специализированные представления'
