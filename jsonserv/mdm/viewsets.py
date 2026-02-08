from jsonserv.core.viewsets import CommonViewSet

from jsonserv.mdm.models import RawRow
from jsonserv.mdm.serializers import RawRowSerializer, RawRowSerializerDetailed, RawRowSerializerList


class RawRowViewSet(CommonViewSet):
    queryset = RawRow.objects.all().order_by('code')
    serializer_class = RawRowSerializer
    serializer_class_list = RawRowSerializerList
    serializer_class_detailed = RawRowSerializerDetailed

    # Поля фильтрации
    filterset_fields = (
        'group',
    )
    # Поля поиска
    search_fields = (
        'code',
        'title',
        'description'
    )
