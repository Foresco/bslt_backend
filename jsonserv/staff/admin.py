from django.contrib import admin
from .models import StaffPosition, Person, PersonStaffPosition
# from jsonserv.core.admin import ListAdmin  # Класс для списков
# Функционал импорта
# from import_export.admin import ImportExportModelAdmin

admin.site.register(StaffPosition)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('person', 'person_profile')
    search_fields = ['person']
    ordering = ('person', )


@admin.register(PersonStaffPosition)
class PersonStaffPositionAdmin(admin.ModelAdmin):
    list_display = ('person', 'staff_position', 'place')
    search_fields = ['person']
    list_filter = ['staff_position', 'place']
    ordering = ('person', )
