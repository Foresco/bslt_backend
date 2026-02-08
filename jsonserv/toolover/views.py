from rest_framework.generics import ListAPIView
from django_filters import BooleanFilter
from django_filters.rest_framework import FilterSet

from jsonserv.toolover.models import ToolClass
from jsonserv.toolover.serializers import ToolClassTreeSerializer


class ToolClassTreeRootFilter(FilterSet):
    root = BooleanFilter(field_name='parent', lookup_expr='isnull')

    class Meta:
        model = ToolClass
        fields = (
            'parent',
        )


class ToolClassTree(ListAPIView):
    queryset = ToolClass.objects.all()
    serializer_class = ToolClassTreeSerializer
    name = 'toolclass-branch'
    filterset_class = ToolClassTreeRootFilter  # Дополнительный фильтра для корневого элемента
    paginator = None  # Отключение пагинации (в дереве не нужна)

    # Поля фильтрации
    filterset_fields = (
        'parent',
        'class_id'
    )
    # Поля поиска
    search_fields = (
        'class_name',
        'preferred_name'
    )
