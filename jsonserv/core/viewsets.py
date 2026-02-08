from django_filters import DateFilter, Filter
from rest_framework.response import Response
from rest_framework import viewsets, status, filters

from jsonserv.core.models import Classification, MeasureUnit, Place, Property, PropertyValue, SystemUser, UserProfile
from jsonserv.core.serializers import (ClassificationSerializer, ClassificationSerializerDetailed,
                                       MeasureUnitSerializer, MeasureUnitSerializerDetailed, MeasureUnitSerializerList,
                                       PlaceSerializer, PlaceSerializerDetailed, PlaceSerializerList,
                                       PropertySerializer, PropertySerializerDetailed, PropertySerializerList,
                                       PropertyValueSerializer, PropertyValueSerializerList,
                                       UserSerializer, UserSerializerNoPwd, UserSerializerDetailed, UserProfileSerializer,
                                       UserProfileSerializerDetailed, UserProfileSerializerList)


class EqualFilter(Filter):
    """Фильтр, формирующий сравнение равно"""
    def filter(self, qs, value):
        if value not in (None, ''):
            return qs.filter(**{self.field_name: value})
        return qs


class DateEqualFilter(DateFilter):
    """Фильтр, формирующий сравнение равно для даты"""
    def filter(self, qs, value):
        if value not in (None, ''):
            return qs.filter(**{self.field_name: value})
        return qs


class CommonViewSet(viewsets.ModelViewSet):
    """Типовой для наследования всеми ViewSet"""
    queryset = None
    serializer_class = None  # Сериализатор для сохранения
    serializer_class_detailed = None  # Сериализатор для просмотра свойств
    serializer_class_list = None  # Сериализатор для просмотра списка

    def get_serializer_class(self):
        if self.action == 'retrieve' and self.serializer_class_detailed:
            return self.serializer_class_detailed
        elif self.action == 'list' and self.serializer_class_list:
            return self.serializer_class_list
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        request.data['crtd_sess'] = request.session.get('user_session_id', 1)
        # print(request.data)
        return super().create(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        # Добавление в свойства записи редактировавшей сессии
        request.data['edt_sess'] = request.session.get('user_session_id', 1)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # Удаление производится путем указания в свойствах записи удалившей сессии
        instance = self.get_object()
        user_session_id = request.session.get('user_session_id', 1)
        instance.dlt_sess = user_session_id  # Указание идентификатора сессии
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)




class ListViewSet(viewsets.ModelViewSet):
    """Типовой ViewSet для обслуживания объектов типа список"""
    serializer_class = None  # Переопределяется в дочернем классе
    queryset = None  # Переопределяется в дочернем классе


class ClassificationViewSet(CommonViewSet):
    queryset = Classification.objects.all()
    serializer_class = ClassificationSerializer
    serializer_class_detailed = ClassificationSerializerDetailed  # Сериализатор для просмотра свойств

    # Поля фильтрации
    filterset_fields = (
        'group',
    )
    # Поля поиска
    search_fields = (
        'code',
        'description'
    )


class MeasureUnitViewSet(CommonViewSet):
    queryset = MeasureUnit.objects.all().order_by('unit_name')
    serializer_class = MeasureUnitSerializer
    serializer_class_detailed = MeasureUnitSerializerDetailed
    serializer_class_list = MeasureUnitSerializerList

    # Поля фильтрации
    filterset_fields = (
        'measure_system',
        'essence',
    )
    # Поля поиска
    search_fields = (
        'unit_name',
    )


class PlaceViewSet(CommonViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    serializer_class_detailed = PlaceSerializerDetailed
    serializer_class_list = PlaceSerializerList

    # Поля фильтрации
    filterset_fields = (
        'parent',
        'is_point',
        'is_buyer',
        'is_supplier'
    )
    # Поля поиска
    search_fields = (
        'code',
    )


class PropertyViewSet(CommonViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    serializer_class_detailed = PropertySerializerDetailed
    serializer_class_list = PropertySerializerList

    # Поля фильтрации
    filterset_fields = (
        'group',
    )
    # Поля поиска
    search_fields = (
        'property_name',
    )


class PropertyValueViewSet(CommonViewSet):
    queryset = PropertyValue.objects.all()
    serializer_class = PropertyValueSerializer
    serializer_class_list = PropertyValueSerializerList

    # Поля фильтрации
    filterset_fields = (
        'entity',
    )


class UserViewSet(viewsets.ModelViewSet):
    queryset = SystemUser.objects.all().order_by('username')
    serializer_class = UserSerializer
    serializer_class_detailed = UserSerializerDetailed
    serializer_class_no_pwd = UserSerializerNoPwd

    def get_serializer_class(self):
        # Пришлось сделать, так как наследует не CommonViewSet
        if self.action == 'retrieve':
            return self.serializer_class_detailed
        # elif self.action == 'list' and self.serializer_class_list:
        #     return self.serializer_class_list
        elif self.action == 'partial_update':
            # При сохранении проверяем обновление пароля и используем разные сериализаторы
            if not self.request.data.get('password', ''): # Если не передан пароль
                return self.serializer_class_no_pwd # Сериализатор без паролей
        return self.serializer_class

    # Поля фильтрации
    search_fields = (
        'username',
        'first_name',
        'last_name'
    )


class UserProfileViewSet(CommonViewSet):
    queryset = UserProfile.objects.all().order_by('user_name')
    serializer_class = UserProfileSerializer
    serializer_class_detailed = UserProfileSerializerDetailed
    serializer_class_list = UserProfileSerializerList

    # Поля фильтрации
    filterset_fields = (
        'dismissed',
    )
    # Поля поиска
    search_fields = (
        'user_name',
        'user__username'
    )
