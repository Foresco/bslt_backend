from django.apps import AppConfig


class PdmConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'  # Тип ключевых полей по умолчанию
    name = 'jsonserv.pdm'
    verbose_name = 'PDM Управление производственными данными'

    def ready(self):
        # Обязательно подключаем получателей сигналов, чтобы они работали
        from jsonserv.pdm import receivers
