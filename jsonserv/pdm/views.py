from itertools import chain
import json
from django.db.models import Func, F, Value, CharField, IntegerField
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from jsonserv.core.fileutils import get_sql_file_path
from jsonserv.core.dbutils import execute_sql_from_file

from jsonserv.core.models import Entity, Link, UserSettings
from jsonserv.pdm.models import Designer, NoticeLink, PartLink, PartObject, Role, Route
from jsonserv.pdm.serializers import (PartObjectRefSerializer, SameStaffSerializerList,
                                      ParentSerializerList, RolesDesignersSerializerList,
                                      NomCodesObjectSerializerList, RouteSerializer)
from jsonserv.docarchive.models import EntityDocumentVersion

from jsonserv.rest.views import JSONResponse


class LevenshteinLessEqual(Func):
    """Функция вычисления расстояния Левенштейна"""
    template = "%(function)s(%(expressions)s, '%(search_term)s', %(depth)s)"
    function = "levenshtein_less_equal"

    def __init__(self, expression, search_term, depth, **extras):
        super(LevenshteinLessEqual, self).__init__(
            expression,
            search_term=search_term,
            depth=depth,
            **extras
        )


@api_view(['GET', ])
def get_parents(request, pk):
    """Предоставление списка объектов-родителей"""
    # Непосредственные родители по всем связям
    parents = Link.objects.filter(child=pk).exclude(
        # Связь с извещениями отображается отдельно
        # Связь с архивными документами не отображается (пока) TODO: Реализовать через права доступа
        link_class__in=('noticelink', 'arcdocumentobject')
    ).order_by(
        'parent__code'
    ).annotate(
        child__partobject__prod_order_id=Value(None, IntegerField()),
        child__partobject__prod_order__code=Value(None, CharField())
    ).values('parent__type_key', 'parent_id', 'parent__code', 'parent__partobject__title', 'quantity',
             'parent__partobject__prod_order_id', 'parent__partobject__prod_order__code')
    # Экземпляры, входящие в состав заказов
    in_orders = PartLink.objects.filter(
        child__partobject__origin=pk,
        child__partobject__prod_order__isnull=False  # Только относящиеся к заказам
    ).order_by(
        'parent__code',
        'parent__partobject__prod_order__code'
    ).annotate(
        parent__partobject__prod_order_id=F('child__partobject__prod_order_id'),
        parent__partobject__prod_order__code=F('child__partobject__prod_order__code')
    ).values('parent__type_key', 'parent_id', 'parent__code', 'parent__partobject__title', 'quantity',
             'parent__partobject__prod_order_id', 'parent__partobject__prod_order__code')
    if request.GET.get('root', False):  # Признак отображения корневого уровня
        # Соединяем результаты запросов, добавляя экземпляры из заказов
        rows = chain(parents, in_orders)
    else:
        rows = parents
    serializer = ParentSerializerList(rows, many=True)
    return Response(serializer.data)


@api_view(['GET', ])
def get_curdesingner(request):
    """Получение разработчика-текущего пользователя"""
    des = dict()  # Пустой словарь на случай, если не найдем
    if request.user.id:
        user_id = request.user.id
        # Получаем текущего пользователя как разработчика
        himself = Designer.get_by_user(user_id).first()
        if himself:
            des = dict(pk=himself['designer__pk'],
                       value=himself['designer__designer'])
    return JSONResponse(des)


@api_view(['GET', ])
def get_roledesingners(request):
    """Предоставление списка подходящих разработчиков для каждой роли"""
    # Проверяем наличие данного набора в настройках пользователя
    cur_set = UserSettings.objects.filter(user=request.user, setting_id='designers').first()
    if cur_set:
        # Возвращаем набор из настроек
        return Response(json.loads(cur_set.setting_value))
    # Иначе обрабатываем статистику по ролям
    rows = Role.objects.all()
    serializer = RolesDesignersSerializerList(
        rows, many=True, context={'user_id': request.user.id})
    return Response(serializer.data)


@api_view(['GET', ])
def get_nomcodes(request):
    """Предоставление списка номенклатурных кодов, начинающихся на указанные символы"""
    nom_code = request.GET.get('nom_code', '')
    if nom_code:
        rows = PartObject.objects.filter(nom_code__startswith=nom_code).order_by('nom_code')
    else:
        # Просто все строки, где указан номенклатурный код
        rows = PartObject.objects.filter(nom_code__isnull=False).order_by('nom_code')
    serializer = NomCodesObjectSerializerList(rows, many=True)
    return Response(serializer.data)


@api_view(['GET', ])
def get_same(request, pk):
    """Предоставление списка похожих на указанный объект"""
    # Получение свойств исходного объекта
    try:
        obj = PartObject.objects.get(pk=pk)
    except PartObject.DoesNotExist:
        return Response({"message": f"Не найден указаный объект"}, status=status.HTTP_404_NOT_FOUND)
    # Параметры запроса
    code = obj.code  # Обозначение
    depth = request.GET.get('depth', 2)  # Глубина
    rows = PartObject.objects.annotate(
        lev_dist=LevenshteinLessEqual(F('code'), code, depth)
    ).filter(lev_dist__lte=depth).exclude(pk=pk)
    serializer = PartObjectRefSerializer(rows, many=True)
    return Response(serializer.data)


@api_view(['GET', ])
def get_samestaff(request, pk):
    """Предоставление списка похожих по составу на указанный объект"""
    sql_file = get_sql_file_path('pdm', 'same_staff_get.sql')
    rows = execute_sql_from_file(sql_file, dict(object_id=pk), to_dict=True)
    serializer = SameStaffSerializerList(rows, many=True)
    return Response(serializer.data)
    # return JSONResponse(rows)


@api_view(['GET', ])
def parts_compare(request):
    """Сравнение составов двух объектов"""
    first_id = request.GET.get('first', 0)
    second_id = request.GET.get('second', 0)
    if not first_id or not second_id:
        return Response({"message": "Не указаны идентификаторы объектов (first, second)"},
                        status=status.HTTP_404_NOT_FOUND)
    # Общий запрос
    plst = PartLink.get_staff_queryset().annotate(
        code=F('child__code'), title=F('child__partobject__title'), part_type=F('child__partobject__part_type')
    ).values('child', 'code', 'title', 'part_type')
    # Получение состава первого объекта
    s1 = plst.filter(parent=first_id)
    k1 = [i['child'] for i in s1]
    # Получение состава второго объекта
    s2 = plst.filter(parent=second_id)
    k2 = [i['child'] for i in s2]
    # Выбираем то, что есть в обоих составах
    comm = [x for x in s2 if x['child'] in k1]
    # Выбираем то чего нет в составе второго
    d1 = [x for x in s1 if x['child'] not in k2]
    # Выбираем то, чего нет в составе первого
    d2 = [x for x in s2 if x['child'] not in k1]
    # Собираем в общий список
    cmp = list()
    for i in comm:
        i['group'] = "Совпадают"
        cmp.append(i)
    for i in d1:
        i['group'] = "Входят только в первый"
        cmp.append(i)
    for i in d2:
        i['group'] = "Входят только во второй"
        cmp.append(i)
    return JSONResponse(cmp)


@api_view(['GET', ])
def get_into_top(request, pk):
    """Предоставление входимости до верхнего уровня"""
    sql_file = get_sql_file_path('pdm', 'into_top.sql')
    rows = execute_sql_from_file(sql_file, dict(
        object_id=pk, quantity=1, link_classes=None), to_dict=True)
    # serializer = IntoTopSerializerList(rows)
    return JSONResponse(rows)


@api_view(['POST', ])
def create_same_route(request, pk):
    """Создание подобного указанному маршруту маршрута"""
    try:
        source = Route.objects.get(pk=pk)  # Получение исходного маршрута
    except Route.DoesNotExist:
        return Response({"message": "Исходный маршрут не найден"}, status=status.HTTP_404_NOT_FOUND)
    object_id = request.data['object']
    user_session_id = request.session.get('user_session_id', 0)
    if user_session_id:  # обработка нулевого значения user_session_id
        try:
            # Объект получатель маршрута
            obj = PartObject.objects.get(pk=object_id)
        except PartObject.DoesNotExist:
            return Response({"message": "Объект получатель маршрут не найден"}, status=status.HTTP_404_NOT_FOUND)
        same_route = source.create_same(obj, user_session_id)
        serializer = RouteSerializer(same_route)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response({"message": 'Не указан идентификатор сессии'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST', ])
def renum(request):
    """Перенумерация позиций в составе"""
    # Идентификатор родителя в составе которого меняют позиции
    parent_id = request.data["parent"]
    # Идентификатор связи, с которой начинаю изменения
    link_id = request.data["pk"]
    position = request.data["position"]  # Начальный номер позиции
    # Получение состава объекта
    links = PartLink.get_staff_queryset()
    links = links.filter(parent_id=parent_id)

    user_session_id = request.session.get('user_session_id', 1)
    # TODO: Сделать нормальную обработку нулевого значения user_session_id
    # Перебираем все записи
    cnt = 0  # Счетчик измененных связей
    do_change = False  # Признак необходимости перенумерации
    for link in links:
        if do_change or link.pk == link_id:
            do_change = True
            # Изменяем свойства связи
            link.position = position
            link.edt_sess = user_session_id
            # Сохраняем с признаком отключения проверок (чтобы не срабатывали повторы позиций)
            link.save(no_check=True)
            cnt += 1
            position += 1

    return Response({"message": f"Изменено {cnt} связей"}, status=status.HTTP_201_CREATED)


@api_view(['POST', ])
def update_order_part(request, pk):
    """Обновление объекта в заказе на основе данных из КД"""
    try:
        obj = PartObject.objects.get(pk=pk)  # Получение объекта
    except PartObject.DoesNotExist:
        return Response({"message": "Объект заказа не найден"}, status=status.HTTP_404_NOT_FOUND)
    user_session_id = request.session.get('user_session_id', 0)
    # Вызываем соответствующий метод объекта
    mess_txt, err = obj.update_in_order(user_session_id, request.data.get('properties', False),
                                        request.data.get('staff', False), request.data.get('notices', False))
    if err:
        return Response(mess_txt, status=status.HTTP_404_NOT_FOUND)

    if request.data.get('files', False):
        # Для замены файлов используем специальный метод
        EntityDocumentVersion.update_documents_in_order(pk, obj.origin_id, user_session_id, mess_txt)

    if len(mess_txt):
        return Response({"message": f"Свойства объекта в заказе изменены: {', '.join(mess_txt)}"},
                        status=status.HTTP_201_CREATED)

    return Response({"message": f"Свойства объекта в заказе совпадают с исходным"},
                    status=status.HTTP_201_CREATED)
