from django.db import models
from django.core.exceptions import SuspiciousOperation

from jsonserv.core.models import (Entity, HistoryTrackingMixin, Link, List, MeasureUnit, PeriodTrackingMixin, Place)
from jsonserv.manufacture.models import ProdOrderLink


class PriceType(List):
    """Типы цен"""
    class Meta:
        verbose_name = "Тип цены"
        verbose_name_plural = "Типы цен"
        default_permissions = ()
        # permissions = [('change_pricetype', 'Тип цены. Редактирование'),
                       # ('view_pricetype', 'Тип цены. Просмотр')]


class Price(HistoryTrackingMixin, PeriodTrackingMixin):  # Поставщики и цены
    # Цена устанавливается на период, новая цена оканчивает действие старой (для отслеживания ценовой истории)
    supplier = models.ForeignKey(Place, related_name='supplied_objects', on_delete=models.CASCADE,
                                 blank=False, null=False, verbose_name='Поставщик')
    supplied_entity = models.ForeignKey(Entity, related_name='suppliers', on_delete=models.CASCADE, blank=False,
                                        null=False, verbose_name='Поставляемая позиция')
    price_type = models.ForeignKey(PriceType, related_name='price_type_prices', on_delete=models.SET_NULL, blank=True,
                                   null=True, verbose_name='Тип цены')                                    
    for_order = models.ForeignKey(Entity, related_name='store_objects', on_delete=models.CASCADE,
                                  blank=True, null=True, verbose_name='Заказ')
    price = models.FloatField(null=True, blank=True, verbose_name='Цена поставки')
    price_unit = models.ForeignKey(MeasureUnit, null=True, on_delete=models.SET_NULL, related_name='prices',
                                   verbose_name='Единица измерения цены')
    quantity = models.FloatField(default=1, null=True, blank=True, verbose_name='Поставляемое за цену количество')
    quantity_unit = models.ForeignKey(MeasureUnit, null=True, on_delete=models.SET_NULL,
                                      related_name='supplied_quantities', verbose_name='Единица измерения количества')
    supply_date = models.DateField(null=True, blank=True, verbose_name='Предполагаемая дата поставки')
    is_active = models.BooleanField(default=True, null=False, verbose_name='Использовать при расчетах')
    article = models.CharField(max_length=50, null=True, verbose_name='Артикул')
    doc = models.CharField(max_length=40, null=True, verbose_name='Документ на поставку')
    comment = models.TextField(blank=True, null=True, verbose_name='Примечание')

    def __str__(self):
        return f'{self.supplied_entity} поставляется {self.supplier}'

    @staticmethod
    def get_or_create_item(prop_dict):
        return Price.objects.get_or_create(supplier=prop_dict['supplier'], supplied_entity=prop_dict['supplied_entity'],
                                           defaults=prop_dict)

    def save(self, *args, **kwargs):
        """ Добавление ЕИ по умолчанию"""
        if not kwargs.get('price_unit', None):  # Если не передана единица измерения
            ei = MeasureUnit.objects.get(short_name="руб.")
            setattr(self, 'price_unit', ei)  # Указание рублей ка единицы измерения
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Поставка поставщика"
        verbose_name_plural = "Поставки поставщиков"
        default_permissions = ()
        permissions = [('change_price', 'Поставка поставщика. Редактирование'),
                       ('view_price', 'Поставка поставщика. Просмотр')]


class SupplyOrder(Entity):
    """Заказ на поставку материалов и комплектующих"""
    supplier = models.ForeignKey(Place, related_name='ordered_objects', on_delete=models.CASCADE,
                                 blank=False, null=False, verbose_name='Поставщик')
    order_date = models.DateField(null=True, blank=True, verbose_name='Дата заказа')
    amount = models.FloatField(null=True, blank=True, verbose_name='Сумма заказа')

    def check_before_delete(self):
        """Проверка перед удалением, в потомках может быть уточнен"""
        if self.ordered_positions.count():  # Проверка наличия позиций в составе
            raise SuspiciousOperation("Удаление невозможно: у заказа есть позиции")

    class Meta:
        verbose_name = "Заказ на поставку"
        verbose_name_plural = "Заказы на поставку"
        default_permissions = ()
        permissions = [('change_supplyorder', 'Заказ на поставку. Редактирование'),
                       ('view_supplyorder', 'Заказ на поставку. Просмотр')]


class SupplyOrderStaff(Link):
    """Заказанные материалы и комплектующие"""

    class Meta:
        verbose_name = "Состав заказа на поставку"
        verbose_name_plural = "Составы заказов на поставку"
        default_permissions = ()
        permissions = [('change_supplyorderstaff', 'Состав заказа на поставку. Редактирование'),
                       ('view_supplyorderstaff', 'Состав заказа на поставку. Просмотр')]


class OrderProdPosition(HistoryTrackingMixin):
    """Производственные позиции в заказах на поставку"""
    supply_order = models.ForeignKey(SupplyOrder, null=False, on_delete=models.CASCADE,
                                     related_name='ordered_positions', verbose_name='Заказ на поставку')
    prod_order_link = models.ForeignKey(ProdOrderLink, null=False, on_delete=models.CASCADE,
                                        related_name='in_supply_orders', verbose_name='Позиция заказа на производство')


    class Meta:
        verbose_name = "Производственная позиция в заказе"
        verbose_name_plural = "Производственные позиции в заказах"
        default_permissions = ()
        permissions = [('change_orderprodposition', 'Производственная позиция в заказе. Редактирование'),
                       ('view_orderprodposition', 'Производственная позиция в заказе. Просмотр')]
