from rest_framework.generics import ListAPIView
from django.db.models import F, Subquery
from django.db.models.functions import Coalesce

from jsonserv.manufacture.models import ProdOrderLink
from jsonserv.manufacture.views import ship_quantity, ProdOrderStaffListFilter

from jsonserv.supply.serializers import SupplyMaterListSerializerList


class SupplyMaterList(ListAPIView):
    serializer_class = SupplyMaterListSerializerList
    filterset_class = ProdOrderStaffListFilter  # Особые настройки фильтрации
    name = 'prod-order-mater-list'

    def get_queryset(self):
        a = ProdOrderLink.objects.values(
            'pk',
            'parent__code',
            'parent__pk',
            'parent__type_key',
            'child__code',
            'child__partobject__title',
            'child__type_key',
            'child__partobject__part_type',
            'child__pk',
            'quantity',
            'mater_state__value_class',
            'child__design_mater__child__code'
        ).annotate(
            ship_quantity=Coalesce(Subquery(ship_quantity), 0.0),
            not_supplied=F('quantity')-F('ship_quantity')
        ).order_by(
            'parent__prodorder__order_date',
            'parent__code',
            'child__code'
        )
        # print(a.query)
        return a

    # Поля поиска
    search_fields = (
        'parent__code',
        'child__code',
        'child__partobject__title'
    )
