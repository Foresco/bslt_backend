from django.contrib import admin

from .models import (RawProperty)


@admin.register(RawProperty)
class RawPropertyAdmin(admin.ModelAdmin):
    list_display = ('property_name', 'external_name', 'property_type')
    search_fields = ['property_name', 'external_name']
    list_filter = ['property_type']
    ordering = ('order_num', )
