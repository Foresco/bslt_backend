from django.db import models
from django.core.exceptions import SuspiciousOperation

from jsonserv.core.models import (List, Enterprise, Entity, Link, HistoryTrackingMixin, Place, UserSession)
from jsonserv.pdm.models import Route


class ProdOrderState(List):  # Состояния производственных заказов
    class Meta:
        verbose_name = "Состояние производственного заказа"
        verbose_name_plural = "Состояния производственных заказов"
        default_permissions = ()
        permissions = [('change_prodorderstate', 'Состояние производственного заказа. Редактирование'),
                       ('view_prodorderstate', 'Состояние производственного заказа. Просмотр')]


class SpecAccountState(List):
    """Состояния специального счета"""
    class Meta:
        verbose_name = "Состояние специального счета"
        verbose_name_plural = "Состояния специальных счетов"
        default_permissions = ()


class PaymentState(List):
    """Состояния оплаты"""
    class Meta:
        verbose_name = "Состояние оплаты"
        verbose_name_plural = "Состояния оплат"
        default_permissions = ()


class ProdOrder(Entity):  # Заказ на производство
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name='Наименование')
    state = models.ForeignKey(ProdOrderState, blank=True, null=True, on_delete=models.SET_DEFAULT,
                              default=1, verbose_name='Состояние')
    unit = models.ForeignKey(to='core.MeasureUnit', related_name='prod_measure_unit', on_delete=models.SET_DEFAULT,
                             default=1, blank=True, null=True, verbose_name='Единица измерения')
    weight = models.FloatField(null=True, blank=True, verbose_name='Вес/Масса')
    weight_unit = models.ForeignKey(to='core.MeasureUnit', related_name='prod_weight_unit',
                                    on_delete=models.SET_DEFAULT, default=None, blank=True, null=True,
                                    verbose_name='Единица измерения веса')
    order_maker = models.ForeignKey(Place, related_name='orders_made', on_delete=models.SET_NULL,
                                    blank=True, null=True, verbose_name='Заказчик')
    order_date = models.DateField(blank=True, null=True, verbose_name='Плановая дата отгрузки')
    enterprise = models.ForeignKey(Enterprise, related_name='prod_orders',
                                   on_delete=models.SET_DEFAULT, default=None, blank=True, null=True,
                                   verbose_name='Предприятие, получившее заказ')
    spec_account = models.ForeignKey(SpecAccountState, blank=True, null=True,  default=None,
                                     on_delete=models.SET_DEFAULT,
                                     verbose_name='Специальный счет')
    calc_date = models.DateField(blank=True, null=True, verbose_name='Дата калькуляции')
    payment_state = models.ForeignKey(PaymentState, blank=True, null=True, default=None,
                                     on_delete=models.SET_DEFAULT,
                                     verbose_name='Состояние оплаты')
    milit_test = models.BooleanField(blank=True, null=True, default=False, 
                                     verbose_name='Согласование с военной примекой')
    milit_comment = models.CharField(max_length=100, blank=True, null=True, 
                                     verbose_name='Комментарий к согласованию с ВП')

    def get_caption(self):
        """Формирование понятной надписи для разных целей"""
        a = self.code
        if self.order_maker:
            a = f'{a} от {self.order_maker.code}'
        if self.order_date:
            return f'{a} на {self.order_date.strftime("%d.%m.%Y")}'
        return f'{a} | Заказ на производство'

    def check_before_delete(self):
        # Метод проверки перед удалением
        if Link.get_children_count(self):  # Проверка наличия состава
            raise SuspiciousOperation("Удаление невозможно: у заказа есть есть состав")

    class Meta:
        verbose_name = "Производственный заказ"
        verbose_name_plural = "Производственные заказы"
        default_permissions = ()
        permissions = [('change_prodorder', 'Производственный заказ. Редактирование'),
                       ('view_prodorder', 'Производственный заказ. Просмотр')]


class Shipment(HistoryTrackingMixin):
    """Отгрузки продукции"""
    prod_order_link = models.ForeignKey(to='ProdOrderLink', related_name='prodorder_link_shipments',
                                        on_delete=models.CASCADE, blank=False, null=False,
                                        verbose_name='Позиция производственного заказа')
    shipment_date = models.DateField(blank=True, null=True, verbose_name='Дата отгрузки')
    quantity = models.FloatField(null=True, blank=True, verbose_name='Отгруженное количество')
    comment = models.TextField(blank=True, null=True, verbose_name='Примечание к отгрузке')
    shipper = models.ForeignKey(Place, related_name='place_shipments', on_delete=models.CASCADE,
                                blank=True, null=True, verbose_name='Отгрузившее юридическое лицо')

    def __str__(self):
        return f'{self.prod_order_link} отгружена {self.shipment_date} в количестве {self.quantity}'

    class Meta:
        verbose_name = "Отгрузка позиции заказа"
        verbose_name_plural = "Отгрузки позиций заказа"
        default_permissions = ()
        permissions = [('change_shipment', 'Отгрузка. Редактирование'),
                       ('view_shipment', 'Отгрузка. Просмотр')]


class SupplyState(List):
    """Состояния снабжения"""
    class Meta:
        verbose_name = "Состояние снабжения"
        verbose_name_plural = "Состояния снабжения"
        default_permissions = ()
        # permissions = [('change_supplystate', 'Состояние снабжения. Редактирование'),
        #                ('view_supplystate', 'Состояние снабжения. Просмотр')]


class OrderLinkTpRowState(List):
    """Состояния операции в составе заказа"""
    class Meta:
        verbose_name = "Состояние операции в составе заказа"
        verbose_name_plural = "Состояния операций в составе заказов"
        default_permissions = ()


class ProdOrderLink(Link):
    """Связь Входит в производственный заказ"""
    unit = models.ForeignKey(to='core.MeasureUnit', related_name='prodorder_links_unit', on_delete=models.SET_DEFAULT,
                             default=1, blank=True, null=True, verbose_name='Единица измерения количества')
    route = models.ForeignKey(to='pdm.Route', related_name='prodorder_links_route', on_delete=models.SET_DEFAULT,
                              default=None, blank=True, null=True, verbose_name='Маршрут изготовления')
    mater_state = models.ForeignKey(SupplyState, blank=True, null=True, on_delete=models.SET_DEFAULT,
                                    default=None, related_name='prodorder_links_mater',
                                    verbose_name='Состояние материал')
    tool_state = models.ForeignKey(SupplyState, blank=True, null=True, on_delete=models.SET_DEFAULT,
                                   default=None, related_name='prodorder_links_tool',
                                   verbose_name='Состояние инструмент')
    billet_desc = models.TextField(blank=True, null=True, verbose_name='Описание заготовки')
    price_no_nds = models.FloatField(blank=True, null=True, verbose_name='Цена без НДС')
    design_doc = models.ForeignKey(SupplyState, blank=True, null=True, on_delete=models.SET_DEFAULT,
                                    default=None, related_name='prodorder_links_design_doc',
                                    verbose_name='Конструкторская документация')

    def save(self, *args, **kwargs):
        # Назначение активного маршрута по-умолчанию
        if self.route is None:
            ro = Route.get_active(self.child)
            if ro:
                self.route = ro
        super(ProdOrderLink, self).save(*args, **kwargs)

    def check_before_delete(self):
        # Метод проверки перед удалением
        if self.prodorder_link_workers.count():  # Проверка наличия связей с заданиями рабочим
            raise SuspiciousOperation("Удаление невозможно: у вхождения есть задания исполнителям")
        if self.prodorder_link_shipments.count():  # Проверка наличия отгрузок
            raise SuspiciousOperation("Удаление невозможно: у вхождения есть отгрузки")
        if self.billet_desc:  # Проверка наличия заготовки
            raise SuspiciousOperation("Удаление невозможно: у вхождения есть заготовка")

    def get_route_id(self):
        """Получение идентификатора маршрута"""
        if self.route_id:
            return self.route_id
        else:
            # Пробуем получить маршрут по умолчанию
            routes = Route.objects.filter(subject=self.child, is_active=True)
            if routes:
                return routes[0].pk
        return 0


    def __str__(self):
        return self.child.code + ' нужно изготовить по заказу ' + self.parent.code

    class Meta:
        verbose_name = "Связь Входит в производственный заказ"
        verbose_name_plural = "Связи Входит в производственные заказы"
        default_permissions = ()
        permissions = [('change_prodorderlink', 'Связь Входит в производственный заказ. Редактирование'),
                       ('view_prodorderlink', 'Связь Входит в производственный заказ. Просмотр')]


class LinkWorkerState(List):  # Состояния заданий исполнителям
    class Meta:
        verbose_name = "Состояние заданию исполнителю"
        verbose_name_plural = "Состояния заданий исполнителям"
        default_permissions = ()


class ProdOrderLinkWorker(HistoryTrackingMixin):
    # Связь между позициями заказа и работниками исполнителями
    prod_order_link = models.ForeignKey(to='ProdOrderLink', related_name='prodorder_link_workers',
                                        on_delete=models.CASCADE, blank=False, null=False,
                                        verbose_name='Позиция производственного заказа')
    tp_row = models.ForeignKey(to='pdm.TpRow', related_name='tp_row_workers', on_delete=models.CASCADE,
                               blank=True, null=True, verbose_name='Операция технологического процесса')
    worker = models.ForeignKey(to='core.UserProfile', related_name='worker_prodorder_links', on_delete=models.CASCADE,
                               blank=False, null=False, verbose_name='Работник')
    quantity = models.FloatField(null=True, blank=True, verbose_name='Количество')
    comment = models.TextField(blank=True, null=True, verbose_name='Примечание')
    link_state = models.ForeignKey(LinkWorkerState, blank=False, null=False, on_delete=models.CASCADE, default=1,
                                   verbose_name='Состояние задания')

    def __str__(self):
        return f'{self.prod_order_link} изготавливает {self.worker}'

    class Meta:
        verbose_name = "Связь Изготавливает позицию заказа"
        verbose_name_plural = "Связи Изготавливает позицию заказа"
        default_permissions = ()
        permissions = [('change_prodorderlinkworker', 'Связь Изготавливает позицию заказа. Редактирование'),
                       ('view_prodorderlinkworker', 'Связь Изготавливает позицию заказа. Просмотр')]


class ProdOrderLinkTpRow(HistoryTrackingMixin):
    """Связь между позициями заказа, операциями и их свойствами"""
    prod_order_link = models.ForeignKey(to='ProdOrderLink', related_name='prodorder_link_tprows',
                                        on_delete=models.CASCADE, blank=False, null=False,
                                        verbose_name='Позиция производственного заказа')
    tp_row = models.ForeignKey(to='pdm.TpRow', related_name='tp_row_props', on_delete=models.CASCADE,
                               blank=True, null=True, verbose_name='Операция технологического процесса')
    prog_state = models.ForeignKey(OrderLinkTpRowState, blank=True, null=True, on_delete=models.SET_DEFAULT,
                                   default=None, related_name='prodorder_tprow_links_prog',
                                   verbose_name='Состояние разработки УП для ЧПУ')

    def __str__(self):
        return f'{self.tp_row} в {self.prod_order_link} в состоянии {self.prog_state}'

    class Meta:
        verbose_name = "Значение свойства операции позиций в заказе"
        verbose_name_plural = "Значения свойств операций позиций в заказе"
        default_permissions = ()
        permissions = [('change_prodorderlinktprow', 'Значение свойства операции позиции заказа. Редактирование'),
                       ('view_prodorderlinktprow', 'Значение свойства операции позиции заказа. Просмотр')]


class WorkShift(List):
    """Варианты рабочих смен"""
    class Meta:
        verbose_name = "Рабочая смена"
        verbose_name_plural = "Рабочие смены"
        default_permissions = ()
        permissions = [('change_workshift', 'Рабочая смена. Редактирование'),
                       ('view_workshift', 'Рабочая смена. Просмотр')]


class WorkerShift(HistoryTrackingMixin):
    """Рабочие смены работников"""
    shift_date = models.DateField(blank=True, null=True, verbose_name='Дата работы')
    worker = models.ForeignKey(to='core.UserProfile', related_name='worker_shifts', on_delete=models.CASCADE,
                               blank=False, null=False, verbose_name='Работник смены')
    work_shift = models.ForeignKey(WorkShift, blank=True, null=True, on_delete=models.SET_NULL,
                                   verbose_name='Смена работы')
    ratio = models.FloatField(null=False, default=1, verbose_name="Коэффициент",
                              help_text="Коэффициент трудового участия")

    @staticmethod
    def get_or_create_item(prop_dict):
        return WorkerShift.objects.get_or_create(shift_date=prop_dict['shift_date'],
                                                 worker=prop_dict['worker'],
                                                 work_shift=prop_dict['work_shift'],
                                                 defaults=prop_dict)

    def __str__(self):
        return f'{self.worker} работал {self.shift_date} в {self.work_shift}'

    class Meta:
        ordering = ['shift_date', 'worker', 'work_shift']
        verbose_name = "Рабочая смена работника"
        verbose_name_plural = "Рабочие смены работников"
        default_permissions = ()
        permissions = [('change_workershift', 'Рабочая смена работника. Редактирование'),
                       ('view_workershift', 'Рабочая смена работника. Просмотр')]


class WorkerReportConsist(HistoryTrackingMixin):
    # Состав отчетов о выполненных работах
    task_link = models.ForeignKey(to='ProdOrderLinkWorker', related_name='worker_reports', on_delete=models.CASCADE,
                                  blank=False, null=False,  verbose_name='Задание')
    report_date = models.DateField(blank=True, null=True, verbose_name='Дата выполнения')
    work_shift = models.ForeignKey(WorkShift, blank=True, null=True, on_delete=models.SET_NULL,
                                   verbose_name='Рабочая смена выполнения')
    quantity = models.FloatField(null=False, blank=False, default=0, verbose_name='Количество')
    bad_quantity = models.FloatField(null=True, blank=True, verbose_name='Количество брак')
    work_time = models.FloatField(null=True, blank=True, verbose_name='Затраты труда по времени')
    aux_time = models.FloatField(null=True, blank=True, verbose_name='Время на наладку')
    comment = models.TextField(blank=True, null=True, verbose_name='Примечание')
    worker_shift = models.ForeignKey(WorkerShift, null=True, on_delete=models.SET_NULL,
                                     verbose_name="Рабочая смена задания")

    def save(self, *args, **kwargs):
        """Установка смены рабочего, на которой выполнено задание"""
        if self.report_date:  # Смены рабочего создаются только при наличии даты
            session_id = UserSession.objects.get(pk=self.edt_sess) if self.edt_sess else self.crtd_sess
            worker_shift, result = WorkerShift.get_or_create_item(dict(shift_date=self.report_date,
                                                                  worker=self.task_link.worker,
                                                                  work_shift=self.work_shift,
                                                                  crtd_sess=session_id))
            self.worker_shift = worker_shift
        else:
            self.worker_shift = None  # Иначе смену убираем
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.task_link} сделал {self.quantity} {self.report_date}'

    class Meta:
        ordering = ['report_date']
        verbose_name = "Изготовленная позиция заказа"
        verbose_name_plural = "Изготовленные позиции заказа"
        default_permissions = ()
        permissions = [('change_workerreportconsist', 'Изготовленная позиция заказа. Редактирование'),
                       ('view_workerreportconsist', 'Изготовленная позиция заказа. Просмотр')]
