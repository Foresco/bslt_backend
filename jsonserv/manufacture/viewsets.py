import django_filters  # Специальные фильтры
from django.db.models import Count, F, Sum, Q, Subquery
from django.db.models.functions import Coalesce
from jsonserv.core.viewsets import CommonViewSet
from jsonserv.rest.views import get_user_profile

from jsonserv.core.viewsets import DateEqualFilter, EqualFilter
from jsonserv.manufacture.models import (ProdOrder, ProdOrderLink, ProdOrderLinkTpRow, ProdOrderLinkWorker,
                                         Shipment, WorkerReportConsist, WorkerShift)

from jsonserv.manufacture.serializers import (ProdOrderSerializer,
                                              ProdOrderSerializerDetailed, ProdOrderLinkSerializer,
                                              ProdOrderSerializerList,
                                              ProdOrderLinkSerializerList, ProdOrderLinkTpRowSerializer,
                                              ProdOrderLinkWorkerSerializerList,
                                              ProdOrderLinkWorkerSerializer,
                                              ShipmentSerializer, ShipmentSerializerList,
                                              WorkerReportConsistSerializer, WorkerReportConsistSerializerList,
                                              WorkerShiftSerializer, WorkerShiftSerializerList)

from jsonserv.manufacture.views import ship_quantity


class ProdOrderViewSet(CommonViewSet):
    queryset = ProdOrder.objects.all()
    serializer_class = ProdOrderSerializer
    serializer_class_list = ProdOrderSerializerList
    serializer_class_detailed = ProdOrderSerializerDetailed

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


class ProdOrderLinkViewSet(CommonViewSet):
    queryset = ProdOrderLink.objects.all()
    serializer_class = ProdOrderLinkSerializer
    serializer_class_list = ProdOrderLinkSerializerList
    serializer_class_detailed = ProdOrderLinkSerializer
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    # Поля фильтрации
    filterset_fields = (
        'parent',
    )

    def get_queryset(self):
        if self.action == 'list':
            # Агрегация с фильтрацией неудаленных
            done_quantity = Sum("prodorder_link_workers__worker_reports__quantity",
                                filter=Q(prodorder_link_workers__worker_reports__dlt_sess=0))
            return ProdOrderLink.objects.annotate(
                done_quantity=done_quantity,
                ship_quantity=Coalesce(Subquery(ship_quantity), 0.0),
            ).order_by(
                'child__code'
            )
        return ProdOrderLink.objects.all()


class ProdOrderLinkTpRowViewSet(CommonViewSet):
    queryset = ProdOrderLinkTpRow.objects.all()
    serializer_class = ProdOrderLinkTpRowSerializer
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    # Поля фильтрации
    filterset_fields = (
        'prod_order_link',
        'tp_row'
    )


class ProdOrderLinkWorkerViewSet(CommonViewSet):
    queryset = ProdOrderLinkWorker.objects.all()
    serializer_class = ProdOrderLinkWorkerSerializer
    serializer_class_list = ProdOrderLinkWorkerSerializerList

    def create(self, request, *args, **kwargs):
        # Заполнение идентификатора пользователя текущим, если он не заполнен
        if 'worker' not in request.data:
            request.data['worker'] = get_user_profile(self.request.session)
        return super().create(request, *args, **kwargs)

    # Поля фильтрации
    filterset_fields = (
        'prod_order_link',
        'tp_row'
    )


class ShipmentViewSet(CommonViewSet):
    queryset = Shipment.objects.all().order_by('shipment_date')
    serializer_class = ShipmentSerializer
    serializer_class_list = ShipmentSerializerList
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    # Поля фильтрации
    filterset_fields = (
        'prod_order_link',
    )


class WorkerReportConsistViewSet(CommonViewSet):
    queryset = WorkerReportConsist.objects.all()
    serializer_class = WorkerReportConsistSerializer
    serializer_class_list = WorkerReportConsistSerializerList
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    # Поля фильтрации
    filterset_fields = (
        'task_link',
    )


class WorkerShiftFilter(django_filters.FilterSet):
    """Особые фильтры для списка заказов в работе"""
    min_date = django_filters.DateFilter(field_name="shift_date", lookup_expr='gte')
    max_date = django_filters.DateFilter(field_name="shift_date", lookup_expr='lte')
    equal_date = DateEqualFilter(field_name="shift_date")
    worker = django_filters.NumberFilter(field_name="worker")
    work_shift = EqualFilter(field_name="work_shift")

    class Meta:
        fields = ['equal_date', 'min_date', 'max_date', 'worker', 'shift']


class WorkerShiftViewSet(CommonViewSet):
    queryset = WorkerShift.objects.all()
    serializer_class = WorkerShiftSerializer
    serializer_class_list = WorkerShiftSerializerList
    # serializer_class_detailed = WorkerShiftSerializerDetailed
    filterset_class = WorkerShiftFilter  # Особые настройки фильтрации

    def get_queryset(self):
        if self.action == 'list':
            # Агрегация с фильтрацией неудаленных
            aux_time = Sum("workerreportconsist__aux_time", filter=Q(workerreportconsist__dlt_sess=0))
            report_count = Count("workerreportconsist__pk", filter=Q(workerreportconsist__dlt_sess=0))
            work_time = Sum(
                F("workerreportconsist__work_time") * (
                        Coalesce(F("workerreportconsist__quantity"), 0.0) + Coalesce(
                    F("workerreportconsist__bad_quantity"), 0.0)),
                filter=Q(workerreportconsist__dlt_sess=0))
            return WorkerShift.objects.select_related('worker').annotate(
                work_time=work_time / 60,  # Пересчет в часы
                report_count=report_count,  # Количество отчетов за смену
                aux_time=Coalesce(aux_time, 0.0),
            ).filter(
                report_count__gt=0  # Только смены, где были отчеты
            ).order_by(
                'shift_date',
                'worker__user_name',
                'work_shift__order_num'
            )
        return WorkerShiftViewSet.queryset
