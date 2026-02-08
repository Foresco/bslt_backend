import datetime

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand
from django.http import HttpRequest
from importlib import import_module


def init_session(session_key):
    """
    Initialize same session as done for ``SessionMiddleware``.
    """
    engine = import_module(settings.SESSION_ENGINE)
    return engine.SessionStore(session_key)


class Command(BaseCommand):
    help = "Kill all active sessions"

    def handle(self, **options):
        """
        Читает всех доступных пользователей и все доступные не истекшие сессии. Then
        Затем выходит из каждой сессии. Начинает с прошлого дня, чтобы обойти проблему с временными зонами
        и не придумывать что-то сложное.
        """
        start = datetime.datetime.now() - datetime.timedelta(days=1)
        request = HttpRequest()

        sessions = Session.objects.filter(expire_date__gt=start)

        print('Найдено %d не истекших сессий.' % len(sessions))

        for session in sessions:
            username = session.get_decoded().get('_auth_user_id')
            request.session = init_session(session.session_key)

            logout(request)
            print('Пользователь %r успешно вышел.' % username)

        print('Команда выполнена!')