from django.contrib import admin
from .models import (ToolClass, ToolProduct, PlibClass, VendorPlibClass,
                     PlibProperty, SpecificClass, SpecificClassification,
                     GtcPackage, GtcProperty, GtcPropertyClass, MainGtcPropertyClass,
                     ToolSource, ToolState, ToolPreference)
from jsonserv.core.admin import ListAdmin


class ToolClassAdmin(admin.ModelAdmin):
    list_display = ('class_id', 'class_name', 'parent')
    list_filter = ['parent']
    search_fields = ['class_name']
    ordering = ('class_id', 'class_name', )


class ToolProductAdmin(admin.ModelAdmin):
    list_display = ('code', 'product_id', 'description')
    # list_filter = ['parent']
    search_fields = ['code']
    ordering = ('code', )


class PlibClassAdmin(admin.ModelAdmin):
    list_display = ('code', 'class_name', 'parent')
    list_filter = ['parent']
    search_fields = ['class_name']
    ordering = ('class_name', 'code', )


class VendorPlibClassAdmin(admin.ModelAdmin):
    list_display = ('plib_class', 'supplier_bsu', 'version')
    list_filter = ['plib_class']
    ordering = ('plib_class', 'supplier_bsu', )


class PlibPropertyAdmin(admin.ModelAdmin):
    list_display = ('code', 'property_name')
    ordering = ('code', )


# class VendorPlibPropertyAdmin(admin.ModelAdmin):
#     list_display = ('plib_property', 'name_scope')
#     ordering = ('plib_property', )


class SpecificClassificationAdmin(admin.ModelAdmin):
    list_display = ('tool_product', 'specific_class')
    ordering = ('tool_product',)


class GtcPropertyAdmin(admin.ModelAdmin):
    list_display = ('gtc_application', 'gtc_generic', 'plib_property', 'property_index', 'main_location', 'item_type')
    list_filter = ['main_class', 'property_class']
    # search_fields = ['class_name']
    ordering = ('property_index', 'taxonomy_application',)


# Списки значений
admin.site.register(ToolSource, ListAdmin)
admin.site.register(ToolState, ListAdmin)
admin.site.register(ToolPreference, ListAdmin)
admin.site.register(MainGtcPropertyClass, ListAdmin)
admin.site.register(GtcPropertyClass, ListAdmin)
admin.site.register(SpecificClass, ListAdmin)


# Со специальными настройками
admin.site.register(ToolProduct, ToolProductAdmin)
admin.site.register(ToolClass, ToolClassAdmin)
admin.site.register(PlibClass, PlibClassAdmin)
admin.site.register(VendorPlibClass, VendorPlibClassAdmin)
admin.site.register(PlibProperty, PlibPropertyAdmin)
# admin.site.register(VendorPlibProperty, VendorPlibPropertyAdmin)
admin.site.register(SpecificClassification, SpecificClassificationAdmin)
admin.site.register(GtcProperty, GtcPropertyAdmin)
