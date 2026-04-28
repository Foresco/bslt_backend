import datetime

from django.db import models
from django.db.models import Max
from jsonserv.core.models import HistoryTrackingMixin, List, Place, Entity, UserProfile, Link, fn_head_key


class TaskType(List):
    """Типы заданий"""
    class Meta:
        verbose_name = "Тип задания"
        verbose_name_plural = "Типы заданий"
        default_permissions = ()
        # permissions = [('change_tasktype', 'Тип задания. Редактирование'),
        #                ('view_tasktype', 'Тип задания. Просмотр')]


class Task(Entity):
    """Задания пользователям"""
    task_date = models.DateField(blank=True, null=True, verbose_name="Дата выдачи задания")
    task_type = models.ForeignKey(TaskType, blank=True, null=True, on_delete=models.SET_NULL,
                                  verbose_name="Тип задания")
    income_number = models.CharField(max_length=30, blank=True, null=True, verbose_name="Входящий номер")
    task_from = models.CharField(max_length=110, blank=True, null=True, verbose_name="Задание от")
    task_theme = models.CharField(max_length=200, blank=True, null=True, verbose_name="Тема")
    # task = models.TextField(blank=True, null=True, verbose_name="Содержание")
    next = models.ForeignKey(to='Task', blank=True, null=True, on_delete=models.SET_NULL,
                             verbose_name="Следующее задание")
    order_num = models.PositiveIntegerField(null=False, verbose_name='Порядок в списке',
                                            help_text='Порядок сортировки задания в списке')

    @staticmethod
    def get_or_create_item(prop_dict):
        # Уникальность контролируется в рамках типа задания
        return Task.objects.get_or_create(code=prop_dict['code'], task_type=prop_dict['task_type'], defaults=prop_dict)

    @staticmethod
    def get_next_order_num(task_type):
        """Определение следующего порядкового номера"""
        order_max = Task.objects.filter(task_type=task_type).aggregate(Max('order_num'))
        if order_max['order_num__max']:
            return order_max['order_num__max'] + 1  # Следующий
        return 1

    @staticmethod
    def get_key_prepare(props):
        # Присвоение уникального проверочного ключа
        if type(props) is dict:
            return fn_head_key(f"{props['code']}.{props['task_type']}")
        else:  # Экземпляр модели
            return fn_head_key(f"{props.code}.{props.task_type}")

    @property
    def is_expired(self):
        """признак просроченности задания"""
        return True if self.taskuser_set.filter(
            deadline__lte=datetime.date.today().strftime("%Y-%m-%d")
        ).count() > 0 else False

    def get_caption(self):
        """Формирование понятной надписи для разных целей"""
        code = f'{self.income_number} ({self.code})' if self.income_number else self.code
        return code + f' {self.task_type} '
    
    def check_same_count(self):
        """Проверка наличия задания с таким же номером"""
        if Task.objects.filter(code=self.code, task_type=self.task_type).exclude(pk=self.pk).count():
            return f'Задача с номером [{self.code}] существует'
        return ''

    def save(self, *args, **kwargs):
        # Генерация следующего номера задания
        if not self.order_num:
            self.order_num = Task.get_next_order_num(self.task_type)
        if not self.code:
            self.code = str(self.order_num)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Задание"
        verbose_name_plural = "Задания"
        ordering = ['-order_num', '-task_date', '-code']
        default_permissions = ()
        permissions = [('change_task', 'Задание. Редактирование'),
                       ('view_task', 'Задание. Просмотр')]


class TaskRefer(Link):
    """Связи заданий с объектами"""
    class Meta:
        verbose_name = "Объект задания"
        verbose_name_plural = "Объекты заданий"
        default_permissions = ()
        permissions = [('change_taskrefer', 'Объект задания. Редактирование'),
                       ('view_taskrefer', 'Объект задания. Просмотр')]


class TaskUser(HistoryTrackingMixin):
    """Пользователи, получившие задания"""
    task = models.ForeignKey(Task, null=False, blank=False, on_delete=models.CASCADE, verbose_name="Задание")
    user = models.ForeignKey(UserProfile, related_name='user_task_links', on_delete=models.CASCADE,
                             blank=False, null=False, verbose_name='Исполнитель')
    deadline = models.DateField(blank=True, null=True, verbose_name='Срок выполнения')
    time_norm = models.FloatField(blank=True, null=True, verbose_name='Трудоемкость')
    unit = models.ForeignKey(to='core.MeasureUnit', null=True, on_delete=models.SET_NULL,
                             verbose_name='ЕИ трудоемкости')
    taker_sess = models.IntegerField(blank=False, null=False, default=0)
    executor_sess = models.IntegerField(blank=False, null=False, default=0)

    @staticmethod
    def get_or_create_item(prop_dict):
        return TaskUser.objects.get_or_create(task=prop_dict['task'], user=prop_dict['user'], defaults=prop_dict)

    class Meta:
        verbose_name = "Задание пользователю"
        verbose_name_plural = "Задания пользователям"
        default_permissions = ()
        permissions = [('change_taskuser', 'Задание пользователю. Редактирование'),
                       ('view_taskuser', 'Задание пользователю. Просмотр')]


class LetterType(List):
    """Типы писем"""
    class Meta:
        verbose_name = "Тип письма"
        verbose_name_plural = "Типы писем"
        default_permissions = ()
        # permissions = [('change_lettertype', 'Тип письма. Редактирование'),
        #                ('view_lettertype', 'Тип письма. Просмотр')]


class LetterDirection(List):
    """Варианты направлений писем"""
    class Meta:
        verbose_name = "Направление письма"
        verbose_name_plural = "Направления писем"
        default_permissions = ()
        # permissions = [('change_letterdirection', 'Направление письма. Редактирование'),
        #                ('view_letterdirection', 'Направление письма. Просмотр')]


class Letter(Entity):
    """Письма"""
    direction = models.ForeignKey(LetterDirection, null=False, default=3, on_delete=models.CASCADE,
                                  verbose_name='Направление')
    reg_date = models.DateField(blank=False, null=False, verbose_name='Дата регистрации')
    letter_num = models.CharField(max_length=60, blank=True, null=True, verbose_name='Номер на письме')
    letter_date = models.DateField(blank=True, null=True, verbose_name='Дата на письме')
    letter_type = models.ForeignKey(LetterType, blank=True, null=True, on_delete=models.CASCADE,
                                    verbose_name='Тип документа')
    sender = models.ForeignKey(Place, blank=False, null=False, on_delete=models.CASCADE, related_name='sended_letters',
                               verbose_name='Отправитель')
    receiver = models.ForeignKey(Place, blank=True, null=True, on_delete=models.SET_NULL,
                                 related_name='received_letters', verbose_name='Получатель')
    # income = models.ForeignKey(to='Letter', blank=True, null=True, verbose_name='Входящее письмо')
    letter_theme = models.CharField(max_length=200, blank=True, null=True, verbose_name='Тема письма')

    @property
    def key_code(self):
        """Формирование составного ключевого атрибута"""
        return self.code + ' ' + str(self.reg_date)[0:4]

    @staticmethod
    def get_key_prepare(props):
        # Присвоение уникального проверочного ключа
        if type(props) is dict:
            return fn_head_key(props['code'] + str(props['reg_date'])[0:4])
        else:  # Экземпляр модели
            return fn_head_key(props.code + str(props.reg_date)[0:4])

    def get_caption(self):
        """Формирование понятной надписи для разных целей"""
        code = f'{self.code} {self.reg_date.strftime("%d.%m.%Y")}' if self.reg_date else self.code
        return code + ' | Письмо '

    class Meta:
        verbose_name = "Письмо"
        verbose_name_plural = "Письма"
        default_permissions = ()
        permissions = [('change_letter', 'Письмо. Редактирование'),
                       ('view_letter', 'Письмо. Просмотр')]


class LetterLink(Link):
    """Связи писем с упоминаемыми объектами"""
    # letter = models.ForeignKey(Letter, blank=False, null=False, on_delete=models.CASCADE,
    #                            related_name='letter_objects', verbose_name='Письмо')
    # letter_object = models.ForeignKey(Entity, blank=False, null=False, on_delete=models.CASCADE,
    #                                   related_name='in_letters', verbose_name='Объект')
    # object_status_id = models.IntegerField(blank=True, null=True)
    # letter_status_id = models.IntegerField(blank=True, null=True)
    # pack_type = models.SmallIntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.child.code} упоминается в письме {self.parent}"

    class Meta:
        verbose_name = "Связь письма"
        verbose_name_plural = "Связи писем"
        default_permissions = ()
        permissions = [('change_letterlink', 'Связь письма. Редактирование'),
                       ('view_letterlink', 'Связь письма. Просмотр')]


class Comment(HistoryTrackingMixin):
    """Комментарии"""
    COMMENTTYPECHOICES = (
        ('E', 'Ощибка'),
        ('C', 'Комментарий'),
    )
    entity = models.ForeignKey(to='core.Entity', related_name='entity_commented', on_delete=models.CASCADE,
                               null=False, verbose_name='Ссылка на комментируемй объект')
    comment_type = models.CharField(max_length=1, null=False, default='C', choices=COMMENTTYPECHOICES,
                                     verbose_name='Тип комментария')
    parent = models.ForeignKey(to='Comment', related_name='parent_comment', on_delete=models.SET_NULL,
                               blank=True, null=True, verbose_name='Исходный комментарий',
                               help_text='Комментарий, на который отвечает данный')
    comment_datetime = models.DateTimeField(auto_now_add=True, null=False, verbose_name='Время комментирования',
                                            help_text='Дата и время публикации комментария')
    comment_text = models.TextField(blank=True, null=True, verbose_name='Текст комментария')

    def __str__(self):
        return self.comment_text

    class Meta:
        ordering = ['comment_datetime']
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        default_permissions = ()
        permissions = [('change_comment', 'Комментарий. Редактирование'),
                       ('view_comment', 'Комментарий. Просмотр')]
