from django.apps import AppConfig


class ManufactureConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'  # Тип ключевых полей по умолчанию
    name = 'jsonserv.manufacture'
    verbose_name = 'Управление производством'

    def ready(self):
        # Обязательно подключаем получателей сигналов, чтобы они работали
        from jsonserv.manufacture import receivers
