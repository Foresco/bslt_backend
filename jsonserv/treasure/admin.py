from django.contrib import admin
from jsonserv.core.admin import ListAdmin

from .models import WeightNormSet, WeightNorm, WeightNormType


@admin.register(WeightNormSet)
class WeightNormSetAdmin(admin.ModelAdmin):
    list_display = ('entity', 'material', 'norm_document')
    search_fields = ['entity']
    list_filter = ['material', 'norm_document']
    ordering = ('entity', ) # Порядок сортировки в списке


@admin.register(WeightNorm)
class WeightNormSetAdmin(admin.ModelAdmin):
    list_display = ('norm_set', 'norm_type', 'norm', 'unit')
    search_fields = ['entity']
    list_filter = ['norm_type', ]
    ordering = ('norm_set', 'norm_type') # Порядок сортировки в списке

# Простые списки
admin.site.register(WeightNormType, ListAdmin)