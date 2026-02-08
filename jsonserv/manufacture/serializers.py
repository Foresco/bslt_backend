from django.db.models import F, Func, OuterRef, Subquery
from django.db.models.functions import Coalesce
from rest_framework import serializers
from jsonserv.core.serializers import (EnterpriseRefSerializer, EntityRefSerializer, EntitySerializer,
                                       UserProfileSerializerDetailed)
from jsonserv.pdm.serializers import TitleField
from jsonserv.manufacture.common import ship_quantity
from jsonserv.supply.serializers import OrderPosMaterSuppliersList

# Классы, подлежащие сериализации
from jsonserv.pdm.models import Route, TpRow
from jsonserv.manufacture.models import (ProdOrder, ProdOrderLink, ProdOrderLinkTpRow, ProdOrderLinkWorker,
                                         Shipment, WorkerReportConsist, WorkerShift)


class ObjectOperationSerializerList(serializers.Serializer):
    """Сериализатор описания операций производства"""
    pk = serializers.IntegerField(source='point_tp_rows__pk')  # Идентификатор строки техпроцесса
    place_code = serializers.CharField(source='place__code')
    operation_name = serializers.CharField(source='point_tp_rows__operation__operation_name')
    route_point_order_num = serializers.IntegerField(source='order_num')
    tp_row_order_num = serializers.IntegerField(source='point_tp_rows__order_num')
    done_quantity = serializers.FloatField()
    # subject = serializers.IntegerField()


class ProdOrderPosOperationSerializerList(ObjectOperationSerializerList):
    """Сериализатор описания операций позиции производственного заказа"""
    set_quantity = serializers.FloatField()


class ProdOrderPosReportSerializerList(serializers.Serializer):
    """Сериализатор описания отчетов операций производства"""
    pk = serializers.IntegerField(source='worker_reports__pk')
    place_code = serializers.CharField(source='tp_row__route_point__place__code')
    operation_name = serializers.CharField(source='tp_row__operation__operation_name')
    route_point_order_num = serializers.IntegerField(source='tp_row__route_point__order_num')
    tp_row_order_num = serializers.IntegerField(source='tp_row__order_num')
    worker_name = serializers.CharField(source='worker__user_name')
    report_date = serializers.DateField(source='worker_reports__report_date', format='%d.%m.%Y')
    done_quantity = serializers.FloatField(source='worker_reports__quantity')
    bad_quantity = serializers.FloatField(source='worker_reports__bad_quantity')
    comment = serializers.CharField(source='worker_reports__comment')
    shift_num = serializers.IntegerField(source='worker_reports__work_shift__order_num')


class ProdOrderSerializerDetailed(serializers.ModelSerializer):
    """Сериализатор полного описания производственного заказа для отображения"""
    group = EntityRefSerializer(read_only=True)
    order_maker = EntityRefSerializer(read_only=True)
    enterprise = EnterpriseRefSerializer(read_only=True)

    class Meta:
        model = ProdOrder
        fields = (
            'pk',
            'code',
            'description',
            'group',
            'order_maker',
            'order_date',
            'state',
            'enterprise',
            'spec_account'
        )


class ProdOrderSerializerList(serializers.ModelSerializer):
    order_maker = serializers.SlugRelatedField(read_only=True, slug_field='code')
    order_date = serializers.DateField(format="%d.%m.%Y")
    state = serializers.SlugRelatedField(read_only=True, slug_field='list_value')

    class Meta:
        model = ProdOrder
        fields = (
            'pk',
            'code',
            'description',
            'order_maker',
            'order_date',
            'state'
        )


class ProdOrderSerializer(serializers.ModelSerializer):
    """Сериализатор описания производственного заказа для сохранения"""

    class Meta:
        model = ProdOrder
        fields = (
            'pk',
            'code',
            'title',
            'description',
            'group',
            'order_maker',
            'order_date',
            'state',
            'enterprise',
            'spec_account',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )

    def get_code(self, obj):
        return getattr(obj, 'code', '')  # Необходимо для обхода ограничения по заполненности

class RoutesListField(serializers.Field):
    """Отображение списка маршрутов объекта"""

    def to_representation(self, value):
        # Классное решение!
        rts = Route.objects.filter(
            subject=value
        ).values('pk', 'route_name')
        if rts:
            return list(map(lambda x: dict(pk=x['pk'], value=x['route_name']), rts))
        return


class ProdOrderLinkSerializerList(serializers.Serializer):
    """Сериализатор описания объектов состава производственного заказа"""
    pk = serializers.IntegerField(read_only=True)  # Идентификатор строки задания
    child = EntitySerializer()
    title = TitleField(source='child_id')
    quantity = serializers.FloatField()  # Количество в задании
    done_quantity = serializers.FloatField()
    ship_quantity = serializers.FloatField()
    route = serializers.IntegerField(source='route_id')
    routes_list = RoutesListField(source='child_id')


class ProdOrderLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProdOrderLink
        fields = (
            'pk',
            'parent',
            'child',
            'quantity',
            'route',
            'comment',
            'mater_state',
            'tool_state',
            'billet_desc',
            'price_no_nds',
            'design_doc',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class ProdOrderLinkTpRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProdOrderLinkTpRow
        fields = (
            'pk',
            'prod_order_link',
            'tp_row',
            'prog_state',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class ProdOrderLinkWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProdOrderLinkWorker
        fields = (
            'pk',
            'prod_order_link',
            'tp_row',
            'worker',
            'quantity',
            'comment',
            'link_state',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class ProdOrderLinkWorkerSerializerList(serializers.ModelSerializer):
    """Сериализатор для списка исполнителей позиции в заказе"""
    worker = UserProfileSerializerDetailed()

    class Meta:
        model = ProdOrderLinkWorker
        fields = (
            'pk',
            'prod_order_link',
            'worker',
            'quantity',
            'comment',
            # 'edt_sess',
            # 'crtd_sess',
            # 'dlt_sess'
        )


class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = (
            'pk',
            'prod_order_link',
            'shipment_date',
            'quantity',
            'comment',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class ShipmentSerializerList(serializers.ModelSerializer):
    shipment_date = serializers.DateField(format="%d.%m.%Y")

    class Meta:
        model = ProdOrderLinkWorker
        fields = (
            'pk',
            'shipment_date',
            'quantity',
            'comment',
        )


class WorkerReportConsistSerializer(serializers.ModelSerializer):
    """Сериализатор для строки отчета исполнителя"""

    class Meta:
        model = WorkerReportConsist
        fields = (
            'pk',
            'task_link',
            'work_shift',
            'report_date',
            'quantity',
            'bad_quantity',
            'work_time',
            'aux_time',
            'comment',
            'crtd_sess',
            'edt_sess',
            'dlt_sess'
        )


class WorkerReportConsistSerializerList(serializers.ModelSerializer):
    """Сериализатор для строки отчета исполнителя"""
    report_date = serializers.DateField(format="%d.%m.%Y")

    class Meta:
        model = WorkerReportConsist
        fields = (
            'pk',
            'report_date',
            'quantity',
            'bad_quantity',
            'work_time',
            'aux_time',
            'comment',
        )


class ProgStateClass(serializers.Field):
    """Отображение класса состояния управляющей программы"""

    def to_representation(self, value):
        a = ProdOrderLinkTpRow.objects.filter(
            prod_order_link=value['pk'],
            tp_row=value['route__route_points__point_tp_rows__pk']
        ).first()
        return a.prog_state.value_class if a and a.prog_state else None


class PositionsOperationSerializerList(serializers.Serializer):
    pk = serializers.CharField(source='route__route_points__point_tp_rows__pk')
    link_id = serializers.IntegerField(source='pk')  # Идентификатор связи в заказе
    code = serializers.CharField(source='parent__code')  # Номер заказа
    parent_id = serializers.IntegerField(source='parent__pk')  # Идентификатор заказа
    parent_state = serializers.CharField(source='parent__prodorder__state__list_value')  # Состояние заказа
    order_date = serializers.DateField(source='parent__prodorder__order_date', format='%d.%m.%Y')  # Дата заказа
    type_key = serializers.CharField(source='child__type_key')  # Тип изготавливаемой позиции
    part_type = serializers.CharField(source='child__partobject__part_type')  # Подтип изготавливаемой позиции
    child_id = serializers.IntegerField(source='child__pk')  # Изготавливаемая позиция
    child = serializers.CharField(source='child__code')  # Изготавливаемая позиция
    title = serializers.CharField(source='child__partobject__title')  # Наименование
    quantity = serializers.FloatField()  # Количество в заказе
    place_code = serializers.CharField(source='route__route_points__place__code')
    operation_name = serializers.CharField(
        source='route__route_points__point_tp_rows__operation__operation_name')
    route_point_order_num = serializers.IntegerField(source='route__route_points__order_num')
    tp_row_order_num = serializers.IntegerField(
        source='route__route_points__point_tp_rows__order_num')
    done_quantity = serializers.FloatField()
    bad_quantity = serializers.FloatField()
    ship_quantity = serializers.FloatField()
    prog_state = ProgStateClass(source='*')


class PosOperationSerializer(serializers.Serializer):
    """Сериализатор операции у позиции"""
    pk = serializers.IntegerField()
    operation_name = serializers.CharField(source='operation__operation_name')
    place_code = serializers.CharField(source='route_point__place__code')
    task_quantity = serializers.IntegerField()
    done_quantity = serializers.FloatField()
    prog_state = serializers.IntegerField()


class PosOperationsList(serializers.Field):
    """Отображение списка операций позиции в заказе"""

    def to_representation(self, value):
        # Подсчет всех заданий по данной позиции
        task_quantity = ProdOrderLinkWorker.objects.filter(
            tp_row=OuterRef('pk'), prod_order_link=value['pk'], dlt_sess=0
        ).order_by().annotate(task_quantity=Func(F('pk'), function='COUNT')).values(
            'task_quantity')
        # Подсчет выполненного количества
        done_quantity = ProdOrderLinkWorker.objects.filter(
            tp_row=OuterRef('pk'), prod_order_link=value['pk'], dlt_sess=0,
            worker_reports__dlt_sess=0
        ).order_by().annotate(done_quantity=Func(F('worker_reports__quantity'), function='SUM')).values(
            'done_quantity')
        # Состояние подготовки операции
        prog_state = ProdOrderLinkTpRow.objects.filter(
            prod_order_link=value['pk'], tp_row=OuterRef('pk')
        ).order_by('id').values('prog_state')
        opers = TpRow.objects.filter(
            route_id=value['route_id'],
            route__dlt_sess=0,
            route_point__dlt_sess=0,
            dlt_sess=0
        ).values(
            'pk',
            'operation__operation_name',
            'route_point__place__code'
        ).annotate(
            task_quantity=Subquery(task_quantity),
            done_quantity=Subquery(done_quantity),
            prog_state=Subquery(prog_state)
        ).order_by(
            'route_point__order_num',
            'order_num',
            'task_quantity',
            'done_quantity'
        )
        if opers:
            serializer = PosOperationSerializer(opers, many=True)
            return serializer.data
        return None


class ProdOrderPosSerializerList(serializers.Serializer):
    pk = serializers.IntegerField(read_only=True)  # Идентификатор связи
    type_key = serializers.CharField(source='child__type_key')  # Тип изготавливаемой позиции
    part_type = serializers.CharField(source='child__partobject__part_type')  # Подтип изготавливаемой позиции
    child_id = serializers.IntegerField(source='child__id')  # Изготавливаемая позиция
    child = serializers.CharField(source='child__code')  # Изготавливаемая позиция
    title = serializers.CharField(source='child__partobject__title')  # Наименование
    quantity = serializers.FloatField()  # Количество в задании
    price_no_nds = serializers.FloatField()  # Цена без НДС
    mater_state = serializers.CharField(source='mater_state__value_class')  # Метка состояния поставки материала
    design_doc = serializers.CharField(source='design_doc__value_class')  # Метка состояния КД
    supply_orders = OrderPosMaterSuppliersList(source='pk')
    ship_quantity = serializers.FloatField()


class ProdOrderPosList(serializers.Field):
    """Отображение всех позиций в заказе"""

    def to_representation(self, value):
        """Список фильтруется по позиции состава"""
        positions = ProdOrderLink.objects.filter(
            parent=value,
        ).values(
            'pk',
            'child__id',
            'child__code',
            'child__type_key',
            'child__partobject__part_type',
            'child__partobject__title',
            'quantity',
            'mater_state__value_class',
            'price_no_nds',
            'design_doc__value_class'
            
        ).annotate(
            ship_quantity=Coalesce(Subquery(ship_quantity), 0.0)
        ).order_by(
            'child__code'
        )

        if positions:
            serializer = ProdOrderPosSerializerList(positions, many=True)
            return serializer.data
        return None
    

class ProdOrderContractSerializerList(serializers.Serializer):
    pk = serializers.IntegerField(read_only=True)  # Идентификатор заказа
    code = serializers.CharField()  # Номер заказа
    type_key = serializers.CharField()  # Тип заказа
    order_maker = serializers.CharField(source='order_maker__code')  # Заказчик
    order_state = serializers.CharField(source='state__list_value')  # Состояние заказа
    order_date = serializers.DateField(format='%d.%m.%Y')  # Дата заказа
    calc_date = serializers.DateField(format='%d.%m.%Y')  # Дата калькуляции
    spec_account = serializers.CharField(source='spec_account__list_value')  # Состояние спецсчета
    mater_state = serializers.CharField()  # Метка состояния поставки материала
    design_doc_state = serializers.CharField()  # Метка состояния КД
    payment_state = serializers.CharField(source='payment_state__value_class')  # Состояние оплаты заказа
    milit_test = serializers.BooleanField()
    milit_comment = serializers.CharField()
    shipment_count = serializers.FloatField()
    unshipped_quantity = serializers.FloatField()
    positions = ProdOrderPosList(source='pk')


class ProdOrderInWorkSerializerList(serializers.Serializer):
    pk = serializers.IntegerField(read_only=True)  # Идентификатор связи
    code = serializers.CharField(source='parent__code')  # Номер заказа
    parent_id = serializers.IntegerField(source='parent__pk')  # Идентификатор заказа
    parent_type_key = serializers.CharField(source='parent__type_key')  # Тип заказа
    parent_state = serializers.CharField(source='parent__prodorder__state__list_value')  # Состояние заказа
    order_date = serializers.DateField(source='parent__prodorder__order_date', format='%d.%m.%Y')  # Дата заказа
    order_maker = serializers.CharField(source='parent__prodorder__order_maker__code')  # Заказчик
    type_key = serializers.CharField(source='child__type_key')  # Тип изготавливаемой позиции
    part_type = serializers.CharField(source='child__partobject__part_type')  # Подтип изготавливаемой позиции
    child_id = serializers.IntegerField(source='child__pk')  # Изготавливаемая позиция
    child = serializers.CharField(source='child__code')  # Изготавливаемая позиция
    title = serializers.CharField(source='child__partobject__title')  # Наименование
    quantity = serializers.FloatField()  # Количество в задании
    mater_state = serializers.CharField(source='mater_state__value_class')  # Метка состояния поставки материала
    tool_state = serializers.CharField(source='tool_state__value_class')  # Метка состояния поставки инструмента
    done_quantity = serializers.FloatField()
    ship_quantity = serializers.FloatField()
    oper_quantity = serializers.FloatField()
    operations = PosOperationsList(source='*')


class ProdOrderMaterSerializerList(serializers.Serializer):
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
    surface = serializers.CharField(source='child__partobject__surface')  # Габарит и поверхность
    billet_desc = serializers.CharField()  # Описание заготовки


class WorkerTaskSerializerList(serializers.Serializer):
    pk = serializers.IntegerField(read_only=True)  # Идентификатор строки задания
    link_id = serializers.IntegerField(source='prod_order_link__id')  # Идентификатор связи из состава
    code = serializers.CharField(source='prod_order_link__parent__code')  # Номер заказа
    order_date = serializers.DateField(source='prod_order_link__parent__prodorder__order_date',
                                       format='%d.%m.%Y')  # Дата заказа
    type_key = serializers.CharField(source='prod_order_link__child__type_key')  # Тип изготавливаемой позиции
    part_type = serializers.CharField(
        source='prod_order_link__child__partobject__part_type')  # Подтип изготавливаемой позиции
    child_id = serializers.IntegerField(source='prod_order_link__child__pk')  # Изготавливаемая позиция
    child = serializers.CharField(source='prod_order_link__child__code')  # Изготавливаемая позиция
    title = serializers.CharField(source='prod_order_link__child__partobject__title')  # Наименование
    staff_quantity = serializers.FloatField(source='prod_order_link__quantity')  # Количество в составе
    operation_id = serializers.CharField(source='tp_row__id')  # Идентификатор строки техпроцесса
    operation_name = serializers.CharField(source='tp_row__operation__operation_name')  # Операция
    tp_row_order_num = serializers.IntegerField(source='tp_row__order_num')  # Порядок следования операции
    route_point_order_num = serializers.IntegerField(
        source='tp_row__route_point__order_num')  # Порядок следования элемента маршрута
    quantity = serializers.FloatField()  # Количество в задании
    done_quantity = serializers.FloatField()
    prog_state = serializers.CharField(
        source='prog_states__prog_state__value_class')  # Метка состояния управляющей программы


class WorkerShiftPosList(serializers.Field):
    """Отображение всех отчетов за смену работника"""

    def to_representation(self, value):
        """Список фильтруется по позиции состава"""
        positions = WorkerReportConsist.objects.filter(
            worker_shift=value,
        ).values(
            'pk',
            'task_link__prod_order_link__pk',
            'task_link__prod_order_link__parent__code',
            'task_link__prod_order_link__child__id',
            'task_link__prod_order_link__child__code',
            'task_link__prod_order_link__child__partobject__title',
            'task_link__tp_row__route_point__place__code',
            'task_link__tp_row__operation__operation_name',
            'task_link__tp_row__route_point__order_num',
            'task_link__tp_row__order_num',
            'aux_time',
            'work_time',
            'quantity',
            'bad_quantity'
        ).order_by(
            'task_link__prod_order_link__child__code',
            'task_link__tp_row__route_point__order_num',
            'task_link__tp_row__order_num'
        )

        if positions:
            serializer = WorkerShiftPosSerializerList(positions, many=True)
            return serializer.data
        return None


class WorkerShiftSerializerList(serializers.Serializer):
    pk = serializers.IntegerField(read_only=True)
    worker = serializers.CharField(source='worker.user_name')
    shift_date = serializers.DateField(format="%d.%m.%Y")
    work_shift = serializers.CharField(source='work_shift.list_value')
    aux_time = serializers.FloatField()
    work_time = serializers.DecimalField(max_digits=5, decimal_places=2)
    ratio = serializers.FloatField()
    positions = WorkerShiftPosList(source='pk')


class WorkerShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerShift
        fields = (
            'pk',
            'ratio',
            'edt_sess',
        )


class WorkerShiftPosSerializerList(serializers.Serializer):
    pk = serializers.IntegerField(read_only=True)
    link_id = serializers.IntegerField(source='task_link__prod_order_link__pk')
    parent_code = serializers.CharField(source='task_link__prod_order_link__parent__code')
    child_id = serializers.IntegerField(source='task_link__prod_order_link__child__id')
    place_code = serializers.CharField(source='task_link__tp_row__route_point__place__code')
    operation_name = serializers.CharField(source='task_link__tp_row__operation__operation_name')
    route_point__order_num = serializers.IntegerField(source='task_link__tp_row__route_point__order_num')
    route_point__order_num = serializers.IntegerField(source='task_link__tp_row__order_num')
    aux_time = serializers.FloatField()
    work_time = serializers.FloatField()
    quantity = serializers.FloatField()
    bad_quantity = serializers.FloatField()
    full_code = serializers.SerializerMethodField()

    def get_full_code(self, obj):
        if obj['task_link__prod_order_link__child__partobject__title']:
            return '{} {}'.format(obj['task_link__prod_order_link__child__code'],
                                  obj['task_link__prod_order_link__child__partobject__title'])
        return obj['task_link__prod_order_link__child__code']
