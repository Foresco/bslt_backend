import django_filters  # Специальные фильтры
from jsonserv.core.viewsets import DateEqualFilter, EqualFilter
from jsonserv.core.viewsets import CommonViewSet

from jsonserv.supply.models import OrderProdPosition, Price, SupplyOrder
from jsonserv.supply.serializers import (OrderProdPositionSerializer, OrderProdPositionSerializerList,
                                         PriceSerializer, PriceSerializerList,
                                         SupplyOrderSerializer, SupplyOrderSerializerDetailed, SupplyOrderSerializerList)


class OrderProdPositionViewSet(CommonViewSet):
    queryset = OrderProdPosition.objects.all()
    serializer_class = OrderProdPositionSerializer
    serializer_class_list = OrderProdPositionSerializerList
    serializer_class_detailed = OrderProdPositionSerializer
    paginator = None

    def get_queryset(self):
        if self.action == 'list':  # Для списка обогащаем набор данными
            return OrderProdPosition.objects.all().values(
                'pk',
                'supply_order__code',
                'supply_order__pk',
                'prod_order_link__pk',
                'prod_order_link__comment',
                'prod_order_link__parent_id',
                'prod_order_link__parent__code',
                'prod_order_link__child_id',
                'prod_order_link__child__code',
                'prod_order_link__child__partobject__title',
                'prod_order_link__child__partobject__surface',
                'prod_order_link__child__design_mater__child_id',
                'prod_order_link__child__design_mater__child__code',
                'prod_order_link__billet_desc',
                'prod_order_link__quantity',
                'prod_order_link__mater_state__pk',
                'prod_order_link__mater_state__value_class'
            ).order_by(
                'prod_order_link__parent__code',
                'prod_order_link__child__code'
            )
        return OrderProdPositionViewSet.queryset  # Иначе по умолчанию

    # Поля фильтрации
    filterset_fields = (
        'supply_order',
        'prod_order_link',
        'prod_order_link__child'
    )


class PriceViewSet(CommonViewSet):
    queryset = Price.objects.all().order_by('price_type__order_num', 'price_type__list_value')
    serializer_class = PriceSerializer
    serializer_class_list = PriceSerializerList
    # serializer_class_detailed = PriceSerializerDetailed
    pagination_class = None

    # Поля фильтрации
    filterset_fields = (
        'supplied_entity',
    )


class SupplyOrderListFilter(django_filters.FilterSet):
    """Особые фильтры для списка заказов на поставку"""
    min_date = django_filters.DateFilter(field_name="order_date", lookup_expr='gte')
    max_date = django_filters.DateFilter(field_name="order_date", lookup_expr='lte')
    equal_date = DateEqualFilter(field_name="order_date")
    supplier = EqualFilter(field_name="supplier")

    class Meta:
        fields = ['supplier', 'equal_date', 'min_date', 'max_date']


class SupplyOrderViewSet(CommonViewSet):
    queryset = SupplyOrder.objects.all().order_by('-order_date', 'code')
    filterset_class = SupplyOrderListFilter  # Особые настройки фильтрации
    serializer_class = SupplyOrderSerializer
    serializer_class_list = SupplyOrderSerializerList
    serializer_class_detailed = SupplyOrderSerializerDetailed

    # Поля поиска
    search_fields = (
        'code',
        'description',
    )
