from django.urls import path
from jsonserv.supply import views, viewsets

urlpatterns = [
    path('rest/supplymater/', views.SupplyMaterList.as_view(), name=views.SupplyMaterList.name)
]

router_urls = {
    'rest/orderprodposition': viewsets.OrderProdPositionViewSet,
    'rest/price': viewsets.PriceViewSet,
    'rest/supplyorder': viewsets.SupplyOrderViewSet
}
