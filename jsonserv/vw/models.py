from django.db import models
from jsonserv.pdm.models import PartObject


class StaffTree(models.Model):
    """Модель для отображения дерева состава"""
    parent = models.ForeignKey(PartObject, related_name='tree_child_objects', on_delete=models.CASCADE,
                               blank=False, null=False, verbose_name='Ссылка на родителя')
    child = models.ForeignKey(PartObject, related_name='tree_parent_objects', on_delete=models.CASCADE,
                              blank=False, null=False, verbose_name='Ссылка на потомка')
    part_type_id = models.CharField(max_length=20, null=False, verbose_name='Имя типа')
    code = models.CharField(max_length=200, null=False, blank=False, verbose_name='Обозначение')
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name='Наименование')
    quantity = models.FloatField(null=True, blank=True, verbose_name='Количество')
    position = models.PositiveIntegerField(null=True, blank=True, verbose_name='Позиция')
    format_string = models.TextField(null=True, blank=True, verbose_name='Формат')
    weight = models.FloatField(null=True, blank=True, verbose_name='Вес/Масса')
    designer = models.CharField(max_length=100, null=True, blank=True, verbose_name='Фамилия И.О. разработчика')
    des_state = models.CharField(max_length=100, null=True, blank=True, default='', verbose_name='Состояние')
    material = models.CharField(max_length=200, null=True, blank=True, verbose_name='Материал')
    notice = models.CharField(max_length=200, null=True, blank=True, verbose_name='Номер извещения')
    has_staff = models.BooleanField(null=False, verbose_name='Признак наличия состава')
    # files = models.TextField(null=True, blank=True, verbose_name='Файлы')
    can_has_staff = models.BooleanField(null=False, verbose_name='Признак возможности наличия состава')
    label = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Метка')
    has_arcdocs = models.BooleanField(null=False, verbose_name='Признак наличия архивных документов')
    ratio = models.FloatField(null=True, blank=True, verbose_name='Коэффициент')
    to_replace = models.TextField(blank=True, null=True, verbose_name='Заменяемые позиции')
    outdated = models.BooleanField(null=False, verbose_name='Признак изменения исходной версии')

    class Meta:
        managed = False
        db_table = 'vw_staff_tree'
        default_permissions = ()


class StaffRoot(models.Model):
    """Модель для отображения корня дерева состава"""
    # parent = models.ForeignKey(PartObject, related_name='root_objects', on_delete=models.CASCADE,
    #                            blank=False, null=False, verbose_name='Ссылка на родителя')
    child = models.ForeignKey(PartObject, related_name='root_parent_objects', on_delete=models.CASCADE,
                              blank=False, null=False, verbose_name='Ссылка на потомка')
    part_type_id = models.CharField(max_length=20, null=False, verbose_name='Имя типа')
    code = models.CharField(max_length=200, null=False, blank=False, verbose_name='Обозначение')
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name='Наименование')
    quantity = models.FloatField(null=True, blank=True, verbose_name='Количество')
    position = models.PositiveIntegerField(null=True, blank=True, verbose_name='Позиция')
    format_string = models.TextField(null=True, blank=True, verbose_name='Формат')
    weight = models.FloatField(null=True, blank=True, verbose_name='Вес/Масса')
    designer = models.CharField(max_length=100, null=True, blank=True, verbose_name='Фамилия И.О. разработчика')
    des_state = models.CharField(max_length=100, null=True, blank=True, default='', verbose_name='Состояние')
    material = models.CharField(max_length=200, null=True, blank=True, verbose_name='Материал')
    notice = models.CharField(max_length=200, null=True, blank=True, verbose_name='Номер извещения')
    has_staff = models.BooleanField(null=False, verbose_name='Признак наличия состава')
    # files = models.TextField(null=True, blank=True, verbose_name='Файлы')
    can_has_staff = models.BooleanField(null=False, verbose_name='Признак возможности наличия состава')
    label = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='Метка')
    has_arcdocs = models.BooleanField(null=False, verbose_name='Признак наличия архивных документов')
    ratio = models.FloatField(null=True, blank=True, verbose_name='Коэффициент')
    to_replace = models.TextField(blank=True, null=True, verbose_name='Заменяемые позиции')
    outdated = models.BooleanField(null=False, verbose_name='Признак изменения исходной версии')

    class Meta:
        managed = False
        db_table = 'vw_root_tree'
        default_permissions = ()
