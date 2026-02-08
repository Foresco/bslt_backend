from django.urls import path
from jsonserv.mdm import views, viewsets

urlpatterns = [
    path('rest/rawrowpropvalues/<int:pk>/', views.rawrow_prop_values_get, name='rawrowpropvalues')
]

router_urls = {
    'rest/rawrow': viewsets.RawRowViewSet,
}
