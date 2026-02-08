# Модели для доступа к данным системы Базальта 1.0
import os.path
from copy import copy
from django.db import models
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from .utils import dims, get_change


def prepare_id(address, id):
    """Формирование уникального идентификатора в виде http-ссылки"""
    return f'{address}.php?id={id}'


def check_lost(obj):
    """Проверка что объект не потерянный"""
    if obj.del_tract_id == 0:
        object_orders = obj.order_child.all()
        if not object_orders.count():
            return True  # Считаем такие объекты потерянными и не выгружаем их связи
    return False


# Менеджер, возвращающий только неудаленные
class NotDeletedRows(models.Manager):
    def get_queryset(self):
        # Не имеющие отметки об удалении
        return super().get_queryset().filter(del_tract_id__isnull=True)


class NotDeletedRows1(models.Manager):
    def get_queryset(self):
        # Не имеющие отметки об удалении и относящиеся к объектам
        return super().get_queryset().filter(del_tract_id__isnull=True, dim_id=1)


class NotDeletedRows5(models.Manager):
    def get_queryset(self):
        # Не имеющие отметки об удалении и относящиеся к файлам
        return super().get_queryset().filter(del_tract_id__isnull=True, dim_id=5)


class NotDeletedRows12(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(del_tract_id__isnull=True, dim_id=12)


class NotDeletedRows13(models.Manager):
    def get_queryset(self):
        # Не имеющие отметки об удалении и относящиеся к извещениям
        return super().get_queryset().filter(del_tract_id__isnull=True, dim_id=13)


class NotDeletedRows29(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(del_tract_id__isnull=True, dim_id=29)


class NotDeletedRows33(models.Manager):
    def get_queryset(self):
        # !!! При тестировании выгружаем 1 документ
        return super().get_queryset().filter(del_tract_id__isnull=True, dim_id=33).filter(object_id=739)


class AllRows33(models.Manager):
    """Вс строки, в том числе удаленные"""
    def get_queryset(self):
        # !!! При тестировании выгружаем 1 документ
        return super().get_queryset().filter(dim_id=33).exclude(object_id=739)


# Менеджер, возвращающий только неудаленные и объекты из заказа
class NotDeletedAndOrderRows(models.Manager):
    def get_queryset(self):
        # Не имеющие отметки об удалении
        return super().get_queryset().filter(Q(del_tract_id__isnull=True) | Q(del_tract_id=0))


# Менеджер, возвращающий только активные неудаленные
class ActiveNotDeleted(models.Manager):
    def get_queryset(self):
        # Не имеющие отметки об удалении
        return super().get_queryset().filter(is_active=1, del_tract_id__isnull=True)


# Предпочтительности
class Preference(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    pref_name = models.CharField(max_length=40)
    pref_level = models.SmallIntegerField()
    pref_colour = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'preferences'
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='PartPreference', )
        node['id'] = prepare_id('preference', self.id)
        node['list_value'] = self.pref_name
        node['order_num'] = self.id
        node['is_default'] = True if self.id == 1 else False
        exp_list.append(node)
        return exp_list


# Источники поступления
class Source(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    source_name = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'sources'
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='PartSource', )
        node['id'] = prepare_id('source', self.id)
        node['list_value'] = self.source_name
        node['order_num'] = self.id
        node['is_default'] = True if self.id == 1 else False
        exp_list.append(node)
        return exp_list


class State(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    state_name = models.CharField(max_length=25)

    class Meta:
        managed = False
        db_table = 'states'
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='PartState', )
        node['id'] = prepare_id('state', self.id)
        node['list_value'] = self.state_name
        node['order_num'] = self.id
        node['is_default'] = True if self.id == 1 else False
        exp_list.append(node)
        return exp_list


# Измеряемые сущности
class Essence(models.Model):
    essence_name = models.CharField(max_length=35)

    class Meta:
        managed = False
        db_table = 'essences'
        default_permissions = ()

    def to_dict(self):
        exp_list = list()
        node = dict(model='Essence', )
        node['essence_name'] = self.essence_name
        node['id'] = prepare_id('essence', self.id)
        exp_list.append(node)
        return exp_list


# Единицы измерения
class Unit(models.Model):
    essence = models.ForeignKey(to='Essence', on_delete=models.CASCADE)
    unit_name = models.CharField(max_length=40)
    short_name = models.CharField(max_length=10)
    unit_code = models.CharField(max_length=3, blank=True, null=True)
    numerator = models.ForeignKey(to='Unit', related_name='numerator_unit', blank=True, null=True,
                                  on_delete=models.CASCADE)
    denominator = models.ForeignKey(to='Unit', related_name='denominator_unit', blank=True, null=True,
                                    on_delete=models.CASCADE)
    separator_char = models.CharField(max_length=1, blank=True, null=True)
    base = models.ForeignKey(to='Unit', related_name='base_unit', blank=True, null=True,
                             on_delete=models.CASCADE)
    ratio = models.FloatField()
    # order_key = models.SmallIntegerField(blank=True, null=True)
    tract_id = models.IntegerField(null=False, blank=False)
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'units'
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        # Выгружаем ссылочные сущности
        exp_list.add_if_not_empty(self.essence)
        # Выгружаем все ссылочные единицы измерения
        exp_list.add_if_not_empty(self.numerator)
        exp_list.add_if_not_empty(self.denominator)
        if self.base_id != 0:  # Ссылки на ноль не выгружаем
            exp_list.add_if_not_empty(self.base)
        # Добавляем свойства самой единицы измерения
        node = dict(model='MeasureUnit', )
        # Свойства - значения
        node['unit_name'] = self.unit_name
        node['short_name'] = self.short_name
        node['unit_code'] = self.unit_code
        node['ratio'] = self.ratio
        # node['order_key'] = self.order_key
        node['separator_char'] = self.separator_char if self.separator_char else ''
        node['id'] = prepare_id('unit', self.id)
        # Свойства - ссылки
        if self.essence is not None:
            node['essence'] = prepare_id('essence', self.essence.id)
        if self.numerator is not None:
            node['numerator'] = prepare_id('unit', self.numerator.id)
        if self.denominator is not None:
            node['denominator'] = prepare_id('unit',self.denominator.id)
        if self.base_id != 0:
            node['base'] = prepare_id('unit', self.base.id)
        exp_list.append(node)
        return exp_list


# Типы объектов
class ObjectType(models.Model):
    type_name = models.CharField(max_length=25)
    div_name = models.CharField(max_length=25)
    doc_key = models.SmallIntegerField()
    form_id = models.IntegerField(blank=True, null=True)
    has_staff = models.SmallIntegerField()
    has_billet = models.SmallIntegerField()
    has_route = models.SmallIntegerField()
    check_names = models.SmallIntegerField()
    check_states = models.SmallIntegerField()
    # generator = models.CharField(max_length=25, blank=True, null=True)
    tract_id = models.IntegerField(null=False, blank=False)
    del_tract_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'object_types'
        default_permissions = ()

    TYPEKEYS = {
        1: 'document',
        2: 'complex',
        3: 'assembly',
        4: 'detail',
        5: 'standart',
        6: 'other',
        7: 'material',
        8: 'complect',
        9: 'sortament',
        10: 'exemplar',
        11: 'order',
        12: 'select',
        13: 'rigging',
        14: 'tool',
        15: 'equipment',
        16: 'plan',
        17: 'device',
        18: 'process',
        19: 'chain',
        20: 'prodspec',
        21: 'stage'
    }

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='PartType', )
        # Свойства - значения
        node['part_type'] = ObjectType.TYPEKEYS[self.id]
        node['type_name'] = self.type_name
        node['div_name'] = self.div_name
        node['order_num'] = self.id
        node['has_staff'] = True if self.has_staff == 1 else False
        node['check_states'] = True if self.check_states == 1 else False
        # node['generator'] = self.generator
        node['id'] = prepare_id('object_type', self.id)
        exp_list.append(node)
        return exp_list


# Объекты
class PartObject(models.Model):
    type = models.ForeignKey(to='ObjectType', on_delete=models.CASCADE)
    object_code = models.CharField(max_length=200)
    auto_code = models.SmallIntegerField()
    object_name = models.CharField(max_length=250, blank=True, null=True)
    doc = models.ForeignKey(to='PartObject', related_name='parent_document', on_delete=models.CASCADE)
    draft_format = models.CharField(max_length=15, blank=True, null=True)
    object_abbr = models.CharField(max_length=45, blank=True, null=True)
    is_top = models.SmallIntegerField()
    nom_code = models.CharField(max_length=15, blank=True, null=True)
    source = models.ForeignKey(to='Source', on_delete=models.DO_NOTHING)
    group = models.ForeignKey(to='ObjectGroup', blank=True, null=True, on_delete=models.DO_NOTHING)
    unit = models.ForeignKey(to='Unit', related_name='measure_unit', blank=True, null=True,
                             on_delete=models.DO_NOTHING)
    weight = models.FloatField(blank=True, null=True)
    w_unit = models.ForeignKey(to='Unit', related_name='weight_unit', blank=True, null=True,
                               on_delete=models.DO_NOTHING)
    pref = models.ForeignKey(to='Preference', blank=True, null=True, on_delete=models.DO_NOTHING)
    picture_id = models.IntegerField(blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    state = models.ForeignKey(to='State', blank=True, null=True, on_delete=models.DO_NOTHING)
    litera = models.CharField(max_length=2, blank=True, null=True)
    surface = models.CharField(max_length=50, blank=True, null=True)
    check_code = models.CharField(max_length=200)
    rating = models.SmallIntegerField()
    tract_id = models.IntegerField(null=False, blank=False)
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedAndOrderRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        ordering = ['id']
        db_table = 'objects'
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        # Для стадий другой вариант
        if self.type.id == 21:
            node = dict(model='Stage', code=self.object_code, id=prepare_id('stage', self.id))
            exp_list.append(node)
            return exp_list

        # Добавляем описание типа Производственное подразделение (он уже должен быть зарегистрирован)
        exp_list.append({'id': 'partobject', 'type_key': 'partobject', 'model': 'EntityType'})
        node = dict(model='PartObject', type_key='partobject')
        # Проверка вхождения объекта в производственный заказ
        if self.del_tract_id == 0:
            object_orders = self.order_child.all()
            if object_orders.count():
                # Если объект входит в заказ
                for i in object_orders:
                    exp_list.add_if_not_empty(i.parent)
                    exp_list.add_if_not_empty(i.source)
                    node['origin'] = prepare_id(ObjectType.TYPEKEYS[i.source.type.id], i.source.id)
                    node['prod_order'] = prepare_id(ObjectType.TYPEKEYS[i.parent.type.id], i.parent.id)
            # else: Пока отключили, потому что были сбои при загрузке (потерянные ссылки)
            #     return None  # Считаем такие объекты потерянными и не выгружаем
        # Свойства - значения
        node['code'] = self.object_code
        node['auto_code'] = True if self.auto_code == 1 else False
        node['description'] = self.remark
        node['title'] = self.object_name
        node['abbr'] = self.object_abbr
        node['is_top'] = True if self.is_top == 1 else False
        node['nom_code'] = self.nom_code
        node['weight'] = self.weight
        node['surface'] = self.surface
        node['part_type'] = prepare_id('object_type', self.type.id)
        node['id'] = prepare_id(ObjectType.TYPEKEYS[self.type.id], self.id)

        exp_list.add_if_not_empty(self.type)
        # Свойства - ссылки
        if hasattr(self, 'doc'):
            exp_list.add_if_not_empty(self.doc)
            node['parent'] = prepare_id(ObjectType.TYPEKEYS[self.doc.type.id], self.doc.id)
        if self.group is not None:
            exp_list.add_if_not_empty(self.group)
            node['group'] = prepare_id('group', self.group.id)
        if self.unit is not None:
            exp_list.add_if_not_empty(self.unit)
            node['unit'] = prepare_id('unit', self.unit.id)
        if self.w_unit is not None:  # hasattr(self, 'w_unit'):
            exp_list.add_if_not_empty(self.w_unit)
            node['weight_unit'] = prepare_id('unit', self.w_unit.id)
        if self.litera:
            # Добавляем описание отдельного элемента списка
            exp_list.append({'id': 'literas.' + self.litera, 'list_value': self.litera, 'model': 'PartLitera'})
            node['litera'] = f'literas.{self.litera}'
        if self.state is not None:
            exp_list.add_if_not_empty(self.state)
            node['state'] = prepare_id('state', self.state.id)
        if hasattr(self, 'source'):
            exp_list.add_if_not_empty(self.source)
            node['source'] = prepare_id('source', self.source.id)
        if self.pref is not None:
            exp_list.add_if_not_empty(self.pref)
            node['preference'] = prepare_id('preference', self.pref.id)

        exp_list.append(node)
        return exp_list


# Дополнительный класс, копия PartObject, предназначенный для выгрузки опеределенных массивов объектов,
# например, материалов или сортаментов
class ObjectToExport(models.Model):
    type = models.ForeignKey(to='ObjectType', on_delete=models.CASCADE)
    object_code = models.CharField(max_length=200)
    auto_code = models.SmallIntegerField()
    object_name = models.CharField(max_length=250, blank=True, null=True)
    doc = models.ForeignKey(to='PartObject', related_name='parent_document_exp', on_delete=models.CASCADE)
    draft_format = models.CharField(max_length=15, blank=True, null=True)
    object_abbr = models.CharField(max_length=45, blank=True, null=True)
    is_top = models.SmallIntegerField()
    nom_code = models.CharField(max_length=15, blank=True, null=True)
    source = models.ForeignKey(to='Source', on_delete=models.DO_NOTHING)
    group = models.ForeignKey(to='ObjectGroup', blank=True, null=True, on_delete=models.DO_NOTHING)
    unit = models.ForeignKey(to='Unit', related_name='measure_unit_exp', blank=True, null=True,
                             on_delete=models.DO_NOTHING)
    weight = models.FloatField(blank=True, null=True)
    w_unit = models.ForeignKey(to='Unit', related_name='weight_unit_exp', blank=True, null=True,
                               on_delete=models.DO_NOTHING)
    pref = models.ForeignKey(to='Preference', blank=True, null=True, on_delete=models.DO_NOTHING)
    picture_id = models.IntegerField(blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    state = models.ForeignKey(to='State', blank=True, null=True, on_delete=models.DO_NOTHING)
    litera = models.CharField(max_length=2, blank=True, null=True)
    surface = models.CharField(max_length=50, blank=True, null=True)
    check_code = models.CharField(max_length=200)
    rating = models.SmallIntegerField()
    tract_id = models.IntegerField(null=False, blank=False)
    del_tract_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'objects_export'
        ordering = ['tract_id', 'id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        # Добавляем описание типа Производственное подразделение (он уже должен быть зарегистрирован)
        exp_list.append({'id': 'partobject', 'type_key': 'partobject', 'model': 'EntityType'})
        node = dict(model='PartObject', type_key='partobject')
        # Проверка вхождения объекта в производственный заказ
        if self.del_tract_id == 0:
            object_orders = self.order_child.all()
            if object_orders.count():
                # Если объект входит в заказ
                for i in object_orders:
                    exp_list.add_if_not_empty(i.parent)
                    exp_list.add_if_not_empty(i.source)
                    node['origin'] = prepare_id(ObjectType.TYPEKEYS[i.source.type.id], i.source.id)
                    node['prod_order'] = prepare_id(ObjectType.TYPEKEYS[i.parent.type.id], i.parent.id)
            else:
                return None  # Считаем такие объекты потерянными и не выгружаем
        # Свойства - значения
        node['code'] = self.object_code
        node['auto_code'] = True if self.auto_code == 1 else False
        node['description'] = self.remark
        node['title'] = self.object_name
        node['abbr'] = self.object_abbr
        node['is_top'] = True if self.is_top == 1 else False
        node['nom_code'] = self.nom_code
        node['weight'] = self.weight
        node['surface'] = self.surface
        node['part_type'] = prepare_id('object_type', self.type.id)
        node['id'] = prepare_id(ObjectType.TYPEKEYS[self.type.id], self.id)

        exp_list.add_if_not_empty(self.type)
        # Свойства - ссылки
        if hasattr(self, 'doc'):
            exp_list.add_if_not_empty(self.doc)
            node['parent'] = prepare_id(ObjectType.TYPEKEYS[self.doc.type.id], self.doc.id)
        if self.group is not None:
            exp_list.add_if_not_empty(self.group)
            node['group'] = prepare_id('group', self.group.id)
        if self.unit is not None:
            exp_list.add_if_not_empty(self.unit)
            node['unit'] = prepare_id('unit', self.unit.id)
        if self.w_unit is not None:  # hasattr(self, 'w_unit'):
            exp_list.add_if_not_empty(self.w_unit)
            node['weight_unit'] = prepare_id('unit', self.w_unit.id)
        if self.litera:
            # Добавляем описание отдельного элемента списка
            exp_list.append({'id': 'literas.' + self.litera, 'list_value': self.litera, 'model': 'PartLitera'})
            node['litera'] = f'literas.{self.litera}'
        if self.state is not None:
            exp_list.add_if_not_empty(self.state)
            node['state'] = prepare_id('state', self.state.id)
        if hasattr(self, 'source'):
            exp_list.add_if_not_empty(self.source)
            node['source'] = prepare_id('source', self.source.id)
        if self.pref is not None:
            exp_list.add_if_not_empty(self.pref)
            node['preference'] = prepare_id('preference', self.pref.id)

        exp_list.append(node)
        return exp_list


# Менеджер с одним файлом на время импорта
class OneFile(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(pk=138115)


class Docs(models.Model):
    dim_id = models.SmallIntegerField()
    object = models.ForeignKey(to=PartObject, on_delete=models.CASCADE)
    doc_code = models.CharField(max_length=100)
    doc_type = models.CharField(max_length=30, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    archive_cell = models.CharField(max_length=50, blank=True, null=True)
    folder = models.ForeignKey(to='Folders', on_delete=models.CASCADE)
    designer = models.ForeignKey(to='SystemUser', blank=True, null=True, on_delete=models.CASCADE)
    design_date = models.DateField(blank=True, null=True)
    version_num = models.SmallIntegerField(blank=True, null=True)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    # objects = OneFile()  # На время тестирования оставляем один файл

    root_folder = r'/mnt/uploaded'

    class Meta:
        abstract = True  # Это абстрактный класс
        managed = False
        # db_table = 'docs'
        # db_table = 'documents_export'
        ordering = ['id']
        default_permissions = ()

    def get_ref(self):
        # Проверка что объект существует и не потерянный
        try:
            # Бывает, что объект уже удален
            so = self.object
        except ObjectDoesNotExist:
            print("There is no object for document.")
            return None
        if check_lost(so):
            return None
        return prepare_id(ObjectType.TYPEKEYS[so.type.id], so.id)

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка

        # Документ
        doc = dict(model='FileDocument')
        doc['doc_code'] = self.doc_code
        # Архив по умолчанию
        exp_list.append({'id': 'archive.1', 'archive_name': 'Основной архив', 'model': 'FileArchive'})
        doc['archive'] = 'archive.1'
        if self.doc_type:
            # Добавляем описание отдельного элемента списка
            exp_list.append({'id': f'dt.{self.doc_type}', 'list_value': self.doc_type, 'model': 'DocumentType'})
            doc['doc_type'] = f'dt.{self.doc_type}'
        doc['id'] = f'documents.{self.id}'
        exp_list.append(doc)

        # Версия документа
        version = dict(model='DocumentVersion')
        version['document'] = f'documents.{self.id}'
        version['description'] = self.description
        version['version_num'] = self.version_num
        version['id'] = f'versions.{self.id}'
        # Проверка ссылки на документ у извещений
        notices = NoticeLinksDoc.objects.filter(object_id=self.id)
        if notices:  # Если ссылка(и) нашлась
            notice = notices[0]
            exp_list.add_if_not_empty(notice.notice) # Добавляем описание извещения
            version['notice'] = prepare_id('notice', notice.notice.id)
            version['change_num'] = notice.change_num
            if notice.change_type:
                # Добавляем описание отдельного элемента списка
                exp_list.append(
                    {'id': f'change_types.{notice.change_type}',
                     'list_value': notice.change_type, 'model': 'ChangeType'}
                )
                version['change_type'] = f'change_types.{notice.change_type}'

        exp_list.append(version)

        # Связь с объектом
        obj_lnk = self.get_ref()
        if obj_lnk:
            exp_list.add_if_not_empty(self.object)
            link = dict(model='EntityDocumentVersion')
            link['entity'] = obj_lnk
            link['document_version'] = f'versions.{self.id}'
            if self.del_tract_id:
                link['old_version'] = True  # Отмечаем старые версии
            link['id'] = f'edvlink.{self.object.id}.{self.id}'
            exp_list.append(link)

        # Расположение файла
        dig_file = dict(model='DigitalFile')
        dig_file['document_version'] = f'versions.{self.id}'
        dig_file['file_name'] = self.doc_code
        dig_file['src'] = os.path.join(Docs.root_folder, self.folder.folder_name, self.doc_code)
        dig_file['id'] = prepare_id('file', self.id)
        exp_list.append(dig_file)

        # Роль у версии
        if hasattr(self, 'designer') and self.designer:
            exp_list.append({'id': 'designer', 'list_value': 'Разработал', 'model': 'Role'})
            des_role = dict(model='VersionDesignRole')
            des_role['document_version'] = f'versions.{self.id}'
            des_role['role'] = 'designer'
            exp_list.add_if_not_empty(self.designer)
            des_role['designer'] = prepare_id('designer', self.designer.id)
            if self.design_date:
                des_role['role_date'] = str(self.design_date)
            des_role['id'] = f'vrole.{self.id}.{self.designer.id}'
            exp_list.append(des_role)

        return exp_list


# Файлы объектов (dim_id = 1)
class DocsObject(Docs):
    # objects = NotDeletedRows1()

    class Meta:
        managed = False
        db_table = 'documents_export'
        ordering = ['id']
        default_permissions = ()


# Файлы задач (dim_id = 12)
class DocsTask(Docs):
    object = models.ForeignKey(to='Tasks', on_delete=models.CASCADE)

    objects = NotDeletedRows12()

    def get_ref(self):
        return prepare_id('task', self.object.id)

    class Meta:
        managed = False
        db_table = 'documents_export'
        ordering = ['id']
        default_permissions = ()


# Файлы извещений (dim_id = 13)
class DocsNotice(Docs):
    object = models.ForeignKey(to='ChangeNotice', on_delete=models.CASCADE)

    objects = NotDeletedRows13()

    def get_ref(self):
        return prepare_id('notice', self.object.id)

    class Meta:
        managed = False
        db_table = 'documents_export'
        ordering = ['id']
        default_permissions = ()


# Файлы писем (dim_id = 29)
class DocsLetter(Docs):
    object = models.ForeignKey(to='Letters', on_delete=models.CASCADE)

    objects = NotDeletedRows29()

    def get_ref(self):
        return prepare_id('letter', self.object.id)

    class Meta:
        managed = False
        db_table = 'documents_export'
        ordering = ['id']
        default_permissions = ()


# Файлы архивных документов
class ArchiveDocs(Docs):
    object = models.ForeignKey(to='Arcdocuments', on_delete=models.CASCADE)
    folder = models.ForeignKey(to='ArchiveFolders', on_delete=models.CASCADE)

    # objects = NotDeletedRows33()
    objects = AllRows33()  # Все записи, в т.ч. удаленные

    root_folder = r'/mnt/uploaded2'

    def get_ref(self):
        return prepare_id('arcdoc', self.object.id)

    class Meta:
        db_table = 'docs'
        managed = False
        ordering = ['id']
        default_permissions = ()

    def to_dict(self):
        if check_lost(self.object):
            # Удаленные объекты не выгружаем
            return None
        exp_list = ItemsList()  # Доработанный класс списка

        # Добавляем описание архива
        exp_list.append({'id': 'archives.2', 'archive_name': 'Архив документации', 'model': 'FileArchive'})

        # Документ
        doc = dict(model='FileDocument')
        doc['doc_code'] = self.doc_code
        doc['archive'] = 'archives.2'  # Архив не по умолчанию
        if self.doc_type:
            # Добавляем описание отдельного элемента списка
            exp_list.append({'id': f'dt.{self.doc_type}', 'list_value': self.doc_type, 'model': 'DocumentType'})
            doc['doc_type'] = f'dt.{self.doc_type}'
        doc['id'] = f'adocuments.{self.id}'
        exp_list.append(doc)

        # Версия документа
        version = dict(model='DocumentVersion')
        version['document'] = f'adocuments.{self.id}'
        version['description'] = self.description
        version['version_num'] = self.version_num
        version['id'] = f'aversions.{self.id}'

        # Проверка ссылки на документ у извещений
        notices = NoticeLinksDoc.objects.filter(object_id=self.id)
        if notices:  # Если ссылка(и) нашлась
            notice = notices[0]
            exp_list.add_if_not_empty(notice.notice)  # Добавляем описание извещения
            version['notice'] = prepare_id('notice', notice.notice.id)
            version['change_num'] = notice.change_num
            if notice.change_type:
                # Добавляем описание отдельного элемента списка
                exp_list.append(
                    {'id': f'change_types.{notice.change_type}',
                     'list_value': notice.change_type, 'model': 'ChangeType'}
                )
                version['change_type'] = f'change_types.{notice.change_type}'

        exp_list.append(version)

        # Связь с объектом
        obj_lnk = self.get_ref()
        if obj_lnk:
            exp_list.add_if_not_empty(self.object)
            link = dict(model='EntityDocumentVersion')
            link['entity'] = obj_lnk
            link['document_version'] = f'aversions.{self.id}'
            if self.del_tract_id:
                link['old_version'] = True  # Отмечаем старые версии
            link['id'] = f'aedvlink.{self.object.id}.{self.id}'
            exp_list.append(link)

        # Расположение файла
        dig_file = dict(model='DigitalFile')
        dig_file['document_version'] = f'aversions.{self.id}'
        dig_file['file_name'] = self.doc_code
        dig_file['archive_id'] = 2  # Архив не по умолчанию
        dig_file['src'] = os.path.join(ArchiveDocs.root_folder, self.folder.folder_name, self.doc_code)
        dig_file['id'] = prepare_id('afile', self.id)
        exp_list.append(dig_file)

        # Роль у версии
        if hasattr(self, 'designer') and self.designer:
            exp_list.append({'id': 'designer', 'list_value': 'Разработал', 'model': 'Role'})
            des_role = dict(model='VersionDesignRole')
            des_role['document_version'] = f'aversions.{self.id}'
            des_role['role'] = 'designer'
            exp_list.add_if_not_empty(self.designer)
            des_role['designer'] = prepare_id('designer', self.designer.id)
            if self.design_date:
                des_role['role_date'] = str(self.design_date)
            des_role['id'] = f'avrole.{self.id}.{self.designer.id}'
            exp_list.append(des_role)

        return exp_list


# Экземпляры сортаментов
class Exemplar(models.Model):
    mater = models.ForeignKey(to='PartObject', related_name='material', on_delete=models.CASCADE)
    sort = models.ForeignKey(to='PartObject', related_name='sortament', on_delete=models.CASCADE)
    exemplar = models.ForeignKey(to='PartObject', related_name='exemplar', on_delete=models.CASCADE)
    thickness = models.FloatField(blank=True, null=True)
    width = models.FloatField(blank=True, null=True)
    wall = models.FloatField(blank=True, null=True)
    unit_id = models.IntegerField(blank=True, null=True)
    typesize = models.CharField(max_length=20, blank=True, null=True)
    tract_id = models.IntegerField(null=False, blank=False)
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'exemplars'
        ordering = ['id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        exp_list.add_if_not_empty(self.mater)
        exp_list.add_if_not_empty(self.sort)
        exp_list.add_if_not_empty(self.exemplar)
        # Ссылка на материал
        node = dict(model='TypeSizeMater', )
        node['id'] = f'draft_maters.m.{self.id}'
        node['parent'] = prepare_id('material', self.mater.id)
        node['child'] = prepare_id('exemplar', self.exemplar.id)
        exp_list.append(node)
        # Ссылка на сортамент
        node = dict(model='TypeSizeSort', )
        node['id'] = f'draft_maters.s.{self.id}'
        node['parent'] = prepare_id('sortament', self.sort.id)
        node['child'] = prepare_id('exemplar', self.exemplar.id)
        node['thickness'] = self.thickness
        node['width'] = self.width
        node['wall'] = self.wall
        if hasattr(self, 'unit'):
            exp_list.add_if_not_empty(self.unit)
            node['unit'] = prepare_id('unit', self.unit.id)
        node['typesize'] = self.typesize
        exp_list.append(node)
        return exp_list


# Классификационные группы
class ObjectGroup(models.Model):
    group_name = models.CharField(max_length=60)
    group_code = models.CharField(max_length=15, blank=True, null=True)
    order_key = models.IntegerField()
    visible = models.SmallIntegerField()
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey(to='ObjectGroup', related_name='parent_group', on_delete=models.DO_NOTHING)
    picture_id = models.IntegerField(blank=True, null=True)
    tract_id = models.IntegerField(null=False, blank=False)
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'object_groups'
        ordering = ['id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        # Выгружаем ссылочные сущности
        if self.parent_id != 0:
            exp_list.add_if_not_empty(self.parent)
        exp_list.append(dict(id='classification', type_key='classification',
                             model='EntityType'))  # Ссылка на элемент справочника типов
        node = dict(model='Classification', type_key='classification')
        # Свойства - значения
        node['code'] = self.group_name
        node['description'] = self.description
        node['group_code'] = self.group_code
        node['order_num'] = self.order_key
        node['id'] = prepare_id('group', self.id)
        # Свойства - ссылки
        if self.parent_id != 0:
            node['group'] = prepare_id('group', self.parent.id)
        exp_list.append(node)
        return exp_list


# Состав
class Part(models.Model):
    parent = models.ForeignKey(to='PartObject', related_name='parent_object', on_delete=models.CASCADE)
    child = models.ForeignKey(to='PartObject', related_name='child_object', on_delete=models.CASCADE)
    draft_zone = models.CharField(max_length=5, blank=True, null=True)
    position = models.SmallIntegerField(blank=True, null=True)
    quantity = models.FloatField(blank=True, null=True)
    reg_quantity = models.FloatField(blank=True, null=True)
    sin_quantity = models.FloatField(blank=True, null=True)
    unit = models.ForeignKey(to='Unit', on_delete=models.DO_NOTHING, related_name='in_partlinks')
    remark = models.CharField(max_length=25, blank=True, null=True)
    to_replace = models.TextField(blank=True, null=True)
    first_use = models.SmallIntegerField(blank=True, null=True)
    not_buyed = models.SmallIntegerField(blank=True, null=True)
    section_id = models.SmallIntegerField(blank=True, null=True)
    tract_id = models.IntegerField(null=False, blank=False)
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        ordering = ['parent', 'child']
        db_table = 'parts_export'
        # db_table = 'parts'
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        # Проверка что объект не потерянный
        if check_lost(self.parent):
            return None
        if check_lost(self.child):
            return None
        node = dict(model='PartLink', )
        # Описания родителя и потомка
        exp_list.add_if_not_empty(self.parent)
        exp_list.add_if_not_empty(self.child)
        # Описания параметров вхождения
        node['parent'] = prepare_id(ObjectType.TYPEKEYS[self.parent.type.id], self.parent.id)
        node['child'] = prepare_id(ObjectType.TYPEKEYS[self.child.type.id], self.child.id)
        node['quantity'] = self.quantity
        node['comment'] = self.remark
        node['draft_zone'] = self.draft_zone
        node['position'] = self.position
        node['reg_quantity'] = self.reg_quantity
        node['sin_quantity'] = self.sin_quantity
        if hasattr(self, 'unit'):
            exp_list.add_if_not_empty(self.unit)
            node['unit'] = prepare_id('unit', self.unit.id)
        node['to_replace'] = self.to_replace
        node['first_use'] = True if self.first_use == 1 else False
        node['not_buyed'] = True if self.not_buyed == 1 else False
        node['id'] = f'parts.{self.id}'
        exp_list.append(node)
        return exp_list


class OrderParts(models.Model):
    parent = models.ForeignKey(to='PartObject', related_name='order_parts', on_delete=models.CASCADE)
    source = models.ForeignKey(to='PartObject', related_name='was_procrated', on_delete=models.CASCADE)
    # child = models.ForeignKey(to='ObjectToExport', related_name='order_child', on_delete=models.CASCADE)
    child = models.ForeignKey(to='PartObject', related_name='order_child', on_delete=models.CASCADE)
    tract_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'order_parts'
        ordering = ['parent', 'child', 'source']
        default_permissions = ()


# Производственные подразделения
class Place(models.Model):
    place_type = models.CharField(max_length=7, blank=True, null=True)
    place_form = models.CharField(max_length=10, blank=True, null=True)
    place_name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=6, blank=True, null=True)
    place_code = models.CharField(max_length=25, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    group = models.ForeignKey(to='ObjectGroup', related_name='group_places', on_delete=models.DO_NOTHING)
    parent = models.ForeignKey(to='Place', related_name='parent_place', on_delete=models.DO_NOTHING)
    ratio = models.FloatField(blank=True, null=True)
    rating = models.SmallIntegerField(blank=True, null=True)
    is_point = models.SmallIntegerField(blank=True, null=True)
    # is_account = models.SmallIntegerField(blank=True, null=True)
    visible = models.SmallIntegerField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    sitelink = models.CharField(max_length=50, blank=True, null=True)
    # head = models.ForeignKey(to='SystemUser', related_name='place_head', blank=True, null=True, on_delete=models.DO_NOTHING)
    tract_id = models.IntegerField(null=False, blank=False)
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'places'
        ordering = ['id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        # Добавляем описание типа Производственное подразделение (он уже должен быть зарегистрирован)
        exp_list.append({'id': 'place', 'type_key': 'place', 'model': 'EntityType'})
        node = dict(model='Place', type_key='place')
        # Свойства - значения
        node['code'] = self.place_name
        node['description'] = self.remark
        node['short_name'] = self.short_name
        node['place_code'] = self.place_code
        node['address'] = self.address
        node['sitelink'] = self.sitelink
        node['ratio'] = self.ratio
        node['visible'] = True if self.visible == 1 else False
        node['is_point'] = True if self.is_point == 1 else False
        # node['is_account'] = True if self.is_account == 1 else False
        node['id'] = prepare_id('place', self.id)
        # Свойства - ссылки
        if hasattr(self, 'group'):
            exp_list.add_if_not_empty(self.group)
            node['group'] = prepare_id('group', self.group.id)
        if hasattr(self, 'parent'):
            exp_list.add_if_not_empty(self.parent)
            node['parent'] = prepare_id('place', self.parent.id)
        if self.place_type:
            # Добавляем описание отдельного элемента списка
            exp_list.append(
                {'id': 'place_types.' + self.place_type, 'list_value': self.place_type, 'model': 'PlaceType'})
            node['place_type'] = f'place_types.{self.place_type}'
        # if hasattr(self, 'head') and self.head is not None:
        #     exp_list.add_if_not_empty(self.head)
        #     node['head'] = 'users.' + str(self.head.id)
        exp_list.append(node)
        return exp_list


# Маршруты
class Route(models.Model):
    object = models.ForeignKey(to='PartObject', on_delete=models.CASCADE)
    route_name = models.CharField(max_length=15)
    process_code = models.CharField(max_length=30, blank=True, null=True)
    group_process = models.ForeignKey(to='Route', related_name='group_tp', blank=True, null=True,
                                      on_delete=models.DO_NOTHING)
    var_code = models.CharField(max_length=5, blank=True, null=True)
    billet = models.ForeignKey(to='Billet', blank=True, null=True, on_delete=models.DO_NOTHING)
    time_norm = models.FloatField(blank=True, null=True)
    time_norm_cont = models.FloatField(blank=True, null=True)
    unit = models.ForeignKey(to='Unit', related_name='norm_unit', blank=True, null=True, on_delete=models.DO_NOTHING)
    min_party = models.SmallIntegerField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.SmallIntegerField(blank=True, null=True)
    quant = models.FloatField(blank=True, null=True)
    quant_unit = models.ForeignKey(to='Unit', related_name='quant_unit', blank=True, null=True,
                                   on_delete=models.DO_NOTHING)
    remark = models.CharField(max_length=50, blank=True, null=True)
    first = models.ForeignKey(to='RoutePoint', blank=True, null=True, on_delete=models.DO_NOTHING)
    state = models.ForeignKey(to='State', blank=True, null=True, on_delete=models.DO_NOTHING)
    tract_id = models.IntegerField(null=False, blank=False)
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = ActiveNotDeleted()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'routes'
        default_permissions = ()


# Состав маршрутов
class RoutePoint(models.Model):
    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'route_points'
        default_permissions = ()


# Заготовки
class Billet(models.Model):
    object = models.ForeignKey(to='PartObject', related_name='billet_object', on_delete=models.DO_NOTHING)
    row_id = models.IntegerField(blank=True, null=True)
    billet_name = models.CharField(max_length=15)
    is_active = models.SmallIntegerField(blank=True, null=True)
    mater = models.ForeignKey(to='PartObject', related_name='billet_mater', on_delete=models.DO_NOTHING)
    billet_size = models.CharField(max_length=15, blank=True, null=True)
    alt_size = models.CharField(max_length=15, blank=True, null=True)
    object_quantity = models.SmallIntegerField(blank=True, null=True)
    billet_quantity = models.FloatField(blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)
    norm = models.FloatField(blank=True, null=True)
    unit = models.ForeignKey(to='Unit', related_name='billet_norm_unit', blank=True, null=True,
                             on_delete=models.DO_NOTHING)
    source_id = models.SmallIntegerField(blank=True, null=True)
    not_count = models.SmallIntegerField(blank=True, null=True)
    treatment = models.TextField(blank=True, null=True)
    tract_id = models.IntegerField(null=False, blank=False)
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = ActiveNotDeleted()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'billets'
        default_permissions = ()


# Конструкторские материалы
class DraftMaters(models.Model):
    object = models.ForeignKey(to='PartObject', related_name='parеnt_object', on_delete=models.CASCADE,
                               blank=False, null=False, verbose_name='Ссылка на объект')
    mater = models.ForeignKey(to='PartObject', related_name='mater_object', on_delete=models.CASCADE,
                              blank=False, null=False, verbose_name='Ссылка на материал')
    tract_id = models.IntegerField(null=False, blank=False)
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        ordering = ['id']
        # db_table = 'design_maters_export'
        db_table = 'draft_maters'
        default_permissions = ()

    def to_dict(self):
        # print(self.id)
        # Проверка что объект не потерянный
        if check_lost(self.object):
            return None
        exp_list = ItemsList()  # Доработанный класс списка
        exp_list.add_if_not_empty(self.object)
        exp_list.add_if_not_empty(self.mater)
        node = dict(model='DesignMater', )
        node['id'] = f'draft_maters.{self.id}'
        # Свойства - ссылки
        node['parent'] = prepare_id(ObjectType.TYPEKEYS[self.object.type.id], self.object.id)
        node['child'] = prepare_id(ObjectType.TYPEKEYS[self.mater.type.id], self.mater.id)
        exp_list.append(node)
        return exp_list


# Технологические операции
class Operations(models.Model):
    group = models.ForeignKey(to='ObjectGroup', on_delete=models.CASCADE)
    operation_name = models.CharField(max_length=40)
    full_name = models.CharField(max_length=150, blank=True, null=True)
    operation_code = models.CharField(max_length=7, blank=True, null=True)
    instruction = models.CharField(max_length=20, blank=True, null=True)
    min_norm = models.FloatField(blank=True, null=True)
    max_norm = models.FloatField(blank=True, null=True)
    unit = models.ForeignKey(to='Unit', on_delete=models.DO_NOTHING)
    tract_id = models.IntegerField(null=False, blank=False)
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'operations'
        default_permissions = ()


# Цены
class Price(models.Model):
    object = models.ForeignKey(to='PartObject', on_delete=models.CASCADE)
    supplier = models.ForeignKey(to='Place', on_delete=models.CASCADE)
    quantity = models.FloatField()
    unit = models.ForeignKey(to='Unit', related_name='quantity_unit', blank=True, null=True, on_delete=models.CASCADE)
    price = models.FloatField(blank=True, null=True)
    price_unit = models.ForeignKey(to='Unit', related_name='price_unit', blank=True, null=True,
                                   on_delete=models.CASCADE)
    is_active = models.SmallIntegerField(blank=True, null=True)
    article = models.CharField(max_length=50, blank=True, null=True)
    doc = models.CharField(max_length=40, blank=True, null=True)
    supply_date = models.DateField(blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    tract_id = models.IntegerField(null=False, blank=False)
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'prices'
        default_permissions = ()
        ordering = ['id']

    def to_dict(self):
        # Проверка что объект не потерянный
        if check_lost(self.object):
            return None
        exp_list = ItemsList()  # Доработанный класс списка
        exp_list.add_if_not_empty(self.object)
        exp_list.add_if_not_empty(self.supplier)
        node = dict(model='Price', )
        node['id'] = f'prices.{self.id}'
        # Свойства - ссылки
        node['supplied_entity'] = prepare_id(ObjectType.TYPEKEYS[self.object.type.id], self.object.id)
        node['supplier'] = prepare_id('place', self.supplier.id)
        node['supply'] = self.price
        if self.price_unit:
            exp_list.add_if_not_empty(self.price_unit)
            node['price_unit'] = prepare_id('unit', self.price_unit.id)
        node['quantity'] = self.quantity
        if self.price_unit:
            exp_list.add_if_not_empty(self.price_unit)
            node['price_unit'] = prepare_id('unit', self.price_unit.id)
        if self.supply_date:
            node['supply_date'] = str(self.supply_date)
        node['is_active'] = True if self.is_active == 1 else False
        node['doc'] = self.doc
        node['comment'] = self.remark
        exp_list.append(node)
        return exp_list


# Производственные накладные
class Waybill(models.Model):
    waybill_number = models.IntegerField()
    waybill_date = models.DateField()
    order_id = models.IntegerField(blank=True, null=True)
    source_waybill_id = models.IntegerField(blank=True, null=True)
    is_return = models.SmallIntegerField(blank=True, null=True)
    set_place_id = models.IntegerField()
    get_place_id = models.IntegerField()
    sender_id = models.IntegerField(blank=True, null=True)
    supplier_id = models.IntegerField(blank=True, null=True)
    remark = models.CharField(max_length=30, blank=True, null=True)
    tract_id = models.IntegerField(null=False, blank=False)
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = ActiveNotDeleted()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'waybills'
        default_permissions = ()


class Reasons(models.Model):
    reason_code = models.CharField(primary_key=True, max_length=2)
    reason = models.CharField(max_length=85)

    class Meta:
        managed = False
        db_table = 'reasons'
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='NoticeReason', )
        node['id'] = 'reasons.' + self.reason_code
        node['value_code'] = self.reason_code
        node['list_value'] = self.reason
        node['order_num'] = self.id
        exp_list.append(node)
        return exp_list


class RenditionTails(models.Model):
    tail = models.CharField(primary_key=True, max_length=3)

    class Meta:
        managed = False
        db_table = 'rendition_tails'
        ordering = ['tail']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='RenditionTail', )
        node['id'] = 'tails.' + self.tail
        node['list_value'] = self.tail
        # node['order_num'] = int(self.tail)
        exp_list.append(node)
        return exp_list


class Renditions(models.Model):
    parent = models.ForeignKey(to='PartObject', related_name='object_renditions', blank=False, null=False,
                               on_delete=models.CASCADE)
    object = models.ForeignKey(to='PartObject', related_name='rendition', blank=False, null=False,
                               on_delete=models.CASCADE)
    tail = models.CharField(max_length=3)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'renditions'
        ordering = ['id']
        default_permissions = ()

    def to_dict(self):
        # Проверка что объект не потерянный
        if check_lost(self.parent):
            return None
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='Rendition')
        exp_list.append({'id': f'tails.{self.tail}', 'list_value': self.tail,
                         'model': 'RenditionTail'})
        try:
            # Бывает, что объект уже удален
            exp_list.add_if_not_empty(self.parent)
            node['parent'] = prepare_id(ObjectType.TYPEKEYS[self.parent.type.id], self.parent.id)
        except ObjectDoesNotExist:
            print("There is no parent here.", self)
            return list()
        try:
            # Бывает, что объект уже удален
            exp_list.add_if_not_empty(self.object)
            node['rendition'] = prepare_id(ObjectType.TYPEKEYS[self.object.type.id], self.object.id)
        except ObjectDoesNotExist:
            print("There is no rendition here.", self)
            return list()

        node['tail'] = f'tails.{self.tail}'
        node['id'] = f'rendition.{self.id}'
        exp_list.append(node)
        return exp_list


class ChangeNotice(models.Model):
    notice_num = models.CharField(max_length=14)
    notice_type = models.CharField(max_length=3, blank=True, null=True)
    notice_date = models.DateField()
    content = models.TextField(blank=True, null=True)
    reason_code = models.CharField(max_length=2, blank=True, null=True)
    reserve = models.CharField(max_length=50, blank=True, null=True)
    valid_date = models.DateField(blank=True, null=True)
    approve_date = models.DateField(blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)
    directions = models.CharField(max_length=100, blank=True, null=True)
    usages = models.TextField(blank=True, null=True)
    # attachment = models.TextField(blank=True, null=True)
    state = models.ForeignKey(to='State', blank=True, null=True, on_delete=models.DO_NOTHING)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        ordering = ['notice_num', 'notice_date']
        managed = False
        db_table = 'notices'
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        # Добавляем описание типа Извещение об изменениях (он уже должен быть зарегистрирован)
        exp_list.append({'id': 'notice', 'type_key': 'notice', 'model': 'EntityType'})
        node = dict(model='Notice', type_key='notice')
        node['code'] = self.notice_num
        node['description'] = self.content
        if self.notice_type:
            # Добавляем описание отдельного элемента списка
            exp_list.append(
                {'id': f'notice_types.{self.notice_type}', 'value_code': self.notice_type,
                 'list_value': self.notice_type, 'model': 'NoticeType'})
            node['notice_type'] = f'notice_types.{self.notice_type}'
        if self.notice_date:
            node['notice_date'] = str(self.notice_date)
        if self.valid_date:
            node['valid_date'] = str(self.valid_date)
        if self.approve_date:
            node['approve_date'] = str(self.approve_date)
        if self.deadline:
            if str(self.deadline) == '1900-01-01':
                node['urgently'] = True
                node['deadline'] = None
            else:
                # print(str(self.deadline))
                node['deadline'] = str(self.deadline)
        if self.reason_code:
            # Получаем описание элемента списка
            reason = Reasons.objects.get(reason_code=self.reason_code)
            # Добавляем описание отдельного элемента списка
            exp_list.append({'id': f'reasons.{self.reason_code}', 'value_code': self.reason_code,
                             'list_value': reason.reason,
                             'model': 'NoticeReason'})
            node['reason'] = f'reasons.{self.reason_code}'

        node['reserve'] = self.reserve
        node['directions'] = self.directions
        node['usages'] = self.usages
        node['description'] = self.content
        # node['attachment'] = self.attachment
        if self.state is not None:
            exp_list.add_if_not_empty(self.state)
            node['state'] = prepare_id('state', self.state.id)
        node['id'] = prepare_id('notice', self.id)
        exp_list.append(node)
        return exp_list


class NoticeLinks(models.Model):
    notice = models.ForeignKey(to='ChangeNotice', blank=False, null=False, on_delete=models.CASCADE)
    dim_id = models.SmallIntegerField()
    object = models.ForeignKey(to='PartObject', related_name='notices', blank=False, null=False,
                               on_delete=models.CASCADE)
    # old = models.ForeignKey(to='PartObject', related_name='close_notices', blank=True, null=True,
    #                         on_delete=models.DO_NOTHING)
    change_num = models.SmallIntegerField(blank=True, null=True)
    change_type = models.CharField(max_length=10, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    is_done = models.SmallIntegerField()
    is_order_part = models.SmallIntegerField()
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows1()  # Менеджер по умолчанию

    class Meta:
        ordering = ['id']
        managed = False
        abstract = True  # Это абстрактный класс
        db_table = 'notice_links'
        default_permissions = ()

    def get_ref(self):
        return prepare_id(ObjectType.TYPEKEYS[self.object.type.id], self.object.id)

    def to_dict(self):
        # Проверка что объект не потерянный
        if check_lost(self.object):
            return None
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='NoticeLink')
        exp_list.add_if_not_empty(self.notice)
        exp_list.add_if_not_empty(self.object)
        # Описания параметров вхождения
        node['parent'] = prepare_id('notice', self.notice.id)
        node['child'] = self.get_ref()
        if self.change_type:
            # Добавляем описание отдельного элемента списка
            exp_list.append(
                {'id': f'change_types.{self.change_type}', 'list_value': self.change_type, 'model': 'ChangeType'})
            node['change_type'] = f'change_types.{self.change_type}'
        node['change_num'] = self.change_num
        node['is_done'] = True if self.is_done == 1 else False

        # try:
        #     if self.old:
        #         # Бывает, что объект уже удален
        #         exp_list.add_if_not_empty(self.old)
        #         node['old'] = prepare_id(ObjectType.TYPEKEYS[self.old.type.id], self.old.id)
        # except ObjectDoesNotExist:
        #     print("There is no old here.", self)

        node['id'] = f'notice_links.{self.id}'
        exp_list.append(node)
        return exp_list


class NoticeLinksObject(NoticeLinks):
    # Связь извещений с объектами конструкции

    class Meta:
        ordering = ['id']
        managed = False
        db_table = 'notice_links'
        default_permissions = ()


class NoticeLinksDoc(NoticeLinks):
    # Связь извещений с файлами
    # Не грузим, так как на извещения теперь ссылаются версии файлов (см. Docs)
    object = models.ForeignKey(to='DocsObject', related_name='doc_notices', blank=False, null=False,
                               on_delete=models.CASCADE)

    objects = NotDeletedRows5()  # Менеджер по умолчанию

    def get_ref(self):
        return f'versions.{self.object.id}'

    class Meta:
        ordering = ['id']
        managed = False
        db_table = 'notice_links'
        default_permissions = ()


class NoticeLinksArcDoc(NoticeLinks):
    object = models.ForeignKey(to='Arcdocuments', related_name='arcdoc_notices', blank=False, null=False,
                               on_delete=models.CASCADE)

    objects = NotDeletedRows33()

    def get_ref(self):
        return prepare_id('arcdoc', self.object.id)

    class Meta:
        ordering = ['id']
        managed = False
        db_table = 'notice_links'
        default_permissions = ()


class NoticeRecipients(models.Model):
    notice = models.ForeignKey(to='ChangeNotice', blank=False, null=False, on_delete=models.CASCADE)
    place = models.ForeignKey(to='Place', related_name='receving_notices', blank=False, null=False,
                              on_delete=models.CASCADE)
    remark = models.TextField(blank=True, null=True)
    is_sent = models.SmallIntegerField(blank=True, null=True)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        ordering = ['id']
        managed = False
        db_table = 'notice_recipients'
        default_permissions = ()

    def to_dict(self):
        # Проверка что объект не потерянный
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='NoticeRecipient')
        exp_list.add_if_not_empty(self.notice)
        exp_list.add_if_not_empty(self.place)
        # Описания параметров вхождения
        node['parent'] = prepare_id('notice', self.notice.id)
        node['child'] = prepare_id('place', self.place.id)
        if self.remark:
            node['comment'] = self.remark
        node['is_sent'] = True if self.is_sent == 1 else False

        node['id'] = f'notice_recipients.{self.id}'
        exp_list.append(node)
        return exp_list


class SystemUser(models.Model):
    login = models.CharField(max_length=25, blank=True, null=True)
    password = models.CharField(max_length=32, blank=True, null=True)
    user_name = models.CharField(max_length=100, blank=True, null=True)
    designer = models.CharField(max_length=25, blank=True, null=True)
    user_position = models.CharField(max_length=110, blank=True, null=True)
    user_phone = models.CharField(max_length=20, blank=True, null=True)
    user_mail = models.CharField(max_length=30, blank=True, null=True)
    is_group = models.SmallIntegerField(blank=True, null=True)
    place = models.ForeignKey(to='Place', blank=True, null=True, on_delete=models.CASCADE)
    # work_rank = models.SmallIntegerField(blank=True, null=True)
    picture_id = models.IntegerField(blank=True, null=True)
    styletable = models.CharField(max_length=15, blank=True, null=True)
    dismissed = models.SmallIntegerField(blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'users'
        ordering = ['id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        # User
        if self.login:
            node = dict(model='SystemUser', )
            node['username'] = self.login
            node['last_name'] = self.user_name
            # node['password'] = '111'
            node['id'] = prepare_id('user', self.pk)
            exp_list.append(copy(node))

        # UserProfile
        userprofile_id = ''
        if self.user_name:
            node = dict(model='UserProfile', )
            node['user_name'] = self.user_name
            node['dismissed'] = True if self.dismissed == 1 else False
            node['styletable'] = self.styletable
            node['is_group'] = True if self.is_group == 1 else False
            if self.login:
                node['user'] = prepare_id('user', self.pk)
            userprofile_id = f'user_profiles.{self.pk}'
            node['id'] = userprofile_id
            # print(node)
            exp_list.append(copy(node))

        # Designer
        if self.designer:
            node = dict(model='Designer', )
            node['designer'] = self.designer if self.designer else self.user_name
            node['id'] = prepare_id('designer', self.id)
            if userprofile_id:
                node['designer_profile'] = userprofile_id
            # print(node)
            exp_list.append(copy(node))

        if self.user_position or self.user_phone or self.user_mail:
            # Person
            node = dict(model='Person', )
            node['person'] = self.user_name if self.user_name else self.designer
            node['user_position'] = self.user_position
            node['user_phone'] = self.user_phone
            node['user_mail'] = self.user_mail
            if self.place is not None:
                exp_list.add_if_not_empty(self.place)
                node['place'] = prepare_id('place', self.place.id)
            # node['designer_r'] = self.designer_r
            # node['designer_d'] = self.designer_d
            # node['work_rank'] = self.work_rank
            node['id'] = f'persons.{self.id}'
            if userprofile_id:
                node['person_profile'] = userprofile_id
            # print(node)
            exp_list.append(node)
        return exp_list


class Designer(models.Model):
    login = models.CharField(max_length=25, blank=True, null=True)
    password = models.CharField(max_length=32, blank=True, null=True)
    user_name = models.CharField(max_length=100, blank=True, null=True)
    designer = models.CharField(max_length=25, blank=True, null=True)
    user_position = models.CharField(max_length=110, blank=True, null=True)
    user_phone = models.CharField(max_length=20, blank=True, null=True)
    user_mail = models.CharField(max_length=30, blank=True, null=True)
    is_group = models.SmallIntegerField(blank=True, null=True)
    place = models.ForeignKey(to='Place', blank=True, null=True, on_delete=models.CASCADE)
    picture_id = models.IntegerField(blank=True, null=True)
    styletable = models.CharField(max_length=15, blank=True, null=True)
    dismissed = models.SmallIntegerField(blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'users'
        ordering = ['id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        # User
        if self.login:
            node = dict(model='SystemUser', )
            node['username'] = self.login
            node['last_name'] = self.user_name if self.user_name else self.login
            node['password'] = '111'
            node['id'] = prepare_id('user', self.pk)
            exp_list.append(copy(node))

        # UserProfile
        userprofile_id = ''
        if self.user_name:
            node = dict(model='UserProfile', )
            node['user_name'] = self.user_name
            node['dismissed'] = True if self.dismissed == 1 else False
            node['styletable'] = self.styletable
            node['is_group'] = True if self.is_group == 1 else False
            if self.login:
                node['user'] = prepare_id('user', self.pk)
            userprofile_id = f'user_profiles.{self.pk}'
            node['id'] = userprofile_id
            # print(node)
            exp_list.append(copy(node))

        # Designer
        if self.designer:
            node = dict(model='Designer', )
            node['designer'] = self.designer if self.designer else self.user_name
            node['id'] = prepare_id('designer', self.id)
            if userprofile_id:
                node['designer_profile'] = userprofile_id
            # print(node)
            exp_list.append(copy(node))

        if self.user_position or self.user_phone or self.user_mail:
            # Person
            node = dict(model='Person', )
            node['person'] = self.user_name if self.user_name else self.designer
            node['user_position'] = self.user_position
            node['user_phone'] = self.user_phone
            node['user_mail'] = self.user_mail
            if self.place is not None:
                exp_list.add_if_not_empty(self.place)
                node['place'] = prepare_id('place', self.place.id)
            # node['designer_r'] = self.designer_r
            # node['designer_d'] = self.designer_d
            # node['work_rank'] = self.work_rank
            node['id'] = f'persons.{self.id}'
            if userprofile_id:
                node['person_profile'] = userprofile_id
            # print(node)
            exp_list.append(node)
        return exp_list


# Транзакции
class Transaction(models.Model):
    user = models.ForeignKey(SystemUser, on_delete=models.CASCADE)
    tract_datetime = models.DateTimeField()
    user_ip = models.CharField(max_length=15, blank=True, null=True)
    remark = models.CharField(max_length=30, blank=True, null=True)
    note_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'transactions'
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='UserSession', )
        node['id'] = f'usersessions.{self.id}'
        exp_list.add_if_not_empty(self.user)
        node['session_datetime'] = str(self.tract_datetime)
        node['user'] = prepare_id('user', self.user.id)
        node['user_ip'] = self.user_ip
        node['comment'] = self.remark
        exp_list.append(node)
        return exp_list


# История редактирования
class History(models.Model):
    object_id = models.IntegerField()
    dim_id = models.SmallIntegerField()
    tract = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    param_id = models.IntegerField()
    param_value = models.CharField(max_length=250, blank=True, null=True)
    unit_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'history_export'
        ordering = ['tract_id', 'dim_id', 'object_id', 'param_id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='HistoryLog', )
        node['id'] = f'historylog.{self.pk}'
        node['table_name'] = dims[self.dim_id]
        if self.dim_id == 1:
            obj = PartObject.objects.get(pk=self.object_id)
            exp_list.add_if_not_empty(obj)
            node['object_id'] = self.object_id
        node['changes'] = get_change(self.param_id, self.param_value, self.unit_id)
        exp_list.add_if_not_empty(self.tract)
        node['edt_sess'] = f'usersessions.{self.tract.pk}'
        exp_list.append(node)
        if node['changes']:
            return exp_list
        return list()  # Записи с пустыми изменениями не возвращаем


class Roles(models.Model):
    role_name = models.CharField(max_length=25)
    # order_key = models.SmallIntegerField(blank=True, null=True)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        ordering = ['id']
        db_table = 'roles'
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='Role', )
        node['id'] = prepare_id('role', self.id)
        node['list_value'] = self.role_name
        # node['order_num'] = self.order_key
        node['is_default'] = True if self.id == 1 else False
        exp_list.append(node)
        return exp_list


class DesignRoles(models.Model):
    object = models.ForeignKey(to='PartObject', related_name='design_roles', on_delete=models.CASCADE)
    dim_id = models.SmallIntegerField()
    role = models.ForeignKey(to='Roles', related_name='object_roles', on_delete=models.CASCADE)
    designer = models.ForeignKey(to='Designer', related_name='user_roles', on_delete=models.CASCADE)
    role_date = models.DateField(blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows1()  # Менеджер по умолчанию

    class Meta:
        managed = False
        ordering = ['id']
        # db_table = 'roles_export'
        db_table = 'design_roles'
        default_permissions = ()

    def to_dict(self):
        # Проверка что объект не потерянный
        if check_lost(self.object):
            return None
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='DesignRole')
        # Описания родителя и потомка
        exp_list.add_if_not_empty(self.object)
        exp_list.add_if_not_empty(self.role)
        exp_list.add_if_not_empty(self.designer)
        # Описания параметров вхождения
        node['subject'] = prepare_id(ObjectType.TYPEKEYS[self.object.type.id], self.object.id)
        node['role'] = prepare_id('role', self.role.id)
        node['designer'] = prepare_id('designer', self.designer.id)
        node['role_date'] = self.role_date
        if self.remark is not None:
            node['comment'] = self.remark
        node['id'] = f'design_roles.{self.id}'
        exp_list.append(node)
        return exp_list


class DesignRolesNotice(models.Model):
    object = models.ForeignKey(to='ChangeNotice', related_name='notice_design_roles', on_delete=models.CASCADE)
    dim_id = models.SmallIntegerField()
    role = models.ForeignKey(to='Roles', related_name='notice_roles', on_delete=models.CASCADE)
    designer = models.ForeignKey(to='Designer', related_name='user_notice_roles', on_delete=models.CASCADE)
    role_date = models.DateField(blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows13()  # Менеджер по умолчанию

    class Meta:
        managed = False
        ordering = ['id']
        db_table = 'design_roles'
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='DesignRole')
        # Описания родителя и потомка
        exp_list.add_if_not_empty(self.object)
        exp_list.add_if_not_empty(self.role)
        exp_list.add_if_not_empty(self.designer)
        # Описания параметров вхождения
        node['subject'] = prepare_id('notice', self.object.id)
        node['role'] = prepare_id('role', self.role.id)
        node['designer'] = prepare_id('designer', self.designer.id)
        node['role_date'] = self.role_date
        if self.remark is not None:
            node['comment'] = self.remark
        node['id'] = f'design_roles.{self.id}'
        exp_list.append(node)
        return exp_list


class ObjectFormats(models.Model):
    object = models.ForeignKey(to='PartObject', related_name='object_formats', on_delete=models.CASCADE)
    order_key = models.IntegerField(null=False)
    format_letter = models.CharField(max_length=5, blank=False, null=False)
    quantity = models.IntegerField(null=True)

    class Meta:
        managed = False
        ordering = ['object', 'order_key']
        db_table = 'formats_export'
        default_permissions = ()

    def to_dict(self):
        # Проверка что объект не потерянный
        if check_lost(self.object):
            return None
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='PartObjectFormat')
        # Описания родителя
        exp_list.add_if_not_empty(self.object)
        # Добавляем описание отдельного элемента списка форматов
        exp_list.append({'id': self.format_letter, 'list_value': self.format_letter, 'model': 'PartFormat'})
        node['part_object'] = prepare_id(ObjectType.TYPEKEYS[self.object.type.id], self.object.id)
        node['format'] = self.format_letter
        if self.quantity:
            node['list_quantity'] = self.quantity
        node['order_num'] = self.order_key
        node['id'] = f'object_formats.{self.object.id}.{self.object.id}'
        exp_list.append(node)
        return exp_list


class ArcDocFormats(models.Model):
    document = models.ForeignKey(to='ArcDocuments', on_delete=models.CASCADE, blank=False, null=False,
                                 verbose_name='Ссылка на архивный документ')
    list_quantity = models.SmallIntegerField()
    format_number = models.CharField(max_length=2)
    format_quantity = models.SmallIntegerField()
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'formats'
        ordering = ['document', 'id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='PartObjectFormat')
        # Описания родителя
        exp_list.add_if_not_empty(self.document)
        if self.format_quantity > 1:
            format_letter = f'{self.format_number}x{self.format_quantity}'
        else:
            format_letter = self.format_number
        # Добавляем описание отдельного элемента списка форматов
        exp_list.append({'id': format_letter, 'list_value': format_letter, 'model': 'PartFormat'})
        node['part_object'] = prepare_id('arcdoc', self.document.id)
        node['format'] = format_letter
        if self.list_quantity:
            node['list_quantity'] = self.list_quantity
        else:
            node['list_quantity'] = 1
        node['id'] = f'arc_formats.{self.id}'
        exp_list.append(node)
        return exp_list


class Folders(models.Model):
    prefix_char = models.CharField(max_length=1)
    folder_name = models.CharField(max_length=8)
    folder_num = models.SmallIntegerField()
    files_quant = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'folders'
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        # Добавляем описание архива
        exp_list.append({'id': 'main', 'archive_name': 'Основной', 'core_directory': 'C:/', 'model': 'FileArchive'})
        node = dict(model='Folder')
        node['archive'] = 'main'
        node['folder_name'] = self.folder_name
        node['folder_num'] = self.folder_num
        node['id'] = f'folders.{self.id}'
        exp_list.append(node)
        return exp_list


class ArchiveFolders(models.Model):
    prefix_char = models.CharField(max_length=1)
    folder_name = models.CharField(max_length=8)
    folder_num = models.SmallIntegerField()
    files_quant = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'folders'
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        # Добавляем описание архива
        exp_list.append({'id': 'main', 'archive_name': 'Основной', 'core_directory': 'C:/', 'model': 'FileArchive'})
        node = dict(model='Folder')
        node['archive'] = 'main'
        node['folder_name'] = self.folder_name
        node['folder_num'] = self.folder_num
        node['id'] = f'folders.{self.id}'
        exp_list.append(node)
        return exp_list


class DocFiles(models.Model):
    """Скорее всего использоваться не будет"""
    # dim_id = models.IntegerField()
    object = models.ForeignKey(to='PartObject', related_name='doc_files', on_delete=models.CASCADE)
    doc_code = models.CharField(max_length=10, blank=False, null=False)
    folder = models.ForeignKey(to='Folders', on_delete=models.CASCADE)
    prefix_char = models.CharField(max_length=1)
    folder_name = models.CharField(max_length=8)
    version_num = models.IntegerField()
    source = models.CharField(max_length=1)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        ordering = ['id']
        # db_table = 'documents_export'
        db_table = 'vwfiles'
        default_permissions = ()

    def to_dict(self):
        # exp_list = ItemsList()  # Доработанный класс списка
        # Документ и связанные с ним понятия
        exp_list = Docs.objects.get(pk=self.pk).to_dict()

        # Файл версии документа
        # Каталог
        exp_list.add_if_not_empty(self.folder)
        node = dict(model='DigitalFile')
        node['document_version'] = f'versions.{self.id}'
        node['file_name'] = self.doc_code
        node['folder'] = f'folders.{self.folder.id}'
        node['id'] = prepare_id('file', self.id)
        exp_list.append(node)
        return exp_list


class Tasks(models.Model):
    task_number = models.IntegerField()
    task_date = models.DateField(blank=True, null=True)
    task_type = models.CharField(max_length=30, blank=True, null=True)
    income_number = models.CharField(max_length=30, blank=True, null=True)
    task_from = models.CharField(max_length=110, blank=True, null=True)
    task_theme = models.CharField(max_length=200, blank=True, null=True)
    task = models.TextField(blank=True, null=True)
    next = models.ForeignKey(to='Tasks', blank=True, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(to='SystemUser', blank=False, null=False, on_delete=models.CASCADE)
    deadline = models.DateField(blank=True, null=True)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'tasks'
        ordering = ['id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        exp_list.append({'id': 'task', 'type_key': 'task', 'model': 'EntityType'})
        node = dict(model='Task', type_key='task')
        node['id'] = prepare_id('task', self.id)
        node['code'] = str(self.task_number)
        if self.task_date:
            node['task_date'] = str(self.task_date)
        node['income_number'] = self.income_number
        node['task_from'] = self.task_from
        node['task_theme'] = self.task_theme
        node['description'] = self.task
        if self.task_type:
            # Добавляем описание отдельного элемента списка
            exp_list.append(
                {'id': f'task_types.{self.task_type}', 'list_value': self.task_type, 'model': 'TaskType'})
            node['task_type'] = f'task_types.{self.task_type}'
        if self.next:
            exp_list.add_if_not_empty(self.next)
            node['next'] = prepare_id('tasks', self.next.id)
        if self.user:
            exp_list.add_if_not_empty(self.user)
            exp_list.append(
                {'id': f'task_users.{self.id}', 'model': 'TaskUser',
                 'task': prepare_id('task', self.id),
                 'user': f'user_profiles.{self.user.id}',
                 'deadline': str(self.deadline)
                 })

        exp_list.append(node)
        return exp_list


class TaskRefer(models.Model):
    object = models.ForeignKey(to='PartObject', related_name='object_tasks', on_delete=models.CASCADE)
    dim_id = models.SmallIntegerField()
    task = models.ForeignKey(to='Tasks', on_delete=models.CASCADE)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows1()  # Менеджер по умолчанию

    class Meta:
        abstract = True
        managed = False
        db_table = 'task_refer'
        ordering = ['id']
        default_permissions = ()

    def get_ref(self):
        return prepare_id(ObjectType.TYPEKEYS[self.object.type.id], self.object.id)

    def to_dict(self):
        # Проверка что объект не потерянный
        if check_lost(self.object):
            return None
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='TaskRefer')
        # Описания родителя и потомка
        exp_list.add_if_not_empty(self.object)
        exp_list.add_if_not_empty(self.task)
        # Описания параметров вхождения
        node['parent'] = prepare_id('task', self.task.id)
        node['child'] = self.get_ref()

        node['id'] = f'task_refer.{self.id}'
        exp_list.append(node)
        return exp_list


class TaskReferNotice(TaskRefer):
    object = models.ForeignKey(to='ChangeNotice', related_name='notice_tasks', on_delete=models.CASCADE)

    objects = NotDeletedRows13()  # Менеджер по умолчанию

    def get_ref(self):
        return prepare_id('notice', self.object.id)

    class Meta:
        managed = False
        db_table = 'task_refer'
        ordering = ['id']
        default_permissions = ()


class TaskReferObject(TaskRefer):

    class Meta:
        managed = False
        db_table = 'task_refer'
        ordering = ['id']
        default_permissions = ()


class Arcdocuments(models.Model):
    document_code = models.CharField(max_length=200)
    document_name = models.CharField(max_length=110, blank=True, null=True)
    document_num = models.CharField(max_length=50)
    type_id = models.SmallIntegerField(blank=True, null=True)
    reg_date = models.DateField()
    list_count = models.SmallIntegerField(blank=True, null=True)
    state = models.ForeignKey(to='State', blank=True, null=True, on_delete=models.DO_NOTHING)
    stage = models.ForeignKey(to='PartObject', blank=True, null=True, on_delete=models.DO_NOTHING)
    place = models.ForeignKey(to='Place', blank=True, null=True, on_delete=models.DO_NOTHING)
    remark = models.TextField(blank=True, null=True)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'arcdocuments'
        ordering = ['id']
        default_permissions = ()

    DOC_TYPES = {
        1: 'Конструкторский документ',
        2: 'Технологический документ',
        3: 'Монтажный документ',
        4: 'Письмо',
        5: 'Служебная записка',
        6: 'Прочее'
    }

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        exp_list.append({'id': 'arcdocument', 'type_key': 'arcdocument', 'model': 'EntityType'})
        node = dict(model='ArcDocument', type_key='arcdocument')
        exp_list.add_if_not_empty(self.state)
        # exp_list.add_if_not_empty(self.place)
        if self.type_id:
            exp_list.append(
                {'id': f'doc_types.{self.type_id}',
                 'list_value': Arcdocuments.DOC_TYPES[self.type_id],
                 'model': 'DocumentType'})
            node['doc_type'] = f'doc_types.{self.type_id}'

        if self.stage:
            exp_list.append({'id': 'stage', 'type_key': 'stage', 'model': 'EntityType'})
            exp_list.append(
                {'id': f'stages.{self.stage.id}',
                 'code': self.stage.object_code,
                 'type_key': 'stage',
                 'model': 'Stage'})
            node['parent'] = f'stages.{self.stage.id}'

        node['code'] = self.document_code
        node['document_name'] = self.document_name
        node['document_num'] = self.document_num
        node['reg_date'] = str(self.reg_date)
        node['list_count'] = self.list_count

        if self.state:
            node['document_state'] = prepare_id('state', self.state.id)
        # Вроде как нет их заполненных в исходных данных
        # if self.place:
        #     node['document_place'] = 'places.' + str(self.place.id)

        node['id'] = prepare_id('arcdoc', self.id)
        exp_list.append(node)
        return exp_list


class ArcdocLinks(models.Model):
    document = models.ForeignKey(to='Arcdocuments', related_name='partobjects', blank=False, null=False,
                                 on_delete=models.CASCADE)
    dim_id = models.SmallIntegerField()
    object = models.ForeignKey(to='PartObject', related_name='arcdocs', blank=False, null=False,
                               on_delete=models.CASCADE)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'arcdoc_links'
        ordering = ['id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='ArcDocumentObject')

        exp_list.add_if_not_empty(self.document)
        node['parent'] = prepare_id('arcdoc', self.document.id)
        exp_list.add_if_not_empty(self.object)
        node['child'] = prepare_id(ObjectType.TYPEKEYS[self.object.type.id], self.object.id)
        node['id'] = f'arcdoclink.{self.id}'
        exp_list.append(node)
        return exp_list


class Deliveries(models.Model):
    receiver = models.ForeignKey(to='Place', blank=True, null=True, on_delete=models.DO_NOTHING)
    delivery_date = models.DateField()
    remark = models.TextField(blank=True, null=True)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'deliveries'
        ordering = ['id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='Delivery')

        exp_list.add_if_not_empty(self.receiver)

        node['delivery_date'] = str(self.delivery_date)
        node['comment'] = self.remark
        node['delivery_num'] = self.id

        if self.receiver:
            node['receiver'] = prepare_id('place', self.receiver.id)

        node['id'] = prepare_id('delivery', self.id)
        exp_list.append(node)
        return exp_list


class DeliveryArcdocs(models.Model):
    delivery = models.ForeignKey(to='Deliveries', blank=False, null=False, on_delete=models.CASCADE)
    arcdoc = models.ForeignKey(to='Arcdocuments', blank=False, null=False, on_delete=models.CASCADE)
    exemplar_num = models.CharField(max_length=20, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'delivery_arcdocs'
        ordering = ['id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='DeliveryArcdoc')

        exp_list.add_if_not_empty(self.delivery)
        node['delivery'] = prepare_id('delivery', self.delivery.id)
        exp_list.add_if_not_empty(self.arcdoc)
        node['arc_doc'] = prepare_id('arcdoc', self.arcdoc.id)

        node['exemplar_num'] = str(self.exemplar_num)
        node['comment'] = self.remark

        node['id'] = f'deliveryarcdoc.{self.id}'
        exp_list.append(node)
        return exp_list


class Properties(models.Model):
    prop_name = models.CharField(max_length=50)
    prop_type = models.SmallIntegerField()
    parent = models.ForeignKey(to='Properties', on_delete=models.SET_NULL, blank=True, null=True)
    essences = models.CharField(max_length=25, blank=True, null=True)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    PROP_TYPES = {
        1: 'S',
        2: 'F',
        3: 'R',
        5: 'D',
        6: 'L'
    }

    PROP_NAMES = {
        1: 'Строка',
        2: 'Число',
        3: 'Диапазон',
        5: 'Дата',
        6: 'Ссылка'
    }
    # '4' = > 'Группа свойств', '5' = > 'Дата', '6' = > 'Классификационная группа'

    class Meta:
        managed = False
        db_table = 'properties'
        ordering = ['id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка

        if self.prop_type == 4: # Это группа свойств
            node = dict(model='Classification')
            node['code'] = self.prop_name
            node['id'] = prepare_id('group', self.id)
        else:
            node = dict(model='Property')
            node['property_name'] = self.prop_name
            node['property_name_rus'] = self.prop_name

            exp_list.append(
                {'id': 'property_types.' + Properties.PROP_TYPES[self.prop_type],
                 'model': 'PropertyType',
                 'property_type': Properties.PROP_TYPES[self.prop_type],
                 'description': Properties.PROP_NAMES[self.prop_type]})

            node['property_type'] = 'property_types.' + Properties.PROP_TYPES[self.prop_type]

            if self.parent_id:
                node['group'] = prepare_id('group', self.parent.id)

            node['id'] = prepare_id('property', self.id)
        exp_list.append(node)
        return exp_list


class PropValues(models.Model):
    object = models.ForeignKey(PartObject, null=False, blank=False, on_delete=models.CASCADE)
    dim_id = models.SmallIntegerField()
    prop = models.ForeignKey(Properties, null=False, blank=False, on_delete=models.CASCADE)
    prop_value_min = models.FloatField(blank=True, null=True)
    prop_value_max = models.FloatField(blank=True, null=True)
    prop_value = models.CharField(max_length=255, blank=True, null=True)
    unit = models.ForeignKey(Unit, null=False, blank=False, on_delete=models.CASCADE)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'prop_values'
        ordering = ['id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='PropertyValue')
        exp_list.add_if_not_empty(self.object)
        node['entity'] = prepare_id(ObjectType.TYPEKEYS[self.object.type.id], self.object.id)
        exp_list.add_if_not_empty(self.prop)
        node['property'] = prepare_id('property', self.prop.id)

        node['value'] = self.prop_value
        node['value_min'] = self.prop_value_min
        node['value_max'] = self.prop_value_max

        if self.unit_id:
            exp_list.add_if_not_empty(self.unit)
            node['unit'] = prepare_id('unit', self.unit.id)

        node['id'] = f'propvalues.{self.id}'
        exp_list.append(node)
        return exp_list


class LetterTypes(models.Model):
    type_name = models.CharField(max_length=30)
    order_key = models.SmallIntegerField(blank=True, null=True)
    del_tract_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'letter_types'
        ordering = ['id']
        default_permissions = ()


class Letters(models.Model):
    DIRECTIONS = {
        1: 'Входящее',
        2: 'Исходящее',
        3: 'Общее'
    }

    direction_id = models.SmallIntegerField()
    reg_num = models.CharField(max_length=15)
    reg_date = models.DateField()
    letter_num = models.CharField(max_length=60, blank=True, null=True)
    # letter_date = models.DateField(blank=True, null=True)
    type = models.ForeignKey(LetterTypes, blank=True, null=True, on_delete=models.CASCADE)
    sender = models.ForeignKey(to='Place', blank=True, null=True, related_name='sen', on_delete=models.CASCADE)
    receiver = models.ForeignKey(to='Place', blank=True, null=True, related_name='res', on_delete=models.CASCADE)
    # income_id = models.IntegerField(blank=True, null=True)
    letter_theme = models.CharField(max_length=200, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    # group = models.ForeignKey(ObjectGroup, related_name='let', blank=True, null=True, on_delete=models.DO_NOTHING)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'letters'
        ordering = ['id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        exp_list.append({'id': 'letter', 'type_key': 'letter', 'model': 'EntityType'})
        node = dict(model='Letter', type_key='letter')
        node['id'] = prepare_id('letter', self.id)
        node['code'] = str(self.reg_num)
        if self.reg_date:
            node['reg_date'] = str(self.reg_date)
        node['letter_num'] = self.letter_num
        # node['letter_date'] = self.letter_date
        node['letter_theme'] = self.letter_theme
        node['description'] = self.remark
        if self.type:
            # Добавляем описание отдельного элемента списка
            exp_list.append({'id': f'letter_types.{self.type.id}', 'list_value': self.type.type_name,
                             'order_num': self.type.order_key, 'model': 'LetterType'})
            node['letter_type'] = f'letter_types.{self.type.id}'
        if self.direction_id:
            # Добавляем описание отдельного элемента списка
            exp_list.append({'id': f'letter_directions.{self.direction_id}',
                             'list_value': Letters.DIRECTIONS[self.direction_id],
                             'order_num': self.direction_id, 'model': 'LetterDirection'})
            node['direction'] = f'letter_directions.{self.direction_id}'

        # if self.group:
        #     exp_list.add_if_not_empty(self.group)
        #     node['group'] = 'object_groups.' + str(self.group.id)

        if self.sender is not None:
            exp_list.add_if_not_empty(self.sender)
            node['sender'] = prepare_id('place', self.sender.id)

        if self.receiver is not None:
            exp_list.add_if_not_empty(self.receiver)
            node['receiver'] = prepare_id('place', self.receiver.id)

        exp_list.append(node)
        return exp_list


class LetterLinks(models.Model):
    letter = models.ForeignKey(Letters, blank=False, null=False, on_delete=models.CASCADE)
    # dim_id = models.SmallIntegerField()
    object = models.ForeignKey(PartObject, blank=False, null=False, on_delete=models.CASCADE)
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)
    # object_status_id = models.IntegerField(blank=True, null=True)
    # letter_status_id = models.IntegerField(blank=True, null=True)
    # pack_type = models.SmallIntegerField(blank=True, null=True)

    objects = NotDeletedRows()  # Менеджер по умолчанию

    class Meta:
        managed = False
        db_table = 'letter_links'
        ordering = ['id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='LetterLink')
        exp_list.add_if_not_empty(self.letter)
        exp_list.add_if_not_empty(self.object)
        # Описания параметров вхождения
        node['parent'] = prepare_id('letter', self.letter.id)
        node['child'] = prepare_id(ObjectType.TYPEKEYS[self.object.type.id], self.object.id)

        node['id'] = f'letter_links.{self.id}'
        exp_list.append(node)
        return exp_list


class Uploads(models.Model):
    """Загрузки файлов"""
    file_name = models.CharField(max_length=20)
    upload_datetime = models.DateTimeField()
    tract_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'uploads'
        ordering = ['id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='FileUpload')
        node['file_name'] = self.file_name
        node['upload_date'] = str(self.upload_datetime)[:10]  # Оставляем только дату

        node['id'] = prepare_id('upload', self.id)
        exp_list.append(node)
        return exp_list


class UploadArcdocs(models.Model):
    """Таблица загруженных архивных документов"""
    upload = models.ForeignKey(Uploads, blank=False, null=False, on_delete=models.CASCADE)
    arcdoc = models.ForeignKey(Arcdocuments, blank=False, null=False, on_delete=models.CASCADE)
    tract_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'upload_arcdocs'
        ordering = ['id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='UploadArcdoc')
        exp_list.add_if_not_empty(self.upload)
        exp_list.add_if_not_empty(self.arcdoc)
        # Описания параметров вхождения
        node['file_upload'] = prepare_id('upload', self.upload.id)
        node['arc_doc'] = prepare_id('arcdoc', self.arcdoc.id)

        node['id'] = f'upload_arcdocs.{self.id}'
        exp_list.append(node)
        return exp_list


class Prefixes(models.Model):
    """Таблица префиксов обозначений"""
    prefix_code = models.CharField(max_length=15, null=False, blank=False, verbose_name='Префикс обозначения')
    project_code = models.CharField(max_length=15, null=False, blank=False, verbose_name='Обозначение проекта')
    description = models.CharField(max_length=100, null=True, blank=True, verbose_name='Описание префикса обозначения')
    tract_id = models.IntegerField()
    del_tract_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'prefixes'
        ordering = ['id']
        default_permissions = ()

    def to_dict(self):
        exp_list = ItemsList()  # Доработанный класс списка
        node = dict(model='CodePrefix')
        node['prefix_code'] = self.prefix_code
        node['project_code'] = self.project_code
        node['description'] = self.description
        node['id'] = f'prefixes.{self.id}'
        exp_list.append(node)
        return exp_list


class ItemsList(list):
    """Список с доработанным функционалом добавления"""

    @staticmethod
    def to_dict_checked(prop_entity):
        """Только при наличии ссылки на эксземпляр сущности вызывается ее метод"""
        if prop_entity is not None:
            return prop_entity.to_dict()
        return None

    def add_if_not_empty(self, prop_entity):
        # TODO: Сделать накопление и проверку ранее добавленных
        # Добавляет только если есть значения
        item_list = self.to_dict_checked(prop_entity)
        if item_list is not None:
            self += item_list


class Exporter():
    # Список экспортируемых сущностей
    @staticmethod
    def list_to_export():
        # Возвращает ссылки на сущности, предназначенные для экспорта
        # Нужно учитывать, что некоторые сущности через ссылки могут экспортировать другие сущности
        return DocsObject,
        # Letters, Part,
        # Tasks, TaskReferObject, TaskReferNotice, DocsTask,
        # Deliveries, DeliveryArcdocs,
        # DesignRolesNotice,
        # Arcdocuments, ArcdocLinks, ArcDocFormats, NoticeLinksArcDoc, ArchiveDocs,
        # ChangeNotice, NoticeLinksObject, NoticeRecipients, DocsNotice,
        # PropValues, DraftMaters, DesignRoles,
        # Renditions, ObjectFormats,
        # PartObject,
        # LetterLinks, DocsLetter,
        # Prefixes, Exemplar,
        # Uploads, UploadArcdocs,
        # RenditionTails,
        # ObjectToExport,
        # ObjectGroup,
        # Price,
        # History,
        # SystemUser,
        # Properties,
        # Roles,
        # Essence, Unit
