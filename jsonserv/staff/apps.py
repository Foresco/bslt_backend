from django.apps import AppConfig


class StaffConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'  # Тип ключевых полей по умолчанию
    name = 'jsonserv.staff'
    verbose_name = 'Штатное расписание'
