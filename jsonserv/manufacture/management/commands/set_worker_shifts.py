# Команда обновления ссылок на смены рабочих у отчетов работников
from django.core.management.base import BaseCommand

from jsonserv.manufacture.models import WorkerReportConsist


class Command(BaseCommand):
    help = 'Set worker shift in every worker report'

    def add_arguments(self, parser):
        # Идентификатор сессии
        parser.add_argument('session_id', type=int, help='Идентификатор сессии')

    def handle(self, *args, **options):
        edt_sess = options['session_id']
        cnt = 0  # Счетчик
        for i in WorkerReportConsist.objects.all():
            # Установка смены производится в момент сохранения отчета встроенным кодом
            i.edt_sess = edt_sess
            i.save()
            cnt += 1
        print(cnt)
