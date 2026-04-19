import uuid  # Для генерации уникальных идентификаторов
from copy import copy
import datetime as dt # Для работы с датами по умолчанию
from hashlib import md5
from importlib import import_module
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User, Permission
from django.db.models.fields.related import ForeignKey
from django.db.models.fields import DateField, Field
from model_utils.managers import InheritanceManager

# Класс для прямого доступа к данным
from django.db import connection

from django.core.exceptions import ObjectDoesNotExist, ValidationError, SuspiciousOperation
from django.conf import settings  # для обращения к настройкам

from .file_uploader import FileUploader  # Перемещение файлов в архив
from jsonserv.core.models_dispatcher import ModelsDispatcher


# Функции формирования уникальных текстовых ключей
def collapse_dots(src_str):
    """Функция замены множества точек на одну"""
    while src_str.find('..') != -1:
        src_str = src_str.replace('..', '.')
    return src_str


def fn_head_key(code, parent_code=''):
    """Ключ для уникального обозначения
    ВНИМАНИЕ! Изменение данной функции может привести к задвоениям данных!"""
    map1 = str.maketrans('-—,_', '....', '" ()/\'\\')  # Заменяемые, заменяющие, удаляемые
    map2 = str.maketrans(r'АВЕЁЗКМНОOРСТУХ*№', r'ABEE3KMH00PCTYXXN')  # Заменяемые, заменяющие
    source = str(code) + parent_code  # Иногда (при импорте, например) приходит целое число в code
    result = source.translate(map1)  # Замена символов похожего смысла и удаление незначащих символов
    result = collapse_dots(result)
    result = result.upper()
    result = result.translate(map2)  # Замена символов похожего написания
    return result


def fn_sorted_key(code, parent_code=''):
    """Ключ со значением, отсортированным по значениям, разделенными пробелами"""
    b = code.split()
    if parent_code:
        b.append(parent_code)
        # b = b + parent_code.split()  # Если вдруг решим и ГОСТ дробить
    b.sort()
    return ' '.join(b)
    # return collapse_dots(''.join(sorted(code)))


def text_key(source):
    """Ключ для текста произвольной длины"""
    result = fn_head_key(source).encode('utf-8')  # сначала очищаем и перекодируем текст
    m = md5()
    m.update(result)
    return m.hexdigest()


def add_to_history(row):
    """Добавление в историю информации об изменении"""
    if row.pk:
        # Это обновление
        cls = row.__class__
        old = cls.all_objects.get(pk=row.pk)  # Объект может быть и удаленным, поэтому all_objects
        new = row
        changed_fields = dict()
        for field in cls._meta.get_fields():
            field_name = field.name
            if field_name in ('edt_sess', 'dlt_sess', 'head_key'):  # Данные поля не сохраняем в истории
                continue
            new_value = getattr(new, field_name, None)
            if getattr(old, field_name, None) != new_value:
                if isinstance(field, ForeignKey):  # От ссылок берем ключ
                    changed_fields[field_name] = new_value.pk if new_value else ''
                elif isinstance(field, DateField):  # Даты надо форматировать
                    changed_fields[field_name] = f'{new_value:%d.%m.%Y}' if new_value else ''
                else:
                    changed_fields[field_name] = new_value
        if changed_fields:  # Если найдены изменения
            session = UserSession.get_session_by_id(row.edt_sess)
            histrow = dict(table_name=cls.__name__.lower(), object_id=row.pk, edt_sess=session)
            histrow['changes'] = changed_fields
            HistoryLog.objects.create(**histrow)


def add_to_history_new(row):
    """Добавление в историю информации об объекте в момент создания"""
    if row.pk:
        cls = row.__class__
        changed_fields = dict()
        for field in cls._meta.get_fields():
            field_name = field.name
            if field_name in ('edt_sess', 'dlt_sess', 'id', 'crtd_sess', 'type_key', 'head_key', 'guid', 'entity_ptr'):
                # Данные поля не сохраняем в истории
                continue
            new_value = getattr(row, field_name, None)
            if new_value:
                if isinstance(field, ForeignKey):  # От ссылок берем ключ
                    changed_fields[field_name] = new_value.pk if new_value else ''
                elif isinstance(field, DateField):  # Даты надо форматировать
                    if isinstance(new_value, str):
                        changed_fields[field_name] = f'{new_value}' if new_value else ''
                    else:
                        changed_fields[field_name] = f'{new_value:%d.%m.%Y}' if new_value else ''
                elif isinstance(field, Field):
                    changed_fields[field_name] = new_value
        if changed_fields:  # Если найдены изменения
            session = row.crtd_sess
            histrow = dict(table_name=cls.__name__.lower(), object_id=row.pk, edt_sess=session)
            histrow['changes'] = changed_fields
            HistoryLog.objects.create(**histrow)


def check_access(right, user, default=True):  # Возможно, нужно вынести в какой-то отдельный модуль
    """Проверка права доступа к пользователя к праву"""
    if right:
        # Проверяем права доступа (имя права доступа формируем на основе права)
        return user.has_perm(f'{right.content_type.app_label}.{right.codename}')
    return default  # Если право доступа не указано, то доступ по умолчанию


class RightMixin(models.Model):  # Миксин для администрирования прав
    value_right = models.ForeignKey(Permission, on_delete=models.SET_DEFAULT, null=True, blank=True, default=None,
                                    verbose_name='Право доступа к записи')

    class Meta:
        abstract = True


class UserSession(models.Model):  # Сессии (Транзакции) пользователей
    user = models.ForeignKey(to='auth.User', null=True, on_delete=models.SET_NULL, verbose_name='Пользователь',
                             help_text='Идентификатор пользователя, выполнявшего данную сессию')
    session_datetime = models.DateTimeField(auto_now_add=True, null=False, verbose_name='Время входа',
                                            help_text='Дата и время начала сессии')
    user_ip = models.GenericIPAddressField(protocol='IPv4', blank=True,
                                           verbose_name='IP адрес', null=True, help_text='IP-адрес пользователя')
    comment = models.CharField(max_length=512, null=True, blank=True, verbose_name='Примечание', help_text='Примечание')
    notice_id = models.IntegerField(null=True,
                                    help_text='Идентификатор извещения (в соответствии с данными об извещениях)')

    @property
    def user_profile_user_name(self):
        # Получение Ф.И.О. из профиля пользователя
        try:
            return self.user.userprofile.user_name
        except ObjectDoesNotExist:
            return self.user.username

    @staticmethod
    def get_session_by_id(session_id):
        """Получение сессии по идентификатору"""
        return UserSession.objects.get(pk=session_id)

    def __str__(self):
        return f'{self.user.username} {self.user_ip}. Date: {self.session_datetime}'

    @staticmethod
    def get_or_create_item(prop_dict):
        return UserSession.objects.get_or_create(user=prop_dict['user'],
                                                 session_datetime=prop_dict['session_datetime'], defaults=prop_dict)

    class Meta:
        ordering = ('-session_datetime',)
        verbose_name = 'Сессия пользователя'
        verbose_name_plural = 'Сессии пользователей'
        default_permissions = ()
        # permissions = [('change_usersession', 'Сессия пользователя. Редактирование'),
        #                ('view_usersession', 'Сессия пользователя. Просмотр')]


class UserSettings(models.Model):  # Произвольные настройки пользователя
    user = models.ForeignKey(to='auth.User', null=False, blank=False, related_name='user_settings',
                             on_delete=models.CASCADE,
                             verbose_name='Пользователь')
    setting_id = models.CharField(max_length=20, null=False, blank=False, verbose_name='Идентификатор настройки')
    setting_value = models.TextField(blank=True, null=True, verbose_name='Содержание настройки')

    @staticmethod
    def save_settings(user, setting_id, setting_value):
        cur_set = UserSettings.objects.filter(user=user, setting_id=setting_id).first()
        if cur_set:  # Если настройка найдена, обновляем
            cur_set.setting_value = setting_value
            cur_set.save()
        else:
            cur_set = UserSettings(user=user, setting_id=setting_id, setting_value=setting_value)
            cur_set.save()
        return cur_set

    class Meta:
        verbose_name = 'Настройка пользователя'
        verbose_name_plural = 'Настройки пользователей'
        default_permissions = ()


class Panel(models.Model):  # Панели дашбордов
    AREACHOICES = (
        ('center', 'Центр'),
        ('east', 'Справа'),
        ('west', 'Слева'),
        ('top', 'Сверху'),
    )
    panel_name = models.CharField(max_length=50, null=False, unique=True, verbose_name='Имя панели')
    area = models.CharField(max_length=6, null=False, default='center', choices=AREACHOICES,
                            verbose_name='Область дашборда')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    view_right = models.ForeignKey(Permission, on_delete=models.SET_DEFAULT, null=True, blank=True, default=None,
                                   related_name="view_panels", verbose_name='Право на просмотр панели')
    edit_right = models.ForeignKey(Permission, on_delete=models.SET_DEFAULT, null=True, blank=True, default=None,
                                   related_name="edit_panels", verbose_name='Право на редактирование панели')
    check_state = models.BooleanField(default=False, null=False, blank=False,
                                      verbose_name='Учитывать права доступа к состоянию')

    def __str__(self):
        return self.panel_name

    @staticmethod
    def get_or_create_item(prop_dict):
        return Panel.objects.get_or_create(panel_name=prop_dict['panel_name'], defaults=prop_dict)

    class Meta:
        ordering = ['panel_name', ]
        verbose_name = 'Панель дашборда'
        verbose_name_plural = 'Панели дашбордов'
        default_permissions = ()
        permissions = [('change_panel', 'Панель дашборда. Редактирование'),
                       ('view_panel', 'Панель дашборда. Просмотр'),
                       # Дополнительные разрешения для общих панелей
                       ('view_entity_list', 'Список экземпляров сущностей. Просмотр'),
                       ('view_entity_props', 'Свойства экземпляра сущности. Просмотр'),
                       ('view_soundsame', 'Панель Похожие. Просмотр'),
                       ('change_service', 'Сервисные функции. Редактирование')]


class FormField(RightMixin):  # Поля свойств в формах
    form_name = models.CharField(max_length=25, null=False, verbose_name='Имя формы', db_index=True,
                                 help_text='Имя формы (совпадает с именем сущности)')
    field_name = models.CharField(max_length=20, null=False, verbose_name='Имя поля',
                                  help_text='Имя поля свойств в форм (совпадает с именем поля модели)')
    order_num = models.PositiveIntegerField(null=False, default=1, verbose_name='Порядок в форме',
                                            help_text='Порядок поля среди других полей формы')
    caption = models.CharField(max_length=30, null=True, verbose_name='Подпись',
                               help_text='Подпись у поля на форме')
    read_only = models.BooleanField(blank=False, null=False, default=False, verbose_name='Только чтение')
    max_size = models.PositiveIntegerField(null=True, blank=True, verbose_name='Количество символов в поле',
                                           help_text='Максимальное допустимое количество символов в поле')
    required = models.BooleanField(blank=False, null=False, default=False, verbose_name='Обязательное поле')
    list_keys = models.CharField(max_length=50, blank=True, null=True, default=None,
                                 verbose_name='Ключи отбора подстановки')
    default_value = models.CharField(max_length=255, blank=True, null=True, verbose_name="Значение по умолчанию")
    hide_in_create = models.BooleanField(blank=False, null=False, default=False, verbose_name='Скрывать при создании')
    target = models.CharField(max_length=20, blank=True, null=True, default=None,
                              verbose_name='Имя модели для получения списка подстановки')
    leave_func = models.CharField(max_length=20, blank=True, null=True, default=None,
                                  verbose_name='Имя, вызываемой при покидании поля')
    field_style = models.CharField(max_length=255, blank=True, null=True, default=None,
                                   verbose_name='Стиль оформления поля')
    

    # hide_empty = models.BooleanField(default=False, blank=False, null=False, verbose_name="Скрывать если пусто")
    # vidget = models.CharField(max_length=20, null=True, blank=True, verbose_name='Виджет для заполнения',
    #                           help_text='Вспомогательный виджет для заполнения значения поля')

    def __str__(self):
        return self.field_name

    @staticmethod
    def type_fields_list(type_name):
        """Получение отсортированного списка описаний полей для типа"""
        order_num = 1
        ordered_fields = dict()
        # Получение списка полей формы по имени типа
        fields = FormField.objects.filter(form_name=type_name.lower()).order_by('order_num', 'field_name')
        for field in fields:
            ordered_fields[field.field_name] = dict(order_num=order_num, caption=field.caption, required=field.required,
                                                    list_keys=field.list_keys, target=field.target,
                                                    default=field.default_value, value_right=field.value_right,
                                                    read_only=field.read_only, hide_in_create=field.hide_in_create,
                                                    leave_func=field.leave_func, field_style=field.field_style)
            order_num += 1
        return ordered_fields

    class Meta:
        ordering = ('form_name', 'order_num', 'field_name')
        verbose_name = 'Поле свойств в форме'
        verbose_name_plural = 'Поля свойств в форме'
        unique_together = ('form_name', 'field_name',)
        default_permissions = ()
        # permissions = [('change_formfield', 'Поле свойств в форме. Редактирование'),
        #                ('view_formfield', 'Поле свойств в форме. Просмотр')]


class TypeSetting(RightMixin):  # Настройки типов
    type_key = models.CharField(max_length=50, null=False, unique=True, verbose_name='Имя типа или дашборда')
    dashboard = models.CharField(max_length=20, null=False, default='main', verbose_name='JS-пакет для отображения')
    page_header = models.CharField(max_length=30, null=False, blank=True, default='',
                                   verbose_name='Заголовок дашборда (опционально)')
    extra_js = models.CharField(max_length=255, null=True, blank=True, verbose_name='Дополнительные файлы js')

    def __str__(self):
        return f'{self.type_key} использует {self.dashboard}'

    @staticmethod
    def get_dashboard(type_key):
        """Возвращает имя дашборда для данного типа"""
        try:
            qr = TypeSetting.objects.get(type_key=type_key)
            return qr.dashboard, qr.page_header, qr.value_right, qr.extra_js
        except ObjectDoesNotExist:
            return 'main', '', None, None  # Значение по умолчанию

    class Meta:
        ordering = ['type_key']
        verbose_name = 'Настройка дашборда'
        verbose_name_plural = 'Настройки дашбордов'
        default_permissions = ()
        # permissions = [('change_typesetting', 'Настройка дашборда. Редактирование'),
        #                ('view_typesetting', 'Настройка дашборда. Просмотр')]


# Абстрактный класс списков
class List(models.Model):
    order_num = models.PositiveIntegerField(null=False, default=1, verbose_name='Порядок в списке',
                                            help_text='Порядок сортировки значения в списке')
    list_value = models.CharField(max_length=100, null=False, blank=True, default='', verbose_name='Значение')
    is_default = models.BooleanField(default=False, null=False, verbose_name='Значение по умолчанию Да/Нет',
                                     help_text='Признак значения по умолчанию')
    value_class = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='Стиль оформления')

    def __str__(self):
        return self.list_value

    @classmethod
    def get_or_create_item(cls, prop_dict):
        return cls.objects.get_or_create(list_value=prop_dict['list_value'], defaults=prop_dict)

    @classmethod
    def get_values(cls, s_key):
        """Формирование набора значений списка"""
        return cls.objects.all().order_by('order_num', 'list_value').values('pk', 'list_value')

    @classmethod
    def get_value_id(cls, list_value):
        """Получение идентификатора строки списка"""
        a = cls.objects.filter(list_value=list_value).first()
        if a:
            return a.id
        return None

    @classmethod
    def values_list(cls):
        """Получение списка значений модели"""
        return list(map(lambda x: dict(value=x['pk'], text=x['list_value']), cls.objects.values('pk', 'list_value')))

    def get_caption(self):
        """Формирование понятной надписи для разных целей"""
        return f'{self.list_value} | Значение из списка'

    class Meta:
        abstract = True  # Это абстрактный класс
        ordering = ('order_num', 'list_value')
        verbose_name = 'Значение из списка'
        verbose_name_plural = 'Значения списка'
        default_permissions = ()


# Абстрактный класс списков с кодами
class CodedList(List):
    value_code = models.CharField(max_length=10, null=False, blank=True, default='', verbose_name='Код')

    def __str__(self):
        return f'{self.list_value} (код {self.value_code})'

    def get_caption(self):
        """Формирование понятной надписи для разных целей"""
        return f'{self.list_value} ({self.value_code}) | Значение кодированного списка'

    class Meta:
        abstract = True  # Это абстрактный класс
        ordering = ['order_num']
        verbose_name = 'Значение из списка с кодом'
        verbose_name_plural = 'Значения списков с кодами'
        default_permissions = ()


# Абстрактный класс структурированных по разделам списков с кодами
class StructuredList(CodedList):
    s_key = models.IntegerField(null=False, default=0, verbose_name='Идентификатор раздела')

    @classmethod
    def get_values(cls, user, s_key=0):
        """Формирование набора значений списка"""
        return cls.objects.filter(s_key=s_key).order_by('order_num', 'list_value').values('pk', 'list_value')

    @classmethod
    def values_list(cls, s_key=0):
        """Получение списка значений. Выполняется фильтрация по разделу"""
        return list(map(lambda x: dict(value=x['pk'], text=x['list_value']),
                        cls.objects.filter(s_key=s_key).values('pk', 'list_value')))

    class Meta:
        abstract = True  # Это абстрактный класс
        ordering = ['order_num']
        verbose_name = 'Значение из списка с кодом и разделом'
        verbose_name_plural = 'Значения списков с кодами и разделами'
        default_permissions = ()


# Менеджер, возвращающий только не удаленные объекты
class NotDeletedObjects(models.Manager):
    def get_queryset(self):
        return super(NotDeletedObjects, self).get_queryset().filter(
            dlt_sess=0  # Не имеющие отметки об удалении
        )


class CreateTrackingMixin(models.Model):  # Миксин для отслеживания создания
    crtd_sess = models.ForeignKey(to='core.UserSession', related_name='%(app_label)s_%(class)s', null=False,
                                  on_delete=models.DO_NOTHING)  # Идентификатор создавшей транзакции

    class Meta:
        abstract = True


class HistoryTrackingMixin(models.Model):  # Миксин для отслеживания истории
    crtd_sess = models.ForeignKey(to='core.UserSession', related_name='%(app_label)s_%(class)s', null=False,
                                  on_delete=models.DO_NOTHING, verbose_name='Идентификатор создавшей транзакции')
    edt_sess = models.IntegerField(null=False, default=0, verbose_name='Идентификатор редактирующей транзакции')
    dlt_sess = models.IntegerField(null=False, default=0, db_index=True,
                                   verbose_name='Идентификатор удалившей транзакции')
    # is_new_vrsn = models.NullBooleanField(default=False, null=False, verbose_name='Признак новой версии')

    objects = NotDeletedObjects()
    all_objects = models.Manager()  # Все объект, включая удаленные, без фильтрации

    def save(self, *args, **kwargs):
        """Добавление функционала отслеживания изменения
           Контроль наличия ссылок на создавшие и отредактировавшие сессии"""
        is_new = True
        if self.id:  # Если объект существовал ранее
            is_new = False
            add_to_history(self)  # До записи фиксируем внесенные изменения
        super().save(*args, **kwargs)
        if is_new:
            # Данные о новом объекте записываем в историю только после сохранения (получения id)
            add_to_history_new(self)  # После записи фиксируем внесенные изменения

    def check_before_delete(self):
        """Проверка перед удалением, в потомках может быть уточнен"""
        if isinstance(self, Entity):  # Только сущности могут иметь связи
            if Link.objects.filter(child=self).count():  # Проверка наличия связей с родителями
                raise SuspiciousOperation("Удаление невозможно: у объекта есть вхождения")

    def delete(self, *args, **kwargs):
        # при удалении запись в поле dlt_sess идентификатора сессии
        # Метод проверки перед удалением (у разных сущностей разный, но по умолчанию заглушка, см. выше)
        # Метод в случае неудачной проверки генерирует исключение SuspiciousOperation
        self.check_before_delete()
        if isinstance(self, Entity):  # Только сущности могут иметь связи
            # Удаление всех связей объекта
            links = Link.objects.filter(parent=self, dlt_sess=0)
            links.update(dlt_sess=self.dlt_sess)

        super().save()

    def delete_force(self, *args, **kwargs):
        """Удаление объекта со всеми связями"""
        # при удалении запись в поле dlt_sess идентификатора сессии
        if isinstance(self, Entity):  # Только сущности могут иметь связи
            # Удаление всех связей объекта
            links = Link.objects.filter(parent=self, dlt_sess=0)
            links.update(dlt_sess=self.dlt_sess)
            links = Link.objects.filter(child=self, dlt_sess=0)
            links.update(dlt_sess=self.dlt_sess)

        super().save()

    def delete_row(self):
        """Реальное удаление записи"""
        super().delete()

    class Meta:
        abstract = True


class GraphicFile(CreateTrackingMixin):
    """Графические файлы"""
    file_name = models.CharField(max_length=40, null=False, blank=False, unique=True,
                                 verbose_name='Наименование файла', help_text='Контрольная сумма + расширение')
    source_file_name = models.CharField(max_length=255, null=False, blank=False,
                                        verbose_name='Исходное наименование файла')
    extension = models.CharField(max_length=6, null=False, blank=False, verbose_name='Расширение файла')

    # description = models.TextField(null=True, blank=True, verbose_name='Описание файла')

    @staticmethod
    def get_or_create_item(prop_dict):
        # Помещаем файл в архив
        file_uploader = FileUploader()
        prop_dict['file_name'] = file_uploader.file_get(prop_dict['file_name'])  # Скачиваем файл

        if not file_uploader.error_check():  # Если получение прошло без ошибок
            prop_dict['source_file_name'] = file_uploader.file_name_get()
            prop_dict['extension'] = file_uploader.file_ext_get()
            new_item, created = GraphicFile.objects.get_or_create(file_name=prop_dict['file_name'], defaults=prop_dict)
            if created:  # Если файл ранее не существовал
                file_uploader.file_put(prop_dict['file_name'])
            return new_item, created
        return None, None

    def __str__(self):
        return f'{self.source_file_name} ({self.file_name})'

    class Meta:
        verbose_name = 'Графический файл'
        verbose_name_plural = 'Графические файлы'
        default_permissions = ()
        permissions = [('change_graphicfile', 'Графический файл. Редактирование'),
                       ('view_graphicfile', 'Графический файл. Просмотр')]


class EntityType(models.Model):  # Типы сущностей
    type_key = models.CharField(max_length=50, null=False, primary_key=True, verbose_name='Имя типа',
                                help_text='Имя типа(ключ)')
    type_name = models.CharField(max_length=50, null=False, verbose_name='Наименование типа')
    div_name = models.CharField(max_length=50, null=False, verbose_name='Наименование раздела')
    doc_key = models.BooleanField(default=False, null=False, verbose_name='Признак составного ключа')
    table_name = models.CharField(max_length=50, null=False, verbose_name='Таблица с данными')
    generator = models.CharField(max_length=50, null=True, blank=True, verbose_name='Генератор обозначений')

    def __str__(self):
        return f'{self.type_name} ({self.type_key})'

    @staticmethod
    def get_or_create_item(prop_dict):
        return EntityType.objects.get_or_create(type_key=prop_dict['type_key'], defaults=prop_dict)

    @staticmethod
    def get_doc_key(type_key):
        return EntityType.objects.get(pk=type_key).doc_key

    class Meta:
        verbose_name = 'Тип сущности'
        verbose_name_plural = 'Типы сущностей'
        default_permissions = ()
        # permissions = [('change_entitytype', 'Тип сущности. Редактирование'),
        #                ('view_entitytype', 'Тип сущности. Просмотр')]


class EntityGraphic(HistoryTrackingMixin):  # Иллюстрации к объектам
    entity = models.ForeignKey(to='Entity', related_name='graphics', on_delete=models.CASCADE,
                               blank=False, null=False, verbose_name='Ссылка на объект')
    graphic = models.ForeignKey(to='GraphicFile', related_name='graphic_objects', on_delete=models.CASCADE,
                                blank=False, null=False, verbose_name='Ссылка на иллюстрацию')

    def __str__(self):
        return f'{self.graphic} иллюстрирует {self.entity}'

    @staticmethod
    def get_or_create_item(prop_dict):
        return EntityGraphic.objects.get_or_create(entity=prop_dict['entity'], graphic=prop_dict['graphic'],
                                                   defaults=prop_dict)

    class Meta:
        verbose_name = 'Иллюстрация к объекту'
        verbose_name_plural = 'Иллюстрации к объектам'
        default_permissions = ()


class TypePanel(models.Model):  # Дашбороды типов
    type_key = models.CharField(max_length=50, null=False, verbose_name='Имя типа', db_index=True)
    panel = models.ForeignKey(Panel, on_delete=models.CASCADE, verbose_name='Имя панели')
    in_list = models.BooleanField(null=False, default=False, verbose_name='Для списка')
    in_single = models.BooleanField(null=False, default=False, verbose_name='Для экземпляра')
    start_params = models.TextField(null=True, blank=True, verbose_name='Параметры формирования панели')
    view_right = models.ForeignKey(Permission, on_delete=models.SET_DEFAULT, null=True, blank=True, default=None,
                                   related_name="view_type_panels", verbose_name='Право на просмотр панели у типа')
    edit_right = models.ForeignKey(Permission, on_delete=models.SET_DEFAULT, null=True, blank=True, default=None,
                                   related_name="edit_type_panels",
                                   verbose_name='Право на редактирование панели у типа')

    def __str__(self):
        return f'Дашборд "{self.type_key}" содержит панель "{self.panel.panel_name}"'

    @staticmethod
    def type_panels(type_key, in_single=False):
        """Возвращает все панели данного типа сущностей для списка, для формы свойств"""
        qr = TypePanel.objects.filter(type_key=type_key)
        if in_single:  # Если запрошен набор панелей для дашборда свойств экземпляра
            qr = qr.filter(in_single=True)
        else:  # Иначе возвращается набор панелей для списка
            qr = qr.filter(in_list=True)
        return qr

    @staticmethod
    def get_or_create_item(prop_dict):
        return TypePanel.objects.get_or_create(type_key=prop_dict['type_key'], panel=prop_dict['panel'],
                                               defaults=prop_dict)

    class Meta:
        ordering = ['type_key', 'panel']
        unique_together = ('type_key', 'panel',)
        verbose_name = 'Панель типа'
        verbose_name_plural = 'Панели типов'
        default_permissions = ()
        permissions = [('change_typepanel', 'Панель типа. Редактирование'),
                       ('view_typepanel', 'Панель типа. Просмотр')]


class MenuItem(models.Model):  # Пункты меню
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               related_name='subitems', verbose_name='Пункт меню родитель')
    item_name = models.CharField(max_length=20, null=False, unique=True, verbose_name='Имя пункта меню')
    caption = models.CharField(max_length=60, null=False, verbose_name='Текст пункта меню')
    style = models.CharField(max_length=20, blank=True, verbose_name='Стиль пункта меню')
    action = models.CharField(max_length=50, blank=True, verbose_name='Действие или ссылка')
    order_num = models.PositiveIntegerField(null=False, default=1, verbose_name='Порядок в перечне')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    item_right = models.ForeignKey(Permission, on_delete=models.SET_DEFAULT, null=True, blank=True, default=None,
                                   verbose_name='Право доступа')

    def save(self, *args, **kwargs):
        # Автоматическое отслеживание порядка следования
        self.order_num = MenuItem._meta.get_field('order_num').get_default()  #Значение по умолчанию
        if not self.order_num:
            dc = MenuItem.objects.filter(parent=self.parent).aggregate(
            order_num_max=models.Max('order_num'),
            cnt=models.Count('order_num'))
            if dc['cnt']:
                # Следующий порядковый номер
                self.order_num = dc['order_num_max'] + 1

        super(MenuItem, self).save(*args, **kwargs)
    
    @staticmethod
    def get_or_create_item(prop_dict):
        return MenuItem.objects.get_or_create(item_name=prop_dict['item_name'], defaults=prop_dict)

    def item_with_children(self, user):
        """Возвращает описание и все подпункты пункта"""
        children = []
        for child in self.subitems.filter(is_active=True).order_by('order_num'):
            if check_access(child.item_right, user):
                children.append(child.item_with_children(user))
        return {
            'id': self.id, 'caption': self.caption, 'action': self.action, 'style': self.style,
            'order_num': self.order_num,
            'children': children
        }

    def __str__(self):
        return self.item_name

    class Meta:
        ordering = ['item_name']
        verbose_name = 'Пункт меню'
        verbose_name_plural = 'Пункты меню'
        default_permissions = ()
        permissions = [('view_mi_settings', 'Пункт меню Настройки')
                       # ('change_menuitem', 'Пункт меню. Редактирование'),
                       # ('view_menuitem', 'Пункт меню. Просмотр'),
                       # Дополнительные права для конкретных пунктов меню
                       # Начинаются с view_mi_ далее идентификатор пункта меню как в свойствах
                       ]


# Классы для хранения данных

class Essence(models.Model):  # Измеряемые сущности
    essence_name = models.CharField(max_length=35, unique=True, null=False, verbose_name='Наименование')

    def __str__(self):
        return self.essence_name

    @staticmethod
    def get_or_create_item(prop_dict):
        return Essence.objects.get_or_create(essence_name=prop_dict['essence_name'], defaults=prop_dict)

    @staticmethod
    def suggest(user, str_filter, int_limit, init_filter):
        """Формирование набора значений для списка подстановки"""
        if str_filter:  # Фильтрацию применяем, если указан фильтр
            items = Essence.objects.filter(essence_name__icontains=str_filter)
        else:
            items = Essence.objects.all()
        items = items.order_by('essence_name')[0:int(int_limit)]

        return list(map(lambda x: dict(pk=x['pk'], value=x['essence_name']), items.values('pk', 'essence_name')))

    class Meta:
        verbose_name = 'Измеряемая сущность'
        verbose_name_plural = 'Измеряемые сущности'
        ordering = ['essence_name']
        default_permissions = ()
        # permissions = [('change_essence', 'Измеряемая сущность. Редактирование'),
        #                ('view_essence', 'Измеряемая сущность. Просмотр')]


class MeasureSystem(List):  # Системы измерения

    class Meta:
        verbose_name = 'Система измерения'
        verbose_name_plural = 'Системы измерения'
        default_permissions = ()
        # permissions = [('change_measuresystem', 'Система измерения. Редактирование'),
        #                ('view_measuresystem', 'Система измерения. Просмотр')]


class MeasureUnit(HistoryTrackingMixin, models.Model):  # Единицы измерения
    SEPARATORCHOICES = (
        ('', 'Нет'),
        ('*', 'Умножать'),
        ('/', 'Делить'),
    )
    essence = models.ForeignKey(to='Essence', on_delete=models.SET_DEFAULT, default=None, null=True,
                                verbose_name='Измеряемая сущность')
    unit_name = models.CharField(max_length=40, null=False, verbose_name='Наименование')
    short_name = models.CharField(max_length=10, null=False, verbose_name='Краткое наименование')
    unit_code = models.CharField(max_length=3, null=True, blank=True, verbose_name='Код')
    numerator = models.ForeignKey(to='MeasureUnit', related_name='numerator_unit', on_delete=models.SET_DEFAULT,
                                  default=None, blank=True, null=True, verbose_name='Числитель')
    denominator = models.ForeignKey(to='MeasureUnit', related_name='denominator_unit', on_delete=models.SET_DEFAULT,
                                    default=None, blank=True, null=True, verbose_name='Знаменатель')
    separator_char = models.CharField(max_length=1, null=True, blank=True, choices=SEPARATORCHOICES, default='',
                                      verbose_name='Символ разделитель')
    base = models.ForeignKey(to='MeasureUnit', related_name='base_unit', on_delete=models.SET_DEFAULT,
                             default=None, blank=True, null=True, verbose_name='Базовая единица измерения')
    ratio = models.FloatField(null=True, blank=True, verbose_name='В базовых единицах')
    order_num = models.PositiveIntegerField(null=False, default=1, verbose_name='Порядок сортировки')
    measure_system = models.ForeignKey(to='MeasureSystem', on_delete=models.SET_DEFAULT, default=None, blank=True,
                                       null=True, verbose_name='Система измерения')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    @staticmethod
    def suggest(user, str_filter, int_limit, init_filter):
        """Формирование набора значений для списка подстановки"""
        if str_filter:  # Фильтрацию применяем, если указан фильтр
            items = MeasureUnit.objects.filter(Q(unit_name__icontains=str_filter) | Q(short_name__icontains=str_filter))
        else:
            items = MeasureUnit.objects.all()
        if init_filter:
            items = items.filter(**init_filter)
        items = items.order_by('unit_name')[0:int(int_limit)]

        return list(map(lambda x: dict(pk=x['pk'], value=x['short_name']), items.values('pk', 'short_name')))

    def __str__(self):
        return self.unit_name

    @staticmethod
    def get_or_create_item(prop_dict):
        return MeasureUnit.objects.get_or_create(unit_name=prop_dict['unit_name'], defaults=prop_dict)

    def get_caption(self):
        """Формирование понятной надписи для разных целей"""
        return f'{self.unit_name} ({self.short_name})'

    class Meta:
        verbose_name = 'Единица измерения'
        verbose_name_plural = 'Единицы измерения'
        default_permissions = ()
        permissions = [('change_measureunit', 'Единица измерения. Редактирование'),
                       ('view_measureunit', 'Единица измерения. Просмотр')]


# Менеджер, возвращающий только действующие на дату объекты
class DatePeriodObjects(models.Manager):
    def get_queryset(self):
        return super(DatePeriodObjects, self).get_queryset().filter(
            dlt_sess=0,  # Не имеющие отметки об удалении
            begin_date_lte=dt.date.today,  # Уже действует
            end_date_gte=dt.date.today  # Еще действует
        )


# Миксин для отслеживания периодов действия
class PeriodTrackingMixin(models.Model):
    begin_date = models.DateField(verbose_name='Дата начала действия', null=False, blank=True,
                                  default=dt.date.today)
    end_date = models.DateField(verbose_name='Дата окончания действия',
                                default=dt.date(2099, 12, 31), null=True, blank=True)
    is_active = models.BooleanField(default=True, null=False, verbose_name='Признак активности')

    objects = DatePeriodObjects()

    class Meta:
        abstract = True


# Менеджер, возвращающий только удаленные объекты
class DeletedObjects(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(
            dlt_sess=0  # Имеющие отметки об удалении
        )


# Базовая сущность
class Entity(HistoryTrackingMixin):
    type_key = models.ForeignKey(to='EntityType', blank=False, null=False, on_delete=models.CASCADE,
                                 verbose_name='Тип сущности')
    parent = models.ForeignKey(to='Entity', related_name='related_objects', on_delete=models.SET_DEFAULT,
                               default=None, blank=True, null=True, verbose_name='Ссылка на документ')
    code = models.CharField(max_length=200, null=False, blank=False, verbose_name='Обозначение')
    auto_code = models.BooleanField(null=False, default=False, verbose_name='Обозначение автоматическое')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    head_key = models.CharField(max_length=400, editable=False, null=False, blank=True, verbose_name='Уникальный ключ',
                                db_index=True)
    group = models.ForeignKey(to='Classification', related_name='group_members', on_delete=models.SET_DEFAULT,
                              default=None, blank=True, null=True, verbose_name='Классификационная группа')
    rating = models.PositiveIntegerField(blank=True, null=True, default=0,
                                         verbose_name='Рейтинг упоминаний объекта в связях')
    properties = models.JSONField(null=True, blank=True, verbose_name='Дополнительные свойства')
    picture = models.ForeignKey(GraphicFile, on_delete=models.SET_DEFAULT, default=None, null=True, blank=True,
                                related_name='icon_for_entities', verbose_name='Файл иллюстрации')
    guid = models.UUIDField(default=uuid.uuid4, editable=False)
    sorted_key = models.CharField(max_length=400, editable=False, null=True, blank=True,
                                  verbose_name='Уникальный отсортированный ключ', db_index=True)
    # hidden = models.BooleanField(default=False, null=False, verbose_name='Признак сокрытия объекта в списках')

    inheritors = InheritanceManager()  # Классы-наследники

    @property
    def key_code(self):
        """Формирование составного ключевого атрибута для отображения в формах"""
        if self.parent and self.type_key.doc_key:
            return self.code + ' ' + self.parent.code
        return self.code

    @property
    def entity_label(self):
        return self.entitylabel.label

    @staticmethod
    def get_key_prepare(props, key_generator=fn_head_key):
        # Генерация head_code С учетом ссылки на документ У разных классов может отличаться
        # Может передаваться как словарь, так и экземпляр модели
        if type(props) is dict:
            if 'parent' in props and props['parent'] and EntityType.get_doc_key(props['type_key'].type_key):
                return key_generator(props['code'], props['parent'].code)
            return key_generator(props['code'])
        else:  # Экземпляр модели
            if props.parent and EntityType.get_doc_key(props.type_key.type_key):
                return key_generator(props.code, props.parent.code)
            else:
                return key_generator(props.code)

    @classmethod
    def get_or_create_item(cls, prop_dict):
        if 'type_key' not in prop_dict:  # Указание типа объекта
            # Получаем ссылку на основе имени класса экземпляра
            try:
                prop_dict['type_key'] = EntityType.objects.get(pk=cls.__name__.lower())
            except ObjectDoesNotExist as e:
                raise ObjectDoesNotExist(f"Tип {cls.__name__} не зарегистрирован в EntityType") from e
        prop_dict['head_key'] = cls.get_key_prepare(prop_dict, fn_head_key)
        # Проверяем по уникальному ключу в рамках типа сущности
        return cls.objects.get_or_create(head_key=prop_dict['head_key'], type_key=prop_dict['type_key'],
                                         defaults=prop_dict)

    @classmethod
    def suggest(cls, user, str_filter, int_limit, init_filter):
        """Формирование набора значений для списка подстановки"""

        def cnct(code, parent):
            """Формирование обозначения из двух полей Обозначение и родитель """
            if parent:
                return code + ' ' + parent
            return code

        # Если переданы дополнительные фильтрующие параметры, начинаем с них
        filter_params = init_filter if init_filter else dict()
        if str_filter:  # Фильтрацию применяем, если указан фильтр
            if getattr(settings, 'SEARCH_IN_MIDDLE', False):
                filter_params['head_key__icontains'] = fn_head_key(str_filter, '')  # Вариант в любом месте
            else:
                filter_params['head_key__istartswith'] = fn_head_key(str_filter, '')  # Вариант Начинается с
        if filter_params:  # Фильтрацию применяем, если указан фильтры
            items = cls.objects.filter(**filter_params)
        else:
            items = cls.objects.all()
        items = items.order_by('rating', 'code')[0:int(int_limit)]
        return list(map(lambda x: dict(pk=x['pk'], value=cnct(x['code'], x['parent__code'])),
                        items.values('pk', 'code', 'parent__code')))

    def get_inheritor(self):
        """Получение экземпляра наследника"""
        return Entity.inheritors.filter(pk=self.pk).select_subclasses().first()

    def recast_head_code(self, edt_sess):
        """Перерасчет проверочного ключа"""
        self.edt_sess = edt_sess
        self.save()

    def check_same_count(self):
        """Проверка наличия объекта с таким же ключом"""
        # Внимание! Сейчас уникальность контролируется внутри типа
        if Entity.objects.filter(head_key=self.head_key, type_key=self.type_key).exclude(pk=self.pk).count():
            return f'Ключевой атрибут [{self.head_key}] не уникален'
        return ''

    def check_before_delete(self):
        # Метод проверки перед удалением
        if Link.get_parents_count(self):  # Проверка наличия связей с родителями
            raise SuspiciousOperation("Удаление невозможно: у объекта есть связи")

    def save(self, *args, **kwargs):
        if not hasattr(self, 'type_key'):  # Указание типа объекта
            # Получаем ссылку на основе имени класса экземпляра
            try:
                self.type_key = EntityType.objects.get(pk=type(self).__name__.lower())
            except ObjectDoesNotExist as e:
                raise ObjectDoesNotExist(f"Tип {type(self).__name__} не зарегистрирован в EntityType") from e
        generator_path = ''  # Будет использоваться как признак наличия генератора
        if self.type_key.generator:
            # Если для обработки объекта используется генератор, а обозначение не указано
            generator_path = f'jsonserv.{self.type_key.generator}'
            generator_module = import_module(generator_path)  # Импортируем генератор обозначений
            gcls = getattr(generator_module, 'GeneratorExt')  # Расширенный класс GeneratorExt
            gitm = gcls()  # Экземпляр генератора
        if generator_path:
            # Если указан генератор обрабатываем объект до сохранения
            gitm.process_before(self)
        self.head_key = self.get_key_prepare(self, fn_head_key)  # Генерация ключа
        self.sorted_key = self.get_key_prepare(self, fn_sorted_key)  # Дополнительный отсортированный ключ

        # Проверка уникальности head_code корректная обработка ошибок Отключать здесь
        if self.pk and 1 == 2: # Не пойму, зачем я это сделал... поэтому отключил
            # Определяем модель типа объекта
            source_model = ModelsDispatcher.get_entity_class_by_entity_name(self.type_key.pk)
            parent = source_model.objects.get(pk=self.pk)
            msg = parent.check_same_count()  # Проверяем по модели родителя
        else:
            # Проверка по старому варианту
            msg = self.check_same_count()

        if msg:
            raise ValidationError(msg)
        super(Entity, self).save(*args, **kwargs)
        if generator_path:
            # Если указан генератор, выполняем метод после сохранения
            gitm.process_after(self)

    def get_caption(self):
        """Формирование понятной надписи для разных целей"""
        code = f'{self.code} {self.parent.code}' if self.parent else self.code
        return f'{code} | {self.type_key.type_name}'

    def get_description(self):
        """Формирование описание объекта для отображения в строке поиска"""
        return f'{self.type_key.type_name} {self.code} {self.parent.code}' if self.parent else f'{self.type_key.type_name} {self.code}'

    def __str__(self):
        if self.parent:
            return f'{self.code} {self.parent} ({self.id})'
        return f'{self.code} ({self.id})'

    def get_absolute_url(self):
        # Ссылкой является уникальный идентификатор
        return '/%i/' % self.id

    class Meta:
        ordering = ['code']
        indexes = [
            models.Index(fields=['head_key', ]),
            models.Index(fields=['type_key', ]),
        ]
        default_permissions = ()  # Отключаем встроенные разрешения у потомков


# Базовая связь
class Link(HistoryTrackingMixin):
    parent = models.ForeignKey(to='Entity', related_name='child_objects', on_delete=models.CASCADE,
                               blank=False, null=False, verbose_name='Ссылка на родителя')
    child = models.ForeignKey(to='Entity', related_name='parent_objects', on_delete=models.CASCADE,
                              blank=False, null=False, verbose_name='Ссылка на потомка')
    quantity = models.FloatField(null=True, blank=True, verbose_name='Количество')
    ratio = models.FloatField(null=True, blank=True, default=1, verbose_name='Коэффициент')
    comment = models.TextField(blank=True, null=True, verbose_name='Примечание')
    link_class = models.CharField(max_length=20, editable=False, null=False, blank=True, verbose_name='Класс связи',
                                  default='link')

    same_message = 'Повтор входящего объекта'

    @classmethod
    def get_or_create_item(cls, prop_dict):
        return cls.objects.get_or_create(parent=prop_dict['parent'], child=prop_dict['child'], defaults=prop_dict)

    @classmethod
    def create_same(cls, source_item, target_item, user_session):
        """Создание аналогичных источнику связей"""
        links = cls.objects.filter(parent=source_item.id)
        cnt = 0
        usess = UserSession.get_session_by_id(user_session)
        for link in links:
            new_link = copy(link)  # Создание новой связи
            new_link.pk, new_link.id = None, None  # Убираем идентификаторы, чтобы создался новый объект
            # Добавляем новые свойства
            new_link.parent = target_item
            new_link.crtd_sess = usess
            new_link.save()
            cnt += 1
        return cnt

    @classmethod
    def replace(cls, source_item, target_item, user_session):
        """Замена экземпляра сущности новым экземпляром во всех связях"""
        links = cls.objects.filter(child=source_item.id)
        cnt = 0
        for link in links:
            new_link = copy(link)  # Создание новой связи
            new_link.pk, new_link.id = None, None  # Убираем идентификаторы, чтобы создался новый объект
            # Добавляем новые свойства
            new_link.child = target_item
            new_link.crtd_sess = UserSession.get_session_by_id(user_session)
            new_link.save()
            # Удаление существующей связи
            link.dlt_sess = user_session
            link.save()
            cnt += 1
        return cnt

    def check_same_count(self):
        """Проверка наличия такого же объекта в составе"""
        return Link.objects.filter(parent=self.parent, child=self.child).exclude(pk=self.pk).count()

    def cycle_reaction(self):
        """Обработка циклической ссылки"""
        raise SuspiciousOperation(f'Обнаружена циклическая ссылка {self.child_id} в {self.parent_id}')

    def save(self, *args, **kwargs):
        if not kwargs.get('no_check', False):  # Если не передан признак отключения проверок
            if self.dlt_sess == 0:  # если связь не удаляется
                if self.check_same_count():  # Проверка наличия объекта в составе
                    raise SuspiciousOperation(self.same_message)
                if quantity(self.child_id, self.parent_id):  # Проверка циклического вхождения
                    self.cycle_reaction()  # Дочерний класс может иметь свой вариант обработки
        else:
            # Без проверки, но дальше аргумент не передаем
            del kwargs['no_check']
        # Фиксация в истории изменений родителя
        self.parent.edt_sess = max(self.edt_sess, self.crtd_sess_id)  # Родитель был отредактирован
        self.parent.save() # Сохраняем без проверки уникальности

        setattr(self, 'link_class', self.__class__.__name__.lower())  # Указание класса связи
        super().save(*args, **kwargs)

    @staticmethod
    def get_parents_count(child):
        """Получение количества родителей у объекта"""
        return Link.objects.filter(child_id=child.id).count()

    @staticmethod
    def get_children_count(parent):
        """Получение количества потомков у объекта"""
        return Link.objects.filter(parent_id=parent.id).count()

    def __str__(self):
        return f'{self.parent} связана с {self.child}'

    class Meta:
        verbose_name = 'Связь'
        verbose_name_plural = 'Связи'
        default_permissions = ()  # Отключаем встроенные разрешения у потомков
        permissions = [('view_link', 'Связи. Просмотр')]


class Classification(Entity):  # Классификационная группа
    order_num = models.PositiveIntegerField(null=True, blank=True, default=1, verbose_name='Порядок при сортировке',
                                            help_text='Порядок сортировки группы в списке')
    group_code = models.CharField(max_length=15, blank=True, null=True, verbose_name='Код группы')

    def has_children(self):
        """Определение наличия классификационных групп потомков по полю parent"""
        return 1 if self.group_members.filter(type_key='classification').count() else 0

    class Meta:
        ordering = ['code']
        verbose_name = 'Классификационная группа'
        verbose_name_plural = 'Классификационные группы'
        default_permissions = ()
        permissions = [('change_classification', 'Классификационная группа. Редактирование'),
                       ('view_classification', 'Классификационная группа. Просмотр')]
    class BasaltaProps:
        """Подкласс для хранения специфических атрибутов для системы Базальта"""
        # Перечень экспортируемых полей
        json_fields = ('id', 'group', 'order_num', 'code')


class PropertyType(models.Model):  # Типы дополнительных свойств
    property_type = models.CharField(max_length=1, null=False, verbose_name='Тип свойства', primary_key=True)
    description = models.CharField(max_length=20, null=False, blank=False, verbose_name='Описание типа свойства')

    def __str__(self):
        return self.description

    @staticmethod
    def suggest(user, str_filter, int_limit, init_filter):
        """Формирование набора значений для списка подстановки"""
        if str_filter:  # Фильтрацию применяем, если указан фильтр
            items = PropertyType.objects.filter(description__icontains=str_filter)
        else:
            items = PropertyType.objects.all()
        items = items.order_by('description')[0:int(int_limit)]

        return list(map(lambda x: dict(pk=x['pk'], value=x['description']), items.values('pk', 'description')))

    @staticmethod
    def get_or_create_item(prop_dict):
        return PropertyType.objects.get_or_create(property_type=prop_dict['property_type'], defaults=prop_dict)

    class Meta:
        verbose_name = 'Тип дополнительного свойства'
        verbose_name_plural = 'Типы дополнительных свойств'
        default_permissions = ()
        # permissions = [('change_propertytype', 'Тип дополнительного свойства. Редактирование'),
        #                ('view_propertytype', 'Тип дополнительного свойства. Просмотр')]


class Property(HistoryTrackingMixin):  # Дополнительные свойства
    order_num = models.PositiveIntegerField(null=False, default=1, verbose_name='Порядок в списке свойств',
                                            help_text='Порядок сортировки значения в списке свойств')
    property_code = models.CharField(max_length=20, null=True, blank=True, verbose_name='Код свойства')
    property_name = models.CharField(max_length=200, unique=True, null=False, verbose_name='Наименование свойства')
    property_name_rus = models.CharField(max_length=200, null=True, blank=True,
                                         verbose_name='Наименование свойства по-русски')  # Временно, перенести в json
    property_type = models.ForeignKey(PropertyType, null=False, default='T', blank=False, on_delete=models.CASCADE,
                                      verbose_name='Тип свойства', help_text='Тип значений свойства')
    essence = models.ManyToManyField(to='Essence', verbose_name='Измеряемые сущности',
                                     help_text='Каких измеряемых сущностей бывает свойство')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    description_rus = models.TextField(blank=True, null=True, verbose_name='Описание по русски')
    group = models.ForeignKey(Classification, related_name='group_properties', on_delete=models.SET_DEFAULT,
                              default=None, blank=True, null=True, verbose_name='Классификационная группа')

    def __str__(self):
        return f'{self.property_name} ({self.property_code if self.property_code else ""})'
        # return self.property_name_rus if self.property_name_rus else self.property_name

    @staticmethod
    def get_or_create_item(prop_dict):
        return Property.objects.get_or_create(property_name=prop_dict['property_name'], defaults=prop_dict)

    def get_caption(self):
        """Формирование понятной надписи для разных целей"""
        return f'{self.property_name} | Свойство'

    @staticmethod
    def suggest(user, str_filter, int_limit, init_filter):
        """Формирование набора значений для списка подстановки"""
        if str_filter:  # Фильтрацию применяем, если указан фильтр
            items = Property.objects.filter(property_name__icontains=str_filter)
        else:
            items = Property.objects.all()
        items = items.order_by('property_name')[0:int(int_limit)]

        return list(map(lambda x: dict(pk=x['pk'], value=x['property_name']), items.values('pk', 'property_name')))

    class Meta:
        ordering = ['order_num']
        verbose_name = 'Дополнительное свойство'
        verbose_name_plural = 'Дополнительные свойства'
        default_permissions = ()
        permissions = [('change_property', 'Дополнительное свойство. Редактирование'),
                       ('view_property', 'Дополнительное свойство. Просмотр')]


class PropertyUnit(models.Model):  # Возможные единицы измерения для свойства (дополнительное ограничение из GTC)
    property = models.ForeignKey(Property, null=False, verbose_name='Свойство', on_delete=models.CASCADE)
    measure_unit = models.ForeignKey(MeasureUnit, null=False, on_delete=models.CASCADE,
                                     verbose_name='Единица измерения')

    @staticmethod
    def get_or_create_item(prop_dict):
        return PropertyUnit.objects.get_or_create(property=prop_dict['property'],
                                                  measure_unit=prop_dict['measure_unit'], defaults=prop_dict)

    class Meta:
        verbose_name = 'Единица измерения свойства'
        verbose_name_plural = 'Единицы измерения свойства'
        default_permissions = ()
        permissions = [('change_propertyunit', 'Единица измерения свойства. Редактирование'),
                       ('view_propertyunit', 'Единица измерения свойства. Просмотр')]


class PropertyValue(HistoryTrackingMixin):
    """Хранение значений дополнительных свойств сущностей"""
    entity = models.ForeignKey(Entity, related_name='entity_properties', on_delete=models.CASCADE,
                               null=False, verbose_name='Ссылка на объект')
    property = models.ForeignKey(Property, related_name='property_values', on_delete=models.CASCADE,
                                 null=False, verbose_name='Ссылка на дополнительное свойство')
    value = models.TextField(verbose_name='Значение', null=True, blank=True)
    value_min = models.FloatField(verbose_name='Значение число', null=True, blank=True)
    value_max = models.FloatField(verbose_name='Значение число максимальное', null=True, blank=True)
    value_date = models.DateField(verbose_name='Значение дата', null=True, blank=True)
    unit = models.ForeignKey(to='MeasureUnit', related_name='unit_values', on_delete=models.SET_NULL,
                             blank=True, null=True, verbose_name='Единица измерения')
    value_number = models.PositiveIntegerField(null=False, default=1, verbose_name='Номер значения',
                                               help_text='Номер значения с одинаковым свойством')

    def __str__(self):
        return f'{self.entity} имеет свойство {self.property}'

    @staticmethod
    def get_or_create_item(prop_dict):
        if 'value_number' not in prop_dict:
            prop_dict['value_number'] = 1  # Значение входит в состав ключа поиска
        return PropertyValue.objects.get_or_create(entity=prop_dict['entity'], property=prop_dict['property'],
                                                   value_number=prop_dict['value_number'],
                                                   defaults=prop_dict)

    class Meta:
        verbose_name = 'Значение дополнительного свойства'
        verbose_name_plural = 'Значения дополнительных свойств'
        default_permissions = ()
        permissions = [('change_propertyvalue', 'Значение дополнительного свойства. Редактирование'),
                       ('view_propertyvalue', 'Значение дополнительного свойства. Просмотр')]


class PropertyValueRelation(models.Model):
    """Взаимосвязи значений свойств"""
    parent_value = models.ForeignKey(PropertyValue, related_name='depended_values', on_delete=models.CASCADE,
                                     null=False, verbose_name='Ссылка на родительское значение свойства')
    child_value = models.ForeignKey(PropertyValue, related_name='parent_values', on_delete=models.CASCADE,
                                    null=False, verbose_name='Ссылка на зависящее значение свойства')
    link_type = models.CharField(max_length=50, null=False, blank=False, verbose_name='Тип связи')
    description = models.TextField(null=True, blank=True, verbose_name='Описание связи')

    def __str__(self):
        return f'{self.child_value} зависит от {self.child_value} как {self.link_type}'

    @staticmethod
    def get_or_create_item(prop_dict):
        return PropertyValueRelation.objects.get_or_create(parent_value=prop_dict['parent_value'],
                                                           child_value=prop_dict['child_value'],
                                                           link_type=prop_dict['link_type'],
                                                           defaults=prop_dict)

    class Meta:
        verbose_name = 'Зависимое дополнительное свойство'
        verbose_name_plural = 'Зависимые дополнительные свойств'
        default_permissions = ()
        # permissions = [('change_propertyvaluerelation', 'Зависимое дополнительное свойство. Редактирование'),
        #                ('view_propertyvaluerelation', 'Зависимое дополнительное свойство. Просмотр')]


class PlaceType(List):  # Типы подразделений
    class Meta:
        verbose_name = 'Тип производственного подразделения'
        verbose_name_plural = 'Типы производственных подразделений'
        ordering = ['order_num']
        default_permissions = ()
        permissions = [('change_placetype', 'Тип производственного подразделения. Редактирование'),
                       ('view_placetype', 'Тип производственного подразделения. Просмотр')]


class Place(Entity):  # Информация о структуре предприятия
    place_type = models.ForeignKey(to='PlaceType', on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name='Тип подразделения', related_name='type_places')
    short_name = models.CharField(max_length=15, null=True, blank=True, verbose_name='Краткое обозначение')
    place_code = models.CharField(max_length=15, null=True, blank=True, verbose_name='Код (ИНН/КПП)')
    address = models.TextField(null=True, blank=True, verbose_name='Адрес')
    sitelink = models.URLField(null=True, blank=True, verbose_name='Сайт')
    head = models.ForeignKey(to='UserProfile', on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name='Руководитель', related_name='managed_places')
    ratio = models.FloatField(null=False, default=1, verbose_name='Коэффициент выхода материала')
    visible = models.BooleanField(null=False, blank=False, default=True, verbose_name='Признак видимости')
    is_point = models.BooleanField(null=False, blank=False, default=False, verbose_name='Участвует в производстве')
    is_account = models.BooleanField(null=False, blank=False, default=False, verbose_name='Ведется учет полуфабрикатов')
    is_buyer = models.BooleanField(null=False, blank=False, default=False, verbose_name='Покупатель')
    is_supplier = models.BooleanField(null=False, blank=False, default=False, verbose_name='Поставщик')

    class Meta:
        verbose_name = 'Производственное подразделение'
        verbose_name_plural = 'Производственные подразделения'
        default_permissions = ()
        permissions = [('change_place', 'Производственное подразделение. Редактирование'),
                       ('view_place', 'Производственное подразделение. Просмотр')]


class Enterprise(HistoryTrackingMixin):
    """Предприятия пользователя"""
    enterprise_name = models.CharField(max_length=150, null=False, blank=False, unique=True,
                                       verbose_name='Наименование предприятия')
    short_name = models.CharField(max_length=15, null=False, blank=False,
                                  unique=True, verbose_name='Краткое наименование')
    description = models.TextField(null=True, blank=True, verbose_name='Описание предприятия')

    def __str__(self):
        return self.enterprise_name

    @staticmethod
    def suggest(user, str_filter, int_limit, init_filter):
        """Формирование набора значений для списка подстановки
        Внимание! Отображаются только пользователи, которые могут получать задачи"""
        if str_filter:  # Фильтрацию применяем, если указан фильтр
            items = Enterprise.objects.filter(short_name__icontains=str_filter)
        else:
            items = Enterprise.objects.all()
        items = items.order_by('short_name')[0:int(int_limit)]

        return list(map(lambda x: dict(pk=x['pk'], value=x['short_name']), items.values('pk', 'short_name')))

    class Meta:
        ordering = ('enterprise_name',)
        verbose_name = 'Предприятие'
        verbose_name_plural = 'Предприятия'
        default_permissions = ()


class SystemUser(User):
    """Надстройка над базовым классом для добавление нужных функций"""
    __password = None # Для хранения значения до обновления

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__password = self.password # Запоминаем старое значение

    @staticmethod
    def suggest(user, str_filter, int_limit, init_filter):
        """Формирование набора значений для списка подстановки"""
        if str_filter:  # Фильтрацию применяем, если указан фильтр
            items = User.objects.filter(username__icontains=str_filter)
        else:
            items = User.objects.all()
        items = items.order_by('username')[0:int(int_limit)]

        return list(map(lambda x: dict(pk=x['pk'], value=x['username']), items.values('pk', 'username')))

    @staticmethod
    def get_or_create_item(prop_dict):
        return SystemUser.objects.get_or_create(username=prop_dict['username'], defaults=prop_dict)
    
    def save(self, *args, **kwargs):
        if self.password != self.__password and hasattr(self, 'userprofile_id'): # Если пароль изменился - делаем отметку в профиле
            self.userprofile.set_password_changed(self.edt_sess)
        super(User, self).save(*args, **kwargs)
        self.__password = self.password

    def get_caption(self):
        """Формирование понятной надписи для разных целей"""
        return f'{self.username} - {self.last_name} {self.first_name} | Пользователь системы'

    class Meta:
        proxy = True  # Используется существующая модель. Все ради метода suggest
        default_permissions = ()
        verbose_name = 'Пользователь системы'
        verbose_name_plural = 'Пользователи системы'


class SystemPermission(Permission):
    """Надстройка над базовым классом для добавление нужных функций"""

    @staticmethod
    def get_or_create_item(prop_dict):
        return SystemPermission.objects.get_or_create(codename=prop_dict['codename'], defaults=prop_dict)

    class Meta:
        proxy = True  # Используется существующая модель. Все ради возможности ссылаться при импорте
        default_permissions = ()
        verbose_name = 'Право доступа системы'
        verbose_name_plural = 'Права доступа системы'


class DownloadCheckGroup(models.Model):
    """Группы контроля скачивания файлов"""
    group_name = models.CharField(max_length=100, null=False, blank=False, verbose_name='Наименование группы контроля загрузок')
    download_limit_day = models.IntegerField(null=False, default=0, verbose_name='Количество скачиваний в день')
    download_limit_month = models.IntegerField(null=False, default=0, verbose_name='Количество скачиваний в месяц')
    download_limit_year = models.IntegerField(null=False, default=0, verbose_name='Количество скачиваний в год')

    def __str__(self):
        return f'{self.group_name} {self.download_limit_day}/{self.download_limit_month}/{self.download_limit_year}'

    @staticmethod
    def suggest(user, str_filter, int_limit, init_filter):
        """Формирование набора значений для списка подстановки"""
        if str_filter:  # Фильтрацию применяем, если указан фильтр
            items = DownloadCheckGroup.objects.filter(group_name__icontains=str_filter)
        else:
            items = DownloadCheckGroup.objects.all()
        items = items.order_by('group_name')[0:int(int_limit)]

        return list(map(lambda x: dict(pk=x['pk'], value=x['group_name']), items.values('pk', 'group_name')))

    def get_caption(self):
        """Формирование понятной надписи для разных целей"""
        return f'{self.group_name} | Группа контроля скачивания файлов'

    class Meta:
        ordering = ('group_name',)
        verbose_name = 'Группа контроля скачиваний файлов'
        verbose_name_plural = 'Группы контроля скачиваний файлов'
        default_permissions = ()


# Менеджер, возвращающий только не уволенных, которые могут получать задания
class NotDismissedTaskable(NotDeletedObjects):
    def get_queryset(self):
        return super(NotDismissedTaskable, self).get_queryset().filter(taskable=True, dismissed=False)


class UserProfile(HistoryTrackingMixin):
    """Дополнительная информация о пользователе"""
    user = models.OneToOneField(SystemUser, on_delete=models.CASCADE, null=True, verbose_name='Логин')
    user_name = models.CharField(max_length=100, null=False, blank=False, verbose_name='Фамилия Имя Отчество')
    # styletable = models.CharField(max_length=15, null=True, blank=True, default='',
    #                               verbose_name='Наименование стиля для оформления интерфейса')
    taskable = models.BooleanField(default=False, null=True, blank=True,
                                   verbose_name='Признак  возможности выдавать пользователю задания')
    dismissed = models.BooleanField(default=False, null=True, blank=True, verbose_name='Уволен')
    dashboard = models.CharField(max_length=25, null=True, blank=True, default='search',
                                 verbose_name='Дашборд по умолчанию',
                                 help_text='Дашборд, отображаемый пользователю после входа в систему')
    password_expire = models.BooleanField(default=False, null=False, verbose_name='Периодическая смена пароля', 
                                          help_text='Требовать периодическую смену пароля пользователем')
    password_changed = models.DateTimeField(auto_now_add=True, verbose_name='Дата изменения пароля')
    api_only = models.BooleanField(default=False, null=False, verbose_name="Только для доступа к API",
                                   help_text='Отметка пользователей, не имеющих права входа в основную Базальту')
    log_actions = models.BooleanField(default=False, null=False, verbose_name="Логировать действия пользователя",
                                   help_text='Отметка пользователей, действия которых логируются')
    download_group = models.ForeignKey(DownloadCheckGroup, on_delete=models.SET_NULL, null=True, blank=True,
                                       verbose_name='Группа контроля загрузки', related_name='controlled_profiles')

    for_suggest = NotDismissedTaskable()  # Менеджер для списков подстановки

    @staticmethod
    def get_by_user(user):
        """Возвращает идентификатор пользовательского профиля, связанный с указанным пользователем"""
        try:
            qr = UserProfile.objects.get(user=user)
            return qr.pk
        except ObjectDoesNotExist:
            return 0  # Значение по умолчанию

    @staticmethod
    def get_user_dashboard(user):
        """Получение дашборда пользователя"""
        default_dashboard = '/search/'  # Значение по умолчанию
        try:
            qr = UserProfile.objects.get(user=user)
            if qr.password_expire:
                return f'/{qr.dashboard}/'
        except ObjectDoesNotExist:
            return default_dashboard
        return default_dashboard
    
    @staticmethod
    def check_password_expire(user):
        """Проверка истечения срока действия пароля пользователя"""
        try:
            qr = UserProfile.objects.get(user=user)
            if qr.password_expire:
                return False
        except ObjectDoesNotExist:
            return True
        return False


    @staticmethod
    def get_or_create_item(prop_dict):
        return UserProfile.objects.get_or_create(user_name=prop_dict['user_name'], defaults=prop_dict)

    @staticmethod
    def suggest(user, str_filter, int_limit, init_filter):
        """Формирование набора значений для списка подстановки
        Внимание! Отображаются только пользователи, которые могут получать задачи"""
        if str_filter:  # Фильтрацию применяем, если указан фильтр
            items = UserProfile.for_suggest.filter(user_name__icontains=str_filter)
        else:
            items = UserProfile.for_suggest.all()
        items = items.order_by('user_name')[0:int(int_limit)]

        return list(map(lambda x: dict(pk=x['pk'], value=x['user_name']), items.values('pk', 'user_name')))

    def is_password_date_expired(self):
        if self.password_expire: # Если нужно контролировать срок действия пароля
            lp = getattr(settings, 'PASSWORD_EXPIRE_PERIOD', 30) # Получаем срок жизни пароля из настроек
            # Все хорошо, если пароль менялся позже чем установленный срок, иначе True
            return self.password_changed < dt.datetime.now() - dt.timedelta(days=lp)
        return False
    
    def set_password_changed(self, edt_sess):
        """Фиксация факта смены пароля пользователя"""
        self.password_changed = dt.datetime.now()
        self.edt_sess = edt_sess
        self.save()

    def loginable(self):
        """Профиль допускает вход в систему"""
        if self.dismissed or self.api_only:
            return False
        return True
    
    def __str__(self):
        return self.user_name

    def get_caption(self):
        """Формирование понятной надписи для разных целей"""
        return f'{self.user_name} ({self.user}) | Профиль пользователя'

    def check_download_limit(self):
        """Проверка достижения профилем лимита скачиваний"""
        if self.download_group:
            # Если у пользователя есть группа контроля количеств скачиваний
            # Подсчет количества скачиваний за год
            cnt = ActionLog.year_download_count(self)
            if cnt >= self.download_group.download_limit_year:
                return True
            # Подсчет количества скачиваний за месяц
            cnt = ActionLog.month_download_count(self)
            if cnt >= self.download_group.download_limit_month:
                return True
            # Подсчет количества скачиваний за день
            cnt = ActionLog.day_download_count(self)
            if cnt >= self.download_group.download_limit_day:
                return True
        return False  # Вариант по умолчанию

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
        ordering = ['user_name']
        default_permissions = ()
        permissions = [('change_userprofile', 'Профиль пользователя. Редактирование'),
                       ('view_userprofile', 'Профиль пользователя. Просмотр')]


class Language(CodedList):  # Языки

    class Meta:
        verbose_name = 'Язык'
        verbose_name_plural = 'Языки'
        default_permissions = ()
        permissions = [('change_language', 'Язык. Редактирование'),
                       ('view_language', 'Язык. Просмотр')]


class LanguageValue(models.Model):  # Переводы значений на другие языки
    row_id = models.IntegerField(null=False, verbose_name='Ссылка на запись', db_index=True)
    field_name = models.CharField(max_length=50, null=False, blank=False, verbose_name='Имя поля')
    language = models.ForeignKey(to='Language', on_delete=models.CASCADE, null=False, blank=False,
                                 verbose_name='Язык значения')
    lang_value = models.CharField(max_length=255, null=True, blank=True, verbose_name='Значение на языке')

    class Meta:
        verbose_name = 'Значение на другом языке'
        verbose_name_plural = 'Значения на других языках'
        default_permissions = ()
        # permissions = [('change_languagevalue', 'Значение на другом языке. Редактирование'),
        #                ('view_languagevalue', 'Значение на другом языке. Просмотр')]


class GenerateNumber(models.Model):
    """Хранение счетчиков генераторов обозначений"""
    generator_name = models.CharField(max_length=25, null=False, blank=False, verbose_name='Наименование генератора')
    div = models.CharField(max_length=10, null=False, blank=True, default='', verbose_name='Раздел генерации')
    current_number = models.PositiveIntegerField(null=False, default=0, verbose_name='Текущее значение генератора')

    def __str__(self):
        return f'{self.generator_name} ({self.div}) {self.current_number}'
    
    def get_current_number(self):
        return self.current_number

    @classmethod
    def get_or_create_item(cls, prop_dict):
        return GenerateNumber.objects.get_or_create(generator_name=prop_dict.get('generator_name', ''), div=prop_dict.get('div', ''),
                                                    defaults=prop_dict)

    class Meta:
        verbose_name = 'Значение генератора'
        verbose_name_plural = 'Значения генераторов'
        default_permissions = ()
        # permissions = [('change_generatenumber', 'Значение генератора. Редактирование'),
        #                ('view_generatenumber', 'Значение генератора. Просмотр')]


class UsageStatistic(models.Model):
    """Статистика обращение к функционалу"""
    pass

    class Meta:
        verbose_name = 'Статистика использования функционала'
        verbose_name_plural = 'Статистика использования функционала'
        default_permissions = ()
        # permissions = [('change_usagestatistic', 'Статистика использования функционала. Редактирование'),
        #                ('view_usagestatistic', 'Статистика использования функционала. Просмотр')]


class HistoryLog(models.Model):
    """Хранение истории изменений"""
    table_name = models.CharField(max_length=50, null=False, verbose_name='Таблица с данными')
    object_id = models.IntegerField(null=False, verbose_name='Идентификатор объекта')
    edt_sess = models.ForeignKey(to='core.UserSession', related_name='related_changes', null=False,
                                 on_delete=models.DO_NOTHING, verbose_name='Идентификатор изменившей транзакции')
    changes = models.JSONField(verbose_name='Изменения')

    @staticmethod
    def get_or_create_item(prop_dict):
        return HistoryLog.objects.get_or_create(table_name=prop_dict['table_name'],
                                                object_id=prop_dict['object_id'],
                                                edt_sess=prop_dict['edt_sess'],
                                                changes=prop_dict['changes'],
                                                defaults=prop_dict)

    class Meta:
        verbose_name = 'История изменения'
        verbose_name_plural = 'Истории изменений'
        default_permissions = ()
        permissions = [('change_historylog', 'История изменения. Редактирование'),
                       ('view_historylog', 'История изменения. Просмотр')]


class Report(models.Model):
    """Отчеты, формируемые системой"""
    report_name = models.CharField(max_length=20, null=False, blank=False, unique=True,
                                   verbose_name='Идентификатор отчета')
    title = models.CharField(max_length=50, null=False, blank=False, verbose_name='Заголовок формы отчета')
    app = models.CharField(max_length=20, null=True, blank=True, verbose_name='Приложение-владелец')
    description = models.TextField(blank=True, null=True, verbose_name='Описание отчета')
    module_url = models.CharField(max_length=150, null=True, blank=True,
                                  verbose_name='Ссылка на внешний модуль генерации')
    file_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='Имя формируемого файла')
    only_format = models.CharField(max_length=4, null=True, blank=True, verbose_name='Единственный формат')

    def get_module_path(self):
        """Получение адреса расположения модуля"""
        return f'jsonserv.{self.app}.reports.{self.report_name}'

    def __str__(self):
        return f'Настройка отчета {self.title} ({self.report_name})'

    class Meta:
        verbose_name = 'Отчет'
        verbose_name_plural = 'Отчеты'
        ordering = ['report_name']
        default_permissions = ()
        # permissions = [('change_report', 'Отчет. Редактирование'),
        #                ('view_report', 'Отчет. Просмотр')]


class ReportParam(models.Model):
    """Параметры отчетов"""
    TYPECHOICES = (
        ('Link', 'Ссылка на объект'),
        ('List', 'Список'),
        ('NumberBox', 'Число'),
        ('DateBox', 'Дата'),
        ('CheckBox', 'Да/Нет'),
        ('RadioButton', 'Выбор варианта'),
        ('TextBox', 'Текстовое поле'),
    )
    report = models.ForeignKey(Report, null=False, blank=False, on_delete=models.CASCADE, related_name='report_params',
                               verbose_name='Отчет')
    param_name = models.CharField(max_length=15, null=False, blank=False, verbose_name='Название параметра')
    caption = models.CharField(max_length=60, null=False, blank=False, verbose_name='Подпись на форме')
    param_type = models.CharField(max_length=15, null=False, default='TextBox', choices=TYPECHOICES,
                                  verbose_name='Тип параметра')
    extra_value = models.CharField(max_length=50, null=True, blank=True, verbose_name='Дополнительные параметры')
    values_list = models.TextField(null=True, blank=True, verbose_name='Возможные значения')
    default_value = models.CharField(max_length=255, null=True, blank=True, verbose_name='Значение по умолчанию')
    required = models.BooleanField(default=False, null=False, verbose_name='Обязательный параметр')
    order_num = models.PositiveIntegerField(null=False, default=1, verbose_name='Порядок следования в форме')
    is_file_name = models.BooleanField(default=False, null=False, verbose_name='Использовать при генерации имени файла')
    list_keys = models.CharField(max_length=150, blank=True, null=True, default=None,
                                 verbose_name='Ключи отбора подстановки')

    class Meta:
        verbose_name = 'Параметр отчета'
        verbose_name_plural = 'Параметры отчетов'
        ordering = ['report', 'order_num', 'caption']
        default_permissions = ()
        # permissions = [('change_reportparam', 'Параметр отчета. Редактирование'),
        #                ('view_reportparam', 'Параметр отчета. Просмотр')]


class ExtraLink(RightMixin):
    """Ссылки на дополнительный функционал
    Отображаются на формах для быстрого доступа к нужному функционалу. В разработке"""
    caption = models.CharField(max_length=50, unique=True, null=False, blank=False, verbose_name='Название параметра')
    link_pattern = models.CharField(max_length=250, null=False, blank=False, verbose_name='Шаблон ссылки')

    @staticmethod
    def get_or_create_item(prop_dict):
        return ExtraLink.objects.get_or_create(caption=prop_dict['caption'], defaults=prop_dict)

    def __str__(self):
        return f'Ссылка {self.caption} ({self.link_pattern})'

    class Meta:
        verbose_name = 'Ссылка на дополнительный функционал'
        verbose_name_plural = 'Ссылки на дополнительный функционал'
        ordering = ['caption']
        default_permissions = ()
        permissions = [('view_extralink', 'Ссылка на дополнительный функционал. Просмотр'), ]


class TypeExtraLink(models.Model):
    """Дополнительные ссылки типов
    привязка дашбордов к ссылкам дополнительного функционала. В разработке"""
    type_key = models.CharField(max_length=50, null=False, verbose_name='Имя типа', db_index=True)
    extra_link = models.ForeignKey(ExtraLink, on_delete=models.CASCADE, verbose_name='Дополнительная ссылка')

    def __str__(self):
        return f'Дашборд "{self.type_key}" содержит ссылку "{self.extra_link.caption}"'

    @staticmethod
    def get_or_create_item(prop_dict):
        return TypeExtraLink.objects.get_or_create(type_key=prop_dict['type_key'], extra_link=prop_dict['extra_link'],
                                                   defaults=prop_dict)

    class Meta:
        ordering = ['type_key', 'extra_link']
        verbose_name = 'Дополнительная ссылка типа'
        verbose_name_plural = 'Дополнительные ссылки типов'
        default_permissions = ()
        permissions = [('change_typeextralink', 'Дополнительная ссылка типа. Редактирование'),
                       ('view_typeextralink', 'Дополнительная ссылка типа. Просмотр')]


class EntityLabel(models.Model):
    """Дополнительные оформительские метки у экземпляров сущностей
    Используются для дополнительного оформления на формах свойств"""
    entity = models.OneToOneField(Entity, on_delete=models.CASCADE, null=True, verbose_name='Экземпляр сущности')
    label = models.CharField(max_length=50, null=False, verbose_name='Метка')

    def __str__(self):
        return f'{self.entity} имеет метку {self.label}'

    class Meta:
        verbose_name = 'Метка экземпляра сущности'
        verbose_name_plural = 'Метки экземпляров сущностей'
        default_permissions = ()


class ActionLog(models.Model):
    """Логирование действий пользователей"""
    ACTIONTYPECHOICES = (
        ('C', 'Форма свойств (карточка)'),
        ('D', 'Скачивание файла'),
        ('A', 'Метод API'),
    )
    action_link = models.CharField(max_length=255, null=False, verbose_name='Запрошенный адрес (ссылка)')
    action_type = models.CharField(max_length=1, null=False, default='C', choices=ACTIONTYPECHOICES,
                                    verbose_name='Тип обращения')
    session =  models.ForeignKey(to='UserSession', related_name='related_actions', null=False,
                                    on_delete=models.DO_NOTHING, verbose_name='Идентификатор транзакции',
                                    help_text='Сессия, выполнившая действие')
    action_datetime = models.DateTimeField(auto_now_add=True, null=False, verbose_name='Время выполнения',
                                            help_text='Дата и время выполнения действия')
    
    def __str__(self):
        return f'{self.session} обратилась к {self.action_link} в {self.action_datetime}'
    
    @staticmethod
    def log_action(action_type, action_link, session):
        """Запись информации в лог"""
        n = ActionLog(action_type=action_type, action_link=action_link, session_id=session.get('user_session_id', 1))
        n.save()

    @staticmethod
    def year_download_count(profile):
        """Подсчет количеств скачиваний профилем за год"""
        current_date = dt.datetime.now()
        start_date = dt.datetime(current_date.year, 1, 1)  # Первый день года
        return ActionLog.objects.filter(session__user=profile.user, action_type='F', action_datetime__gte=start_date).count()
    
    @staticmethod
    def month_download_count(profile):
        """Подсчет количеств скачиваний профилем за месяц"""
        current_date = dt.datetime.now()
        start_date = dt.datetime(current_date.year, current_date.month, 1)  # Первый день месяца
        return ActionLog.objects.filter(session__user=profile.user, action_type='F', action_datetime__gte=start_date).count()
    
    @staticmethod
    def day_download_count(profile):
        """Подсчет количеств скачиваний профилем за день"""
        current_date = dt.datetime.now()
        start_date = dt.datetime(current_date.year, current_date.month, current_date.day)  # Начало текущего дня
        return ActionLog.objects.filter(session__user=profile.user, action_type='F', action_datetime__gte=start_date).count()

    class Meta:
        ordering = ['-action_datetime']
        verbose_name = 'Запись о действии пользователя'
        verbose_name_plural = 'Записи о действиях пользователей'
        default_permissions = ()


# Функции прямого обращения к базе данных
# TODO: Вынести в отдельный модуль
def quantity(parent_id, child_id):
    """Расчет количества вхождения"""
    with connection.cursor() as cursor:
        # Для разных баз данных разный способ вызова хранимых процедур
        if connection.vendor == 'postgresql':
            cursor.callproc('fn_quantity', [parent_id, child_id, 1])
            return cursor.fetchone()[0]
        else:  # Пока только MS SQL
            # Не поддерживает именованные параметры (словари)
            cursor.execute('SELECT dbo.fn_quantity(%s, %s, %s) AS quantity', (parent_id, child_id, 1))
            return cursor.fetchone()[0]

    
def children(object_id, link_classes = ''):
    """Получение всех входящих рекурсивно"""
    with connection.cursor() as cursor:
        # Для разных баз данных разный способ вызова хранимых процедур
        if connection.vendor == 'postgresql':
            cursor.callproc('fn_linked_all', [object_id, 1, link_classes])
        else:  # Пока только MS SQL
            # Не поддерживает именованные параметры (словари)
            cursor.execute('SELECT * FROM dbo.fn_linked_all(%s, %s, %s)', (object_id, 1, link_classes))
        return cursor.fetchall()

