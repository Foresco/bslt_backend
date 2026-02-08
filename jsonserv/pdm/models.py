from copy import copy
import json
from django.core.exceptions import SuspiciousOperation
from django.db import models
from django.db.models import F, FilteredRelation, Max, Q
from django.db.models.functions import Coalesce
from django.conf import settings  # для обращения к настройкам
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from jsonserv.core.fileutils import get_sql_file_path
from jsonserv.core.dbutils import execute_sql_from_file
from jsonserv.core.models import (List, CodedList, Entity, Link, HistoryTrackingMixin, PeriodTrackingMixin,
                                  UserProfile, MeasureUnit, Place, Classification, UserSession, Permission,
                                  RightMixin, fn_head_key, NotDeletedObjects, check_access)

from jsonserv.pdm import signals  # Сигналы приложения


# Менеджер, возвращающий только не удаленные объекты и не объекты в заказах
class ListPartObjects(models.Manager):
    def get_queryset(self):
        return super(ListPartObjects, self).get_queryset().filter(
            dlt_sess=0,  # Не имеющие отметки об удалении
            prod_order__isnull=True  # Не связанные с заказом
        )


class PartType(RightMixin):  # Типы объектов конструкции
    part_type = models.CharField(max_length=20, null=False, primary_key=True, verbose_name='Имя типа',
                                 help_text='Имя типа(ключ)')
    type_name = models.CharField(
        max_length=25, null=False, unique=True, verbose_name='Наименование типа')
    div_name = models.CharField(
        max_length=25, null=False, verbose_name='Раздел спецификации')
    order_num = models.PositiveIntegerField(null=False, default=1, verbose_name='Порядок в списке',
                                            help_text='Порядок сортировки значения в списке')
    has_staff = models.BooleanField(
        default=False, null=False, verbose_name='Может иметь состав')
    check_states = models.BooleanField(
        default=False, null=False, verbose_name='Контролировать доступ к состояниям')
    doc_key = models.BooleanField(
        default=False, null=False, verbose_name='Признак составного ключа')
    code_join = models.BooleanField(
        default=False, null=False, verbose_name='Признак составного обозначения')
    generator = models.CharField(
        max_length=25, blank=True, null=True, verbose_name='Модуль генерации обозначений')
    start_params = models.TextField(
        null=True, blank=True, verbose_name='Параметры формирования дашборда')
    init_params = models.TextField(
        null=True, blank=True, verbose_name='Свойства по умолчанию при создании')

    @staticmethod
    def suggest(user, str_filter, int_limit, init_filter):
        """Формирование набора значений для списка подстановки"""
        if str_filter:  # Фильтрацию применяем, если указан фильтр
            items = PartType.objects.filter(type_name__icontains=str_filter)
        else:
            items = PartType.objects.all()
        items = items.order_by('order_num', 'type_name')[0:int(int_limit)]

        return list(
            map(lambda x: dict(pk=x.part_type, value=x.type_name),
                # Проверка плав доступа пользователя к каждому полученному типу
                list(filter(lambda t: check_access(t.value_right, user), items))))

    @staticmethod
    def get_or_create_item(prop_dict):
        return PartType.objects.get_or_create(part_type=prop_dict['part_type'], defaults=prop_dict)

    @staticmethod
    def get_init_params(part_type):
        """Получение параметров создания по умолчанию для типа объекта"""
        a = PartType.objects.get(part_type=part_type)
        return a.init_params

    @staticmethod
    def get_doc_key(part_type):
        return PartType.objects.get(pk=part_type).doc_key

    def __str__(self):
        return f'Тип объекта конструкции {self.type_name}'

    class Meta:
        verbose_name = "Тип объекта конструкции"
        verbose_name_plural = "Типы объектов конструкции"
        default_permissions = ()
        # permissions = [('change_parttype', 'Тип объекта конструкции. Редактирование'),
        #                ('view_parttype', 'Тип объекта конструкции. Просмотр')]


class PartState(List):  # Состояния объекта конструкции
    view_right = models.ForeignKey(Permission, on_delete=models.SET_DEFAULT, null=True, blank=True, default=None,
                                   related_name="view_part_states", verbose_name='Право на просмотр состояния')
    edit_right = models.ForeignKey(Permission, on_delete=models.SET_DEFAULT, null=True, blank=True, default=None,
                                   related_name="edit_part_states", verbose_name='Право на редактирование состояния')

    class Meta:
        verbose_name = "Состояние объекта конструкции"
        verbose_name_plural = "Состояния объектов конструкции"
        default_permissions = ()
        permissions = [  # ('change_partstate', 'Состояние объекта конструкции. Редактирование'),
            # ('view_partstate', 'Состояние объекта конструкции. Просмотр'),
            # Доступ к конкретным состояниям
            ('change_state_devel', 'Состояние Разработка. Редактирование'),
            ('view_state_devel', 'Состояние Разработка. Просмотр'),
            ('change_state_tested', 'Состояние Проверено. Редактирование'),
            ('view_state_tested', 'Состояние Проверено. Просмотр'),
            ('change_state_agreed',
             'Состояние Согласовано. Редактирование'),
            ('view_state_agreed', 'Состояние Согласовано. Просмотр'),
            ('change_state_approved',
             'Состояние Утверждено. Редактирование'),
            ('view_state_approved', 'Состояние Утверждено. Просмотр'),
            ('change_state_cancel',
             'Состояние Аннулировано. Редактирование'),
            ('view_state_cancel', 'Состояние Аннулировано. Просмотр'),
        ]


class PartSource(List):  # Источник поступления объекта конструкции
    class Meta:
        verbose_name = "Источник поступления объекта конструкции"
        verbose_name_plural = "Источники поступления объектов конструкции"
        default_permissions = ()
        # permissions = [('change_partsource', 'Источник поступления объекта конструкции. Редактирование'),
        #                ('view_partsource', 'Источник поступления объекта конструкции. Просмотр')]


class PartPreference(List):  # Предпочтительность объекта конструкции
    class Meta:
        verbose_name = "Предпочтительность объекта конструкции"
        verbose_name_plural = "Предпочтительности объектов конструкции"
        default_permissions = ()
        # permissions = [('change_partpreference', 'Предпочтительность объекта конструкции. Редактирование'),
        #                ('view_partpreference', 'Предпочтительность объекта конструкции. Просмотр')]


class PartLitera(List):  # Литера объекта конструкции
    class Meta:
        verbose_name = "Литера объекта конструкции"
        verbose_name_plural = "Литеры объектов конструкции"
        default_permissions = ()
        # permissions = [('change_partlitera', 'Литера объекта конструкции. Редактирование'),
        #                ('view_partlitera', 'Литера объекта конструкции. Просмотр')]


class PartFormat(List):  # Варианты форматов

    @staticmethod
    def get_values(user):
        """Формирование набора значений списка, отсортированных по значению"""
        return PartFormat.objects.all().order_by('list_value').values('pk', 'list_value')

    class Meta:
        verbose_name = "Формат"
        verbose_name_plural = "Форматы"
        default_permissions = ()
        permissions = [('change_partformat', 'Формат. Редактирование'),
                       ('view_partformat', 'Формат. Просмотр')]


class RenditionTail(List):  # Варианты приращений в обозначениях исполнений

    @staticmethod
    def generate_by_id(code, tail_id):
        """Формирование обозначения с приращением"""
        tail = RenditionTail.objects.get(pk=tail_id)
        return f'{code}-{tail.list_value}'

    class Meta:
        verbose_name = "Приращение к обозначению исполнения"
        verbose_name_plural = "Приращения к обозначениям исполнений"
        ordering = ('list_value',)
        default_permissions = ()
        # permissions = [('change_renditiontail', 'Приращение к обозначению исполнения. Редактирование'),
        #                ('view_renditiontail', 'Приращение к обозначению исполнения. Просмотр')]


class Stage(Entity):
    """Стадии разработки объектов конструкции"""

    class Meta:
        verbose_name = "Стадия"
        verbose_name_plural = "Стадии"
        default_permissions = ()
        permissions = [('change_stage', 'Стадия. Редактирование'),
                       ('view_stage', 'Стадия. Просмотр')]


class Role(List):
    """Наименования ролей разработчиков"""

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"
        ordering = ['order_num', 'list_value']
        default_permissions = ()
        permissions = [('change_role', 'Роль. Редактирование'),
                       ('view_role', 'Роль. Просмотр')]


class PartObject(Entity):  # Элемент конструкции
    part_type = models.ForeignKey(
        to='PartType', on_delete=models.CASCADE, verbose_name='Тип')
    title = models.CharField(max_length=250, blank=True,
                             null=True, verbose_name='Наименование')
    state = models.ForeignKey(to='PartState', on_delete=models.SET_DEFAULT, default=1, null=True, blank=True,
                              verbose_name='Состояние')
    source = models.ForeignKey(to='PartSource', on_delete=models.SET_DEFAULT, null=True, default=1,
                               verbose_name='Источник поступления')
    preference = models.ForeignKey(to='PartPreference', on_delete=models.SET_DEFAULT, default=1,
                                   verbose_name='Предпочтительность')
    abbr = models.CharField(max_length=50, null=True,
                            blank=True, verbose_name='Кратко')
    is_top = models.BooleanField(
        null=False, default=False, verbose_name='Готовое изделие')
    nom_code = models.CharField(
        max_length=15, null=True, blank=True, verbose_name='Номенклатурный код')
    unit = models.ForeignKey(MeasureUnit, related_name='measure_unit', on_delete=models.SET_NULL,
                             blank=True, null=True, verbose_name='Единица измерения')
    weight = models.FloatField(null=True, blank=True, verbose_name='Вес/Масса')
    weight_unit = models.ForeignKey(MeasureUnit, related_name='weight_unit', on_delete=models.SET_DEFAULT,
                                    default=None, blank=True, null=True, verbose_name='Единица измерения веса')
    litera = models.ForeignKey(to='PartLitera', on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name='Литера')
    surface = models.CharField(
        max_length=50, null=True, blank=True, verbose_name='Поверхность')
    origin = models.ForeignKey(to='PartObject', related_name='procreated', null=True, blank=True,
                               on_delete=models.SET_NULL, verbose_name='Источник, из которого создан')
    prod_order = models.ForeignKey(to='PartObject', related_name='order_positions', null=True, blank=True,
                                   on_delete=models.SET_NULL, verbose_name='Заказ')

    objects = NotDeletedObjects()

    @property
    def key_code(self):
        """Формирование составного ключевого атрибута для отображения в формах"""
        if self.parent and self.part_type.code_join:
            return self.code + ' ' + self.parent.code
        return self.code

    @property
    def formats(self):
        """Формирование списка форматов объекта"""

        def frm(values):
            """Формирование формата"""
            return values[1] if values[0] == 1 else "%sx%s" % values  # Количество 1 не выводим

        frmts = self.object_formats.order_by('format__list_value').values_list(
            'list_quantity', 'format__list_value')
        return ', '.join(frm(x) for x in frmts)

    @property
    def get_code(self):
        """Формирование кода с учетом обозначения родителя"""
        if self.parent and self.part_type.code_join:
            return self.code + ' ' + self.parent.code
        return self.code

    @property
    def get_state_id(self):
        """Замена пустого значения state_id на 0"""
        if self.state_id is None:
            return 0
        return self.state_id

    def is_base_rendition(self):
        """Определение, что это базовое исполнение"""
        return True if self.renditions.all() else False

    def get_caption(self):
        """Формирование понятной надписи для разных целей"""
        parent_code = None
        order_code = None
        # Проверка, что это базовое исполнение
        base_rend = '(Базовое исполнение)' if self.is_base_rendition() else ''

        if self.part_type.code_join and self.parent:
            parent_code = self.parent.code
        if self.prod_order:
            order_code = f'({self.prod_order.code})'
        return ' '.join(
            filter(None, [self.code, parent_code, self.title, order_code, base_rend, '|', self.part_type.type_name]))

    def check_same_count(self):
        """Проверка наличия объекта с таким же ключом"""
        # Присвоение уникального проверочного ключа
        self.head_key = fn_head_key(
            self.code, self.parent.code if self.parent and self.part_type.doc_key else '')
        filters = dict(head_key=self.head_key)

        if self.prod_order:
            # Дополнительно проверяем в рамках производственного заказа
            filters['prod_order'] = self.prod_order
        else:
            filters['prod_order__isnull'] = True

        # Внимание! Сейчас уникальность контролируется внутри типа PartObject
        if PartObject.objects.filter(**filters).exclude(pk=self.pk).count():
            # print(filters)
            return f'Ключевой атрибут объекта конструкции [{self.head_key}] не уникален'
        if self.nom_code:
            del filters['head_key']
            # Дополнительно поиск в номенклатурному коду
            filters['nom_code'] = self.nom_code
            if PartObject.objects.filter(**filters).exclude(pk=self.pk).count():
                return f'Номенклатурный код [{self.nom_code}] не уникален'
        return ''

    def delete(self, *args, **kwargs):
        # Удаление исполнений
        Rendition.objects.filter(rendition=self).update(
            dlt_sess=self.dlt_sess)  # Если это исполнение
        Rendition.objects.filter(parent=self).update(
            dlt_sess=self.dlt_sess)  # Если это базовое исполнение
        super().delete(*args, **kwargs)

    @staticmethod
    def get_or_create_item_in_order(origin_id, prod_order_id, crtd_sess_id):
        """Получение или создание объекта в заказе"""
        return PartObject.create_in_order(origin_id, prod_order_id,
                                          crtd_sess_id)  # Возвращаем созданный или найденный объект

    @staticmethod
    def get_or_create_item(prop_dict):
        parent_code = ''
        if 'parent' in prop_dict:
            if prop_dict['parent']:
                if prop_dict['part_type'].doc_key:
                    parent_code = prop_dict['parent'].code
        prop_dict['head_key'] = fn_head_key(prop_dict['code'], parent_code)
        # Если объект создается в производственном заказе
        if 'prod_order' in prop_dict and prop_dict['prod_order']:
            return PartObject.objects.get_or_create(head_key=prop_dict['head_key'],
                                                    prod_order=prop_dict['prod_order'],
                                                    defaults=prop_dict)
        return PartObject.objects.get_or_create(head_key=prop_dict['head_key'], prod_order=None, defaults=prop_dict)

    def create_same(self, code, crtd_sess):
        """Создание подобного объекта с новым обозначением"""
        if self.parent_id:  # Если есть регламентирующий документ или стадия
            obj = PartObject.objects.filter(head_key=fn_head_key(code), parent=self.parent)  # С учетом стадии
        else:
            obj = PartObject.objects.filter(head_key=fn_head_key(code))
        if obj:
            n = obj[0]  # Если объект с таким обозначением уже существует
        else:
            n = copy(self)
            n.origin_id = self.pk
            # Убираем идентификаторы, чтобы создался новый объект
            n.pk, n.id = None, None
            # Получение параметров создания по умолчанию
            # init_params = PartType.get_init_params(n.part_type.part_type)
            # if init_params:
            #     init_params = json.loads(init_params)  # Преобразуем в словарь
            #     for prop in init_params:
            #         setattr(n, prop, init_params[prop])
            # Добавляем новые свойства
            n.code = code
            n.state_id = 1  # Создаем всегда в состоянии Разработка
            n.crtd_sess = UserSession.get_session_by_id(crtd_sess)
            n.save()
        return n

    @staticmethod
    def suggest(user, str_filter, int_limit, init_filter):
        """Формирование набора значений для списка подстановки
        Отличается от родительского необходимостью исключения объектов из заказов"""

        # Если переданы дополнительные фильтрующие параметры, начинаем с них
        filter_params = init_filter if init_filter else dict()
        if str_filter:
            if getattr(settings, 'SEARCH_IN_MIDDLE', False):
                filter_params['head_key__contains'] = fn_head_key(
                    str_filter, '')  # Вариант в любом месте
            else:
                filter_params['head_key__startswith'] = fn_head_key(
                    str_filter, '')
        if filter_params:
            # Дополнительно поиск в номенклатурному коду
            items = PartObjectFast.objects.filter(Q(**filter_params) | Q(nom_code__startswith=str_filter))
        else:
            items = PartObjectFast.objects.all()
        items = items.order_by('rating', 'code')[0:int(int_limit)]
        # В отличие от остальных suggest добавлен еще и title
        return list(map(lambda x: dict(pk=x['pk'], value=x['code'], title=x['title']),
                        items.values('pk', 'code', 'title')))

    def replace(self, trgt_id, crtd_sess):
        """Замена одного объекта другим во всех связях"""
        sess = UserSession.get_session_by_id(crtd_sess)
        # TODO: Возможно, нужно брать все связи через related_name
        links = PartLink.objects.filter(child=self)
        for lnk in links:
            # Создание новой связи
            n = copy(lnk)
            n.child_id = trgt_id
            n.pk, n.id = None, None  # Убираем идентификаторы, чтобы создался новый объект
            n.crtd_sess = sess
            n.save()
            # Удаление существующей связи
            lnk.delete()

    def get_description(self):
        """Формирование описание объекта для отображения в строке поиска"""
        description = f'{self.code} {self.parent.code}' if self.parent else self.code
        if self.description:
            description = f'{description} {self.description}'
        if self.title:
            description = f'{description} {self.title}'
        if self.prod_order:
            description = f'{description} в заказе {self.prod_order.code}'
        return f'{self.part_type.type_name} {description}'

    def update_in_order(self, user_session_id, properties, staff, notices):
        """Обновление копии объекта в заказе на основе свойств исходного объекта"""
        # Определение идентификатора объекта-источника
        if self.origin is None:
            return {"message": "Объект не относится к заказу"}, True

        mess_txt = list()  # Тексты сообщений об изменениях
        edt_count = 0  # Счетчик выполненных изменений

        # Изменить свойства объекта-копии (наименование, масса) на основе свойств конструкторского объекта
        if properties:
            self.weight = self.origin.weight  # Вес
            self.title = self.origin.title  # Наименование
            self.edt_sess = user_session_id
            self.save()

        # Изменить состав объекта-копии на основе свойств конструкторского объекта
        if staff:
            # Получаем состав копии
            obj_staff = dict((d['child__partobject__origin_id'], d) for d in
                             PartLink.objects.filter(parent=self.pk).values('child__partobject__origin_id', 'position',
                                                                       'quantity', 'pk'))
            # Получаем состав исходного объекта
            origin_staff = dict((d['child_id'], d) for d in
                                PartLink.objects.filter(parent=self.origin_id).values('child_id', 'position', 'quantity',
                                                                                 'pk'))
            # Находим недостающие записи
            difference = list(set(origin_staff.keys()) - set(obj_staff.keys()))
            for r in difference:  # Добавляем то, чего нет в копии
                lnk_dict = dict()
                # Создаем объект
                chld_id = PartObject.get_or_create_item_in_order(r, self.prod_order_id, user_session_id)
                # Создаем связь
                lnk_dict['child'] = PartObject.objects.get(pk=chld_id)
                lnk_dict['parent'] = self  # Входит в текущий объект
                lnk_dict['quantity'] = origin_staff[r]['quantity']
                lnk_dict['position'] = origin_staff[r]['position']
                lnk_dict['crtd_sess_id'] = user_session_id
                lnk = PartLink.get_or_create_item(lnk_dict)
                edt_count += 1

            if edt_count:
                mess_txt.append(f'Добавлено в состав {edt_count}')
                edt_count = 0

            # Удаляем то, чего нет в исходном
            difference = list(set(obj_staff.keys()) - set(origin_staff.keys()))
            for r in difference:
                # Удаляем строку
                d = PartLink.objects.get(pk=obj_staff[r]['pk'])
                d.dlt_sess = user_session_id
                d.save()
                # Удаляем запись из массива
                del obj_staff[r]
                edt_count += 1

            if edt_count:
                mess_txt.append(f'Удалено из состава {edt_count}')
                edt_count = 0

            # Корректируем количество и позицию
            for r in obj_staff.keys():
                if obj_staff[r]['quantity'] != origin_staff[r]['quantity'] or obj_staff[r]['position'] != \
                        origin_staff[r][
                            'position']:
                    d = PartLink.objects.get(pk=obj_staff[r]['pk'])
                    d.quantity = origin_staff[r]['quantity']
                    d.position = origin_staff[r]['position']
                    d.edt_sess = user_session_id
                    d.save()
                    edt_count += 1

            if edt_count:
                mess_txt.append(f'Изменено в составе {edt_count}')
                edt_count = 0

        # Привязать извещения, проведенные для конструкторского объекта
        if notices:
            # Получаем извещения копии
            obj_notices = dict((d['parent_id'], d) for d in
                               NoticeLink.objects.filter(child=self.pk).values('parent_id', 'pk'))
            # Получаем извещения исходного объекта
            origin_notices = dict((d['parent_id'], d) for d in
                                  NoticeLink.objects.filter(child=self.origin.pk).values('parent_id', 'pk'))
            # Находим недостающие записи
            difference = list(set(origin_notices.keys()) - set(obj_notices.keys()))
            for r in difference:  # Добавляем то, чего нет в копии
                # Создаем связь на основе существующей
                src = NoticeLink.objects.get(pk=origin_notices[r]['pk'])
                # Создаем связь
                src.child = self  # Относится к текущему объекту
                src.pk = None
                # Две строки нужны, т.к. модель с наследованием (stackoverflow)
                src.id = None
                src._state.adding = True

                src.crtd_sess_id = user_session_id
                src.save()
                edt_count += 1

            if edt_count:
                mess_txt.append(f'Добавлено извещений {edt_count}')

        return mess_txt, False # Ошибок не было

    @staticmethod
    def create_in_order(origin_id, prod_order_id, crtd_sess_id):
        """Создание объекта в составе заказа"""
        sql_file = get_sql_file_path('pdm', 'create_order_part.sql')
        params = dict(origin_id=origin_id,
                      prod_order_id=prod_order_id, crtd_sess_id=crtd_sess_id)
        rows = execute_sql_from_file(sql_file, params, True)
        return rows[0]['object_id']

    @staticmethod
    def get_head_key(props):
        # Генерация head_code С учетом ссылки на документ У разных типов может отличаться
        # Может передаваться как словарь, так и экземпляр модели
        if type(props) is dict:
            if 'parent' in props and props['parent'] and PartType.get_doc_key(props['part_type']):
                return fn_head_key(props['code'], props['parent'].code)
            return fn_head_key(props['code'])
        else:  # Экземпляр модели
            if props.parent and PartType.get_doc_key(props.part_type.part_type):
                return fn_head_key(props.code, props.parent.code)
            else:
                return fn_head_key(props.code)

    class Meta:
        verbose_name = "Объект конструкции"
        verbose_name_plural = "Объекты конструкции"
        indexes = [
            # Для быстрого поиска объектов из заказа
            models.Index(fields=['prod_order', 'origin']),
        ]
        default_permissions = ()
        permissions = [('change_document', 'Документация. Редактирование'),
                       ('change_complex', 'Комплекс. Редактирование'),
                       ('change_assembly', 'Сборочная единица. Редактирование'),
                       ('change_detail', 'Деталь. Редактирование'),
                       ('change_standart', 'Стандартное изделие. Редактирование'),
                       ('change_other', 'Прочее изделие. Редактирование'),
                       ('change_material', 'Материал. Редактирование'),
                       ('change_complect', 'Комплект. Редактирование'),
                       ('change_sortament', 'Сортамент. Редактирование'),
                       ('change_exemplar', 'Экземпляр сортамента. Редактирование'),
                       ('change_rigging', 'Оснастка. Редактирование'),
                       ('change_tool', 'Инструмент. Редактирование'),
                       ('change_equipment', 'Оборудование. Редактирование'),
                       ('change_tare', 'Тара. Редактирование'),
                       ('change_device', 'Изделие. Редактирование'),
                       ('change_order', 'Заказ. Редактирование'),
                       ('change_select', 'Выборка. Редактирование'),
                       ('change_tpun', 'ТПУН. Редактирование'),
                       ('view_document', 'Документация. Просмотр'),
                       ('view_complex', 'Комплекс. Просмотр'),
                       ('view_assembly', 'Сборочная единица. Просмотр'),
                       ('view_detail', 'Деталь. Просмотр'),
                       ('view_standart', 'Стандартное изделие. Просмотр'),
                       ('view_other', 'Прочее изделие. Просмотр'),
                       ('view_material', 'Материал. Просмотр'),
                       ('view_complect', 'Комплект. Просмотр'),
                       ('view_sortament', 'Сортамент. Просмотр'),
                       ('view_exemplar', 'Экземпляр сортамента. Просмотр'),
                       ('view_rigging', 'Оснастка. Просмотр'),
                       ('view_tool', 'Инструмент. Просмотр'),
                       ('view_equipment', 'Оборудование. Просмотр'),
                       ('view_tare', 'Тара. Просмотр'),
                       ('view_device', 'Изделие. Просмотр'),
                       ('view_order', 'Заказ. Просмотр'),
                       ('view_select', 'Выборка. Просмотр'),
                       ('view_tpun', 'ТПУН. Просмотр')
                       ]


class ListPartObjectsNoOrderParts(models.Manager):
    """Менеджер, возвращающий только не удаленные объекты и не объекты в заказах"""
    def get_queryset(self):
        return super(ListPartObjectsNoOrderParts, self).get_queryset().filter(
            dlt_sess=0,  # Не имеющие отметки об удалении
            prod_order__isnull=True  # Не связанные с заказом
        )


class ListPartObjectsAll(models.Manager):
    """Менеджер, возвращающий только не удаленные объекты в т.ч. объекты в заказах"""
    def get_queryset(self):
        return super(ListPartObjectsAll, self).get_queryset().filter(
            dlt_sess=0  # Не имеющие отметки об удалении
        )


class PartObjectFast(models.Model):
    """Служебная модель для быстрой работы со списками объектов конструкции"""
    parent = models.ForeignKey(to='core.Entity', related_name='related_objects_fast', on_delete=models.SET_DEFAULT,
                               default=None, blank=True, null=True, verbose_name='Ссылка на документ')
    code = models.CharField(max_length=200, null=False,
                            blank=False, verbose_name='Обозначение')
    description = models.TextField(
        blank=True, null=True, verbose_name='Описание')
    group = models.ForeignKey(to='core.Classification', related_name='group_members_fast', on_delete=models.SET_DEFAULT,
                              default=None, blank=True, null=True, verbose_name='Классификационная группа')
    part_type = models.ForeignKey(
        to='PartType', on_delete=models.CASCADE, verbose_name='Тип')
    title = models.CharField(max_length=200, blank=True,
                             null=True, verbose_name='Наименование')
    nom_code = models.CharField(
        max_length=15, null=True, blank=True, verbose_name='Номенклатурный код')
    head_key = models.CharField(max_length=400, editable=False,
                                null=False, blank=True, verbose_name='Уникальный ключ')
    prod_order = models.ForeignKey(to='PartObject', related_name='order_positions_fast', null=True, blank=True,
                                   on_delete=models.SET_NULL, verbose_name='Заказ')
    rating = models.PositiveIntegerField(blank=True, null=True, default=0,
                                         verbose_name='Рейтинг упоминаний объекта в связях')
    # Идентификатор удалившей транзакции
    dlt_sess = models.IntegerField(null=False, default=0, db_index=True)
    ei = models.CharField(max_length=10, null=True,
                          verbose_name='Краткое наименование ЕИ')

    objects = ListPartObjectsNoOrderParts()  # Менеджер для списков
    objects_all = ListPartObjectsAll()  # Менеджер для списков с входящими в заказы

    class Meta:
        ordering = ['code', 'parent__code']
        verbose_name = "Объект конструкции быстро"
        verbose_name_plural = "Объекты конструкции быстро"
        managed = False
        db_table = 'vw_partobject'
        default_permissions = ()


class PartObjectAll(PartObjectFast):
    """Модель для доступа к объектам конструкции, включая объекты из заказов"""

    @staticmethod
    def suggest(user, str_filter, int_limit, init_filter):
        """Формирование набора значений для списка подстановки
        Отличается от основного наличием объектов из заказов"""

        def cnct(code, prod_order_code):
            """Формирование обозначения из двух полей Обозначение и Заказ"""
            if prod_order_code:
                return f'{code} ({prod_order_code})'
            return code

        # Если переданы дополнительные фильтрующие параметры, начинаем с них
        filter_params = init_filter if init_filter else dict()
        if str_filter:
            if getattr(settings, 'SEARCH_IN_MIDDLE', False):
                filter_params['head_key__contains'] = fn_head_key(
                    str_filter, '')  # Вариант в любом месте
            else:
                filter_params['head_key__startswith'] = fn_head_key(
                    str_filter, '')
        if filter_params:
            # Дополнительно поиск в номенклатурному коду
            items = PartObjectFast.objects_all.filter(Q(**filter_params) | Q(nom_code__startswith=str_filter))
        else:
            items = PartObjectFast.objects_all.all()
        items = items.order_by('rating', 'code')[0:int(int_limit)]
        # В отличие от остальных suggest добавлен еще и title
        return list(map(lambda x: dict(pk=x['pk'], value=cnct(x['code'], x['prod_order__code']),
                                       title=x['title']),
                        items.values('pk', 'code', 'title', 'prod_order__code')))

    class Meta:
        ordering = ['code', 'parent__code', ]
        verbose_name = "Объект конструкции из заказа"
        verbose_name_plural = "Объекты конструкции из заказов"
        managed = False
        db_table = 'vw_partobject'
        default_permissions = ()


class Designer(HistoryTrackingMixin):  # Разработчики
    designer_profile = models.OneToOneField(UserProfile, on_delete=models.SET_NULL, null=True,
                                            verbose_name='Профиль пользователя')
    designer = models.CharField(
        max_length=100, null=False, blank=False, verbose_name='Фамилия И.О. разработчика')
    selectable = models.BooleanField(
        default=True, null=False, blank=False, verbose_name='Может выбираться в ролях')

    @staticmethod
    def get_or_create_item(prop_dict):
        return Designer.objects.get_or_create(designer=prop_dict['designer'], defaults=prop_dict)

    @staticmethod
    def suggest(user, str_filter, int_limit, init_filter):
        """Формирование набора значений для списка подстановки"""
        if 'role' in init_filter:  # Если указана роль для сортировки
            a = Designer.objects.annotate(
                designer_rating=FilteredRelation(
                    'designerrating', condition=Q(designerrating__role=init_filter['role'])),
                rating=Coalesce('designer_rating__rating', 0)
            ).order_by('-rating', 'designer')  # Сортируем по рейтингу
        else:
            a = Designer.objects.order_by('designer')
        if str_filter:  # Фильтрацию применяем, если указан фильтр
            if getattr(settings, 'SEARCH_IN_MIDDLE', False):
                # Вариант в любом месте
                items = a.filter(designer__icontains=str_filter)
            else:
                items = a.filter(designer__istartswith=str_filter)
        else:
            items = a.all()
        items = items.filter(selectable=True)[0:int(int_limit)]
        return list(
            map(lambda x: dict(pk=x['pk'], value=x['designer']), items.values('pk', 'designer')))

    def __str__(self):
        return self.designer

    def get_caption(self):
        """Формирование понятной надписи для разных целей"""
        return f'{self.designer} | Разработчик'

    @staticmethod
    def get_by_user(user_id):
        """Получение соответствующего разработчика по идентификатору пользователя"""
        return Designer.objects.filter(designer_profile__user_id=user_id).values(
            designer__pk=F('pk'),
            designer__designer=F('designer')
        )

    class Meta:
        ordering = ['designer']
        verbose_name = "Разработчик"
        verbose_name_plural = "Разработчики"
        default_permissions = ()
        permissions = [('change_designer', 'Разработчик. Редактирование'),
                       ('view_designer', 'Разработчик. Просмотр')]


class DesignRole(HistoryTrackingMixin):  # Роли, выполненные пользователями у объектов
    subject = models.ForeignKey(Entity, related_name='design_roles', on_delete=models.CASCADE,
                                blank=False, null=False, verbose_name='Ссылка на объект')
    role = models.ForeignKey(Role, related_name='role_done', on_delete=models.CASCADE,
                             blank=False, null=False, verbose_name='Ссылка на роль')
    designer = models.ForeignKey(Designer, on_delete=models.CASCADE, null=False, blank=True,
                                 verbose_name='Разработчик')
    role_date = models.DateField(
        verbose_name='Дата выполнения', null=True, blank=True)
    comment = models.TextField(
        blank=True, null=True, verbose_name='Примечание')

    def __str__(self):
        return f'{self.designer} выполнил {self.role} для {self.subject}'

    @staticmethod
    def get_or_create_item(prop_dict):
        return DesignRole.objects.get_or_create(subject=prop_dict['subject'], role=prop_dict['role'],
                                                defaults=prop_dict)

    def check_same_count(self):
        """Проверка наличия объекта такой роли """
        q = DesignRole.objects.filter(subject=self.subject, role=self.role)
        if self.pk:
            # Саму связь исключаем из проверки
            q = q.exclude(pk=self.pk)
        if q.count():
            return True
        return False

    def save(self, *args, **kwargs):
        if self.dlt_sess:  # Если это удаление записи
            DesignerRating.decrease(self.designer, self.role)
        else:
            # Проверить отсутствие повтора роли
            if self.check_same_count():
                raise ValidationError('Данная роль уже есть у объекта')
            if self.pk:  # Если это существующая запись
                old = DesignRole.objects.get(pk=self.pk)
                if old.designer != self.designer or old.role != self.role:  # Если что-то поменялось
                    # Уменьшаем рейтинг предыдущего дизайнера
                    DesignerRating.decrease(old.designer, old.role)
                    # Увеличиваем рейтинг у нового
                    DesignerRating.increase(self.designer, self.role)
            else:
                DesignerRating.increase(self.designer, self.role)
        super(DesignRole, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Роль разработчика"
        verbose_name_plural = "Роли разработчиков"
        default_permissions = ()
        permissions = [('change_designrole', 'Роль разработчика. Редактирование'),
                       ('view_designrole', 'Роль разработчика. Просмотр')]


class DesignerRating(models.Model):
    """Рейтинги разработчика по ролям"""
    designer = models.ForeignKey(
        Designer, null=False, on_delete=models.CASCADE, verbose_name="Разработчик")
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, null=False, verbose_name='Выполненная роль')
    rating = models.PositiveIntegerField(
        default=1, null=False, verbose_name="Количество выполненных ролей")

    def __str__(self):
        return f'{self.designer} выполнил {self.role} {self.rating} раз'

    # Работа с рейтингами пользователей
    @staticmethod
    def increase(designer, role):
        # Увеличение рейтинга пользователя по роли
        r = DesignerRating.objects.filter(designer=designer, role=role).first()
        if r:
            r.rating = F('rating') + 1
            r.save()  # Обновляем существующую запись
        else:
            n = DesignerRating(designer=designer, role=role)
            n.save()  # Создаем новую запись

    @staticmethod
    def decrease(designer, role):
        # Уменьшение рейтинга пользователя по роли
        r = DesignerRating.objects.filter(designer=designer, role=role).first()
        if r:
            r.rating = F('rating') - 1
            r.save()  # Обновляем существующую запись

    class Meta:
        verbose_name = "Рейтинг разработчика"
        verbose_name_plural = "Рейтинги разработчиков"
        constraints = [
            models.UniqueConstraint(
                fields=('designer', 'role'), name='unique_designer_role')
        ]
        default_permissions = ()
        # permissions = [('change_designerrating', 'Рейтинг разработчика. Редактирование'),
        #                ('view_designerrating', 'Рейтинг разработчика. Просмотр')]


class Section(List):  # Раздел спецификации
    class Meta:
        verbose_name = "Раздел спецификации"
        verbose_name_plural = "Разделы спецификации"
        default_permissions = ()
        permissions = [('change_section', 'Раздел спецификации. Редактирование'),
                       ('view_section', 'Раздел спецификации. Просмотр')]


class PartLink(Link):  # Связь Входит в
    draft_zone = models.CharField(
        max_length=5, null=True, blank=True, verbose_name='Зона')
    position = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Позиция')
    reg_quantity = models.FloatField(
        null=True, blank=True, verbose_name='Количество на регулировку')
    # sin_quantity = models.FloatField(null=True, blank=True, verbose_name='Количество свидетель')
    unit = models.ForeignKey(MeasureUnit, related_name='in_partlinks', on_delete=models.SET_NULL,
                             blank=True, null=True, verbose_name='Единица измерения количества')
    to_replace = models.TextField(
        blank=True, null=True, verbose_name='Заменяемые позиции')
    first_use = models.BooleanField(
        blank=False, null=False, default=False, verbose_name='Первое применение')
    not_buyed = models.BooleanField(
        blank=False, null=False, default=False, verbose_name='Не покупать')
    section = models.ForeignKey(to='Section', on_delete=models.SET_DEFAULT, default=None, blank=True, null=True,
                                verbose_name='Раздел спецификации')

    # Текст сообщения об ошибке при добавлении
    same_message = 'Повтор входящего объекта или позиции'

    @staticmethod
    def get_staff_queryset():
        """Получение queryset с составом объектов. Вынесен из-за сложной сортировки"""
        return PartLink.objects.all().order_by(
            'child__partobject__part_type__order_num',  # В соответствии с типом объекта
            # Без номера позиции помещаем в начало списка
            Coalesce(F('position'), 0),
            'child__code'
        )

    def check_same_count(self):
        """Проверка наличия такого же объекта или позиции в составе"""
        if self.position:
            return PartLink.objects.filter(Q(parent=self.parent, child=self.child)
                                           | Q(parent=self.parent, position=self.position)).exclude(pk=self.pk).count()
        return PartLink.objects.filter(parent=self.parent, child=self.child).exclude(pk=self.pk).count()

    class Meta:
        verbose_name = "Связь Входит в"
        verbose_name_plural = "Связи Входит в"
        default_permissions = ()
        permissions = [('change_partlink', 'Связь Входит в. Редактирование'),
                       ('view_partlink', 'Связь Входит в. Просмотр')]

    class BasaltaProps:
        """Подкласс для хранения специфических атрибутов для системы Базальта"""
        track_links = True  # В этой модели нужно отслеживать связи при замене экземпляра (используя метод replace)
        # В этой модели нужно копировать связи при создании подобного (используя метод create_same)
        same_links = True

    def __str__(self):
        return self.child.code + ' входит в ' + self.parent.code


class NoticeType(CodedList):  # Типы извещений согласно ГОСТ 2.503-90
    class Meta:
        verbose_name = "Тип извещения"
        verbose_name_plural = "Типы извещений"
        default_permissions = ()
        # permissions = [('change_noticetype', 'Тип извещения. Редактирование'),
        #                ('view_noticetype', 'Тип извещения. Просмотр')]


class NoticeReason(CodedList):  # Причины выпуска извещений
    class Meta:
        verbose_name = "Причина выпуска извещения"
        verbose_name_plural = "Причины выпуска извещений"
        default_permissions = ()
        # permissions = [('change_noticereason', 'Причина выпуска извещения. Редактирование'),
        #                ('view_noticereason', 'Причина выпуска извещения. Просмотр')]


class Notice(Entity):  # Данные об извещениях об изменениях
    notice_type = models.ForeignKey(to='NoticeType', on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name='Тип извещения')
    notice_date = models.DateField(
        verbose_name='Дата выпуска извещения', null=False, blank=False)
    reason = models.ForeignKey(to='NoticeReason', on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name='Причина выпуска извещения')
    reserve = models.CharField(
        max_length=100, null=True, blank=True, verbose_name='Указания о заделе')
    valid_date = models.DateField(
        verbose_name='Срок действия', null=True, blank=True)
    approve_date = models.DateField(
        verbose_name='Дата утверждения', null=True, blank=True)
    deadline = models.DateField(
        verbose_name='Срок проведения изменений', null=True, blank=True)
    urgently = models.BooleanField(
        verbose_name='Срочно', null=False, blank=False, default=False)
    directions = models.CharField(
        max_length=100, null=True, blank=True, verbose_name='Указания о внедрении')
    usages = models.TextField(null=True, blank=True,
                              verbose_name='Применяемость')
    attachment = models.TextField(
        blank=True, null=True, verbose_name='Приложение')
    state = models.ForeignKey(to='PartState', on_delete=models.SET_DEFAULT, null=True, blank=True, default=1,
                              verbose_name='Состояние')

    def __str__(self):
        return "{} от {}".format(self.code, self.notice_date)

    class Meta:
        verbose_name = "Извещение об изменении"
        verbose_name_plural = "Извещения об изменениях"
        ordering = ['-notice_date', '-approve_date', 'code']
        default_permissions = ()
        permissions = [('change_notice', 'Извещение об изменении. Редактирование'),
                       ('view_notice', 'Извещение об изменении. Просмотр')]


class ChangeType(List):  # Типы изменений по извещению
    class Meta:
        verbose_name = "Тип изменения"
        verbose_name_plural = "Типы изменений"
        default_permissions = ()
        # permissions = [('change_changetype', 'Тип изменения. Редактирование'),
        #                ('view_changetype', 'Тип изменения. Просмотр')]


class NoticeLink(Link):  # Данные о связях извещений с объектами
    old = models.ForeignKey(to='PartObject', related_name='old_entity', on_delete=models.SET_DEFAULT,
                            default=None, blank=True, null=True, verbose_name='Старый объект')
    change_num = models.PositiveIntegerField(
        blank=True, null=True, verbose_name='Номер изменения')
    change_type = models.ForeignKey(to='ChangeType', on_delete=models.SET_NULL, blank=True, null=True,
                                    verbose_name='Тип изменения')
    is_done = models.BooleanField(
        blank=False, null=False, default=False, verbose_name='Признак проведения изменений')

    def __str__(self):
        return f"{self.child.code} изменяется по {self.parent}"

    def link_trace(self, edt_sess):
        """Обработка проведения извещения"""
        if self.is_done:
            return False  # Над проведенным извещением нельзя ничего делать
        else:
            if self.child.partobject.part_type_id == 'order' and self.child.partobject.get_state_id < 4:  # Это заказ и он не утвержден
                # Обработка файлов у заказа
                ntc = self.parent.notice  # Извещение
                docs = ntc.notice_document_versions.all()  # Связанные с извещением версии файлов
                if docs:
                    for doc in docs:
                        doc.up_order_version(self.child, edt_sess)  # Обновляем версии файлов у заказа
        return True  # Можно продолжить изменения

    class Meta:
        verbose_name = "Объект по извещению"
        verbose_name_plural = "Объекты по извещениям"
        default_permissions = ()
        permissions = [('change_noticelink', 'Объект по извещению. Редактирование'),
                       ('view_noticelink', 'Объект по извещению. Просмотр')]


class NoticeRecipient(Link):  # Данные о связях извещений с подразделениями получателями
    is_sent = models.BooleanField(
        blank=False, null=False, default=False, verbose_name='Признак отправки')

    def __str__(self):
        return f"{self.child.code} получает {self.parent.code}"

    class Meta:
        verbose_name = "Получатель извещения"
        verbose_name_plural = "Получатели по извещений"
        default_permissions = ()
        permissions = [('change_noticerecipient', 'Получатель извещения. Редактирование'),
                       ('view_noticerecipient', 'Получатель извещения. Просмотр')]


class DesignMater(Link):  # Данные о конструкторских материалах

    objects = NotDeletedObjects()

    def save(self, *args, **kwargs):
        """При создании новой записи старую надо удалять"""
        if not self.pk:  # Это новая запись
            cur = DesignMater.objects.filter(parent=self.parent)
            cur.update(dlt_sess=self.crtd_sess.id)
        super(DesignMater, self).save(*args, **kwargs)

    @staticmethod
    def is_exists(parent, child):
        # Проверка существования связи
        if DesignMater.objects.filter(parent_id=parent, child_id=child).count() > 0:
            return True
        return False

    def __str__(self):
        return f"{self.parent} конструкторский материал {self.child}"

    class BasaltaProps:
        """Подкласс для хранения специфических атрибутов для системы Базальта"""
        track_links = True  # В этой модели нужно отслеживать связи при замене экземпляра (используя метод replace)
        # В этой модели нужно копировать связи при создании подобного (используя метод create_same)
        same_links = True

    class Meta:
        verbose_name = "Конструкторский материал"
        verbose_name_plural = "Конструкторские материалы"
        default_permissions = ()
        permissions = [('change_designmater', 'Конструкторский материал. Редактирование'),
                       ('view_designmater', 'Конструкторский материал. Просмотр')]


class DesignMaterFast(models.Model):
    """Служебная модель для быстрой работы с конструкторскими материалами"""
    parent = models.ForeignKey(to='core.Entity', related_name='design_mater', on_delete=models.SET_DEFAULT,
                               default=None, blank=True, null=True, verbose_name='Ссылка на объект')
    child = models.ForeignKey(to='core.Entity', related_name='design_objects', on_delete=models.SET_DEFAULT,
                              default=None, blank=True, null=True, verbose_name='Ссылка на материал')

    class Meta:
        verbose_name = "Конструкторский материал быстро"
        verbose_name_plural = "Конструкторские материалы быстро"
        managed = False
        db_table = 'vw_designmater'
        default_permissions = ()


class Rendition(HistoryTrackingMixin):  # Исполнения
    parent = models.ForeignKey(to='PartObject', related_name='renditions', on_delete=models.CASCADE,
                               blank=False, null=False, verbose_name='Ссылка на объект')
    rendition = models.ForeignKey(to='PartObject', related_name='tail_rendition', on_delete=models.CASCADE,
                                  blank=False, null=False, verbose_name='Ссылка на объект')
    tail = models.ForeignKey(to='RenditionTail', on_delete=models.CASCADE,
                             blank=False, null=False, verbose_name='Ссылка на приращение')

    def __str__(self):
        return "{} исполнение {}".format(self.rendition, self.parent)

    @staticmethod
    def get_or_create_item(prop_dict):
        return Rendition.objects.get_or_create(rendition=prop_dict['rendition'], defaults=prop_dict)

    @staticmethod
    def get_renditions(parent_id):
        """Получение всех исполнений базового исполнения"""
        try:  # Определяем, принадлежит ли объект к классу PartObject
            base = PartObject.objects.get(pk=parent_id)
            return base.renditions.all()  # Получаем все исполнения объекта
        except ObjectDoesNotExist:  # Это не PartObject
            None

    def save(self, *args, **kwargs):
        """При создании исполнения ему нужно копировать 
        ссылки на все файлы базового исполнения
        роли розработчиков от базового исполнения"""
        signals.copy_file_links_signal.send(
            sender='rendition', parent=self.parent, child=self.rendition)
        signals.copy_design_roles_signal.send(
            sender='rendition', parent=self.parent, child=self.rendition)
        super(Rendition, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Исполнение"
        verbose_name_plural = "Исполнения"
        default_permissions = ()
        permissions = [('change_rendition', 'Исполнение. Редактирование'),
                       ('view_rendition', 'Исполнение. Просмотр')]


class PartObjectFormat(HistoryTrackingMixin):  # Форматы объектов
    part_object = models.ForeignKey(to='core.Entity', on_delete=models.CASCADE, blank=False, null=False,
                                    related_name='object_formats', verbose_name='Ссылка на объект')
    format = models.ForeignKey(to='PartFormat', on_delete=models.CASCADE, blank=False, null=False,
                               verbose_name='Ссылка на формат')
    list_quantity = models.PositiveIntegerField(blank=False, null=False, default=1,
                                                verbose_name='Количество листов')
    order_num = models.PositiveIntegerField(
        null=False, blank=False, default=0, verbose_name='Порядок в перечне')

    @staticmethod
    def get_or_create_item(prop_dict):
        return PartObjectFormat.objects.get_or_create(part_object=prop_dict['part_object'], format=prop_dict['format'],
                                                      defaults=prop_dict)

    @staticmethod
    def get_next_order_num(part_object):
        """Определение следующего порядкового номера"""
        order_max = PartObjectFormat.objects.filter(
            part_object=part_object).aggregate(Max('order_num'))
        if order_max['order_num__max']:
            return order_max['order_num__max'] + 1  # Следующий
        return 1

    @staticmethod
    def create_same(source_item, target_item, user_session):
        """Создание аналогичных источнику связей"""
        links = PartObjectFormat.objects.filter(part_object=source_item.id)
        cnt = 0
        usess = UserSession.get_session_by_id(user_session)
        for link in links:
            new_link = copy(link)  # Создание новой связи
            # Убираем идентификаторы, чтобы создался новый объект
            new_link.pk, new_link.id = None, None
            # Добавляем новые свойства
            new_link.part_object = target_item
            new_link.crtd_sess = usess
            new_link.save()
            cnt += 1
        return cnt

    def save(self, *args, **kwargs):
        # Расчет порядка следования операции
        if not self.order_num:
            self.order_num = PartObjectFormat.get_next_order_num(
                self.part_object)
        super(PartObjectFormat, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.part_object} имеет формат {self.list_quantity}x{self.format}"

    class Meta:
        verbose_name = "Формат объекта"
        verbose_name_plural = "Форматы объектов"
        default_permissions = ()
        permissions = [('change_partobjectformat', 'Формат объекта. Редактирование'),
                       ('view_partobjectformat', 'Формат объекта. Просмотр')]

    class BasaltaProps:
        """Подкласс для хранения специфических атрибутов для системы Базальта"""
        same_links = True  # В этой модели нужно копировать связи при создании подобного (используя метод create_same)


class TypeSizeMater(Link):  # Данные о материале экземпляра сортамента
    def __str__(self):
        return f"{self.child} изготавливается из материала {self.parent}"

    class Meta:
        verbose_name = "Материал экземпляра сортамента"
        verbose_name_plural = "Материалы экземпляров сортаментов"
        default_permissions = ()
        permissions = [('change_typesizemater', 'Материал экземпляра сортамента. Редактирование'),
                       ('view_typesizemater', 'Материал экземпляра сортамента. Просмотр')]


class TypeSizeSort(Link):  # Данные о сортаменте экземпляра сортамента
    thickness = models.FloatField(
        verbose_name='Толщина', null=True, blank=True)
    width = models.FloatField(verbose_name='Ширина', null=True, blank=True)
    wall = models.FloatField(
        verbose_name='Толщина стенки', null=True, blank=True)
    unit = models.ForeignKey(MeasureUnit, related_name='size_unit', on_delete=models.SET_DEFAULT,
                             default=1, blank=True, null=True, verbose_name='Единица измерения размеров')
    typesize = models.CharField(
        max_length=12, null=True, blank=True, verbose_name='Типоразмер')

    def __str__(self):
        return "{} относится к сортаменту {}".format(self.child, self.parent)

    class Meta:
        verbose_name = "Сортамент экземпляра сортамента"
        verbose_name_plural = "Сортаменты экземпляров сортаментов"
        default_permissions = ()
        permissions = [('change_typesizesort', 'Сортамент экземпляра сортамента. Редактирование'),
                       ('view_typesizesort', 'Сортамент экземпляра сортамента. Просмотр')]


class NormUnit(models.Model):
    """Единицы нормирования"""
    multiplicator = models.PositiveIntegerField(
        null=False, unique=True, verbose_name="Единица нормирования")

    def __str__(self):
        return f"Нормирование на {self.multiplicator}"

    @staticmethod
    def get_or_create_item(prop_dict):
        return NormUnit.objects.get_or_create(multiplicator=prop_dict['multiplicator'], defaults=prop_dict)

    class Meta:
        verbose_name = "Единица нормирования"
        verbose_name_plural = "Единицы нормирования"
        default_permissions = ()
        # permissions = [('change_normunit', 'Единица нормирования. Редактирование'),
        #                ('view_normunit', 'Единица нормирования. Просмотр')]


class Billet(Link):
    """Заготовки"""
    tp_row = models.ForeignKey(to='TPRow', on_delete=models.SET_NULL, blank=True, null=True,
                               verbose_name='Строка технологического процесса')
    billet_name = models.CharField(max_length=15, null=False, blank=False, default='Основная',
                                   verbose_name='Наименование заготовки')
    is_active = models.BooleanField(
        default=False, verbose_name='Признак активности')
    billet_size = models.CharField(max_length=15, null=True, blank=True, default=None,
                                   verbose_name='Размер заготовки')
    alt_size = models.CharField(max_length=15, null=True, blank=True, default=None,
                                verbose_name='Размер заготовки для документов')
    object_quantity = models.SmallIntegerField(
        null=False, blank=False, default=1, verbose_name='Объектов из заготовки')
    billet_quantity = models.FloatField(
        null=True, blank=True, default=None, verbose_name='Заготовок на объект')
    weight = models.FloatField(
        null=True, blank=True, default=None, verbose_name='Черный вес')
    unit = models.ForeignKey(MeasureUnit, on_delete=models.SET_NULL, blank=True, null=True,
                             verbose_name='Единица измерения нормы')
    source = models.ForeignKey(PartSource, on_delete=models.SET_NULL, blank=True, null=True,
                               verbose_name='Источник поступления')
    not_count = models.BooleanField(
        default=False, verbose_name='Не учитывать норму')

    class Meta:
        verbose_name = "Заготовка"
        verbose_name_plural = "Заготовки"
        default_permissions = ()
        permissions = [('change_billet', 'Заготовка. Редактирование'),
                       ('view_billet', 'Заготовка. Просмотр')]


class RoutePoint(HistoryTrackingMixin):
    """Элементы производственных маршрутов"""
    route = models.ForeignKey(to='Route', null=False, blank=False, on_delete=models.CASCADE,
                              related_name='route_points', verbose_name='Производственный маршрут')
    next_point = models.ForeignKey(to='RoutePoint', null=True, blank=True, on_delete=models.SET_NULL, default=None,
                                   verbose_name='Следующий элемент маршрута')
    place = models.ForeignKey(Place, null=False, blank=False, on_delete=models.CASCADE,
                              verbose_name='Производственное подразделение')
    order_num = models.SmallIntegerField(
        null=True, blank=True, verbose_name='Порядковый номер')
    comment = models.CharField(
        max_length=100, null=True, blank=True, verbose_name='Примечание')

    @staticmethod
    def get_or_create_item(prop_dict):
        return RoutePoint.objects.get_or_create(route=prop_dict['route'], place=prop_dict['place'], defaults=prop_dict)

    @staticmethod
    def get_next_order_num(route):
        """Определение следующего порядкового номера"""
        order_max = RoutePoint.objects.filter(
            route=route).aggregate(Max('order_num'))
        if order_max['order_num__max']:
            return order_max['order_num__max'] + 1  # Следующий
        return 1

    def save(self, *args, **kwargs):
        # Расчет порядка следования элемента маршрута
        if not self.order_num:
            self.order_num = RoutePoint.get_next_order_num(self.route)
        super(RoutePoint, self).save(*args, **kwargs)

    def create_same(self, route, crtd_sess):
        """Создание подобного элемента маршрута для другого маршрута"""
        n = copy(self)
        n.route = route
        # Убираем идентификаторы, чтобы создался новый объект
        n.pk, n.id = None, None
        n.crtd_sess = UserSession.get_session_by_id(crtd_sess)
        n.save()
        # Создание строк элемента маршрута
        for tpr in self.point_tp_rows.filter(parent__isnull=True):
            tpr.create_same(n, None, crtd_sess)
        return n

    def delete(self, *args, **kwargs):
        # Дополнительная обработка удаления строки с удалением входящих
        super(RoutePoint, self).delete(*args, **kwargs)

        # Если удаление прошло нормально, то удаляем подчиненные строки
        for row in self.point_tp_rows.filter(dlt_sess=0):
            # TODO: Удалять только операции, остальное удалится при удалении операций (пока так для надежности)
            row.dlt_sess = self.dlt_sess  # Добавляем пометку удаления
            row.delete(*args, **kwargs)

    def __str__(self):
        return f"Элемент {self.place} в маршруте {self.route} ({self.pk})"

    class Meta:
        verbose_name = "Элемент производственного маршрута"
        verbose_name_plural = "Элементы производственных маршрутов"
        default_permissions = ()
        permissions = [('change_routepoint', 'Элемент производственного маршрута. Редактирование'),
                       ('view_routepoint', 'Элемент производственного маршрута. Просмотр')]


class RouteState(List):
    """Варианты состояний производственных маршрутов"""

    class Meta:
        verbose_name = "Состояние производственного маршрута"
        verbose_name_plural = "Состояния производственных маршрутов"
        default_permissions = ()
        # permissions = [('change_routestate', 'Состояние производственного маршрута. Редактирование'),
        #                ('view_routestate', 'Состояние производственного маршрута. Просмотр')]


class Route(HistoryTrackingMixin, PeriodTrackingMixin):
    """Производственные маршруты"""
    subject = models.ForeignKey(PartObject, null=False, blank=False, on_delete=models.CASCADE,
                                related_name="routes", verbose_name='Изготавливаемы объект')
    route_name = models.CharField(max_length=15, null=False, blank=False, default='Основной',
                                  verbose_name='Наименование маршрута')
    process_code = models.CharField(
        max_length=30, null=True, blank=True, verbose_name='Код техпроцесса')
    group_route = models.ForeignKey(to='Route', null=True, blank=True, on_delete=models.CASCADE,
                                    verbose_name='Групповой маршрут')
    var_code = models.CharField(
        max_length=5, null=True, blank=True, verbose_name='Код варианта')
    billet = models.ForeignKey(to='Billet', null=True, blank=True, on_delete=models.SET_NULL, default=None,
                               verbose_name='Заготовка')
    # time_norm = models.FloatField(null=False, blank=False, verbose_name='Норма времени')
    # time_norm_cont = models.FloatField(null=False, blank=False, verbose_name='Норма времени контрактная')
    # time_unit = models.ForeignKey(MeasureUnit, on_delete=models.SET_NULL, blank=True, null=True,
    # verbose_name='Единица измерения нормы')
    min_party = models.SmallIntegerField(
        null=False, blank=False, default=1, verbose_name='Минимальная партия')
    norm_unit = models.ForeignKey(NormUnit, on_delete=models.SET_DEFAULT, default=1,
                                  blank=True, null=True, verbose_name='Единица нормирования')
    comment = models.CharField(
        max_length=50, null=True, blank=True, verbose_name='Примечание')
    first_point = models.ForeignKey(RoutePoint, on_delete=models.SET_NULL, default=None, related_name='starts_route',
                                    blank=True, null=True, verbose_name='Первый элемент маршрута')
    state = models.ForeignKey(to='RouteState', on_delete=models.SET_DEFAULT, default=1, blank=True, null=True,
                              verbose_name='Состояние')
    is_active = models.BooleanField(
        default=True, blank=False, null=False, verbose_name="Признак активности маршрута")

    @staticmethod
    def get_or_create_item(prop_dict):
        return Route.objects.get_or_create(subject=prop_dict['subject'], route_name=prop_dict['route_name'],
                                           defaults=prop_dict)

    @staticmethod
    def get_active(subject):
        """Получение активного маршрута для указанного объекта"""
        ar = Route.objects.filter(subject=subject, is_active=True)
        return ar[0] if ar else None

    def save(self, *args, **kwargs):
        # Заполнение признака активности
        ar = Route.objects.filter(
            subject=self.subject, is_active=True).exclude(pk=self.pk)
        if self.is_active:
            # Снимаем активность у остальных маршрутов
            ar.update(is_active=False)
        else:
            if ar.count() == 0:  # Если активных маршрутов нет, то текущий будет активным
                self.is_active = True
        super(Route, self).save(*args, **kwargs)
        if self.is_active:
            # Отправляем сигнал об использовании данного маршрута в связях
            signals.use_default_route_signal.send(
                sender='route', child=self.subject, route=self)

    def create_same(self, obj, crtd_sess):
        """Создание подобного маршрута для другого объекта"""
        e_route = obj.routes.filter(route_name=self.route_name)
        if e_route:
            # Если маршрут с таким именем у объекта уже существует
            n = e_route[0]
        else:
            n = copy(self)
            n.subject = obj
            # Убираем идентификаторы, чтобы создался новый объект
            n.pk, n.id = None, None
            n.crtd_sess = UserSession.get_session_by_id(crtd_sess)
            n.save()
            # Создание элементов маршрута
            for rp in self.route_points.all():
                rp.create_same(n, crtd_sess)
        return n

    def delete(self, *args, **kwargs):
        # Дополнительная обработка с удалением входящих
        super(Route, self).delete(*args, **kwargs)

        # Если удаление прошло нормально, то удаляем подчиненные строки
        for row in self.route_points.filter(dlt_sess=0):
            row.dlt_sess = self.dlt_sess  # Добавляем пометку удаления
            row.delete(*args, **kwargs)

    def __str__(self):
        return f"Маршрут {self.route_name} для {self.subject} ({self.pk})"

    class Meta:
        verbose_name = "Производственный маршрут"
        verbose_name_plural = "Производственные маршруты"
        default_permissions = ()
        permissions = [('change_route', 'Производственный маршрут. Редактирование'),
                       ('view_route', 'Производственный маршрут. Просмотр')]


class Operation(HistoryTrackingMixin):  # Технологические (производственные) операции
    operation_name = models.CharField(
        max_length=40, null=False, blank=False, verbose_name='Наименование операции')
    full_name = models.CharField(max_length=150, blank=True, null=True, default=None,
                                 verbose_name='Полное наименование операции')
    operation_code = models.CharField(max_length=7, blank=True, null=True, default=None,
                                      verbose_name='Код операции')
    group = models.ForeignKey(Classification, related_name='group_operations', on_delete=models.SET_DEFAULT,
                              default=None, blank=True, null=True, verbose_name='Классификационная группа')
    # instruction = models.CharField(max_length=20, blank=True, null=True, default=None,
    #                                verbose_name='Номер инструкции')
    min_norm = models.FloatField(
        blank=True, null=True, default=None, verbose_name='Минимальная норма времени')
    max_norm = models.FloatField(
        blank=True, null=True, default=None, verbose_name='Максимальная норма времени')
    norm_unit = models.ForeignKey(MeasureUnit, on_delete=models.SET_NULL, blank=True, null=True,
                                  verbose_name='Единица измерения нормы')

    @staticmethod
    def get_or_create_item(prop_dict):
        return Operation.objects.get_or_create(operation_name=prop_dict['operation_name'], defaults=prop_dict)

    def get_caption(self):
        """Формирование понятной надписи для разных целей"""
        return self.operation_name + ' | Производственная операция'

    @staticmethod
    def suggest(user, str_filter, int_limit, init_filter):
        """Формирование набора значений для списка подстановки"""
        if str_filter:  # Фильтрацию применяем, если указан фильтр
            items = Operation.objects.filter(
                operation_name__icontains=str_filter)
        else:
            items = Operation.objects.all()

        return list(
            map(lambda x: dict(pk=x['pk'], value=x['operation_name']), items.values('pk', 'operation_name')))

    def __str__(self):
        return f"Операция {self.operation_name} ({self.pk})"

    class Meta:
        verbose_name = "Производственная операция"
        verbose_name_plural = "Производственные операции"
        default_permissions = ()
        permissions = [('change_operation', 'Производственная операция. Редактирование'),
                       ('view_operation', 'Производственная операция. Просмотр')]


class TpRowType(List):
    """Варианты значений типов строк технологических процессов"""

    class Meta:
        verbose_name = "Тип строки технологического процесса"
        verbose_name_plural = "Типы строк технологических процессов"
        default_permissions = ()
        # permissions = [('change_tprowtype', 'Тип строки технологического процесса. Редактирование'),
        #                ('view_tprowtype', 'Тип строки технологического процесса. Просмотр')]


class TpRowLitera(List):
    """Варианты значений литер строк технологических процессов"""

    class Meta:
        verbose_name = "Литера строки технологического процесса"
        verbose_name_plural = "Литеры строк технологических процессов"
        default_permissions = ()
        # permissions = [('change_tprowlitera', 'Литера строки технологического процесса. Редактирование'),
        #                ('view_tprowlitera', 'Литера строки технологического процесса. Просмотр')]


class TpRow(HistoryTrackingMixin):
    """Строки технологических процессов"""
    route = models.ForeignKey(Route, null=False, blank=False, on_delete=models.CASCADE, related_name='tp_rows',
                              verbose_name='Производственный маршрут')
    route_point = models.ForeignKey(RoutePoint, on_delete=models.SET_NULL, default=None, blank=True, null=True,
                                    related_name='point_tp_rows', verbose_name='Элемент маршрута')
    parent = models.ForeignKey(to='TpRow', on_delete=models.SET_NULL, default=None, blank=True, null=True,
                               related_name='row_tp_rows', verbose_name='Родительская строка техпроцесса')
    operation = models.ForeignKey(Operation, null=True, blank=True, on_delete=models.SET_NULL, default=None,
                                  verbose_name='Производственная операция')
    row_type = models.ForeignKey(TpRowType, null=False, blank=False, on_delete=models.CASCADE,
                                 verbose_name='Тип строки')
    order_num = models.SmallIntegerField(
        null=True, blank=True, verbose_name='Порядковый номер')
    row_num = models.CharField(
        max_length=6, blank=True, null=True, default=None, verbose_name='Номер строки')
    row_text = models.TextField(
        blank=True, null=True, default=None, verbose_name='Содержание строки')
    litera = models.ForeignKey(TpRowLitera, blank=True, null=True, default=None, on_delete=models.SET_NULL,
                               verbose_name='Литера')
    lost = models.FloatField(blank=True, null=True,
                             default=None, verbose_name='Процент потерь')
    lost_alt = models.FloatField(
        blank=True, null=True, default=None, verbose_name='Процент потерь альтернативный')
    replaced = models.ForeignKey(to='TpRow', on_delete=models.SET_NULL, default=None, blank=True, null=True,
                                 related_name='replacing_rows', verbose_name='Заменяемая строка техпроцесса')

    # page_num = models.SmallIntegerField(blank=True, null=True)
    # replacement = models.BooleanField(blank=False, null=False, default=False, verbose_name='Признак замены')

    @staticmethod
    def get_next_order_num(row):
        """Определение следующего порядкового номера"""
        order_max = TpRow.objects.filter(
            route_point=row.route_point, parent=row.parent
        ).aggregate(Max('order_num'))
        if order_max['order_num__max']:
            return order_max['order_num__max'] + 1  # Следующий
        return 1

    @staticmethod
    def get_or_create_item(prop_dict):
        return TpRow.objects.get_or_create(route_point=prop_dict['route_point'], order_num=prop_dict['order_num'],
                                           defaults=prop_dict)

    def save(self, *args, **kwargs):
        # Расчет порядка следования операции
        if not self.order_num:
            self.order_num = TpRow.get_next_order_num(self)
        # При сохранении контролировать отношение элемента и строки ТП к одному маршруту
        if self.route_point:
            self.route = self.route_point.route
        super(TpRow, self).save(*args, **kwargs)

    def check_before_delete(self):
        # Метод проверки перед удалением
        if self.tp_row_workers.count():  # Проверка наличия связей с заданиями рабочим
            raise SuspiciousOperation(
                "Удаление невозможно: у операции есть задания исполнителям")

    def create_same(self, route_point, parent_row, crtd_sess):
        """Создание подобной строки для другого элемента маршрута"""
        n = copy(self)
        n.route_point = route_point
        n.route = route_point.route
        # Убираем идентификаторы, чтобы создался новый объект
        n.pk, n.id = None, None
        n.parent = parent_row
        if n.replaced:  # Если это срока замены, то она заменяет родителя
            n.replaced = parent_row
        n.crtd_sess = UserSession.get_session_by_id(crtd_sess)
        n.save()
        # Создание подчиненных строк
        for tpr in self.row_tp_rows.all():
            tpr.create_same(route_point, n, crtd_sess)
        # Копирование ресурса
        if hasattr(self, 'tpresource'):
            tr = self.tpresource
            tr.create_same(n, crtd_sess)
        return n

    def delete(self, *args, **kwargs):
        # Дополнительная обработка удаления строки с удалением заменяющих
        super(TpRow, self).delete(*args, **kwargs)

        # Удаление связанного ресурса если он есть
        try:
            resource_row = self.tpresource
            resource_row.dlt_sess = self.dlt_sess  # Добавляем пометку удаления
            resource_row.delete(*args, **kwargs)
        except TpResource.DoesNotExist:
            pass

        # Если удаление прошло нормально, то удаляем подчиненные строки
        for row in self.row_tp_rows.filter(dlt_sess=0):
            row.dlt_sess = self.dlt_sess  # Добавляем пометку удаления
            row.delete(*args, **kwargs)

        # Если удаление прошло нормально, то удаляем заменяющие строки
        for row in self.replacing_rows.filter(dlt_sess=0):
            row.dlt_sess = self.dlt_sess  # Добавляем пометку удаления
            row.delete(*args, **kwargs)

    def __str__(self):
        return f"Строка {self.order_num} в элементе маршрута {self.route_point} ({self.pk})"

    class Meta:
        verbose_name = "Строка технологического процесса"
        verbose_name_plural = "Строки технологических процессов"
        default_permissions = ()
        permissions = [('change_tprow', 'Строка технологического процесса. Редактирование'),
                       ('view_tprow', 'Строка технологического процесса. Просмотр')]


class TpResource(Link):
    """Потребляемые при производстве ресурсы"""
    net_weight = models.FloatField(blank=True, null=True, default=None, verbose_name='Чистый вес')
    child_route = models.ForeignKey(Route, null=True, blank=True, on_delete=models.SET_NULL, default=None,
                                    related_name='resources', verbose_name='Производственный маршрут ресурса')
    notice = models.ForeignKey(Notice, related_name='notice_resources', on_delete=models.SET_NULL,
                               blank=True, null=True, verbose_name='Ссылка на извещение')
    route = models.ForeignKey(Route, blank=True, null=True, on_delete=models.CASCADE, related_name="route_resources",
                              verbose_name='Производственный маршрут')
    route_point = models.ForeignKey(RoutePoint, related_name='route_point_resources', on_delete=models.SET_NULL,
                                    blank=True, null=True, verbose_name='Ссылка на элемент маршрута')
    tp_row = models.OneToOneField(TpRow, on_delete=models.SET_NULL, db_index=True,  # related_name='tp_resource',
                                  blank=True, null=True, verbose_name='Ссылка на строку технологического процесса')

    @staticmethod
    def get_or_create_item(prop_dict):
        return TpResource.objects.get_or_create(
            tp_row=prop_dict['tp_row'],
            route_point=prop_dict['route_point'], defaults=prop_dict)

    def check_same_count(self):
        """Проверка наличия такого же объекта в составе не производится"""
        return 0

    def cycle_reaction(self):
        """Обработка циклической ссылки отличается от родительской"""
        self.tp_row.delete_row()  # Удаление созданной строки техпроцесса
        # Удаление заменяющей строки ресурса
        super().cycle_reaction()

    def save(self, *args, **kwargs):
        # При сохранении контролировать отношение элемента и строки ТП к одному маршруту
        if self.tp_row:
            self.route_point = self.tp_row.route_point
            self.route = self.tp_row.route
            self.parent = self.tp_row.route.subject
        elif self.route_point:
            self.route = self.tp_row.route_point.route
            self.parent = self.tp_row.route_point.route.subject
        super().save(*args, **kwargs)

    def create_same(self, tp_row, crtd_sess):
        """Создание подобного ресурса для другой строки"""
        n = copy(self)
        # Убираем идентификаторы, чтобы создался новый объект
        n.pk, n.id = None, None
        n.tp_row = tp_row
        n.route_point = tp_row.route_point
        n.route = tp_row.route
        n.parent = tp_row.route.subject
        n.crtd_sess = UserSession.get_session_by_id(crtd_sess)
        n.save()

    def __str__(self):
        return f"{self.parent} потребляет ресурс {self.child} ({self.pk})"

    class Meta:
        verbose_name = "Потребление ресурса технологического процесса"
        verbose_name_plural = "Потребления ресурсов технологических процессов"
        default_permissions = ()


class WorkRank(List):
    """Варианты значений разрядов работ"""

    class Meta:
        verbose_name = "Разряд рабочего (работ)"
        verbose_name_plural = "Разряды рабочих (работ)"
        default_permissions = ()
        # permissions = [('change_workrank', 'Разряд рабочего. Редактирование'),
        #                ('view_workrank', 'Разряд рабочего. Просмотр')]


class PaymentSystem(List):
    """Системы оплаты труда"""

    class Meta:
        verbose_name = "Система оплаты труда"
        verbose_name_plural = "Системы оплаты труда"
        default_permissions = ()
        permissions = [('change_paymentsystem', 'Система оплаты труда. Редактирование'),
                       ('view_paymentsystem', 'Система оплаты труда. Просмотр')]


class TarifNet(HistoryTrackingMixin):
    """Тарифные сетки"""
    net_name = models.CharField(
        max_length=60, null=False, blank=False, verbose_name='Наименование тарифной сетки')
    payment_system = models.ForeignKey(PaymentSystem, null=False, blank=False, on_delete=models.CASCADE,
                                       verbose_name='Система оплаты труда')

    class Meta:
        verbose_name = "Тарифная сетка"
        verbose_name_plural = "Тарифные сетки"
        default_permissions = ()
        permissions = [('change_tarifnet', 'Тарифная сетка. Редактирование'),
                       ('view_tarifnet', 'Тарифная сетка. Просмотр')]


class TpRowValue(HistoryTrackingMixin):
    """Индивидуальные параметры строки технологического процесса"""
    row = models.ForeignKey(TpRow, null=False, blank=False, on_delete=models.CASCADE,
                            verbose_name='Строка технологического процесса')
    route = models.ForeignKey(Route, null=False, blank=False, on_delete=models.CASCADE,
                              verbose_name='Производственный маршрут')
    norm = models.FloatField(blank=True, null=True,
                             default=None, verbose_name='Норма')
    aux_norm = models.FloatField(
        blank=True, null=True, default=None, verbose_name='Вспомогательная норма')
    norm_unit = models.ForeignKey(MeasureUnit, on_delete=models.SET_NULL, blank=True, null=True,
                                  verbose_name='Единица измерения нормы')
    alt_norm = models.FloatField(
        blank=True, null=True, default=None, verbose_name='Альтернативная норма')
    work_rank = models.ForeignKey(WorkRank, null=True, blank=True, on_delete=models.SET_NULL, default=None,
                                  verbose_name='Разряд рабочего')
    aux_work_rank = models.ForeignKey(WorkRank, null=True, blank=True, on_delete=models.SET_NULL, default=None,
                                      related_name='aux_in_tp_rows', verbose_name='Разряд рабочего альтернативный')
    # cond_factor = models.FloatField(blank=True, null=True)
    tarif_net = models.ForeignKey(TarifNet, null=True, blank=True, on_delete=models.SET_NULL, default=None,
                                  verbose_name='Тарифная сетка')
    aux_tarif_net = models.ForeignKey(TarifNet, null=True, blank=True, on_delete=models.SET_NULL, default=None,
                                      related_name='aux_in_tp_rows', verbose_name='Тарифная сетка альтернативная')
    param_text = models.TextField(
        blank=True, null=True, default=None, verbose_name='Содержание параметра')
    param_1 = models.CharField(
        max_length=25, blank=True, null=True, default=None, verbose_name='Параметр 1')
    param_2 = models.CharField(
        max_length=25, blank=True, null=True, default=None, verbose_name='Параметр 2')
    param_3 = models.CharField(
        max_length=25, blank=True, null=True, default=None, verbose_name='Параметр 3')
    param_4 = models.CharField(
        max_length=25, blank=True, null=True, default=None, verbose_name='Параметр 4')
    param_5 = models.CharField(
        max_length=25, blank=True, null=True, default=None, verbose_name='Параметр 5')
    param_6 = models.CharField(
        max_length=25, blank=True, null=True, default=None, verbose_name='Параметр 6')
    param_7 = models.CharField(
        max_length=25, blank=True, null=True, default=None, verbose_name='Параметр 7')

    class Meta:
        verbose_name = "Параметр строки технологического процесса"
        verbose_name_plural = "Параметры строк технологических процессов"
        default_permissions = ()
        permissions = [('change_tprowvalues', 'Параметр строки технологического процесса. Редактирование'),
                       ('view_tprowvalues', 'Параметр строки технологического процесса. Просмотр')]


class Tarif(HistoryTrackingMixin):
    """Тарифы платы выполнения работ"""
    tarif_net = models.ForeignKey(TarifNet, null=False, blank=False, on_delete=models.CASCADE,
                                  verbose_name='Тарифная сетка')
    work_rank = models.ForeignKey(WorkRank, null=False, blank=False, on_delete=models.CASCADE,
                                  verbose_name='Разряд рабочего')
    # cond_factor = models.FloatField(blank=True, null=True)
    payment = models.FloatField(
        blank=True, null=True, default=None, verbose_name='Размер оплаты')
    payment_unit = models.ForeignKey(MeasureUnit, on_delete=models.SET_NULL, blank=True, null=True,
                                     related_name='tarif_payment', verbose_name='Единица измерения оплаты')

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"
        default_permissions = ()
        permissions = [('change_tarif', 'Тариф. Редактирование'),
                       ('view_tarif', 'Тариф. Просмотр')]
