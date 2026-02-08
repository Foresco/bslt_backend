# Получатели сигналов
from django.dispatch import receiver
from jsonserv.pdm import signals
from jsonserv.manufacture.models import ProdOrderLink

@receiver(signals.use_default_route_signal)
def use_default_route(sender, child, route, **kwargs):
    """Вставка ссылки на на маршрут по умолчанию в связи объекта с заказами"""
    for row in ProdOrderLink.objects.filter(child_id=child, route__isnull=True):
        # Добавляем новые свойства
        row.route = route  # Указываем ссылку на потомка
        row.edt_sess = route.crtd_sess_id  # Указываем новую сессию
        row.save()
