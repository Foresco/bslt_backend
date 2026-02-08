from json import loads
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from jsonserv.exchange.exchange_utils import ModelsDispatcher
from jsonserv.core.models import UserSession, UserProfile

# Сериалайзеры
from jsonserv.core.serializers import EntitySerializer


class JSONResponse(HttpResponse):
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


def get_user_profile(session):
    """Получение идентификатора пользовательского профиля на основе сессии"""
    user_session_id = session.get('user_session_id', 1)
    if user_session_id:
        user_session = UserSession.objects.get(pk=user_session_id)
    else:
        return 0  # Значение по умолчанию
    # Идентификатор профиля пользователя может использоваться в дашбордах
    return UserProfile.get_by_user(user_session.user.pk)


@api_view(['GET', ])
def list_values_get(request, type_key=''):
    """Получение списка значение сущности-списка entity для построения формы редактирования"""
    if type_key:
        instance = ModelsDispatcher.get_entity_class_by_entity_name(type_key)  # Получаем модель
        s_key = request.GET.get('s_key', 0)
        if s_key:
            # Для структурированных списков может дополнительно передаваться ключ
            result = instance.get_values(request.user, s_key)
        else:
            # user для возможного контроля прав
            result = instance.get_values(request.user)
    else:
        result = dict(error='Не указан класс модели-списка (type_key)')

    return JSONResponse(result)


@api_view(['POST', ])
def replace(request, type_key=''):
    """Замена одного объекта другим"""
    if type_key:
        instance = ModelsDispatcher.get_entity_class_by_entity_name(type_key)  # Получаем модель
    else:
        return Response({"message": 'Не указан класс объекта (type_key)'}, status=status.HTTP_404_NOT_FOUND)

    # Получение переданных параметров
    source_id = request.data["source"]
    target_id = request.data["target"]
    # Получение свойств исходного объекта
    try:
        source = instance.objects.get(pk=source_id)
    except instance.DoesNotExist:
        return Response({"message": "Исходный объект не найден"}, status=status.HTTP_404_NOT_FOUND)
    # Получение свойств заменяющего объекта
    try:
        target = instance.objects.get(pk=target_id)
    except instance.DoesNotExist:
        return Response({"message": "Заменяющий объект не найден"}, status=status.HTTP_404_NOT_FOUND)
    user_session_id = request.session.get('user_session_id', 0)
    if user_session_id: # Обработка нулевого значения user_session_id
        # Перебираем все зарегистрированные классы связей
        cnt = 0  # Счетчик измененных связей
        for link_class in ModelsDispatcher.track_link_classes:
            # У каждого класса должен быть соответствующий метод
            cnt += link_class.replace(source, target, user_session_id)
        return Response({"message": f"Изменено {cnt} связей"}, status=status.HTTP_201_CREATED)
    else:
        return Response({"message": 'Не указан идентификатор сессии'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST', ])
def create_same(request, type_key, pk):
    """Создание подобного указанному объекту объекта"""
    if type_key:
        instance = ModelsDispatcher.get_entity_class_by_entity_name(type_key)  # Получаем модель
    else:
        return Response({"message": 'Не указан класс модели (type_key)'}, status=status.HTTP_404_NOT_FOUND)
    try:
        source = instance.objects.get(pk=pk)  # Получение свойств исходного объекта
    except instance.DoesNotExist:
        return Response({"message": "Исходный объект не найден"}, status=status.HTTP_404_NOT_FOUND)
    code = request.data['code']
    user_session_id = request.session.get('user_session_id', 0)
    if user_session_id: # обработко нулевого значения user_session_id
        same_object = source.create_same(code, user_session_id)
        # Перебираем все зарегистрированные классы связей и создаем их копии
        cnt = 0  # Счетчик связей
        for link_class in ModelsDispatcher.same_link_classes:
            # У каждого класса должен быть соответствующий метод
            cnt += link_class.create_same(source, same_object, user_session_id)
        serializer = EntitySerializer(same_object)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response({"message": 'Не указан идентификатор сессии'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET', ])
def suggest_get(request, type_key=''):
    """Получение списка для подстановки в в поле с подсказкой"""
    # Значения по умолчанию
    filter_str, limit, init_filter = '', 30, dict()
    # Проверка наличия дополнительных параметров фильтрации
    for a in request.GET:
        if a == 'filter':
            filter_str = request.GET[a]  # Переопределяем на преданное значение
        elif a == 'limit':
            limit = request.GET[a]  # Переопределяем на преданное значение
        else:
            try:
                init_filter[a] = loads(request.GET[a])  # Дополнительные параметры фильтрации (могут быть в виде JSON)
            except ValueError as e:  # Если не удалось распарсить как JSON
                init_filter[a] = request.GET[a]
    if type_key:
        # Получаем модель
        instance = ModelsDispatcher.get_entity_class_by_entity_name(type_key)
        result = instance.suggest(request.user, filter_str, limit, init_filter)  # Вызываем ее метод
    else:
        result = dict(error='Не указан класс модели (class_name)')

    return JSONResponse(result)
