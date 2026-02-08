from django.db import models
from jsonserv.core.models import Entity


# Внешние приложения
class ExternalPartner(models.Model):
    partner_name = models.CharField(max_length=200, null=False, blank=False,
                                    verbose_name='Наименование внешнего партнера')
    header_url = models.CharField(max_length=100, null=True, blank=True,  verbose_name='Основаня часть web-адреса')

    def __str__(self):
        return self.partner_name

    class Meta:
        verbose_name = "Внешнее приложение"
        verbose_name_plural = "Внешние приложения"
        default_permissions = ()


# Состоявшиеся обмены
class ExchangeSession(models.Model):
    DIRECTIONS = (
        ('I', 'Загрузка'),
        ('O', 'Выгрузка')
     )
    partner = models.ForeignKey(to='ExternalPartner', on_delete=models.CASCADE,
                                blank=True, null=True, verbose_name='Ссылка на внешнее приложение источник данных')
    direction = models.CharField(max_length=1, null=False, default='I', choices=DIRECTIONS,
                                 verbose_name='Направление передачи данных')
    exchange_datetime = models.DateTimeField(auto_now_add=True, null=False, verbose_name='Время обмена',
                                             help_text='Дата и время начала обмена')

    def __str__(self):
        return f"Обмен с {self.partner} от {self.exchange_datetime} {self.direction}"

    class Meta:
        verbose_name = "Сессия обмена данными"
        verbose_name_plural = "Сессии обмена данными"
        default_permissions = ()


# Идентификаторы во внешних приложениях
class ExternalID(models.Model):
    internal = models.ForeignKey(to='core.Entity', on_delete=models.CASCADE, related_name='externals',
                                 blank=False, null=False, verbose_name='Ссылка на внутренний объект')
    # model_name = models.CharField(max_length=20, null=False, blank=False, verbose_name='Наименование модели')
    partner = models.ForeignKey(to='ExternalPartner', on_delete=models.CASCADE,
                                   blank=True, null=True, verbose_name='Ссылка на внешнее приложение')
    external_id = models.CharField(max_length=200, null=False, blank=False,
                                   verbose_name='Идентификатор во внешней системе')
    exchange_session = models.ForeignKey(to='ExchangeSession', on_delete=models.CASCADE,
                                    blank=False, null=False, verbose_name='Ссылка на обмен, установивший значение')

    def __str__(self):
        return f"{self.internal} в {self.partner} обозначается {self.external_id}"

    class Meta:
        verbose_name = "Идентификатор во внешней системе"
        verbose_name_plural = "Идентификаторы во внешних системах"
        default_permissions = ()
        permissions = [('change_external_id', 'Ссылка во внешней системе. Редактирование'),
                       ('view_external_id', 'Ссылка во внешней системе. Просмотр')]
