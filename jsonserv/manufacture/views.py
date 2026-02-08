import django_filters  # Специальные фильтры
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Exists, F, FilteredRelation, Func, Min, OuterRef, Subquery, Q, Window
from django.db.models.functions import Coalesce
from rest_framework.generics import ListAPIView

from jsonserv.rest.views import get_user_profile
from jsonserv.core.viewsets import DateEqualFilter, EqualFilter
from jsonserv.pdm.models import Route, RoutePoint, TpRow
from jsonserv.manufacture.common import ship_quantity

from jsonserv.manufacture.models import (ProdOrder, ProdOrderLink, ProdOrderLinkWorker, Shipment,
                                         WorkerReportConsist)
from jsonserv.manufacture.serializers import (ObjectOperationSerializerList, PositionsOperationSerializerList,
                                              ProdOrderContractSerializerList, ProdOrderInWorkSerializerList,
                                              ProdOrderMaterSerializerList, ProdOrderPosOperationSerializerList,
                                              ProdOrderPosReportSerializerList, WorkerTaskSerializerList,
                                              WorkerReportConsistSerializerList)

# Общие элементы всех запросов
# Подсчет количества отгрузок
shipment_count = ProdOrderLink.objects.filter(
    parent=OuterRef('pk'),
    prodorder_link_shipments__pk__isnull=False,
    prodorder_link_shipments__dlt_sess=0
    # dlt_sess=0 # Вроде не надо? Есть в objects?
).order_by().annotate(
    shipment_count=Func(F('prodorder_link_shipments__pk'), function='COUNT')
).values('shipment_count')

# Анализ отгруженности
unshipped_quantity = ProdOrderLink.objects.filter(
    parent=OuterRef('pk'),
    # dlt_sess=0 # Вроде не надо? Есть в objects?
).order_by().annotate(
    rquantity=Func(F('quantity'), function='SUM'),
    ship_quantity=Func(F('prodorder_link_shipments__quantity'), function='SUM'),
    not_supplied=F('rquantity') - F('ship_quantity')
    ).values(
        'not_supplied'
    )

# Состояние материалов
mater_state = ProdOrderLink.objects.filter(
        parent=OuterRef('pk')
    ).order_by('mater_state_id')

# Состояние КД
design_doc_state = ProdOrderLink.objects.filter(
        parent=OuterRef('pk')
    ).order_by('design_doc_id')    

class ObjectOperationList(ListAPIView):
    """Отображение всех операций изготовления объекта"""
    serializer_class = ObjectOperationSerializerList
    name = 'object-operation-list'
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    def get_queryset(self):
        """Список обязательно фильтруется по объекту"""
        # subject = self.kwargs['subject']
        link = self.kwargs['link']
        # Определение подходящего маршрута
        route_id = ProdOrderLink.objects.get(pk=link).get_route_id()
        # Агрегация всех отчетов по данной позиции
        done_quantity = ProdOrderLinkWorker.objects.filter(
            tp_row=OuterRef('point_tp_rows__pk'), prod_order_link=link,
            worker_reports__dlt_sess=0
        ).order_by().annotate(done_quantity=Func(F('worker_reports__quantity'), function='SUM')).values(
            'done_quantity')
        return RoutePoint.objects.filter(
            route_id=route_id,
            point_tp_rows__pk__isnull=False,  # Указаны операции
            dlt_sess=0,  # Элементы маршрута не удалены
            point_tp_rows__dlt_sess=0  # Операции не удалены
        ).annotate(
            done_quantity=Subquery(done_quantity),
        ).values(
            'point_tp_rows__pk',
            'place__code',
            'point_tp_rows__operation__operation_name',
            'order_num',
            'point_tp_rows__order_num',
            'done_quantity'
        ).order_by(
            'order_num',
            'point_tp_rows__order_num'
        )


class ProdOrderPosOperationList(ListAPIView):
    """Отображение всех операций изготовления позиции из заказа"""
    serializer_class = ProdOrderPosOperationSerializerList
    name = 'prod-order-pos-operation-list'
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    def get_queryset(self):
        """Список обязательно фильтруется по объекту"""
        # subject = self.kwargs['subject']
        link = self.kwargs['link']
        # Определение подходящего маршрута
        route_id = ProdOrderLink.objects.get(pk=link).get_route_id()
        # Агрегация всех заданий по данной позиции
        set_quantity = ProdOrderLinkWorker.objects.filter(
            tp_row=OuterRef('point_tp_rows__pk'), prod_order_link=link
        ).order_by().annotate(set_quantity=Func(F('quantity'), function='SUM')).values(
            'set_quantity')
        # Агрегация всех отчетов по данной позиции
        done_quantity = ProdOrderLinkWorker.objects.filter(
            tp_row=OuterRef('point_tp_rows__pk'), prod_order_link=link,
            worker_reports__dlt_sess=0
        ).order_by().annotate(done_quantity=Func(F('worker_reports__quantity'), function='SUM')).values(
            'done_quantity')
        return RoutePoint.objects.filter(
            route_id=route_id,
            dlt_sess=0,  # Элементы маршрута не удалены
            point_tp_rows__pk__isnull=False,  # Указаны операции
            point_tp_rows__dlt_sess=0  # Операции не удалены
        ).annotate(
            set_quantity=Subquery(set_quantity),
            done_quantity=Subquery(done_quantity)
        ).values(
            'point_tp_rows__pk',
            'place__code',
            'point_tp_rows__operation__operation_name',
            'order_num',
            'point_tp_rows__order_num',
            'set_quantity',
            'done_quantity'
        ).order_by(
            'order_num',
            'point_tp_rows__order_num'
        )


class ProdOrderPosReportList(ListAPIView):
    """Отображение всех отчетов по всем операциям изготовления позиции из заказа"""
    serializer_class = ProdOrderPosReportSerializerList
    name = 'prod-order-pos-report-list'
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    def get_queryset(self):
        """Список фильтруется по позиции состава"""
        link = self.kwargs['link']
        return ProdOrderLinkWorker.objects.filter(
            prod_order_link=link,
            tp_row__dlt_sess=0,  # Операции не удалены
            tp_row__route_point__dlt_sess=0,  # Элементы маршрута не удалены
            worker_reports__dlt_sess=0  # Отчеты не удалены
        ).values(
            'worker_reports__pk',
            'tp_row__route_point__place__code',
            'tp_row__operation__operation_name',
            'tp_row__route_point__order_num',
            'tp_row__order_num',
            'worker__user_name',
            'worker_reports__report_date',
            'worker_reports__quantity',
            'worker_reports__bad_quantity',
            'worker_reports__comment',
            'worker_reports__work_shift__order_num'
        ).order_by(
            'worker_reports__report_date',
            'tp_row__route_point__order_num',
            'tp_row__order_num',
            'worker__user_name'
        )


class PlaceFilter(django_filters.Filter):
    """Фильтрация по признаку наличия прозводственного подразделения"""

    def filter(self, qs, value):
        if value not in (None, ''):
            return qs.filter(Exists(Route.objects.filter(subject=OuterRef(self.field_name), route_points__dlt_sess=0,
                                                         route_points__place=value)))
        return qs


class OperationFilter(django_filters.Filter):
    """Фильтрация по признаку наличия операции"""

    def filter(self, qs, value):
        if value not in (None, ''):
            return qs.filter(Exists(Route.objects.filter(subject=OuterRef(self.field_name), tp_rows__dlt_sess=0,
                                                         tp_rows__route_point__dlt_sess=0, tp_rows__operation=value)))
        return qs


class NotSuppliedFilter(django_filters.Filter):
    """Фильтрация поставленных не полностью"""

    def filter(self, qs, value):
        if value not in (None, '', 'false'):
            return qs.filter(not_supplied__gt=0)
        return qs


class MaterStateNot3Filter(django_filters.Filter):
    """Фильтрация позиций, обеспеченных (mater_state = 3) материалами"""

    def filter(self, qs, value):
        if value in (None, '', 'false'):
            return qs.exclude(mater_state_id=3)  # Исключаем обеспеченные материалы
        return qs


class ProdOrderStaffListFilter(django_filters.FilterSet):
    """Особые фильтры для списка заказов в работе"""
    min_date = django_filters.DateFilter(field_name="parent__prodorder__order_date", lookup_expr='gte')
    max_date = django_filters.DateFilter(field_name="parent__prodorder__order_date", lookup_expr='lte')
    equal_date = DateEqualFilter(field_name="parent__prodorder__order_date")
    ordermaker = django_filters.NumberFilter(field_name="parent__prodorder__order_maker")
    material = EqualFilter(field_name="child__design_mater__child")
    states = django_filters.BaseInFilter(field_name='parent__prodorder__state', lookup_expr='in')
    place = PlaceFilter(field_name='child__pk')
    operation = OperationFilter(field_name='child__pk')
    not_supplied = NotSuppliedFilter()

    class Meta:
        
        fields = ['ordermaker', 'equal_date', 'min_date', 'max_date', 'states', 'place', 'operation', 'material']


class ProdOrderListFilter(django_filters.FilterSet):
    """Особые фильтры для списка заказов в работе"""
    min_date = django_filters.DateFilter(field_name="order_date", lookup_expr='gte')
    max_date = django_filters.DateFilter(field_name="order_date", lookup_expr='lte')
    equal_date = DateEqualFilter(field_name="order_date")
    ordermaker = django_filters.NumberFilter(field_name="order_maker")
    states = django_filters.BaseInFilter(field_name='state', lookup_expr='in')

    class Meta:
        fields = ['ordermaker', 'equal_date', 'min_date', 'max_date', 'states']


class ProdOrderContract(ListAPIView):
    """Получение перечня всех заказов и догворов, находящихся в работе"""
    serializer_class = ProdOrderContractSerializerList
    filterset_class = ProdOrderListFilter  # Особые настройки фильтрации
    name = 'prod-order-contract-list'
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        a = ProdOrder.objects.values(
            'pk',
            'code',
            'type_key',
            'order_date',
            'order_maker',
            'order_maker__code',
            'state',
            'calc_date',
            'state__list_value',
            'spec_account__list_value',
            'payment_state__value_class',
            'milit_test', 
            'milit_comment'
        ).annotate(
            shipment_count=Subquery(shipment_count),
            unshipped_quantity=Subquery(unshipped_quantity),
            mater_state=Subquery(mater_state.values('mater_state__value_class')[:1]),
            design_doc_state=Subquery(mater_state.values('design_doc__value_class')[:1])
        )
        # print(a.query)
        return a

    # Поля поиска
    search_fields = (
        'code',
    )


class ProdOrderInWorkList(ListAPIView):
    """Получение перечня всех заказов и их позиций, находящихся в работе"""
    serializer_class = ProdOrderInWorkSerializerList
    filterset_class  = ProdOrderStaffListFilter  # Особые настройки фильтрации
    name = 'prod-order-in-work-list'

    def get_common_queryset(self):
        # Агрегация всех отчетов по данной позиции
        done_quantity = ProdOrderLinkWorker.objects.filter(
            prod_order_link=OuterRef('pk'),
            worker_reports__dlt_sess=0
        ).order_by().annotate(done_quantity=Func(F('worker_reports__quantity'), function='SUM')).values(
            'done_quantity')
        # Подсчет количества операций
        oper_quantity = TpRow.objects.filter(
            route__subject=OuterRef('child__pk'),
            route_point__dlt_sess=0,
            dlt_sess=0
        ).order_by().annotate(oper_quantity=Func(F('pk'), function='COUNT')).values(
            'oper_quantity')
        a = ProdOrderLink.objects.values(
            'pk',
            'parent__code',
            'parent__pk',
            'parent__type_key',
            'parent__prodorder__order_date',
            'parent__prodorder__order_maker',
            'parent__prodorder__order_maker__code',
            'parent__prodorder__state',
            'parent__prodorder__state__list_value',
            'child__code',
            'child__partobject__title',
            'child__type_key',
            'child__partobject__part_type',
            'child__pk',
            'quantity',
            'route_id',
            'mater_state__value_class',
            'tool_state__value_class'
        ).annotate(
            oper_quantity=Subquery(oper_quantity),
            done_quantity=Subquery(done_quantity),
            ship_quantity=Coalesce(Subquery(ship_quantity), 0.0),
            not_supplied=F('quantity') - F('ship_quantity'),
            min_date=Window(expression=Min('parent__prodorder__order_date'), partition_by=[F('child')]),
        )
        # print(a.query)
        return a

    def get_queryset(self):
        # Ради изменения сортировки в дочерних классах
        parent_ordering = self.request.GET.get('ordering', 'parent__code')
        a = self.get_common_queryset()
        return a.order_by(
            'parent__prodorder__order_date',
            parent_ordering,
            'child__code'
        )

    # Поля поиска
    search_fields = (
        'parent__code',
        'child__code',
        'child__partobject__title'
    )


class PositionInWorkList(ProdOrderInWorkList):
    name = 'position-in-work-list'
    ordering_fields = ['min_date', 'child__code', 'parent__prodorder__order_date', 'parent__code']

    def get_queryset(self):
        # Ради изменения сортировки в дочерних классах
        child_ordering = self.request.GET.get('ordering', 'child__code')
        a = self.get_common_queryset()
        return a.order_by(
            'min_date',
            child_ordering,
            'parent__prodorder__order_date',
            'parent__code'
        )

class PositionsOperationList(ListAPIView):
    """Получение перечня операций позиций всех заказов, находящихся в работе"""
    serializer_class = PositionsOperationSerializerList
    filterset_class  = ProdOrderStaffListFilter  # Особые настройки фильтрации
    name = 'positions-operation-list'

    def get_queryset(self):
        # Идентификатор работника или передается в параметрах или получаем как идентификатор профиля пользователя
        worker = self.request.GET.get('worker', get_user_profile(self.request.session))
        # Агрегация всех отчетов по операции данной позиции
        done_quantity = ProdOrderLinkWorker.objects.filter(
            tp_row=OuterRef('route__route_points__point_tp_rows__pk'),
            prod_order_link=OuterRef('pk'),
            worker_reports__dlt_sess=0
        ).order_by().annotate(done_quantity=Func(F('worker_reports__quantity'), function='SUM')).values(
            'done_quantity')
        bad_quantity = ProdOrderLinkWorker.objects.filter(
            tp_row=OuterRef('route__route_points__point_tp_rows__pk'),
            prod_order_link=OuterRef('pk'),
            worker_reports__dlt_sess=0
        ).order_by().annotate(bad_quantity=Func(F('worker_reports__bad_quantity'), function='SUM')).values(
            'bad_quantity')

        a = ProdOrderLink.objects.select_related('route').filter(
            route__route_points__dlt_sess=0,  # Элементы маршрута не удалены
            route__route_points__point_tp_rows__pk__isnull=False,  # Указаны операции
            route__route_points__point_tp_rows__dlt_sess=0  # Операции не удалены
        ).filter(
            Exists(Route.objects.filter(
                # subject=OuterRef('child__pk'),
                pk=OuterRef('route_id'),
                # Подразделения только те, где работает исполнитель
                route_points__place__place_persons__person__person_profile=worker,
                route_points__place__place_persons__dlt_sess=0))
        ).exclude(
            parent__prodorder__state_id=4  # Заказы в состоянии Отгружен
        ).annotate(
            done_quantity=Subquery(done_quantity),
            bad_quantity=Subquery(bad_quantity),
            ship_quantity=Coalesce(Subquery(ship_quantity), 0.0),
        ).filter(
            quantity__gt=F('ship_quantity')
        ).values(
            'pk',
            'parent__code',
            'parent__pk',
            'parent__prodorder__order_date',
            'parent__prodorder__state',
            'parent__prodorder__state__list_value',
            'child__code',
            'child__partobject__title',
            'child__type_key',
            'child__partobject__part_type',
            'child__pk',
            'route__route_points__point_tp_rows__pk',
            'route__route_points__place__code',
            'route__route_points__point_tp_rows__operation__operation_name',
            'route__route_points__order_num',
            'route__route_points__point_tp_rows__order_num',
            'quantity',
            'done_quantity',
            'bad_quantity',
            'ship_quantity',
            'route__route_points__point_tp_rows__pk'
        ).order_by(
            'parent__prodorder__order_date',
            'parent__code',
            'child__code',
            'route__route_points__order_num',
            'route__route_points__point_tp_rows__order_num'
        )
        # print(a.query)
        return a

    # Поля поиска
    search_fields = (
        'parent__code',
        'child__code',
        'child__partobject__title'
    )


class PositionOperationReportList(ListAPIView):
    """Отображение всех отчетов по операции изготовления позиции из заказа"""
    serializer_class = WorkerReportConsistSerializerList
    name = 'position-operation-report-list'
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    def get_queryset(self):
        tp_row = self.kwargs['tp_row']
        link = self.kwargs['link']
        worker = get_user_profile(self.request.session)
        return WorkerReportConsist.objects.filter(
            task_link__prod_order_link=link,
            task_link__tp_row=tp_row,
            task_link__worker=worker,
            task_link__dlt_sess=0
        ).order_by(
            'report_date'
        )


class ProdOrderMaterListFilter(ProdOrderStaffListFilter):
    show_mater_state_3 = MaterStateNot3Filter()


class ProdOrderMaterList(ListAPIView):
    """Получение перечня всех заказов, их позиций и материалов в них"""
    serializer_class = ProdOrderMaterSerializerList
    filterset_class  = ProdOrderMaterListFilter  # Особые настройки фильтрации
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
            'billet_desc',
            'child__design_mater__child__code',
            'child__partobject__surface',
            'comment'
        ).annotate(
            ship_quantity=Coalesce(Subquery(ship_quantity), 0.0),
            not_supplied=F('quantity') - F('ship_quantity')
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


class WorkerTaskListFilter(django_filters.FilterSet):
    """Особые фильтры для списка заказов в работе"""
    min_date = django_filters.DateFilter(field_name="prod_order_link__parent__prodorder__order_date", lookup_expr='gte')
    max_date = django_filters.DateFilter(field_name="prod_order_link__parent__prodorder__order_date", lookup_expr='lte')
    equal_date = DateEqualFilter(field_name="prod_order_link__parent__prodorder__order_date")
    ordermaker = EqualFilter(field_name="prod_order_link__parent__prodorder__order_maker")
    material = EqualFilter(field_name="prod_order_link__child__design_mater__child")
    states = django_filters.BaseInFilter(field_name='prod_order_link__parent__prodorder__state', lookup_expr='in')
    place = PlaceFilter(field_name='prod_order_link__child__pk')
    operation = OperationFilter(field_name='prod_order_link__child__pk')

    class Meta:
        fields = ['ordermaker', 'equal_date', 'min_date', 'max_date', 'states', 'place', 'operation', 'material']


class WorkerTaskList(ListAPIView):
    """Получение перечня всех задач исполнителя"""
    serializer_class = WorkerTaskSerializerList
    name = 'worker-task-list'
    filterset_class  = WorkerTaskListFilter  # Особые настройки фильтрации
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    def get_queryset(self):
        """Список обязательно фильтруется по исполнителю"""
        # Профиль определяем на основе сессии или передаем принудительно (для отладки)
        worker = self.request.GET.get('worker', get_user_profile(self.request.session))
        # Агрегация всех отчетов по данной позиции
        done_quantity = ProdOrderLinkWorker.objects.filter(
            tp_row=OuterRef('tp_row'), prod_order_link=OuterRef('prod_order_link'),
            worker_reports__dlt_sess=0
        ).order_by().annotate(done_quantity=Func(F('worker_reports__quantity'), function='SUM')).values(
            'done_quantity')
        a = ProdOrderLinkWorker.objects.filter(
            worker=worker
        ).annotate(
            done_quantity=Subquery(done_quantity),
            prog_states=FilteredRelation(
                'prod_order_link__prodorder_link_tprows',
                condition=Q(prod_order_link__prodorder_link_tprows__tp_row=F('tp_row'))
            )
        ).values(
            'pk',
            'prod_order_link__id',
            'prod_order_link__parent__code',
            'prod_order_link__parent__prodorder__order_date',
            'prod_order_link__child__code',
            'prod_order_link__child__type_key',
            'prod_order_link__child__partobject__part_type',
            'prod_order_link__child__partobject__title',
            'prod_order_link__child__pk',
            'prod_order_link__quantity',
            'tp_row__id',
            'tp_row__operation__operation_name',
            'tp_row__route_point__order_num',
            'tp_row__order_num',
            'quantity',
            'done_quantity',
            'prog_states__prog_state__value_class'
        ).exclude(
            link_state_id=3  # Выполненные задания
        ).order_by(
            'prod_order_link__parent__code',
            'prod_order_link__child__code',
            'tp_row__route_point__order_num',
            'tp_row__order_num'
        )
        # print(a.query)
        return a

    # Поля поиска
    search_fields = (
        'prod_order_link__parent__code',
        'prod_order_link__child__code',
        'prod_order_link__child__partobject__title'
    )
