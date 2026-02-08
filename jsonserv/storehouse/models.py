from django.db import models
from jsonserv.core.models import (Entity, PeriodTrackingMixin)  # Базовые модели


class Store(PeriodTrackingMixin):  # Хранение
    store = models.ForeignKey(to='Entity', related_name='stored_objects', on_delete=models.CASCADE,
                              blank=False, null=False, verbose_name='Ссылка на склад')
    pos_entity = models.ForeignKey(to='Entity', related_name='parent_objects', on_delete=models.CASCADE,
                              blank=False, null=False, verbose_name='Ссылка на хранящуюся позицию')
    for_order = models.ForeignKey(to='Entity', related_name='store_objects', on_delete=models.CASCADE,
                              blank=True, null=True, verbose_name='Ссылка на заказ')
    quantity = models.FloatField(null=True, blank=True, verbose_name='Хранящееся количество')
    comment = models.TextField(blank=True, null=True, verbose_name='Примечание')
    delta = models.FloatField(null=True, blank=True, verbose_name='Изменение количества')

    def __str__(self):
        return self.pos_entity + ' хранится на ' + self.store
