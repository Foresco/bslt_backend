from django.db import models
# Базовые модели
from jsonserv.core.models import MeasureUnit, HistoryTrackingMixin, PeriodTrackingMixin, List
from jsonserv.pdm.models import PartObject, NormUnit
from jsonserv.docarchive.models import DocumentVersion


class WeightNormType(List):
    """Виды значений норм"""
    class Meta:
        verbose_name = "Вид нормы драгоценного металла"
        verbose_name_plural = "Виды норм драгоценных металлов"
        default_permissions = ()
        permissions = [('change_weightnormtype', 'Вид нормы драгоценного металла. Редактирование'),
                       ('view_weightnormtype', 'Вид нормы драгоценного металла. Просмотр')]


class WeightNormSet(HistoryTrackingMixin):
    """Установки нормы содержания драгоценных металлов"""
    entity = models.ForeignKey(PartObject, null=False, on_delete=models.CASCADE, related_name='treasures',
                               verbose_name="Объект")
    norm_document = models.ForeignKey(DocumentVersion, null=True, on_delete=models.SET_NULL,
                                      verbose_name='Документ нормирования')
    material = models.ForeignKey(PartObject, null=False, on_delete=models.CASCADE, related_name='treasure_norms',
                                 verbose_name="Драгоценный материал")
    comment = models.CharField(max_length=100, null=True, blank=True, verbose_name='Примечание')

    def __str__(self):
        return f'{self.entity} содержит {self.material} по документу {self.norm_document}'

    @staticmethod
    def get_or_create_item(prop_dict):
        return WeightNormSet.objects.get_or_create(entity=prop_dict['entity'],
                                                   material=prop_dict['material'],
                                                   norm_document=prop_dict['norm_document'],
                                                   defaults=prop_dict)

    class Meta:
        verbose_name = "Установка весов драгоценных металлов"
        verbose_name_plural = "Установки весов драгоценных металлов"
        default_permissions = ()
        permissions = [('change_weightnormset', 'Установка весов драгоценных металлов. Редактирование'),
                       ('view_weightnormset', 'Установка весов драгоценных металлов. Просмотр')]


class WeightNorm(HistoryTrackingMixin, PeriodTrackingMixin):
    """Установленные нормы содержания драгоценных металлов"""
    norm_set = models.ForeignKey(WeightNormSet, null=False, on_delete=models.CASCADE, verbose_name='Установка нормы')
    norm_type = models.ForeignKey(WeightNormType, null=False, on_delete=models.CASCADE, verbose_name='Вид нормы')
    norm = models.FloatField(null=True, verbose_name='Значение нормы')
    norm_unit = models.ForeignKey(NormUnit, null=True, on_delete=models.SET_NULL, verbose_name='Единица нормирования')
    unit = models.ForeignKey(MeasureUnit, null=True, on_delete=models.SET_NULL, verbose_name='Единица измерения нормы')
    is_total = models.BooleanField(null=False, default=False, verbose_name='Признак сводных норм')

    def __str__(self):
        return f'{self.norm_set} {self.norm_type} = {self.norm}'

    @staticmethod
    def get_or_create_item(prop_dict):
        return WeightNorm.objects.get_or_create(norm_set=prop_dict['norm_set'],
                                                norm_type=prop_dict['norm_type'],
                                                is_total=prop_dict['is_total'],
                                                defaults=prop_dict)

    class Meta:
        verbose_name = "Вес драгоценного металла"
        verbose_name_plural = "Веса драгоценных металлов"
        default_permissions = ()
        permissions = [('change_weightnorm', 'Вес драгоценного металла. Редактирование'),
                       ('view_weightnorm', 'Вес драгоценного металла. Просмотр')]
