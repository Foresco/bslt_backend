from jsonserv.core.viewsets import CommonViewSet

from jsonserv.staff.models import Person, StaffPosition, PersonStaffPosition
from jsonserv.staff.serializers import (PersonSerializer, PersonSerializerDetailed, PersonSerializerList,
                                        StaffPositionSerializer, StaffPositionSerializerDetailed,
                                        PersonStaffPositionSerializer, PersonStaffPositionSerializerDetailed,
                                        PersonStaffPositionSerializerList)


class PersonViewSet(CommonViewSet):
    queryset = Person.objects.all().order_by('person')
    serializer_class = PersonSerializer
    serializer_class_detailed = PersonSerializerDetailed
    serializer_class_list = PersonSerializerList

    # Поля поиска
    search_fields = (
        'person',
    )


class StaffPositionViewSet(CommonViewSet):
    queryset = StaffPosition.objects.all()
    serializer_class = StaffPositionSerializer
    serializer_class_detailed = StaffPositionSerializerDetailed
    serializer_class_list = StaffPositionSerializerDetailed


class PersonStaffPositionViewSet(CommonViewSet):
    queryset = PersonStaffPosition.objects.all()
    serializer_class = PersonStaffPositionSerializer
    serializer_class_detailed = PersonStaffPositionSerializerDetailed
    serializer_class_list = PersonStaffPositionSerializerList
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    # Поля фильтрации
    filterset_fields = (
        'person',
    )
