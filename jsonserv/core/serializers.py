import json
from rest_framework import serializers
# Классы, подлежащие сериализации
from django.contrib.auth.models import User, Group
from .models import (Enterprise, EntityType, Entity, Essence, Link, Place, Classification, 
                     MeasureUnit, GraphicFile, DownloadCheckGroup,
                     UserSession, UserProfile, PropertyType, Property, PropertyValue)
from jsonserv.core.models_dispatcher import ModelsDispatcher


class ConstField(serializers.Field):
    """Отображение поля с фиксированным значением"""
    def __init__(self, **kwargs):
        self.const_value = kwargs.get('const_value', '')  # Запоминаем фиксированное значение
        super().__init__()

    def to_representation(self, value):
        return self.const_value


class ListSerializer(serializers.ModelSerializer):
    """Общий сериализатор для списков"""

    class Meta:
        model = None
        fields = ('pk', 'list_value', 'order_num', 'is_default')


def get_list_serializer_class(mdl):
    ListSerializer.Meta.model = mdl
    return ListSerializer()


class EssenceRefSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='essence_name')

    class Meta:
        model = Essence
        fields = ('pk', 'value')


class MeasureUnitRefSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='short_name')

    class Meta:
        model = MeasureUnit
        fields = ('pk', 'value')


class EntityRefSerializer(serializers.ModelSerializer):
    """Сериализация по экземпляру модели"""
    value = serializers.CharField(source='key_code')

    class Meta:
        model = Entity
        fields = ('pk', 'value')


class EntityIdRefSerializer(serializers.JSONField):
    """Сериализация по идентификатору"""

    def to_representation(self, value):
        return EntityRefSerializer(Entity.objects.get(pk=value)).data


class EntityChildObjectSerializer(serializers.JSONField):
    """Уточненное Отображение объекта, на основе метода to_representation его класса"""
    md = ModelsDispatcher()  # Диспетчер, для поиска моделей по наименованию

    def to_representation(self, value):
        data_dict = dict()
        # Определяем класс объекта
        item_model = self.md.get_entity_class_by_entity_name(value.type_key.type_key)
        item = item_model.objects.get(pk=value.id)
        # Наполняем словарь данными
        data_dict['pk'] = value.id
        data_dict['value'] = item.get_description()
        # Сериализуем
        serializer = EntityRefSerializer(data=data_dict)
        if serializer.is_valid(): # Так надо
            return serializer.data
        return None #  На всякий случай


class EnterpriseRefSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='short_name')

    class Meta:
        model = Enterprise
        fields = ('pk', 'value')


class DownloadCheckGroupRefSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='group_name')

    class Meta:
        model = DownloadCheckGroup
        fields = ('pk', 'value')


class ClassificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classification
        fields = (
            'pk',
            'code',
            'description',
            'group_code',
            'order_num',
            'group',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class ClassificationSerializerDetailed(serializers.ModelSerializer):
    group = EntityRefSerializer(read_only=True)

    class Meta:
        model = Classification
        fields = (
            'pk',
            'code',
            'description',
            'group_code',
            'order_num',
            'group')


class ClassificationTreeSerializer(serializers.ModelSerializer):
    """Сериализатор частичного описания классификационной группы для дерева"""

    class Meta:
        model = Classification
        fields = (
            'pk',
            'code',
            'group',
            'has_children'
        )


class EntitySerializer(serializers.ModelSerializer):
    """Сериализатор частичного описания объекта"""

    class Meta:
        model = Entity
        fields = (
            'pk',
            'code',
            'description',
            'type_key'
        )


class ExtraLinkSerializer(serializers.Serializer):
    caption = serializers.CharField(source='extra_link__caption')
    link = serializers.SerializerMethodField('get_link')

    def get_link(self, obj):
        # Форматируем строку ссылки
        return obj['extra_link__link_pattern'].format(id=self.context["id"], host=self.context["host"])


class GraphicFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = GraphicFile
        fields = ('pk', 'file_name')


class LinkedSerializerList(serializers.ModelSerializer):
    """Сериализатор описания связанных объектов для списка"""
    child = EntitySerializer()
    parent = EntitySerializer()

    class Meta:
        model = Link
        fields = (
            'pk',
            'child',
            'parent',
            'quantity',
            'comment',
            'link_class'
        )


class MeasureUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasureUnit
        fields = (
            'pk',
            'essence',
            'unit_name',
            'short_name',
            'unit_code',
            'numerator',
            'denominator',
            'separator_char',
            'base',
            'ratio',
            'order_num',
            'measure_system',
            'is_active',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class MeasureUnitSerializerDetailed(serializers.ModelSerializer):
    essence = EssenceRefSerializer()

    class Meta:
        model = MeasureUnit
        fields = (
            'pk',
            'essence',
            'unit_name',
            'short_name',
            'unit_code',
            'numerator',
            'denominator',
            'separator_char',
            'base',
            'ratio',
            'order_num',
            'measure_system'
        )


class MeasureUnitSerializerList(serializers.ModelSerializer):
    class Meta:
        model = MeasureUnit
        fields = (
            'pk',
            'unit_name',
            'short_name',
            'unit_code'
        )


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = (
            'pk',
            'code',
            'description',
            'place_type',
            'short_name',
            'parent',
            'is_point',
            'is_buyer',
            'is_supplier',
            'edt_sess',
            'crtd_sess',
            'dlt_sess')


class PlaceSerializerDetailed(serializers.ModelSerializer):
    parent = EntitySerializer()

    class Meta:
        model = Place
        fields = (
            'pk',
            'code',
            'description',
            'short_name',
            'place_type',
            'parent',
            'is_point',
            'is_buyer',
            'is_supplier'
        )


class PlaceSerializerList(serializers.ModelSerializer):
    place_type = serializers.SlugRelatedField(read_only=True, slug_field='list_value')
    parent = serializers.SlugRelatedField(read_only=True, slug_field='code')

    class Meta:
        model = Place
        fields = (
            'pk',
            'code',
            'short_name',
            'place_type',
            'parent'
        )


class PropertyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyType
        fields = ('property_type', 'description')


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = (
            'pk',
            'order_num',
            'property_code',
            'property_name',
            'property_name_rus',
            'property_type',
            'description',
            'description_rus',
            'group',
            'edt_sess',
            'crtd_sess',
            'dlt_sess')


class PropertySerializerDetailed(serializers.ModelSerializer):
    group = EntityRefSerializer(read_only=True)
    property_type = PropertyTypeSerializer()

    class Meta:
        model = Property
        fields = (
            'pk',
            'order_num',
            'property_name',
            'property_type',
            'essence',
            'description',
            'group'
        )


class PropertySerializerList(serializers.ModelSerializer):
    property_type = serializers.SlugRelatedField(read_only=True, slug_field='description')

    class Meta:
        model = Property
        fields = (
            'pk',
            'property_name',
            'property_type')


class PropertyValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyValue
        fields = (
            'pk',
            'entity',
            'property',
            'value',
            'value_min',
            'value_max',
            'value_date',
            'unit',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class PropertyValueSerializerList(serializers.ModelSerializer):
    property = serializers.SlugRelatedField(read_only=True, slug_field='property_name')
    unit = MeasureUnitRefSerializer()

    class Meta:
        model = PropertyValue
        fields = (
            'pk',
            'property',
            'value',
            'value_min',
            'value_max',
            'value_date',
            'unit'
        )


class ReportParamSerializer(serializers.Serializer):
    pk = serializers.IntegerField(source='report_params__pk')
    param_name = serializers.CharField(source='report_params__param_name')
    caption = serializers.CharField(source='report_params__caption')
    param_type = serializers.CharField(source='report_params__param_type')
    index = serializers.IntegerField(source='report_params__order_num')
    values_list = serializers.CharField(source='report_params__values_list')
    default_value = serializers.CharField(source='report_params__default_value')
    extra_value = serializers.CharField(source='report_params__extra_value')
    list_keys = serializers.CharField(source='report_params__list_keys')
    is_file_name = serializers.BooleanField(source='report_params__is_file_name')


class UserSerializerNoPwd(serializers.ModelSerializer):
    """Вариант без редактирования пароля"""
    last_login = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = User
        fields = ('pk', 'username', 'first_name', 'last_name', 'last_login', 'groups')


class UserSerializer(serializers.ModelSerializer):
    
    last_login = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = User
        fields = ('pk', 'username', 'first_name', 'last_name', 'password', 'last_login', 'groups')

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data['password'])  # Формирование зашифрованного пароля
        user.save()
        return user

    def update(self, instance, validated_data):
        user = super().update(instance, validated_data)
        try:
            user.set_password(validated_data['password'])  # Формирование зашифрованного пароля
            user.save()
        except KeyError:
            pass
        return user


class UserSerializerDetailed(serializers.ModelSerializer):
    password = ConstField() # Выводим пустое значение в форме

    class Meta:
        model = User
        fields = ('pk', 'username', 'first_name', 'last_name', 'password')


class UserRefSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='username')

    class Meta:
        model = User
        fields = ('pk', 'value')


class UserProfileSerializerDetailed(serializers.ModelSerializer):
    user = UserRefSerializer()
    download_group = DownloadCheckGroupRefSerializer()

    class Meta:
        model = UserProfile
        fields = ('pk', 'user', 'user_name', 'dismissed', 'taskable', 'dashboard', 
                  'password_expire', 'password_changed', 'api_only', 'log_actions', 'download_group')


class UserProfileSerializerList(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = UserProfile
        fields = ('pk', 'user', 'user_name', 'dismissed', 'taskable', 'dashboard')


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('pk', 'user', 'user_name', 'dismissed', 'taskable', 'dashboard', 
                  'password_expire', 'api_only', 'log_actions', 'download_group',
                   'edt_sess', 'crtd_sess', 'dlt_sess')


class UserProfileRefSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='user_name')

    class Meta:
        model = UserProfile
        fields = ('pk', 'value')


class UserGroupListSerializer(serializers.ModelSerializer):
    user_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Group
        fields = (
            'pk',
            'name',
            'user_set'
        )


# class UserGroupSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Group
#         fields = (
#             'pk',
#             'user',
#             'group'
#         )


class UserSessionSerializer(serializers.ModelSerializer):
    session_datetime = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = UserSession
        fields = (
            'pk',
            'session_datetime',
            'user_ip',
            'comment'
        )


class UserSessionUserField(serializers.Field):
    """Отображение пользователя указанной сессии"""

    def to_representation(self, value):
        if value.user.userprofile:
            return value.user.userprofile.user_name
        return value.user.username


class HistorySerializerList(serializers.Serializer):
    pk = serializers.IntegerField()  # Идентфикатор строки
    session = serializers.IntegerField(source='edt_sess__id')  # Идентфикатор строки
    username = serializers.CharField(source='edt_sess__user__username')
    session_datetime = serializers.DateTimeField(source='edt_sess__session_datetime',
                                                 format="%d.%m.%Y %H:%M:%S", read_only=True)
    changes = serializers.JSONField()  # ChangesPreapre()
