from django.urls import path

from jsonserv.sideapi.views import FileSuggest, SearchFiles, GetFile, objects_list_get, prop_values_get


urlpatterns = [
    path('sideapi/filesuggest/', FileSuggest.as_view(), name=FileSuggest.name),
    path('sideapi/searchfiles/', SearchFiles.as_view(), name=SearchFiles.name),
    path('sideapi/list/<slug:type_key>/<slug:sub_type_key>/', objects_list_get, name='objects_list'),
    path('sideapi/file/<int:id>/', GetFile.as_view(), name=GetFile.name),
    path('sideapi/propvalues/<int:id>/', prop_values_get, name='prop_values'),
]
