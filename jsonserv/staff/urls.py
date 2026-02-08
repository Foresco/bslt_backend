# from django.urls import path
from jsonserv.staff import viewsets

router_urls = {
    'rest/staffposition': viewsets.StaffPositionViewSet,
    'rest/person': viewsets.PersonViewSet,
    'rest/personstaffposition': viewsets.PersonStaffPositionViewSet
}
