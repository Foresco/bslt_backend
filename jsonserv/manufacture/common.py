from django.db.models import F, Func, OuterRef
from jsonserv.manufacture.models import Shipment

# Общие элементы всех запросов
# Суммирование всех отгрузок
ship_quantity = Shipment.objects.filter(
    prod_order_link=OuterRef('pk'),
    dlt_sess=0
).order_by().annotate(ship_quantity=Func(F('quantity'), function='SUM')).values('ship_quantity')
