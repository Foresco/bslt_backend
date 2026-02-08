from django.contrib import admin
from jsonserv.supply.models import Price, PriceType
from jsonserv.core.admin import ListAdmin


class PriceAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'supplied_entity', 'is_active', 'article')
    list_filter = ['supplier', 'supplied_entity']
    search_fields = ['supplied_entity']
    ordering = ('supplied_entity', 'is_active')


# Списки
admin.site.register(PriceType, ListAdmin)

# Со специальными настройками
admin.site.register(Price, PriceAdmin)
