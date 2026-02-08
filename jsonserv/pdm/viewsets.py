# from itertools import chain
import django_filters  # Специальные фильтры
from django.db.models import Q
from rest_framework.serializers import ValidationError
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
import json

from jsonserv.exchange.exchange_utils import ModelsDispatcher
from jsonserv.core.fileutils import get_sql_file_path
from jsonserv.core.dbutils import execute_sql_from_file
from jsonserv.core.models import check_access, fn_head_key

from jsonserv.core.viewsets import CommonViewSet, ListViewSet, DateEqualFilter

from jsonserv.pdm.models import (Billet, Designer, DesignMater, DesignRole, Notice, NoticeLink, NoticeRecipient,
                                 Operation, PartObjectFormat, PartLink, PartObjectFast, PartType,
                                 PartObject, Rendition, Role, Route, RoutePoint, TpResource, TpRow, TypeSizeMater,
                                 TypeSizeSort, RenditionTail)
from jsonserv.pdm.serializers import (BilletSerializer, BilletSerializerList,
                                      DesignerSerializer, DesignerSerializerDetailed, DesignerSerializerList,
                                      DesignMaterSerializer, DesignMaterSerializerList,
                                      DesignRoleSerializer, DesignRoleSerializerList,
                                      NoticeSerializer, NoticeSerializerDetailed, NoticeSerializerList,
                                      NoticeLinkSerializer, NoticeLinkSerializerList,
                                      NoticeRecipientSerializer, NoticeRecipientSerializerList,
                                      OperationSerializer, OperationSerializerDetailed, OperationSerializerList,
                                      PartObjectFormatSerializer, PartObjectFormatSerializerList,
                                      PartLinkSerializer, PartLinkSerializerList,
                                      PartObjectSerializer, PartObjectSerializerDetailed, PartObjectSerializerList,
                                      RenditionSerializer, RenditionSerializerList, RoleSerializer,
                                      RouteSerializer, RouteSerializerDetailed, RoutePointSerializer,
                                      RoutePointSerializerDetailed, RoutePointSerializerList,
                                      TpResourceSerializer, TpResourceSerializerDetailed, TpResourceSerializerList,
                                      TpResourceModelSerializer,
                                      TpRowSerializer, TpRowSerializerDetailed, TpRowSerializerList,
                                      TypeSizeMaterSerializer, TypeSizeMaterSerializerList,
                                      TypeSizeSortSerializer, TypeSizeSortSerializerList)


# Класс пагинации для получения больших массивов строк Пока не используется
class LargeResultsSetPagination(PageNumberPagination):
    page_size = 10000
    page_size_query_param = 'limit'
    page_query_param = 'offset'
    max_page_size = 10000


class BilletViewSet(CommonViewSet):
    queryset = Billet.objects.all()
    serializer_class = BilletSerializer
    serializer_class_list = BilletSerializerList
    paginator = None  # Отключение пагинации

    # Поля фильтрации
    filterset_fields = (
        'parent',
        'child',
    )


class DesignerViewSet(CommonViewSet):
    queryset = Designer.objects.all()
    serializer_class = DesignerSerializer
    serializer_class_detailed = DesignerSerializerDetailed
    serializer_class_list = DesignerSerializerList

    # Поля поиска
    search_fields = (
        'designer',
    )


class DesignMaterViewSet(CommonViewSet):
    queryset = DesignMater.objects.all()
    serializer_class = DesignMaterSerializer
    serializer_class_list = DesignMaterSerializerList

    # Поля фильтрации
    filterset_fields = (
        'parent',
    )


class DesignRoleViewSet(CommonViewSet):
    queryset = DesignRole.objects.all().order_by('role__order_num', 'role__list_value')
    serializer_class = DesignRoleSerializer
    serializer_class_list = DesignRoleSerializerList
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    # Поля фильтрации
    filterset_fields = (
        'subject',
    )


class NoticeFilter(django_filters.FilterSet):
    """Особые фильтры для списка извещений"""
    min_date = django_filters.DateFilter(field_name="notice_date", lookup_expr='gte')
    max_date = django_filters.DateFilter(field_name="notice_date", lookup_expr='lte')
    equal_date = DateEqualFilter(field_name="notice_date")

    class Meta:
        model = Notice
        fields = ['group', 'equal_date', 'min_date', 'max_date']


class NoticeViewSet(CommonViewSet):
    queryset = Notice.objects.all().order_by('-notice_date', '-approve_date', 'code')
    serializer_class = NoticeSerializer
    serializer_class_detailed = NoticeSerializerDetailed
    serializer_class_list = NoticeSerializerList
    filterset_class = NoticeFilter  # Особые настройки фильтрации

    # Поля поиска
    search_fields = (
        'code',
        'description'
    )


class NoticeLinkViewSet(CommonViewSet):
    queryset = NoticeLink.objects.exclude(
        child__type_key_id='arcdocument'
    ).order_by('child__code')  # Ссылки на архивные документы не отображаем
    serializer_class = NoticeLinkSerializer
    serializer_class_list = NoticeLinkSerializerList
    paginator = None

    # Поля фильтрации
    filterset_fields = (
        'parent',
        'child'
    )

    def partial_update(self, request, *args, **kwargs):
        """Проведение извещения надо обрабатывать по особому"""
        if self.kwargs.get('is_done', False): # Извещение не проведено и не проводится
            return super().partial_update(request, *args, **kwargs)
        else:  # Извещение проведено или проводится
            nl = NoticeLink.objects.get(pk=self.kwargs['pk'])  # Получаем экземпляр связи
            if nl.link_trace(request.session.get('user_session_id', 1)):  # Проверка и дополнительные действия
                # print('super().partial_update')
                return super().partial_update(request, *args, **kwargs)
        raise ValidationError('Действие над проведенным извещением')


class NoticeRecipientViewSet(CommonViewSet):
    queryset = NoticeRecipient.objects.all().order_by('child__code')
    serializer_class = NoticeRecipientSerializer
    serializer_class_list = NoticeRecipientSerializerList

    # Поля фильтрации
    filterset_fields = (
        'parent',
        'child'
    )


class OperationViewSet(CommonViewSet):
    queryset = Operation.objects.all().order_by('operation_name')
    serializer_class = OperationSerializer
    serializer_class_detailed = OperationSerializerDetailed
    serializer_class_list = OperationSerializerList

    # Поля фильтрации
    filterset_fields = (
        'group',
    )
    # Поля поиска
    search_fields = (
        'operation_name',
        'full_name'
    )


class PartObjectFormatViewSet(CommonViewSet):
    queryset = PartObjectFormat.objects.order_by('format__list_value').all()
    serializer_class = PartObjectFormatSerializer
    serializer_class_list = PartObjectFormatSerializerList
    paginator = None  # Отключение пагинации

    # Поля фильтрации
    filterset_fields = (
        'part_object',
    )


class PartLinkViewSet(CommonViewSet):
    queryset = PartLink.get_staff_queryset()
    serializer_class = PartLinkSerializer
    serializer_class_list = PartLinkSerializerList
    paginator = None  # Отключение пагинации

    # Поля фильтрации
    filterset_fields = (
        'parent',
        'child',
    )

    def create(self, request, *args, **kwargs):
        # Создание нового экземпляра объекта в заказе
        if 'order' in request.data and request.data['order']:  # Если запись добавляется в заказ
            # Находим или создаем объект в заказе
            crtd_sess_id = request.session.get('user_session_id', 1)
            child_id = PartObject.get_or_create_item_in_order(request.data['child'], request.data['order'],
                                                              crtd_sess_id)
            # Подменяем исходный
            request.data['child'] = child_id
        elif not request.data['child']:  # Если входящий объект не указан
            # Надо создавать новый
            # Получение параметров создания по умолчанию
            init_params = PartType.get_init_params(request.data['part_type'])
            if init_params:
                prop_dict = json.loads(init_params)  # Преобразуем в словарь
            else:
                prop_dict = dict()
            # Дополняем переданными параметрами
            prop_dict['code'] = request.data['code']
            prop_dict['title'] = request.data['title']
            if request.data['unit']:  # Может быть передана ЕИ
                prop_dict['unit'] = request.data['unit']
            prop_dict['part_type'] = request.data['part_type']
            prop_dict['crtd_sess'] = request.session.get('user_session_id', 1)

            # Создаем новый объект
            serializer = PartObjectSerializer(data=prop_dict)
            if serializer.is_valid():
                child = serializer.save()
                request.data['child'] = child.pk  # Подменяем исходный id
            else:
                raise ValidationError('Ошибка создания объекта в составе')

        return super().create(request, *args, **kwargs)


class PartObjectFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search')  # Особая обработка поискового запроса
    part_type = django_filters.Filter(field_name='part_type')
    group = django_filters.Filter(field_name='group')

    class Meta:
        model = PartObjectFast
        # Поля поиска
        fields = (
            'search',
        )

    def filter_search(self, queryset, name, value):
        key_value = fn_head_key(str(value))  # Ключ для поиска в поле head_key
        # Комбинация поиска по полям, в т.ч. по head_key
        return queryset.filter(
            Q(code__icontains=value) |
            Q(description__icontains=value) |
            Q(title__icontains=value) |
            Q(nom_code__icontains=value) |
            Q(head_key__icontains=key_value)
        )


class PartObjectViewSet(CommonViewSet):
    queryset = PartObject.objects.all()
    serializer_class = PartObjectSerializer
    serializer_class_detailed = PartObjectSerializerDetailed
    serializer_class_list = PartObjectSerializerList
    # pagination_class = LargeResultsSetPagination  # Увеличенный размер страниц (при запросе)

    def get_queryset(self):
        if self.action == 'list':  # Для списков
            # Используем другую модель - быструю
            qs = PartObjectFast.objects.all()
            # Применяем к ней другой фильтр
            self.filter = PartObjectFilter(self.request.GET, queryset=qs)
            return self.filter.qs
        return PartObjectViewSet.queryset  # Иначе по умолчанию

    def partial_update(self, request, *args, **kwargs):
        # Особая обработка некоторых полей
        def update_states(objs):
            """Обработка обновления состояний у групп объектов"""
            if objs:
                for s in objs:
                    # Проверка прав доступа на редактирование к состоянию (без состояния тоже редактируем)
                    if s.state is None or check_access(s.state.edit_right, self.request.user, True):
                        # Если доступ на редактирование к состоянию есть
                        s.state_id = request.data['state']  # Копируем состояние
                        s.edt_sess = request.session.get('user_session_id', 1)
                        s.save()

        if 'design_mater' in request.data and request.data['design_mater']:  # Если передан конструкторский материал
            if not DesignMater.is_exists(self.kwargs['pk'], request.data['design_mater']):
                # Если сейчас указан другой материал (или не указан) # создаем новую запись
                n = DesignMater(parent_id=self.kwargs['pk'], child_id=request.data['design_mater'])
                n.crtd_sess_id = request.session.get('user_session_id', 1)
                n.save()
        staff_through = request.data.pop('staff_through', False)
        all_renditions = request.data.pop('all_renditions', False)
        if staff_through:  # Если надо обработать весь состав
            # Получение списка входящих объектов
            if all_renditions:
                # С составом исполнений
                sql_file = get_sql_file_path('pdm', 'all_linked_with_renditions.sql')
            else:
                sql_file = get_sql_file_path('pdm', 'all_linked_through.sql')
            rows = execute_sql_from_file(sql_file, dict(parent_id=kwargs['pk'], quantity=1, link_classes='partlink'))
            ids = list(map(lambda x: x[0], rows))  # Список входящих идентификаторов
            ids.remove(int(kwargs['pk']))  # Удаляем родителя (он не обрабатывается)
            if ids:
                # Перебираем входящие
                objs = PartObject.objects.filter(pk__in=ids).exclude(state_id=request.data['state'])
                update_states(objs)
        elif all_renditions:  # Если надо обработать только исполнения
            # Получение списка исполнений
            objs = PartObject.objects.filter(tail_rendition__parent=kwargs['pk']).all()
            update_states(objs)
            
        return super().partial_update(request, *args, **kwargs)

    # Поля фильтрации
    filterset_fields = (
        'group',
        'part_type'
    )


class RenditionViewSet(CommonViewSet):
    queryset = Rendition.objects.all().order_by('tail__list_value')
    serializer_class = RenditionSerializer
    serializer_class_list = RenditionSerializerList
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    def get_queryset(self):
        if self.action == 'list':
            # Проверяем, не является ли объект сам исполнением
            filter_id = self.request.query_params.get('parent', 0)
            rend = Rendition.objects.filter(rendition_id=filter_id).first()
            if rend:
                # Берем родителя для фильтрации
                filter_id = rend.parent_id
            return Rendition.objects.filter(parent_id=filter_id).order_by('tail__list_value')
        return RenditionViewSet.queryset  # Иначе по умолчанию

    def create(self, request, *args, **kwargs):
        # Создание объекта с новым обозначением
        parent = PartObject.objects.get(pk=request.data['parent'])
        code = RenditionTail.generate_by_id(parent.code, request.data['tail'])
        crtd_sess = request.session.get('user_session_id', 1)
        # Создаем объект и добавляем ссылку на него
        rendition = parent.create_same(code, crtd_sess)
        request.data['rendition'] = rendition.pk
        # Копирование связей (состава)
        cnt = 0  # Счетчик связей
        for link_class in ModelsDispatcher.same_link_classes:
            # У каждого класса должен быть соответствующий метод
            cnt += link_class.create_same(parent, rendition, crtd_sess)
        return super().create(request, *args, **kwargs)


class RouteViewSet(CommonViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    serializer_class_detailed = RouteSerializerDetailed
    serializer_class_list = RouteSerializerDetailed
    pagination_class = None

    # Поля фильтрации
    filterset_fields = (
        'subject',
        'group_route'
    )


class RoleViewSet(ListViewSet):
    queryset = Role.objects.all().order_by('order_num', 'list_value')
    serializer_class = RoleSerializer # get_list_serializer_class(Role)
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    # Поля фильтрации
    filterset_fields = (
        'list_value',
    )


class RoutePointViewSet(CommonViewSet):
    queryset = RoutePoint.objects.all()
    serializer_class = RoutePointSerializer
    serializer_class_detailed = RoutePointSerializerDetailed
    serializer_class_list = RoutePointSerializerList
    pagination_class = None

    def get_queryset(self):
        if self.action == 'list':
            return RoutePoint.objects.all().values(
                'pk',
                'order_num',
                'place__code'
            ).order_by(
                'order_num',
            )
        return RoutePointViewSet.queryset

    # Поля фильтрации
    filterset_fields = (
        'route',
    )


class TpResourceViewSet(CommonViewSet):
    queryset = TpResource.objects.all()
    serializer_class = TpResourceSerializer
    serializer_class_detailed = TpResourceSerializerDetailed
    serializer_class_list = TpResourceSerializerList
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    def get_queryset(self):
        if self.action == 'list':
            replaced = self.request.query_params.get('replaced', 0)
            # Или Замены или Не замены
            a = TpRow.objects.all() if replaced else TpRow.objects.filter(replaced__isnull=True)
            return a.values(
                'pk',
                'order_num',
                'tpresource__child',
                'tpresource__child__code'
            ).order_by('order_num')
        elif self.action == 'retrieve':
            return TpRow.objects.all().values(
                'pk',
                'row_type',
                'replaced',
                'tpresource__net_weight',
                # 'tpresource__k_zap',
                'tpresource__quantity',
                # 'tpresource__black_weight',
                'tpresource__notice',
                'order_num',
                'tpresource__child',
                'tpresource__child__partobject__nom_code',
                'tpresource__child__partobject__unit__short_name',
            )
        elif self.action in ('partial_update', 'destroy'):
            return TpRow.objects.all()
        return TpResourceViewSet.queryset

    def get_serializer_class(self):
        # Нужен для подмены сериалайзера при создании
        if self.action == 'create':
            return TpResourceModelSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        # Добавление идентификатора сессии к данным о tp_row
        request.data['tp_row']['crtd_sess'] = request.session.get('user_session_id', 1)
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # TODO: Перенести отработку связанных и подчиненных объектов в модель
        user_session_id = request.session.get('user_session_id', 1)
        # Сначала удаляем строку техпроцесса
        instance_t = self.get_object()
        instance_t.dlt_sess = user_session_id  # Указание идентификатора сессии
        self.perform_destroy(instance_t)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Поля фильтрации
    filterset_fields = (
        'parent',
        'route_point',
        'route',
        'replaced'
    )


class TpRowViewSet(CommonViewSet):
    queryset = TpRow.objects.all()
    serializer_class = TpRowSerializer
    serializer_class_detailed = TpRowSerializerDetailed
    serializer_class_list = TpRowSerializerList
    pagination_class = None

    def get_queryset(self):
        if self.action == 'list':
            # Только операции
            return TpRow.objects.filter(row_type_id=1).values(
                'pk',
                'order_num',
                'operation__operation_name'
            ).order_by(
                'order_num',
            )
        return TpRowViewSet.queryset

    # Поля фильтрации
    filterset_fields = (
        'route_point',
        'route',
    )


class TypeSizeMaterViewSet(CommonViewSet):
    queryset = TypeSizeMater.objects.all()
    serializer_class = TypeSizeMaterSerializer
    serializer_class_list = TypeSizeMaterSerializerList

    # Поля фильтрации
    filterset_fields = (
        'child',
    )


class TypeSizeSortViewSet(CommonViewSet):
    queryset = TypeSizeSort.objects.all()
    serializer_class = TypeSizeSortSerializer
    serializer_class_list = TypeSizeSortSerializerList

    # Поля фильтрации
    filterset_fields = (
        'child',
    )
