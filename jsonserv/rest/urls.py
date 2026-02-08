from django.urls import path, include

from jsonserv.rest.views import create_same, list_values_get, replace, suggest_get


urlpatterns = [
    path('rest/api/', include('rest_framework.urls')),
    path('rest/createsame/<slug:type_key>/<int:pk>/', create_same, name='createsame'),  # Создание подобного объекта
    path('rest/list/<slug:type_key>/', list_values_get, name='list_values'),
    path('rest/replace/<slug:type_key>/', replace, name="replace"),  # Команда замены одного объекта другим
    path('rest/suggest/<slug:type_key>/', suggest_get, name='suggest'),
]
