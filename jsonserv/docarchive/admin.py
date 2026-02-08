from django.contrib import admin
from .models import (FileArchive, Folder, ArchiveCell, FileDocument, DocumentVersion, DigitalFile,
                     EntityDocumentVersion, EntityTypeFileArchive, DocumentType)
from jsonserv.core.admin import ListAdmin, StructuredListAdmin


class FileArchiveAdmin(admin.ModelAdmin):
    list_display = ('archive_name', 'core_directory')
    search_fields = ['archive_name']
    ordering = ('archive_name', )


class FolderAdmin(admin.ModelAdmin):
    list_display = ('folder_name', 'archive')
    list_filter = ['archive']
    search_fields = ['folder_name']
    ordering = ('folder_name', )


class ArchiveCellAdmin(admin.ModelAdmin):
    list_display = ('cell_name', 'parent')
    list_filter = ['cell_name']
    search_fields = ['cell_name']
    ordering = ('parent', 'cell_name')


class FileDocumentAdmin(admin.ModelAdmin):
    list_display = ('doc_code', 'description')
    list_filter = ['doc_type']
    search_fields = ['doc_code']
    ordering = ('doc_code',)


class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ('document', 'archive_cell', 'version_num')
    list_filter = ['version_num', 'archive_cell']
    search_fields = ['document']
    ordering = ('document', 'version_num')


class DigitalFileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'document_version', 'folder')
    list_filter = ['data_format', 'folder']
    search_fields = ['file_name']
    ordering = ('file_name', 'folder')


class EntityDocumentVersionAdmin(admin.ModelAdmin):
    list_display = ('document_version', 'entity', 'document_role')
    list_filter = ['document_role']
    search_fields = ['entity']
    ordering = ('entity', 'document_version')


# Списки
admin.site.register(DocumentType, StructuredListAdmin)


# Со специальными настройками
admin.site.register(FileArchive, FileArchiveAdmin)
admin.site.register(Folder, FolderAdmin)
admin.site.register(ArchiveCell, ArchiveCellAdmin)
admin.site.register(FileDocument, FileDocumentAdmin)
admin.site.register(DocumentVersion, DocumentVersionAdmin)
admin.site.register(DigitalFile, DigitalFileAdmin)
admin.site.register(EntityDocumentVersion, EntityDocumentVersionAdmin)

# Без специальных настроек
admin.site.register(EntityTypeFileArchive)
