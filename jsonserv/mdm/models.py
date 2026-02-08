from django.db import models

from jsonserv.core.models import Classification, Entity, HistoryTrackingMixin, PropertyType


# Объекты на выверке
class RawRow(HistoryTrackingMixin):
    code = models.CharField(max_length=255, null=False, blank=False, verbose_name='Обозначение')
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name='Наименование')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    external_key = models.CharField(max_length=255, null=True, blank=True, db_index=True, verbose_name='Внешний ключ')
    group = models.ForeignKey(Classification, related_name='group_raw_rows', on_delete=models.SET_DEFAULT,
                              default=None, blank=True, null=True, verbose_name='Классификационная группа')
    properties = models.JSONField(null=True, blank=True, verbose_name='Все свойства')
    entity = models.ForeignKey(Entity, related_name='related_raw_rows', on_delete=models.SET_DEFAULT,
                               default=None, blank=True, null=True, verbose_name='Ссылка на экземпляр сущности')

    # is_master_row = models.BooleanField(default=False, blank=False, verbose_name='Признак мастер-строки')

    @staticmethod
    def get_or_create_item(prop_dict):
        return RawRow.objects.get_or_create(external_key=prop_dict['external_key'], defaults=prop_dict)

    class Meta:
        verbose_name = 'Исходный элемент'
        verbose_name_plural = 'Исходные элементы'
        default_permissions = ()
        permissions = [('change_rawrow', 'Объект на выверке. Редактирование'),
                       ('view_rawrow', 'Объект на выверке. Просмотр')]


# Внешние свойства
class RawProperty(models.Model):
    property_name = models.CharField(max_length=150, unique=True, null=False, verbose_name='Наименование свойства')
    order_num = models.PositiveIntegerField(null=False, default=1, verbose_name='Порядок в списке свойств')
    external_name = models.CharField(max_length=150, null=False, blank=False,
                                     verbose_name='Наименование во внешней системе свойства')
    property_type = models.ForeignKey(PropertyType, null=False, default='T', blank=False, on_delete=models.SET_DEFAULT,
                                      verbose_name='Тип свойства')

    @staticmethod
    def get_or_create_item(prop_dict):
        return RawProperty.objects.get_or_create(external_name=prop_dict['external_name'], defaults=prop_dict)

    @staticmethod
    def get_field_ids():
        """Словарь полей и их id"""
        return dict(
            map(lambda kv: (kv['external_name'], kv['pk']), RawProperty.objects.all().values('pk', 'external_name')))

    @staticmethod
    def get_id_names():
        """Словарь id полей и их названий"""
        return dict(
            map(lambda kv: (kv['pk'], kv['property_name']), RawProperty.objects.all().values('pk', 'property_name')))

    class Meta:
        verbose_name = 'Исходное свойство элемента'
        verbose_name_plural = 'Исходные свойства элементов'
        default_permissions = ()
        permissions = [('change_rawproperty', 'Исходное свойство элемента. Редактирование'),
                       ('view_rawproperty', 'Исходное свойство элемента. Просмотр')]

# Модель Классы

# Модель Заявки
