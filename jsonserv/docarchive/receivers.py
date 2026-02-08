# Получатели сигналов
from copy import copy
from django.dispatch import receiver
from jsonserv.pdm import signals


@receiver(signals.copy_file_links_signal)
def copy_file_links(sender, parent, child, **kwargs):
    """Копирование ссылок на файлы от родителя, к потомку"""
    for row in parent.object_documents.all():
        # Проверка, что такой файл к объекту еще не привязан
        if child.object_documents.filter(document_version=row.document_version).count() == 0:
            n = copy(row)
            # Убираем идентификаторы, чтобы создался новый объект
            n.pk, n.id = None, None
            # Добавляем новые свойства
            n.entity = child  # Указываем ссылку на потомка
            n.crtd_sess = child.crtd_sess  # Указываем новую сессию
            n.save()
