from django.urls import path

from jsonserv.manufacture import viewsets
from jsonserv.manufacture.views import (ObjectOperationList, PositionsOperationList,
                                        PositionOperationReportList, PositionInWorkList, 
                                        ProdOrderContract, ProdOrderInWorkList,
                                        ProdOrderMaterList, ProdOrderPosOperationList, ProdOrderPosReportList,
                                        WorkerTaskList)


# URL-адреса
urlpatterns = [
    path('rest/objectoperation/<int:link>', ObjectOperationList.as_view(), name=ObjectOperationList.name),
    path('rest/positioninwork/', PositionInWorkList.as_view(), name=PositionInWorkList.name),
    path('rest/prodordercontract/', ProdOrderContract.as_view(), name=ProdOrderContract.name),
    path('rest/prodorderinwork/', ProdOrderInWorkList.as_view(), name=ProdOrderInWorkList.name),
    path('rest/prodordermater/', ProdOrderMaterList.as_view(), name=ProdOrderMaterList.name),
    path('rest/prodorderposoperation/<int:link>', ProdOrderPosOperationList.as_view(),
         name=ProdOrderPosOperationList.name),
    path('rest/positionsoperation/', PositionsOperationList.as_view(), name=PositionsOperationList.name),
    path('rest/positionsoperationreport/<int:link>/<int:tp_row>', PositionOperationReportList.as_view(),
         name=PositionOperationReportList.name),
    path('rest/prodorderposreport/<int:link>', ProdOrderPosReportList.as_view(), name=ProdOrderPosReportList.name),
    path('rest/workertask/', WorkerTaskList.as_view(), name=WorkerTaskList.name)
]

# REST-сервисы
router_urls = {
    'rest/prodorder': viewsets.ProdOrderViewSet,
    'rest/prodorderlink': viewsets.ProdOrderLinkViewSet,
    'rest/prodorderlinktprow': viewsets.ProdOrderLinkTpRowViewSet,
    'rest/prodorderlinkworker': viewsets.ProdOrderLinkWorkerViewSet,
    'rest/shipment': viewsets.ShipmentViewSet,
    'rest/workerreport': viewsets.WorkerReportConsistViewSet,
    'rest/workershift': viewsets.WorkerShiftViewSet
}

