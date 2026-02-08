from django.apps import AppConfig


class DocarchiveConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'  # Тип ключевых полей по умолчанию
    name = 'jsonserv.docarchive'
    verbose_name = 'Управление архивом документации'

    def ready(self):
        # Обязательно подключаем получателей сигналов, чтобы они работали
        from jsonserv.docarchive import receivers
