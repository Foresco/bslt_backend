from jsonserv.core.viewsets import CommonViewSet

from jsonserv.toolover.models import (ToolClass)
from jsonserv.toolover.serializers import (ToolClassSerializer, ToolClassSerializerDetailed, ToolClassSerializerList)


class ToolClassViewSet(CommonViewSet):
    queryset = ToolClass.objects.all()
    serializer_class = ToolClassSerializer
    serializer_class_detailed = ToolClassSerializerDetailed
    serializer_class_list = ToolClassSerializerList

    # Поля фильтрации
    filterset_fields = (
        'parent',
        'class_id'
    )
    # Поля поиска
    search_fields = (
        'class_id',
        'class_name',
        'preferred_name'
    )
