# Обработка ошибок, приходящих к DRF
from rest_framework.views import exception_handler
from django.http import JsonResponse

# Классы обрабатываемых ошибок
# Ошибка проверки в методах моделей
from django.core.exceptions import ValidationError, ObjectDoesNotExist, SuspiciousOperation
from rest_framework.exceptions import ValidationError as restValidationError


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # checks if the raised exception is of the type you want to handle

    if isinstance(exc, ConnectionError):
        err_data = {'message': 'some custom error messaging'}
        return JsonResponse(err_data, safe=False, status=503)

    if isinstance(exc, ValidationError):
        err_data = {'message': 'Ошибка проверки значений. ' + exc.message}
        return JsonResponse(err_data, safe=False, status=412)

    if isinstance(exc, ObjectDoesNotExist):
        err_data = {'message': f'Ошибка Поиска объекта. {exc}'}
        return JsonResponse(err_data, safe=False, status=412)

    if isinstance(exc, SuspiciousOperation):
        err_data = {'message': f'{exc}'}
        return JsonResponse(err_data, safe=False, status=412)

    if isinstance(exc, restValidationError):
        e = list()
        # Собираем все полученные сообщения
        for field_name, field_errors in exc.detail.items():
            e.append(''.join(field_errors))
        err_data = {'message': ' '.join(e)}
        return JsonResponse(err_data, safe=False, status=412)

    # returns response as handled normally by the framework
    return response
