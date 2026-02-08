from django.urls import path
from .views import get_root, get_tree


urlpatterns = [
    path('rest/vw/stafftree/<int:pk>', get_tree, name='stafftree'),
    path('rest/vw/staffroot/<int:pk>', get_root, name='staffroot'),
]
