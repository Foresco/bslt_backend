from django.urls import path

from jsonserv.docarchive.views import (DocumentTypesList, FileDocumentVersionsList, EntityDocumentsList,
                                       FileUploadPutView, UploadFileView, watermark_get,
                                       GetDocArchiveFile, UploadArcdocsList, NoticeLinkDocView, get_digitalfile)

from jsonserv.docarchive import viewsets


# URL-адреса
urlpatterns = [
    path('file/<int:id>/', GetDocArchiveFile.as_view(), name=GetDocArchiveFile.name),
    path('rest/digitalfile/', get_digitalfile, name='digitalfile'),
    path('rest/entitydocuments/', EntityDocumentsList.as_view(), name=EntityDocumentsList.name),
    path('rest/documenttypes/', DocumentTypesList.as_view(), name=DocumentTypesList.name),
    path('rest/filedocuments/', FileDocumentVersionsList.as_view(), name=FileUploadPutView.name),
    path('rest/watermarkdownload/<int:id>/', watermark_get, name="get_watermark"),
    path('rest/fileuploadput/', FileUploadPutView.as_view(), name=FileUploadPutView.name),
    path('rest/noticelinkdoc/', NoticeLinkDocView.as_view(), name=NoticeLinkDocView.name),
    path('rest/uploadarcdoc/', UploadArcdocsList.as_view(), name=UploadArcdocsList.name),
    path('rest/uploadfile/', UploadFileView.as_view(), name=UploadFileView.name)
]

# REST-сервисы
router_urls = {
    'rest/arcdocument': viewsets.ArcDocumentViewSet,
    'rest/arcdocumentobject': viewsets.ArcDocumentObjectViewSet,
    'rest/codeprefix': viewsets.CodePrefixViewSet,
    'rest/delivery': viewsets.DeliveryViewSet,
    'rest/deliveryarcdoc': viewsets.DeliveryArcdocViewSet,
    'rest/documenttype': viewsets.DocumentTypeViewSet,
    'rest/documentversion': viewsets.DocumentVersionViewSet,
    'rest/entitydocumentversion': viewsets.EntityDocumentVersionViewSet,
    'rest/filedocument': viewsets.FileDocumentViewSet,
    'rest/fileupload': viewsets.FileUploadViewSet,
    'rest/incident': viewsets.IncidentViewSet
}
