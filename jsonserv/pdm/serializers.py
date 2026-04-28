from itertools import chain
from rest_framework import serializers
from jsonserv.core.serializers import (EntityRefSerializer, EntityIdRefSerializer, MeasureUnitRefSerializer,
                                       UserProfileRefSerializer)

# Классы, подлежащие сериализации
from jsonserv.pdm.models import (Billet, Designer, DesignMater, DesignRole, DesignerRating,
                                 NormUnit, Notice, NoticeLink, NoticeRecipient,
                                 Operation, PartObject, PartObjectFast, PartType, PartLitera,
                                 PartObjectFormat, PartLink, Rendition,
                                 Role, Route, RoutePoint, TpResource, TpRow, TpRowType,
                                 TypeSizeMater, TypeSizeSort)


# *** Ссылочные сериалайзеры ***
class MeasurementField(serializers.CharField):
    """Получение единицы измерения объекта конструкции"""
    def to_representation(self, value):
        unit = PartObject.objects.get(pk=value).unit
        if unit:
            return unit.short_name
        return None
    

class PartTypeSerializer(serializers.ModelSerializer):
    pk = serializers.CharField(source='part_type')
    value = serializers.CharField(source='type_name')
    div_name = serializers.CharField()

    class Meta:
        model = PartType
        fields = ('pk', 'value', 'div_name')


class PartLiteraSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartLitera
        fields = ('pk', 'list_value')


class PartObjectRefSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='get_code')  # Функция-свойство

    class Meta:
        model = PartObject
        fields = ('pk', 'value')


class CodeField(serializers.CharField):
    """Получение обозначения объекта конструкции (с учетом признака составного ключа)"""
    def to_representation(self, value):
        return PartObject.objects.get(pk=value).get_code


class OperationRefSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='operation_name')

    class Meta:
        model = Operation
        fields = ('pk', 'value')


# *** Основные сериализаторы ***
class BilletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Billet
        fields = (
            'pk',
            'parent',
            'child',
            'quantity',
            'billet_name',
            'weight',
            'is_active',
            'not_count',
            'object_quantity',
            'billet_size',
            'alt_size',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class BilletSerializerList(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(read_only=True, slug_field='key_code')
    measurement = MeasurementField(source='parent_id')

    class Meta:
        model = Billet
        fields = (
            'pk',
            'parent_id',
            'parent',
            'child_id',
            'child',
            'quantity',
            'weight',
            'measurement',
            'billet_name',
            'object_quantity',
            'billet_size',
            'alt_size',
            'is_active',
            'not_count'
        )


class DesignerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designer
        fields = (
            'pk',
            'designer',
            'designer_profile',
            'selectable',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class DesignerSerializerDetailed(serializers.ModelSerializer):
    designer_profile = UserProfileRefSerializer()

    class Meta:
        model = Designer
        fields = (
            'pk',
            'designer',
            'designer_profile',
            'selectable'
        )


class DesignerSerializerList(serializers.ModelSerializer):
    designer_profile = serializers.SlugRelatedField(read_only=True, slug_field='user_name')

    class Meta:
        model = Designer
        fields = (
            'pk',
            'designer_profile',
            'designer',
        )


class DesignMaterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignMater
        fields = (
            'pk',
            'parent',
            'child',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class DesignMaterSerializerList(serializers.ModelSerializer):
    child = serializers.SlugRelatedField(read_only=True, slug_field='key_code')

    class Meta:
        model = DesignMater
        fields = (
            'pk',
            'child',
            'comment'
        )


class DesignRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignRole
        fields = (
            'pk',
            'subject',
            'role',
            'designer',
            'role_date',
            'comment',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class DesignRoleSerializerList(serializers.ModelSerializer):
    designer_name = serializers.SlugRelatedField(read_only=True, slug_field='designer', source='designer')

    class Meta:
        model = DesignRole
        fields = (
            'pk',
            'role',
            'designer',
            'designer_name',
            'role_date',
            'comment'
        )


class IntoTopSerializerList(serializers.Serializer):
    parent_id = serializers.IntegerField()
    parent_code = serializers.CharField()
    top_id = serializers.IntegerField()
    top_code = serializers.CharField()
    quantity = serializers.FloatField()
    quantity_ratio = serializers.FloatField()


class SameStaffSerializerList(serializers.Serializer):
    pk = serializers.IntegerField(source='id')
    code = serializers.CharField()
    prcnt = serializers.FloatField()


class NoticeLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoticeLink
        fields = (
            'pk',
            'parent',
            'child',
            'comment',
            'old',
            'change_num',
            'change_type',
            'is_done',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class NoticeLinkSerializerList(serializers.ModelSerializer):
    """Сериализатор описания связей извещения для списка"""
    change_type = serializers.SlugRelatedField(read_only=True, slug_field='list_value')
    parent = serializers.SlugRelatedField(read_only=True, slug_field='key_code')
    child = serializers.SlugRelatedField(read_only=True, slug_field='key_code')
    old = serializers.SlugRelatedField(read_only=True, slug_field='key_code')

    class Meta:
        model = NoticeLink
        fields = (
            'pk',
            'parent',
            'parent_id',
            'child',
            'child_id',
            'old',
            'change_type',
            'change_type_id',
            'change_num',
            'is_done',
            'comment'
        )


class NoticeRecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoticeRecipient
        fields = (
            'pk',
            'parent',
            'child',
            'comment',
            'is_sent',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class NoticeRecipientSerializerList(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(read_only=True, slug_field='key_code')
    child = serializers.SlugRelatedField(read_only=True, slug_field='key_code')

    class Meta:
        model = NoticeRecipient
        fields = (
            'pk',
            'parent',
            'parent_id',
            'child',
            'is_sent',
            'comment'
        )


# *** Основные сериализаторы ***
class NoticeSerializer(serializers.ModelSerializer):
    """Сериализатор полного описания извещения об изменениях для сохранения"""

    class Meta:
        model = Notice
        fields = (
            'pk',
            'code',
            'notice_type',
            'description',
            'notice_date',
            'valid_date',
            'approve_date',
            'deadline',
            'urgently',
            'reason',
            'reserve',
            'directions',
            'usages',
            'attachment',
            'state',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class NoticeSerializerDetailed(serializers.ModelSerializer):
    """Сериализатор описания извещения об изменениях для просмотра свойств"""

    class Meta:
        model = Notice
        fields = (
            'pk',
            'code',
            'notice_type',
            'description',
            'notice_date',
            'valid_date',
            'approve_date',
            'deadline',
            'urgently',
            'reason',
            'reserve',
            'directions',
            'usages',
            'attachment',
            'state'
        )


class NoticeSerializerList(serializers.ModelSerializer):
    """Сериализатор описания извещения для списка"""
    notice_type = serializers.SlugRelatedField(read_only=True, slug_field='value_code')
    state = serializers.SlugRelatedField(read_only=True, slug_field='list_value')
    notice_date = serializers.DateField(format="%d.%m.%Y")

    class Meta:
        model = Notice
        fields = (
            'pk',
            'code',
            'notice_type',
            'notice_date',
            'state'
        )


class OperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = (
            'pk',
            'operation_name',
            'full_name',
            'operation_code',
            'group',
            'min_norm',
            'max_norm',
            'norm_unit',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class OperationSerializerDetailed(serializers.ModelSerializer):
    group = EntityRefSerializer()
    norm_unit = MeasureUnitRefSerializer()

    class Meta:
        model = Operation
        fields = (
            'pk',
            'operation_name',
            'full_name',
            'operation_code',
            'group',
            'min_norm',
            'max_norm',
            'norm_unit'
        )


class OperationSerializerList(serializers.ModelSerializer):
    group = serializers.SlugRelatedField(read_only=True, slug_field='code')

    class Meta:
        model = Operation
        fields = (
            'pk',
            'operation_name',
            'full_name',
            'operation_code',
            'group'
        )
class PartObjectFormatSerializer(serializers.ModelSerializer):

    class Meta:
        model = PartObjectFormat
        fields = ('part_object',
                  'format',
                  'list_quantity',
                  'order_num',
                  'edt_sess',
                  'crtd_sess',
                  'dlt_sess'
                  )


class PartObjectFormatSerializerList(serializers.ModelSerializer):
    format = serializers.SlugRelatedField(read_only=True, slug_field='list_value')

    class Meta:
        model = PartObjectFormat
        fields = (
            'pk',
            'format',
            'list_quantity',
            'order_num'
        )


class PartObjectSerializerList(serializers.ModelSerializer):
    group = serializers.SlugRelatedField(read_only=True, slug_field='code')
    parent = serializers.SlugRelatedField(read_only=True, slug_field='code')

    class Meta:
        model = PartObjectFast
        fields = (
            'pk',
            'part_type',
            'code',
            'parent',
            'title',
            'group',
            'nom_code',
            'ei'
        )


class PartObjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = PartObject
        fields = (
            'pk',
            'part_type',
            'code',
            'parent',
            'abbr',
            'title',
            'description',
            'group',
            'state',
            'source',
            'preference',
            'litera',
            'is_top',
            'nom_code',
            'unit',
            'weight',
            'weight_unit',
            'surface',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class DesignMaterField(serializers.Field):
    """Отображение конструкторского материала"""
    def to_representation(self, value):
        dm = DesignMater.objects.filter(parent_id=value).first()
        if dm:
            p = PartObject.objects.get(pk=dm.child.id)
            serializer = PartObjectRefSerializer(p)
            return serializer.data
        return None


class PartObjectSerializerDetailed(serializers.ModelSerializer):
    parent = EntityRefSerializer()
    group = EntityRefSerializer()
    part_type = PartTypeSerializer(read_only=True)
    unit = MeasureUnitRefSerializer()
    weight_unit = MeasureUnitRefSerializer()
    prod_order = EntityRefSerializer()
    origin = EntityRefSerializer()
    design_mater = DesignMaterField(source='pk')

    class Meta:
        model = PartObject
        fields = (
            'pk',
            'part_type',
            'code',
            'parent',
            'abbr',
            'title',
            'description',
            'group',
            'state',
            'source',
            'preference',
            'litera',
            'is_top',
            'nom_code',
            'unit',
            'weight',
            'weight_unit',
            'surface',
            'formats',
            'design_mater',
            'prod_order',
            'origin',
            'entity_label'
        )


class PartLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartLink
        fields = (
            'pk',
            'parent',
            'child',
            'quantity',
            'comment',
            'draft_zone',
            'position',
            'first_use',
            'ratio',
            'to_replace',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class TitleField(serializers.CharField):
    """Получение имени объекта конструкции"""
    def to_representation(self, value):
        return PartObject.objects.get(pk=value).title


class FormatField(serializers.CharField):
    """Получение форматов объекта конструкции"""
    def to_representation(self, value):
        return PartObject.objects.get(pk=value).formats


class PartTypeField(serializers.CharField):
    """Получение типа объекта конструкции"""
    def to_representation(self, value):
        return PartTypeSerializer(PartObject.objects.get(pk=value).part_type).data

    
class RoutesListField(serializers.JSONField):
    """Список маршрутов объекта"""

    def to_representation(self, value):
        return EntityRefSerializer(Route.filter.get(pk=value)).data


class PartLinkSerializerList(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(read_only=True, slug_field='key_code')
    child = CodeField(source='child_id')
    title = TitleField(source='child_id')
    part_type = PartTypeField(source='child_id')
    measurement = MeasurementField(source='child_id')
    formats = FormatField(source='child_id')

    class Meta:
        model = PartLink
        fields = (
            'pk',
            'parent_id',
            'parent',
            'child_id',
            'part_type',
            'child',
            'title',
            'quantity',
            'reg_quantity',
            'measurement',
            'comment',
            'draft_zone',
            'position',
            'to_replace',
            'ratio',
            'first_use',
            'formats'
        )


class RenditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rendition
        fields = (
            'pk',
            'parent',
            'rendition',
            'tail',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class RenditionSerializerList(serializers.ModelSerializer):
    rendition = serializers.SlugRelatedField(read_only=True, slug_field='get_code')
    tail = serializers.SlugRelatedField(read_only=True, slug_field='list_value')
    rendition_id = serializers.IntegerField()
    parent = EntityRefSerializer()

    class Meta:
        model = Rendition
        fields = (
            'pk',
            'parent',
            'rendition',
            'tail',
            'rendition_id'
        )


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = (
            'pk',
            'subject',
            'route_name',
            'process_code',
            'group_route',
            'var_code',
            'billet',
            'min_party',
            'norm_unit',
            'comment',
            'first_point',
            'state',
            'is_active',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class NomCodesObjectSerializerList(serializers.ModelSerializer):
    value = serializers.CharField(source='nom_code')

    class Meta:
        model = PartObject
        fields = (
            'pk',
            'value'
        )


class NormUnitSerializer(serializers.ModelSerializer):
    value = serializers.IntegerField(source='multiplicator')

    class Meta:
        model = NormUnit
        fields = ('pk', 'value')


class ParentSerializerList(serializers.Serializer):
    type_key = serializers.CharField(source='parent__type_key')
    id = serializers.IntegerField(source='parent_id')
    code = serializers.CharField(source='parent__code')
    title = serializers.CharField(source='parent__partobject__title')
    quantity = serializers.FloatField()
    prod_order_id = serializers.IntegerField(source='parent__partobject__prod_order_id')
    prod_order = serializers.CharField(source='parent__partobject__prod_order__code')


class RouteSerializerDetailed(serializers.ModelSerializer):
    subject = EntityRefSerializer()
    norm_unit = NormUnitSerializer()
    # state = RouteStateSerializer()

    class Meta:
        model = Route
        fields = (
            'pk',
            'subject',
            'route_name',
            'process_code',
            'group_route',
            'var_code',
            'billet',
            'min_party',
            'norm_unit',
            'comment',
            'first_point',
            'state',
            'is_active'
        )


class RoleDisignerSerializer(serializers.Serializer):
    """Сериализатор разработчиков у роли"""
    pk = serializers.IntegerField(source='designer__pk')
    value = serializers.CharField(source='designer__designer')


class RoleDesignersList(serializers.Field):
    """Отображение списка подходящих для роли разработчиков"""
    def to_representation(self, value):
        designers = DesignerRating.objects.filter(
            role=value,
            designer__selectable=True,
            rating__gt=0  # С нулевым рейтингом скорее всего ошибка
        ).values(
            'designer__pk',
            'designer__designer'
        ).order_by(
            '-rating'
        )
        if designers:
            if value == 1:  # Для разработки добавляем первым текущего пользователя
                user_id = self.context.get('user_id')
                if user_id:
                    himself = Designer.get_by_user(user_id)  # Получаем текущего пользователя как разработчика
                    # Убираем его из основного списка
                    designers = designers.exclude(designer__designer_profile__user_id=user_id)
                    designers = chain(himself, designers)  # Соединяем результаты запросов
            serializer = RoleDisignerSerializer(designers, many=True)
            return serializer.data
        return None


class RolesDesignersSerializerList(serializers.Serializer):
    pk = serializers.IntegerField(read_only=True)
    designers = RoleDesignersList(source='pk')


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('pk', 'list_value', 'order_num', 'is_default')


class RoutePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutePoint
        fields = (
            'pk',
            'route',
            'next_point',
            'place',
            'order_num',
            'comment',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class RoutePointSerializerDetailed(serializers.ModelSerializer):
    place = EntityRefSerializer()

    class Meta:
        model = RoutePoint
        fields = (
            'pk',
            'route',
            'next_point',
            'place',
            'order_num',
            'comment'
        )


class RoutePointSerializerList(serializers.Serializer):
    pk = serializers.IntegerField()
    order_num = serializers.IntegerField()
    code = serializers.CharField(source='place__code')


class TpRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = TpRow
        fields = (
            'pk',
            'route',
            'route_point',
            'parent',
            'operation',
            'row_type',
            'order_num',
            'row_num',
            'row_text',
            'litera',
            'lost',
            'lost_alt',
            'replaced',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class TpResourceModelSerializer(serializers.ModelSerializer):
    tp_row = TpRowSerializer()

    class Meta:
        model = TpResource
        fields = (
            'pk',
            'parent',
            'child',
            'quantity',
            'net_weight',
            'child_route',
            'notice',
            'tp_row',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )

    def create(self, validated_data):
        # Сначала создаем строку техпроцесса
        tp_row_data = validated_data.pop('tp_row')
        tp_row = TpRow.objects.create(**tp_row_data)
        return TpResource.objects.create(tp_row=tp_row, **validated_data)


class TpResourceSerializer(serializers.Serializer):
    # Нужен для разбора параметров перед записью
    pk = serializers.IntegerField()
    child = serializers.IntegerField()
    quantity = serializers.FloatField()
    net_weight = serializers.FloatField(allow_null=True)  # Чтобы сохранять пустые значения
    notice = serializers.IntegerField()
    tp_row = serializers.IntegerField()
    row_type = serializers.IntegerField()
    edt_sess = serializers.IntegerField()
    crtd_sess = serializers.IntegerField()
    dlt_sess = serializers.IntegerField()

    def update(self, instance, validated_data):
        # Сначала обновляем строку техпроцесса
        row_type_id = validated_data.pop('row_type')
        row_type = TpRowType.objects.get(pk=row_type_id)
        instance.row_type = row_type
        instance.edt_sess = validated_data.get('edt_sess')
        instance.save()

        # Далее сохраняем сам ресурс
        tp_resource = TpResource.objects.get(tp_row=instance.pk)
        serializer = TpResourceModelSerializer(tp_resource, data=validated_data, partial=True)
        if serializer.is_valid():
            tp_resource = serializer.save()
        return tp_resource

    def to_representation(self, instance):
        # Гребаная заглушка, чтобы не было ошибки сохранения
        return {"aa": "bb"}


class TpResourceSerializerDetailed(serializers.Serializer):
    pk = serializers.IntegerField()
    order_num = serializers.IntegerField()
    row_type = serializers.IntegerField()
    child = EntityIdRefSerializer(source='tpresource__child')
    nom_code = serializers.CharField(source='tpresource__child__partobject__nom_code')
    quantity = serializers.FloatField(source='tpresource__quantity')
    net_weight = serializers.FloatField(source='tpresource__net_weight')
    notice = EntityIdRefSerializer(source='tpresource__notice')
    unit = serializers.CharField(source='tpresource__child__partobject__unit__short_name')


class TpResourceSerializerList(serializers.Serializer):
    pk = serializers.IntegerField()
    order_num = serializers.IntegerField()
    child = serializers.IntegerField(source='tpresource__child',)
    code = serializers.CharField(source='tpresource__child__code')


class TpRowSerializerDetailed(serializers.ModelSerializer):
    operation = OperationRefSerializer()

    class Meta:
        model = TpRow
        fields = (
            'pk',
            'route',
            'route_point',
            'parent',
            'operation',
            'row_type',
            'order_num',
            'row_num',
            'row_text',
            'litera',
            'lost',
            'lost_alt'
        )


class TpRowSerializerList(serializers.Serializer):
    pk = serializers.IntegerField()
    order_num = serializers.IntegerField()
    operation_name = serializers.CharField(source='operation__operation_name')


class TypeSizeMaterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeSizeMater
        fields = (
            'pk',
            'parent',
            'child',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class TypeSizeMaterSerializerList(serializers.ModelSerializer):
    parent = EntityRefSerializer()

    class Meta:
        model = TypeSizeMater
        fields = (
            'pk',
            'parent',
        )


class TypeSizeSortSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeSizeSort
        fields = (
            'pk',
            'parent',
            'child',
            'thickness',
            'width',
            'wall',
            'unit',
            'typesize',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class TypeSizeSortSerializerList(serializers.ModelSerializer):
    parent = EntityRefSerializer()
    unit = MeasureUnitRefSerializer()

    class Meta:
        model = TypeSizeSort
        fields = (
            'pk',
            'parent',
            'thickness',
            'width',
            'wall',
            'unit',
            'typesize'
        )
