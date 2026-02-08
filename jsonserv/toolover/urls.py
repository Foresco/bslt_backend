from django.urls import path

from jsonserv.toolover import views
from jsonserv.toolover import viewsets


# URL-адреса
urlpatterns = [
    path('rest/toolclasstree/', views.ToolClassTree.as_view(), name=views.ToolClassTree.name),
]

# REST-сервисы
router_urls = {
    'rest/toolclass': viewsets.ToolClassViewSet,
}
