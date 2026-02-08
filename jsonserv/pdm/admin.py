from django.contrib import admin
from jsonserv.core.admin import ListAdmin, CodedListAdmin  # Классы для списков
from .models import (PartFormat, PartObject, PartType, Notice, Operation, PartState, PartSource, PartLitera, ChangeType,
                     RenditionTail, PartPreference, Role, NoticeType, NoticeReason, NormUnit, Stage, TpRowType)


@admin.register(PartType)  # Альтернативный вариант привязки модели к админ-классу
class PartTypeAdmin(admin.ModelAdmin):
    list_display = ('part_type', 'type_name', 'order_num', 'doc_key', 'code_join', 'value_right')
    list_filter = ['doc_key', ]
    search_fields = ['type_name']
    ordering = ('order_num', )  # Порядок сортировки в списке


class PartObjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'part_type', 'title')
    list_filter = ['part_type']
    search_fields = ['code', 'title']
    ordering = ('part_type', 'code', )


class NoticeAdmin(admin.ModelAdmin):
    list_display = ('code', 'notice_type', 'notice_date')
    search_fields = ['code', ]
    list_filter = ['notice_type', ]
    ordering = ('notice_date', 'code', )


class OperationAdmin(admin.ModelAdmin):
    list_display = ('operation_name', 'operation_code', 'group')
    search_fields = ['operation_name', ]
    # list_filter = ['notice_type', ]
    ordering = ('operation_name', 'operation_code', )


class PartStateAdmin(ListAdmin):
    list_display = ('list_value', 'order_num', 'is_default', 'view_right', 'edit_right')


# Со специальными настройками
admin.site.register(PartObject, PartObjectAdmin)
admin.site.register(Notice, NoticeAdmin)
admin.site.register(Operation, OperationAdmin)
admin.site.register(PartState, PartStateAdmin)
# Простые списки
admin.site.register(PartSource, ListAdmin)
admin.site.register(PartLitera, ListAdmin)
# admin.site.register(NoticeReserve, ListAdmin)
admin.site.register(ChangeType, ListAdmin)
admin.site.register(RenditionTail, ListAdmin)
admin.site.register(PartPreference, ListAdmin)
admin.site.register(PartFormat, ListAdmin)
admin.site.register(Role, ListAdmin)
admin.site.register(TpRowType, ListAdmin)
# Списки с кодами
admin.site.register(NoticeType, CodedListAdmin)
admin.site.register(NoticeReason, CodedListAdmin)
# Без специальных настроек
# admin.site.register(PartLink)
# admin.site.register(DesignRole)
# admin.site.register(Rendition)
# admin.site.register(NoticeLink)
# admin.site.register(NoticeRecipient)
# admin.site.register(TypeSizeSort)
# admin.site.register(TypeSizeMater)
# admin.site.register(DesignMater)
# admin.site.register(PartObjectFormat)
# admin.site.register(DesignerRating)
admin.site.register(NormUnit)
admin.site.register(Stage)
