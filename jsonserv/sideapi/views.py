from ipware import get_client_ip  # Получение ip-пользователя
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import BasicAuthentication
from django.contrib.auth.views import LoginView
from django.contrib.postgres.aggregates import StringAgg
from jsonserv.rest.views import JSONResponse
from jsonserv.core.models_dispatcher import ModelsDispatcher
from jsonserv.core.models import Entity
from jsonserv.core.views import type_fields
from jsonserv.docarchive.models import FileDocument
from jsonserv.docarchive.views import get_file
from jsonserv.pdm.serializers import PartObjectSerializerDetailed
from jsonserv.sideapi.serializers import FileSuggestSerializer, SearchFilesSerializer

# На время отладки
from rest_framework.decorators import api_view


class RestLoginView(LoginView):
    """Доработанное представление для аутентификации через REST"""
    template_name = 'rest_login.html'  # Шаблон формы входа
    
    def form_valid(self, form):
        # Обработка входа пользователя
        # Наполнение и сохранение модели транзакции
        session_model = form['session'].save(commit=False)
        session_model.user_ip, is_routable = get_client_ip(self.request)
        session_model.user = form['user'].get_user()
        # Сохранение модели транзакции
        session_model.save()
        # Добавление в параметры django-сессии идентификатора транзакции
        self.request.session['user_session_id'] = session_model.id

        return None
    

class FileSuggest(ListAPIView):
    queryset = FileDocument.objects.all()
    serializer_class = FileSuggestSerializer
    name = 'file-suggest'
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    search_fields = (
        '^doc_code',
    )
    ordering_fields = (
        'doc_code',
    )
    permission_classes = (
        IsAuthenticated,
    )


class SearchFiles(ListAPIView):
    serializer_class = SearchFilesSerializer
    name = 'file-search'
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    authentication_classes = (BasicAuthentication,)
    permission_classes = (
        IsAuthenticated,
    )

    def get_queryset(self):
        search = self.request.GET.get('search', '')
        return FileDocument.objects.filter(
            doc_code__icontains=search,
            document_versions__digital_files__data_format='application/pdf',  # Только pdf
            document_versions__version_objects__old_version=False
            ).annotate(
                objects=StringAgg(
                "document_versions__version_objects__entity__code",
                delimiter=", ",
                distinct=True,
                ordering="document_versions__version_objects__entity__code",
                )
            ).values(
            'document_versions__pk',
            'document_versions__version_num',
            'document_versions__notice__code',
            'document_versions__change_num',
            'document_versions__change_type__list_value',
            'document_versions__digital_files__file_name',
            'document_versions__digital_files__pk',
            'objects'
        ).order_by(
            'document_versions__digital_files__file_name',
            'document_versions__version_num'
        )[0:10]


class GetFile(APIView):
    """Представление для получения файла из архива"""
    name = 'get_file'
    authentication_classes = (BasicAuthentication, )
    permission_classes = (IsAuthenticated, )

    @staticmethod
    def get(request, **kwargs):
        return get_file(request, **kwargs)


@api_view(['GET', ])
def objects_list_get(request, type_key='', sub_type_key=''):
    """Получение полного списка объектов сущности type_key"""
    if type_key:
        instance = ModelsDispatcher.get_entity_class_by_entity_name(type_key)  # Получаем модель
        if type_key == 'partobject':  # Для этого типа дополнительное условие - подтип
            result = instance.objects.filter(part_type=sub_type_key).order_by('code').values('pk', 'code')
        else:
            result = instance.objects.all().order_by('code').values('pk', 'code')
    else:
        result = dict(error='Не указан класс модели-списка (type_key)')

    return JSONResponse(result)


@api_view(['GET', ])
def prop_values_get(request, id=''):
    """Получение полного списка свойств объекта с их значениями по идентифкатору"""
    if id:
        try:
            entity = Entity.objects.get(pk=id)
            type_key = entity.type_key_id
            instance = ModelsDispatcher.get_entity_class_by_entity_name(type_key)  # Получаем модель
            obj = instance.objects.get(pk=id)
            if type_key == 'partobject':
                sub_type_key = obj.part_type_id
            else:
                sub_type_key = ''
            # Получаем список отображаемых свойств
            props = type_fields(type_key, sub_type_key, request.user)
            # Получаем список значений свойств
            serializer = PartObjectSerializerDetailed(obj)
            # Приклепляем значения свойств к свойствам
            data = serializer.data
            for a in props:
                name = a['name']
                a['value'] = data[name]
            # Выводим результат
            result = props

        except Entity.DoesNotExist:
            return Response({"message": "Исходный объект не найден"}, status=status.HTTP_404_NOT_FOUND)
        

    else:
        result = dict(error='Не указан идентификатор объекта (id)')

    return JSONResponse(result)