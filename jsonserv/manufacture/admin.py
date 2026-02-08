from django.contrib import admin
from jsonserv.core.admin import ListAdmin  # Классы для списков

from .models import (OrderLinkTpRowState, ProdOrderState, SupplyState, ProdOrder)

admin.site.register(OrderLinkTpRowState, ListAdmin)
admin.site.register(ProdOrderState, ListAdmin)
admin.site.register(SupplyState, ListAdmin)


@admin.register(ProdOrder)
class ProdOrderAdmin(admin.ModelAdmin):
    list_display = ('code', 'title')
    search_fields = ['code', 'title']
    ordering = ('code', )
