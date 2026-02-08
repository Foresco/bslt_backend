# Для обеспечения взаимодействия моделей с базой данных Базальты
from .models import (PartObject, Route, Waybill, Essence, Unit, SystemUser, ObjectGroup, Place, Part, DraftMaters,
                     Exemplar, ChangeNotice, Reasons, Roles, DesignRoles, DesignRolesNotice, NoticeLinks, ObjectFormats,
                     DocsObject, DocsTask, DocsLetter, DocsNotice, NoticeLinksDoc, NoticeLinksArcDoc, NoticeLinksObject,
                     NoticeRecipients, ObjectToExport, History, RenditionTails, Renditions, Tasks,
                     TaskReferNotice, TaskReferObject, Arcdocuments, Deliveries, ArcdocLinks, ArchiveDocs,
                     ArchiveFolders, Uploads, UploadArcdocs, Prefixes,
                     ArcDocFormats, DeliveryArcdocs, Properties, PropValues, Letters, LetterLinks, LetterTypes, Price)


# Роутер для переключения некоторых моделей в базу данных Базальты 1.0
class BasaltaDBRouter(object):
    @staticmethod
    def db_for_read(model, **hints):
        models_list = (PartObject, Route, Waybill, Essence, Unit, SystemUser, ObjectGroup, Place, Part, DraftMaters,
                       Exemplar, ChangeNotice, Reasons, Roles, DesignRoles, DesignRolesNotice, NoticeLinks, ObjectFormats,
                       DocsObject, DocsTask, DocsLetter, DocsNotice, NoticeLinksDoc, NoticeLinksArcDoc, NoticeLinksObject,
                       NoticeRecipients, ObjectToExport, History, RenditionTails, Renditions, Tasks,
                       TaskReferNotice, TaskReferObject, Arcdocuments, Deliveries, ArcdocLinks, ArcDocFormats,
                       DeliveryArcdocs, Properties, PropValues, Letters, LetterLinks, LetterTypes, Price,
                       Uploads, UploadArcdocs, Prefixes)
        if model in models_list:
            return 'basaltalegasy'
        return None

    @staticmethod
    def db_for_write(model, **hints):
        models_list = (PartObject, Route, Waybill, Essence, Unit)
        if model in models_list:
            return 'basaltalegasy'
        return None


# Роутер для переключения некоторых моделей в базу данных Архив 1.0
class ArchiveDBRouter(object):
    @staticmethod
    def db_for_read(model, **hints):
        models_list = (ArchiveDocs, ArchiveFolders)
        if model in models_list:
            return 'archivelegasy'
        return None

    @staticmethod
    def db_for_write(model, **hints):
        models_list = (ArchiveDocs, ArchiveFolders)
        if model in models_list:
            return 'archivelegasy'
        return None
