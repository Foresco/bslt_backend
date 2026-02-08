from django.urls import path
from .views import get_external

# URL-адреса
urlpatterns = [
    path('rest/external/<int:pk>', get_external),
]
