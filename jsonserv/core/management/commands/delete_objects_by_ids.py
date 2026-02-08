# Команда удаления объектов ЗАГОТОВКА!!!
from django.core.management.base import BaseCommand

from jsonserv.exchange.exchange_utils import ModelsDispatcher


class Command(BaseCommand):
    help = 'Recast head_code in every entity item'

    def add_arguments(self, parser):
        # Идентификатор сессии
        parser.add_argument('session_id', type=int, help='Идентификатор сессии')
        # Имя обрабатываемой сущности
        parser.add_argument('entity', type=str, nargs='?', default='', help='Имя обрабатываемого класса')

    def handle(self, *args, **options):
        type_key = options['entity']
        if type_key:
            instance = ModelsDispatcher.get_entity_class_by_entity_name(type_key)  # Получаем модель
            edt_sess = options['session_id']
            cnt = 0  # Счетчик
            for i in instance.objects.all():
                i.recast_head_code(edt_sess)
                cnt += 1
                if cnt % 1000 == 0:
                    print(cnt)  # Выводим каждую обработанную тысячу чтобы видеть прогресс
            print(cnt)
