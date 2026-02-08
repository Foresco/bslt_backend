# Вспомогательный код для предоставления доступа к объекту request в моделях
# Пока не используется
from django.conf import settings
from jsonserv.core import models


def RequestExposerMiddleware(get_response):
    def middleware(request):
        models.exposed_request = request
        response = get_response(request)
        return response

    return middleware
