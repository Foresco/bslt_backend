from rest_framework import serializers

from jsonserv.core.serializers import EntityRefSerializer, get_list_serializer_class, MeasureUnitRefSerializer

from jsonserv.supply.models import OrderProdPosition, Price, PriceType, SupplyOrder


class OrderProdPositionSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderProdPosition
        fields = (
            'pk',
            'supply_order',
            'prod_order_link',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class OrderProdPositionSerializerList(serializers.Serializer):
    pk = serializers.IntegerField()
    supply_order = serializers.CharField(source='supply_order__code')
    supply_id = serializers.IntegerField(source='supply_order__pk')
    prod_order_link_id = serializers.IntegerField(source='prod_order_link__pk')
    parent_id = serializers.IntegerField(source='prod_order_link__parent_id')
    parent_code = serializers.CharField(source='prod_order_link__parent__code')
    child_id = serializers.IntegerField(source='prod_order_link__child_id')
    child_code = serializers.CharField(source='prod_order_link__child__code')
    child_title = serializers.CharField(source='prod_order_link__child__partobject__title')
    quantity = serializers.FloatField(source='prod_order_link__quantity')
    mater_id = serializers.IntegerField(source='prod_order_link__child__design_mater__child_id')
    mater_code = serializers.CharField(source='prod_order_link__child__design_mater__child__code')
    surface = serializers.CharField(source='prod_order_link__child__partobject__surface')
    billet_desc = serializers.CharField(source='prod_order_link__billet_desc')  # Заготовка позиции в заказе
    mater_state_id = serializers.IntegerField(source='prod_order_link__mater_state__pk')
    mater_state = serializers.CharField(source='prod_order_link__mater_state__value_class')


class PriceSerializer(serializers.ModelSerializer):

    class Meta:
            model = Price
            fields = (
                'pk',
                'supplier',
                'supplied_entity',
                'price_type',                                    
                # 'for_order',
                'price',
                'price_unit',
                'quantity',
                'quantity_unit',
                'supply_date',
                'is_active',
                'article',
                'doc',
                'comment',
                'edt_sess',
                'crtd_sess',
                'dlt_sess'
                )


class PriceSerializerList(serializers.ModelSerializer):
    supplier = serializers.SlugRelatedField(read_only=True, slug_field='code')
    price_unit = MeasureUnitRefSerializer()
    price_type = get_list_serializer_class(PriceType)

    class Meta:
        model = Price
        fields = (
            'pk',
            'price',
            'price_unit',
            'supplier',
            'price_type'
            )



class SupplyOrderSerializerDetailed(serializers.ModelSerializer):
    supplier = EntityRefSerializer(read_only=True)

    class Meta:
        model = SupplyOrder
        fields = (
            'pk',
            'code',
            'description',
            'supplier',
            'order_date',
            'amount'
            )


class SupplyOrderSerializerList(serializers.ModelSerializer):
    supplier = serializers.SlugRelatedField(read_only=True, slug_field='code')
    order_date = serializers.DateField(format="%d.%m.%Y")

    class Meta:
        model = SupplyOrder
        fields = (
            'pk',
            'code',
            'description',
            'supplier',
            'order_date'
            )


class SupplyOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = SupplyOrder
        fields = (
            'pk',
            'code',
            'description',
            'supplier',
            'order_date',
            'amount',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
            )


class OrderPosMaterSupplierSerializer(serializers.Serializer):
    """Сериализатор заказа на поставку позиции"""
    caption = serializers.CharField(source='supply_order__code')
    id = serializers.IntegerField(source='supply_order__id')
    text = serializers.CharField(source='supply_order__supplier__code')


class OrderPosMaterSuppliersList(serializers.Field):
    """Отображение списка поставщиков материалов для позиции в заказе"""
    def to_representation(self, value):
        supplies = OrderProdPosition.objects.filter(
            prod_order_link=value,
            dlt_sess=0
        ).values(
            'supply_order__code',
            'supply_order__id',
            'supply_order__supplier__code'
        ).order_by(
            'supply_order__order_date',
            'supply_order__code'
        )
        if supplies:
            serializer = OrderPosMaterSupplierSerializer(supplies, many=True)
            return serializer.data
        return None


class SupplyMaterListSerializerList(serializers.Serializer):
    pk = serializers.IntegerField(read_only=True)  # Идентификатор связи
    code = serializers.CharField(source='parent__code')  # Номер заказа
    parent_id = serializers.IntegerField(source='parent__pk')  # Идентификатор заказа
    parent_type_key = serializers.CharField(source='parent__type_key')  # Тип заказа
    type_key = serializers.CharField(source='child__type_key')  # Тип изготавливаемой позиции
    part_type = serializers.CharField(source='child__partobject__part_type')  # Подтип изготавливаемой позиции
    child_id = serializers.IntegerField(source='child__pk')  # Изготавливаемая позиция
    child = serializers.CharField(source='child__code')  # Изготавливаемая позиция
    title = serializers.CharField(source='child__partobject__title')  # Наименование
    quantity = serializers.FloatField()  # Количество в задании
    mater_state = serializers.CharField(source='mater_state__value_class')  # Метка состояния поставки материала
    material = serializers.CharField(source='child__design_mater__child__code')  # Материал
    supply_orders = OrderPosMaterSuppliersList(source='pk')
    ship_quantity = serializers.FloatField()
