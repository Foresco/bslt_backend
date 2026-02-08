from django.db import models
from jsonserv.core.models import HistoryTrackingMixin, Place, UserProfile, List


class PersonCategory(List):
    """Варианты категорий сотрудников"""
    class Meta:
        verbose_name = "Категория сотрудника"
        verbose_name_plural = "Категории сотрудников"
        default_permissions = ()
        # permissions = [('change_personcategory', 'Категория сотрудника. Редактирование'),
        #                ('view_personcategory', 'Категория сотрудника. Просмотр')]


class Person(HistoryTrackingMixin):
    """Сотрудники организации"""
    WORKRANKCHOICES = (
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5),
        (6, 6)
    )
    person_profile = models.OneToOneField(UserProfile, on_delete=models.SET_NULL, null=True,
                                          verbose_name='Профиль пользователя')
    person = models.CharField(max_length=100, null=False, blank=False,
                              verbose_name='Фамилия Имя Отчество сотрудника')
    person_short = models.CharField(max_length=25, null=True, blank=True, default='', verbose_name='Краткое именование',
                                    help_text='Краткое именование сотрудника в документах')
    person_r = models.CharField(max_length=25, null=False, blank=True, default='', verbose_name="Родительный падеж",
                                help_text='Краткое именование пользователя как сотрудника в родительном падеже')
    person_d = models.CharField(max_length=25, null=False, blank=True, default='', verbose_name="Дательный падеж",
                                help_text='Краткое именование пользователя как сотрудника в дательном падеже')

    person_phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='Номер телефона')
    person_mail = models.EmailField(null=True, blank=True, verbose_name='Email')
    person_category = models.ForeignKey(PersonCategory, null=True, blank=True, on_delete=models.SET_NULL,
                                        verbose_name="Категория сотрудника")
    work_rank = models.PositiveIntegerField(null=True, blank=True, choices=WORKRANKCHOICES,
                                            verbose_name='Разряд работника')

    @staticmethod
    def get_or_create_item(prop_dict):
        return Person.objects.get_or_create(person=prop_dict['person'], defaults=prop_dict)

    def get_caption(self):
        """Формирование понятной надписи для разных целей"""
        return f'{self.person} | Сотрудник организации'

    def __str__(self):
        return self.person

    @staticmethod
    def profile_person_plases():
        """Возвращает строку с перечнем мест работы сотрудника, полученную по профилю"""
        pass

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ('person', )
        default_permissions = ()
        permissions = [('change_person', 'Сотрудник. Редактирование'),
                       ('view_person', 'Сотрудник. Просмотр')]


class StaffPosition(HistoryTrackingMixin):
    """Должности"""
    position_name = models.CharField(max_length=60, null=False, blank=False, verbose_name='Должность')

    @staticmethod
    def suggest(user, str_filter, int_limit, init_filter):
        if str_filter:  # Фильтрацию применяем, если указан фильтр
            items = StaffPosition.objects.filter(position_name__icontains=str_filter)
        else:
            items = StaffPosition.objects.all()
        items = items.order_by('position_name')[0:int(int_limit)]

        return list(map(lambda x: dict(pk=x['pk'], value=x['position_name']), items.values('pk', 'position_name')))

    def __str__(self):
        return self.position_name

    class Meta:
        verbose_name = "Должность"
        verbose_name_plural = "Должности"
        default_permissions = ()
        permissions = [('change_staffposition', 'Должность. Редактирование'),
                       ('view_staffposition', 'Должность. Просмотр')]


class PersonStaffPosition(HistoryTrackingMixin):
    """Должности сотрудников"""
    person = models.ForeignKey(Person, on_delete=models.CASCADE, blank=False, null=False,
                               verbose_name='Сотрудник')
    staff_position = models.ForeignKey(StaffPosition, on_delete=models.SET_NULL, null=True, blank=True,
                                       verbose_name='Должность')
    place = models.ForeignKey(Place, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Место работы',
                              related_name='place_persons')
    is_main = models.BooleanField(default=False, null=False, verbose_name='Признак основного места работы')

    class Meta:
        verbose_name = "Должность сотрудника"
        verbose_name_plural = "Должности сотрудников"
        default_permissions = ()
        permissions = [('change_personstaffposition', 'Должность сотрудника. Редактирование'),
                       ('view_personstaffposition', 'Должность сотрудника. Просмотр')]

# class TarifNet(models.Model):
#     """Тарифные сетки"""
#     net_name = models.CharField(max_length=60, null=False, blank=False, verbose_name='Тарифная сетка')
#
#     class Meta:
#         verbose_name = "Тарифная сетка"
#         verbose_name_plural = "Тарифные сетки"
#         default_permissions = ()
#
#
# class Tarif(models.Model):
#     """Тарифы"""
#     net = models.ForeignKey(TarifNet, on_delete=models.CASCADE, null=False, verbose_name='Тарифная сетка'),
#     work_rank = models.PositiveIntegerField(default=3, null=False, verbose_name='Разряд работ')
#     cond_factor = models.FloatField(default=None, verbose_name='Код условий труда')
#     payment = models.FloatField(default=0, verbose_name='Тариф')
#     unit = models.ForeignKey(MeasureUnit, default=None, null=True, on_delete=models.SET_NULL,
#                              verbose_name='Единица измерения')
#
#     class Meta:
#         verbose_name = "Тариф"
#         verbose_name_plural = "Тарифы"
#         default_permissions = ()

