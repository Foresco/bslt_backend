from django.urls import path
from django.contrib.auth.decorators import login_required

from jsonserv.core.service_views import(LoginView, LogoutView, change_password)
from jsonserv.core.views import (ClassificationStaff, ClassificationTree, EntityList, SearchView, 
                                 DashboardView, HistoryList, ReportView,
                                 extra_links_get, GraphicUploadView, LinkList, search_list, 
                                 ReportParamsList,
                                 report_get, caption_get, save_user_settings,
                                 UserGroupList, UserSessionList, entity_properties_get, main_menu_get)

from jsonserv.core import viewsets

# URL-адреса
urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password/', login_required(change_password), name='change_password'),  # Переделать на вью
    path('search/', login_required(SearchView.as_view()), name='search'),  # Форма поиска
    path('', login_required(SearchView.as_view()), name='search_emp'),   # Форма поиска по умолчанию

    # Специализированные дашборды
    path('arm/<slug:dashboard_name>/', login_required(DashboardView.as_view()), name="dashboard"),
    path('arm/<slug:dashboard_name>/<int:id>', login_required(DashboardView.as_view()), name="dashboard_id"),

    # Отчеты
    path('report/<slug:report_name>/', login_required(ReportView.as_view()),  name="report"),
    path('report/<slug:report_name>/<slug:mode>/', login_required(report_get), name="get_report"),

    # REST
    path('rest/classificationstaff/', ClassificationStaff.as_view(), name=ClassificationStaff.name),
    path('rest/classificationtree/', ClassificationTree.as_view(), name=ClassificationTree.name),
    path('rest/caption/<slug:type_key>/<int:id>', caption_get, name='caption'),
    path('rest/extralinks/<slug:type_key>/<int:id>', extra_links_get, name='extra_links'),
    path('rest/entity/<int:pk>', EntityList.as_view(), name=EntityList.name),
    path('rest/history/<slug:table_name>/<int:object>', HistoryList.as_view(), name=HistoryList.name),
    path('rest/link/', LinkList.as_view(), name=LinkList.name),
    path('rest/menu/', main_menu_get, name='menu'),
    path('rest/search/', search_list, name='search_list'),
    path('rest/properties/<slug:type_key>/<slug:sub_type_key>/', entity_properties_get, name='properties'),
    path('rest/reportparams/<slug:report_name>/', ReportParamsList.as_view(), name=ReportParamsList.name),
    path('rest/user/<int:pk>/activity', UserSessionList.as_view(), name=UserSessionList.name),
    path('rest/usergroup', UserGroupList.as_view(), name=UserGroupList.name),
    path('rest/usersettings/', save_user_settings, name='usersettings'),
    path('rest/uploadgraphic/', GraphicUploadView.as_view(), name=GraphicUploadView.name),
    path('rest/uploadgraphic/<int:id>/', GraphicUploadView.as_view(), name=GraphicUploadView.name_del)  # TODO: Объединить с предыдущей строкой
    # Выгрузки
    # path('export/xls/', export_users_xls, name='export_users_xls'),
]

# REST-сервисы
router_urls = {
    'rest/classification': viewsets.ClassificationViewSet,
    'rest/measureunit': viewsets.MeasureUnitViewSet,
    'rest/place': viewsets.PlaceViewSet,
    'rest/property': viewsets.PropertyViewSet,
    'rest/propertyvalue': viewsets.PropertyValueViewSet,
    'rest/systemuser': viewsets.UserViewSet,
    'rest/userprofile': viewsets.UserProfileViewSet,
}
