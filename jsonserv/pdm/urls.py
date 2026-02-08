from django.urls import path
from jsonserv.pdm import views, viewsets


urlpatterns = [
    path('rest/createsameroute/<int:pk>/', views.create_same_route, name='createsameroute'),  # Создание подобного маршрута
    path('rest/curdesingner/', views.get_curdesingner, name='curdesingner'),
    path('rest/intotop/<int:pk>', views.get_into_top, name='intotop'),
    path('rest/nomcode/', views.get_nomcodes, name='nomcode'),
    path('rest/parents/<int:pk>', views.get_parents, name='orderpart'),
    path('rest/partscompare/', views.parts_compare, name='partscompare'),
    path('rest/renum/', views.renum, name='renum'),
    path('rest/roledesingners/', views.get_roledesingners, name='roledesingners'),
    path('rest/soundsame/<int:pk>', views.get_same, name='soundsame'),
    path('rest/staffsame/<int:pk>', views.get_samestaff, name='staffsame'),
    path('rest/updateorderpart/<int:pk>/', views.update_order_part, name='updateorderpart'),
]

router_urls = {
    'rest/billet': viewsets.BilletViewSet,
    'rest/designer': viewsets.DesignerViewSet,
    'rest/designmater': viewsets.DesignMaterViewSet,
    'rest/designrole': viewsets.DesignRoleViewSet,
    'rest/notice': viewsets.NoticeViewSet,
    'rest/noticelink': viewsets.NoticeLinkViewSet,
    'rest/noticerecipient': viewsets.NoticeRecipientViewSet,
    'rest/operation': viewsets.OperationViewSet,
    'rest/partlink': viewsets.PartLinkViewSet,
    'rest/partobject': viewsets.PartObjectViewSet,
    'rest/partobjectformat': viewsets.PartObjectFormatViewSet,
    'rest/rendition': viewsets.RenditionViewSet,
    'rest/role': viewsets.RoleViewSet,
    'rest/route': viewsets.RouteViewSet,
    'rest/routepoint': viewsets.RoutePointViewSet,
    'rest/tpresource': viewsets.TpResourceViewSet,
    'rest/tprow': viewsets.TpRowViewSet,
    'rest/typesizemater': viewsets.TypeSizeMaterViewSet,
    'rest/typesizesort': viewsets.TypeSizeSortViewSet
}

# path('typesizesortlist/<int:child>', views.TypeSizeSortList.as_view(), name=views.TypeSizeSortList.name),
