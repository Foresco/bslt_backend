from django.contrib import admin
from django.contrib.auth.models import Permission  # Для возможности администрировать права

from .models import (MenuItem, Enterprise, EntityType, Panel, TypePanel, TypeSetting, FormField,
                     PlaceType, Place, DownloadCheckGroup,
                     Report, ReportParam, UserProfile, ExtraLink, TypeExtraLink,
                     Essence, MeasureUnit, Property, PropertyValue, PropertyValueRelation, 
                     PropertyUnit, MeasureSystem)
# Функционал импорта
# from import_export.admin import ImportExportModelAdmin


class ListAdmin(admin.ModelAdmin):  # Общий на все списки во всех моделях класс администратор
    list_display = ('list_value', 'order_num', 'is_default')
    search_fields = ('list_value', )  # Поля, по которым возможен текстовый поиск
    ordering = ('order_num', 'list_value')  # Порядок сортировки в списке


class CodedListAdmin(admin.ModelAdmin):  # Общий на все списки кодами во всех моделях класс администратор
    list_display = ('list_value', 'value_code', 'order_num', 'is_default')
    search_fields = ('list_value', 'value_code')  # Поля, по которым возможен текстовый поиск
    ordering = ('order_num', )  # Порядок сортировки в списке


class StructuredListAdmin(admin.ModelAdmin):  # Общий на все структурированные списки во всех моделях класс администратор
    list_display = ('list_value', 'value_code', 'order_num', 'is_default', 's_key')
    search_fields = ('list_value', 'value_code')  # Поля, по которым возможен текстовый поиск
    list_filter = ('s_key', )  # Поля для фильтрации
    ordering = ('s_key', 'order_num', )  # Порядок сортировки в списке


class MenuItemAdmin(admin.ModelAdmin):
    # form = MenuItemForm # Далее надо будет разобраться как подключать более сложные формы
    list_display = ('item_name', 'caption', 'parent', 'order_num', 'item_right')
    list_filter = ['parent']
    search_fields = ['caption']


class EntityTypeAdmin(admin.ModelAdmin):
    list_display = ('type_key', 'type_name')
    search_fields = ['type_name']
    ordering = ('type_key', )


class PanelAdmin(admin.ModelAdmin):
    list_display = ('panel_name', 'area', 'description', 'view_right', 'edit_right')
    list_filter = ('area', )


class TypePanelAdmin(admin.ModelAdmin):
    list_display = ('type_key', 'panel', 'in_list', 'in_single', 'view_right', 'edit_right')
    list_filter = ['type_key', 'in_list', 'in_single']
    ordering = ('type_key', 'panel', 'in_list')

# Вариант с импортом
# class ClassificationAdmin(ImportExportModelAdmin):
#     search_fields = ['code']


class ClassificationAdmin(admin.ModelAdmin):
    list_display = ('code', 'group')
    # list_filter = ['parent', ]
    search_fields = ['code']
    ordering = ('code', )


class FormFieldAdmin(admin.ModelAdmin):
    list_display = ('caption', 'form_name', 'field_name', 'order_num')
    list_filter = ['form_name', 'field_name']


class PlaceAdmin(admin.ModelAdmin):
    list_display = ('place_type', 'code', 'short_name')
    search_fields = ['code', 'place_type']
    list_filter = ['place_type', 'is_point']
    ordering = ('place_type', 'code', )


class PropertyAdmin(admin.ModelAdmin):
    list_display = ('property_name', 'property_name_rus', 'order_num', 'property_type')
    search_fields = ['property_name', ]
    list_filter = ['property_type', ]
    ordering = ('order_num', 'property_name')


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'user')
    search_fields = ['user_name', ]
    # list_filter = ['is_group', ]
    ordering = ('user_name',)


class MeasureUnitAdmin(admin.ModelAdmin):
    list_display = ('unit_name', 'short_name', 'essence', 'order_num')
    list_filter = ['essence']
    search_fields = ['unit_name']
    ordering = ('essence', 'order_num', 'unit_name')


class PropertyValueAdmin(admin.ModelAdmin):
    list_display = ('entity', 'property', 'value', 'value_min', 'unit', 'value_number')
    list_filter = ['property']
    search_fields = ['entity', 'property']
    ordering = ('entity', 'property', 'value_number')


class PropertyValueRelationAdmin(admin.ModelAdmin):
    list_display = ('parent_value', 'child_value', 'link_type')
    ordering = ('parent_value', 'child_value')


class PropertyUnitAdmin(admin.ModelAdmin):
    list_display = ('property', 'measure_unit')
    list_filter = ['measure_unit']
    ordering = ('property', 'measure_unit')


class ReportParamInline(admin.TabularInline):
    model = ReportParam


class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_name', 'title', 'module_url')
    search_fields = ['title', 'report_name']
    ordering = ('title', 'report_name')
    inlines = [
        ReportParamInline,
    ]


class ReportParamAdmin(admin.ModelAdmin):
    list_display = ('report', 'param_name', 'caption', 'order_num')
    list_filter = ['report']
    search_fields = ['report', 'param_name', 'caption']
    ordering = ('report', 'order_num')


class TypeExtraLinkAdmin(admin.ModelAdmin):
    list_display = ('type_key', 'extra_link')
    list_filter = ['type_key', 'extra_link']
    ordering = ('type_key', 'extra_link')


class TypeSettingAdmin(admin.ModelAdmin):
    list_display = ('type_key', 'dashboard', 'page_header')
    list_filter = ('type_key', )


class DownloadCheckGroupAdmin(admin.ModelAdmin):
    list_display = ('group_name', 'download_limit_day', 'download_limit_month', 'download_limit_year')
    search_fields = ['group_name', ]
    # list_filter = ['is_group', ]
    ordering = ('group_name',)


# Со специальными настройками
admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(EntityType, EntityTypeAdmin)
admin.site.register(Panel, PanelAdmin)
admin.site.register(TypePanel, TypePanelAdmin)
admin.site.register(FormField, FormFieldAdmin)
admin.site.register(Place, PlaceAdmin)
admin.site.register(Property, PropertyAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(MeasureUnit, MeasureUnitAdmin)
admin.site.register(PropertyValue, PropertyValueAdmin)
admin.site.register(PropertyValueRelation, PropertyValueRelationAdmin)
admin.site.register(PropertyUnit, PropertyUnitAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(ReportParam, ReportParamAdmin)
admin.site.register(TypeExtraLink, TypeExtraLinkAdmin)
admin.site.register(TypeSetting, TypeSettingAdmin)
admin.site.register(DownloadCheckGroup, DownloadCheckGroupAdmin)

# Без специальных настроек
admin.site.register(Essence)
admin.site.register(Permission)
admin.site.register(Enterprise)
admin.site.register(ExtraLink)

# Простые списки
admin.site.register(PlaceType, ListAdmin)
admin.site.register(MeasureSystem, ListAdmin)
