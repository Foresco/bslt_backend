# Получатели сигналов
from copy import copy
from django.dispatch import receiver
from jsonserv.pdm import signals


@receiver(signals.copy_design_roles_signal)
def copy_design_roles(sender, parent, child, **kwargs):
    """Копирование ссылок на роли разработчика от родителя, к потомку"""
    for row in parent.design_roles.all():
        n = copy(row)
        # Убираем идентификаторы, чтобы создался новый объект
        n.pk, n.id = None, None
        # Добавляем новые свойства
        n.subject = child  # Указываем ссылку на потомка
        n.crtd_sess = child.crtd_sess  # Указываем новую сессию
        n.save()
