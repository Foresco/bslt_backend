import os
from django.http import HttpResponse
from django.views.generic import View
from django.db.models import Q
from django.db.models.functions import Lower
from django.conf import settings  # для обращения к настройкам
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

import logging

from jsonserv.core.fileutils import (get_temp_file_path, handle_uploaded_file, delete_file,
                                     compute_check_sum, http_unload_file, get_mime_type)
from jsonserv.core.views import check_access
from jsonserv.pdm.models import Role
from jsonserv.docarchive.models import (EntityDocumentVersion, DigitalFile, DocumentVersion, EntityTypeFileArchive,
                                        FileDocument, FileUpload, DocumentType,
                                        UploadArcdoc, VersionDesignRole)
from jsonserv.docarchive.serializers import (DocumentsList, FileDocumentSerializer, DocumentVersionSerializer,
                                             DocumentTypeSerializerList, FileDocumentVersionsList,
                                             NoticeLinkDocSerializerList,
                                             EntityDocumentVersionSerializer, UploadArcdocsSerializerList,
                                             VersionDesignRoleSerializer)

from jsonserv.docarchive.accessory.fileuploadprepare import FileUploadImport
from jsonserv.rest.views import JSONResponse
from jsonserv.docarchive.file_prepare import prepare_file_for_unload, prepare_file_for_store

logger = logging.getLogger('basalta')


class EntityDocumentsList(ListAPIView):
    serializer_class = DocumentsList
    name = 'entity-documents-list'
    paginator = None  # Отключение пагинации

    def get_queryset(self):
        all_versions = self.request.GET.get('all_versions', 'false') not in ('false', '0')
        return EntityDocumentVersion.get_documents_queryset(all_versions)

    # Поля фильтрации
    filterset_fields = (
        'entity',
    )


@api_view(['GET', ])
def get_digitalfile(request):
    """Получение свойств файла из архива"""
    des = list()  # Пустой список на случай, если не найдем
    file_names = request.query_params.getlist('file_names[]')
    archive = EntityTypeFileArchive.get_archive_id(request.GET.get('entity', 0))
    if file_names:
        d_files = DigitalFile.objects.select_related('document_version').filter(
            file_name__in=file_names, folder__archive_id=archive,
        ).order_by('-document_version__version_num')
        if d_files:
            for d_file in d_files:
                des.append(
                    dict(pk=d_file.pk, file_name=d_file.file_name, version_num=d_file.document_version.version_num))
    return JSONResponse(des)


class DocumentTypesList(ListAPIView):
    """Список типов документов
    в отличие от стандартного из List анализируются права доступа пользователя"""
    serializer_class = DocumentTypeSerializerList
    name = 'document-types-list'
    paginator = None  # Отключение пагинации

    def list(self, request, *args, **kwargs):
        rows = DocumentType.objects.all().order_by('order_num', 'list_value')
        result = list()
        for row in rows:
            if check_access(row.value_right, request.user, True):  # Если этот тип доступен пользователю
                result.append(dict(pk=row.pk, list_value=row.list_value))
        serializer = DocumentTypeSerializerList(result, many=True)
        return Response(serializer.data)


class FileDocumentVersionsList(ListAPIView):
    """Список файловых документов"""
    serializer_class = FileDocumentVersionsList
    name = 'file-documents-list'
    queryset = DigitalFile.objects.filter(
        Q(document_version__document_roles__role_id=1) | Q(document_version__document_roles__role_id__isnull=True)
    ).order_by(
        Lower('file_name'),
        'document_version__version_num'
    ).values(
        'pk',
        'file_name',
        'document_version_id',
        'document_version__version_num',
        'document_version__notice',
        'document_version__notice__code',
        'document_version__change_num',
        'document_version__change_type__list_value',
        'document_version__document__description',
        'document_version__document__doc_type__list_value',
        'document_version__document_roles__designer__designer',
        'crtd_sess__session_datetime',
        'crtd_sess__user__username'
    )

    def get_queryset(self):
        """Фильтрация списка"""
        search = self.request.query_params.get('search')
        if search is not None:
            return FileDocumentVersionsList.queryset.filter(file_name__icontains=search)
        return FileDocumentVersionsList.queryset


class FileUploadPutView(APIView):
    """Представление для загрузки информации о загрузке файлов из файла xlsx"""
    name = "file-upload-put"
    parser_classes = (MultiPartParser,)

    def post(self, request):
        # return Response({"report": 'Тестовое сообщение'}, status=status.HTTP_201_CREATED)
        file_name = request.data.get('file_name', '')
        prefix = request.data.get('prefix', None)
        stage = request.data.get('stage', None)
        # Пустые значения приходят как null
        if prefix == 'null':
            prefix = None
        if stage == 'null':
            stage = None
        if not file_name:
            return Response({"message": 'Не указан файл для загрузки'}, status=status.HTTP_400_BAD_REQUEST)
        # Проверка существования загрузки с таким именем
        if FileUpload.objects.filter(file_name=file_name).count():
            return Response({"message": 'Такая загрузка уже есть в базе данных'}, status=status.HTTP_400_BAD_REQUEST)
        # Перенос файла во временную директорию
        trgt = os.path.join(getattr(settings, 'TEMP_DIR', 'temp'), file_name)
        if handle_uploaded_file(request.data['file'], trgt):
            crtd_sess_id = request.session.get('user_session_id', 1)
            fp = FileUploadImport(trgt, file_name, stage, prefix, crtd_sess_id)
            # Разбираем данные в таблице
            result = fp.import_table()
            if result:  # Значит, были ошибки
                return Response({"message": result}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"report": fp.report}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "Ошибка получения файла"}, status=status.HTTP_400_BAD_REQUEST)


def get_file(request, **kwargs):
    # Функция получения файла для использования в нескольких местах
    id = kwargs.get("id", None)
    if id:
        file = DigitalFile.objects.get(pk=id)
        if file:
            if os.path.exists(file.file_path):
                file_path, file_name, data_format = prepare_file_for_unload(request, file)
                return http_unload_file(file_path, file_name, data_format)
            else:
                message = f'Указанный файл {file.file_path} не найден в архиве'
        else:
            message = 'Не удалось найти файл в базе данных'
    else:
        message = 'Не указан идентификатор файла'
    return HttpResponse(message)


class GetDocArchiveFile(View):
    """Представление для получения файла из архива"""
    name = "file"

    @staticmethod
    def get(request, **kwargs):
        if not request.user.is_authenticated:
            # Проверка, что пользователь авторизован
            return HttpResponse('Unauthorized', status=401)
        if not request.user.has_perm('docarchive.view_digitalfile'):
            # Проверка наличия права Электронный файл. Просмотр
            return HttpResponse('Недостаточно прав для получения файлов')
        # Вызываем универсальную функцию
        return get_file(request, **kwargs)


class UploadFileView(APIView):
    """Представление для загрузки новых файлов в архив через http-протокол"""
    name = 'upload-file'
    parser_classes = (MultiPartParser,)

    def __init__(self):
        self.request_data = dict()  # словарь с переданными параметрами
        super().__init__()

    def copy_params(self, request):
        # Копирование переданного запроса, так как исходный нельзя менять (immutable)
        for a in ('change_num', 'change_type', 'data_format', 'description', 'design_role_id', 'designer',
                  'digital_file_id', 'doc_type', 'document_version', 'entity', 'file_document_id', 'file_name',
                  'notice', 'watemark', 'watemark_date', 'doc_code', 'doc_name', 'version_stage'):
            if a in request.data:
                self.request_data[a] = request.data[a]

    @staticmethod
    def prepare_data(data, params_list, strict=False):
        """Подготовка словаря для создания сущности
        strict - проверять и заполненность параметров
        """
        dict_data = dict()
        for param in params_list:
            if param in data:
                if data[param] and data[param] != 'null':  # Пустые параметры приходят как текстовый 'null'
                    dict_data[param] = data[param]
                    continue
                elif strict:
                    return False, None, f'отсутствует значение параметра файла {param}'  # Проверка не пройдена
            elif strict:
                return False, None, f'отсутствует параметр файла {param}'  # Проверка не пройдена
            dict_data[param] = None  # Заполняем пустым значением

        return True, dict_data, ''

    def receive_new_file(self, request):
        """Помещение файла в архив"""
        file_params = ('doc_type', 'file_name', 'entity')
        result, file_data, message = self.prepare_data(self.request_data, file_params, True)
        if result:
            # logger.info('Проверка переданных параметров файла выполнена')
            src = get_temp_file_path(file_data['file_name'])  # Каталог и имя для временного сохранения файла
            # перенос файла во временный каталог
            if handle_uploaded_file(request.data['file'], src):
                logger.info('Перенос файла во временное хранилище осуществлен')
                # Если перенос файла прошел удачно, то
                watemark = request.data.get('watemark', 'false') in ('true', 'True')
                watemark_date = request.data.get('watemark_date', '') if watemark else ''
                result, received_file = prepare_file_for_store(src, watemark_date)  # Готовим файл к помещению в архив
                if not result:
                    return result, 'Ошибка подготовки файла для передачи в хранилище'
                logger.info('Файл подготовлен')
                logger.info(received_file)
                self.request_data['src'] = received_file  # Запоминаем расположение полученного и подготовленного файла
                return True, ''
        else:
            return result, message

    def set_archive(self):
        """Установка архива для сохранения документа"""
        if 'archive' not in self.request_data:
            self.request_data['archive'] = EntityTypeFileArchive.get_archive_id(self.request_data['entity'])

        # logger.info(f'self.request_data[archive] = {self.request_data["archive"]}')

    # Функции работы с сущностями
    def fn_file_document(self):
        """Запись информации о файловом документе в базу данных"""
        file_doc_params = ('file_document_id', 'description', 'doc_type', 'archive', 'doc_code', 'doc_name', 'crtd_sess')
        result, file_doc_data, message = self.prepare_data(self.request_data, file_doc_params, False)
        # Проверяем обязательный параметр doc_type
        if 'doc_type' not in file_doc_data:
            file_doc_data['doc_type'] = 1  # Значение по умолчанию
        if self.request_data['file_was_received']:  # Если получен файл от пользователя
            # Поиск файлового документа среди ранее существовавших
            logger.info(
                f"Ищем существующий файловый документ {self.request_data['file_name']} в архиве {self.request_data['archive']}")
            file_document = FileDocument.objects.filter(doc_code__iexact=self.request_data['file_name'],
                                                        archive=self.request_data['archive']).first()
            if file_document:  # Такой документ найден
                file_doc_data['file_document_id'] = file_document.id  # Берем идентификатор от найденного
        if file_doc_data['file_document_id']:  # Если это редактирование документа
            logger.info('Используем существующий файловый документ')
            if 'doc_code' in file_doc_data and not file_doc_data['doc_code']:
                # Если значение обозначения документа не передано, то удаляем его из массива (чтобы не было ошибки)
                del file_doc_data['doc_code']
            # logger.info('file_doc_data')
            # logger.info(file_doc_data)
            file_doc_data['edt_sess'] = self.request_data['crtd_sess']  # Для редактирования
            exist_document_version = FileDocument.objects.get(pk=file_doc_data['file_document_id'])
            serializer = FileDocumentSerializer(exist_document_version, data=file_doc_data, partial=True)
        else:
            logger.info('Создаем новый файловый документ')
            if 'doc_code' not in file_doc_data or not file_doc_data['doc_code']:
                # Если обозначение документа не передано, то берем имя файла
                file_doc_data['doc_code'] = self.request_data['file_name']
            # logger.info('file_doc_data')
            # logger.info(file_doc_data)
            serializer = FileDocumentSerializer(data=file_doc_data)
        if serializer.is_valid():
            file_document = serializer.save()
            self.request_data['next_version_num'] = file_document.get_next_version_num()  # На всякий случай
            self.request_data['document'] = serializer.data['pk']
        else:
            logger.info('Ошибка сериализации FileDocumentSerializer')
            logger.error(serializer.errors)
            return False, 'Ошибка записи файлового документа'
        return True, ''

    def fn_document_version(self):
        """Запись информации о версии документа"""
        doc_version_params = ('document_version_id', 'document', 'description', 'notice', 'change_num', 'change_type', 'version_stage',
                              'crtd_sess')
        result, doc_version_data, message = self.prepare_data(self.request_data, doc_version_params, False)
        # logger.info('doc_version_data')
        # logger.info(doc_version_data)
        if 'document_version' not in self.request_data:
            # Создаем новую версию документа
            logger.info('Создаем новую версию документа')
            doc_version_data['version_num'] = self.request_data['next_version_num']  # Полученное ранее значение
            serializer = DocumentVersionSerializer(data=doc_version_data)
            if serializer.is_valid():
                serializer.save()
            else:
                logger.info('Ошибка сериализации DocumentVersionSerializer')
                logger.error(serializer.errors)
                return False, 'Ошибка создания версии документа'
            self.request_data['document_version'] = serializer.data['pk']
        else:
            # Редактирование существующей версии
            doc_version_data['edt_sess'] = self.request_data['crtd_sess']  # Для редактирования
            exist_document_version = DocumentVersion.objects.get(pk=self.request_data['document_version'])
            serializer = DocumentVersionSerializer(exist_document_version, data=doc_version_data)
            if serializer.is_valid():
                serializer.save()
            else:
                logger.info('Ошибка сериализации DocumentVersionSerializer')
                logger.error(serializer.errors)
                return False, 'Ошибка редактирования версии документа'
        return True, ''

    def fn_digital_file(self):
        """Запись информации о  о файле в базу данных"""
        digital_file_params = ('document_version_id', 'file_name', 'src', 'check_sum', 'archive', 'data_format',
                               'crtd_sess_id')
        # Используем get_or_create_item потому, что файл надо копировать из исходного места в архив
        # Поэтому нужны варианты с id
        self.request_data['crtd_sess_id'] = self.request_data['crtd_sess']
        self.request_data['document_version_id'] = self.request_data['document_version']
        logger.info('Записываем информацию о файле в базу данных')
        result, digital_file_data, message = self.prepare_data(self.request_data, digital_file_params, False)
        logger.info('digital_file_data')
        logger.info(digital_file_data)
        if digital_file_data['data_format'] == 'detect':
            # Если на клиенте не удалось определить формат файла
            # Пробуем определить на основе имени файла
            digital_file_data['data_format'] = get_mime_type(digital_file_data['file_name'])
        file_obj, created = DigitalFile.get_or_create_item(digital_file_data)
        if file_obj:  # Создан новый файл или найден существующий
            # Если он заменял существовавший ранее
            if created:
                logger.info('Новый файл добавлен в базу данных')
            else:
                logger.info('Файл найден в базе данных')
                if file_obj.dlt_sess:  # Файл ранее был удален
                    # Убираем пометку удаления
                    file_obj.dlt_sess = 0
                    file_obj.document_version_id = digital_file_data['document_version_id']
                    file_obj.edt_sess = self.request_data['crtd_sess']
                    logger.info('Снимаем с файла пометку удаления')
                    file_obj.save()
            if 'digital_file_id' in self.request_data and self.request_data['digital_file_id'] != 'null':
                # Удаляем существовавший ранее
                logger.info(f"Удаляем файл, существовавший ранее {self.request_data['digital_file_id']} меткой {self.request_data['crtd_sess']}")
                old = DigitalFile.objects.get(pk=self.request_data['digital_file_id'])
                old.dlt_sess = self.request_data['crtd_sess']
                old.delete()
            return True, ''
        else:
            logger.info('Удаляем остатки неудачного файла из архива')
            delete_file(self.request_data['src'])
            return False, 'Ошибка записи данных о файле'

    def fn_design_role(self):
        """Запись информации о разработчике"""
        designer_role_params = ('design_role_id', 'document_version', 'designer', 'crtd_sess')
        result, designer_role_data, message = self.prepare_data(self.request_data, designer_role_params, False)
        logger.info('designer_role_data')
        logger.info(designer_role_data)
        if designer_role_data['designer']:  # Если указан разработчик
            designer_role_data['role'] = Role.get_value_id('Разработал')
            # Ищем существующую роль
            design_role_exist = VersionDesignRole.objects.filter(
                document_version_id=self.request_data['document_version'],
                role_id=designer_role_data['role']).first()
            if design_role_exist:  # Если это редактирование существующей роли
                logger.info('Редактируем существующую роль')
                designer_role_data['edt_sess'] = self.request_data['crtd_sess']  # Для редактирования
                serializer = VersionDesignRoleSerializer(design_role_exist, data=designer_role_data, partial=True)
            else:
                logger.info('Создаем новую роль')
                serializer = VersionDesignRoleSerializer(data=designer_role_data)
            if serializer.is_valid():
                serializer.save()
            else:
                logger.info('Ошибка сериализации VersionDesignRoleSerializer')
                logger.error(serializer.errors)
                return False, 'Ошибка записи роли Разработал'
        return True, ''

    def fn_entity_document_version(self):
        """присоединяем версию файла к объекту"""
        entity_doc_version_params = ('entity', 'document_version', 'crtd_sess')
        result, entity_doc_version_data, message = self.prepare_data(self.request_data, entity_doc_version_params,
                                                                     False)
        # logger.info('entity_doc_version_data')
        # logger.info(entity_doc_version_data)
        # Пробуем найти ранее присоединенную версию
        link_exists = EntityDocumentVersion.objects.filter(entity_id=entity_doc_version_data['entity'],
                                                           document_version_id=entity_doc_version_data[
                                                               'document_version']).first()
        if link_exists:  # Если связь найдена
            logger.info('связь версии файла с объектом найдена')
            link_exists.old_version = False
            link_exists.edt_sess = self.request_data['crtd_sess']
            link_exists.save()
            # Отмечаем предыдущие версии как старые
            EntityDocumentVersion.mark_old_versions(entity_doc_version_data['entity'], self.request_data['document'],
                                                    entity_doc_version_data['document_version'])
        else:
            serializer = EntityDocumentVersionSerializer(data=entity_doc_version_data)
            if serializer.is_valid():
                logger.info('присоединяем версию файла к объекту')
                serializer.save()
                # Отмечаем предыдущие версии как старые
                EntityDocumentVersion.mark_old_versions(entity_doc_version_data['entity'],
                                                        self.request_data['document'],
                                                        entity_doc_version_data['document_version'])
            else:
                logger.info('Ошибка сериализации EntityDocumentVersionSerializer')
                logger.error(serializer.errors)
                return False, 'Ошибка присоединения версии к объекту'
        return True, ''

    def post(self, request):
        self.copy_params(request)  # Копирование переданных парамтеров
        self.request_data['crtd_sess'] = request.session.get('user_session_id', 1)
        self.request_data['file_was_received'] = False  # Исходное значение
        exist_digital_file = None  # Исходное значение
        self.set_archive()  # Установка архива (если не указан)
        if request.data['file'] and request.data['file'] != 'null':  # Если передан файл
            self.request_data['file_was_received'] = True  # Признак, что файл получен
            result, message = self.receive_new_file(request)  # Помещаем его в архив
            if not result:
                return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)
            # Проверяем наличие такого файла в базе данных
            self.request_data['check_sum'] = compute_check_sum(self.request_data['src'])
            logger.info(
                f"Ищем файл file_name={self.request_data['file_name']} check_sum={self.request_data['check_sum']}")
            exist_digital_file = DigitalFile.objects.filter(file_name__iexact=self.request_data['file_name'],
                                                            folder__archive_id=self.request_data['archive'],
                                                            check_sum=self.request_data['check_sum']).first()
            if exist_digital_file:  # Если найден существующий
                logger.info('В базе найден существующий файл')
                if exist_digital_file.file_name != self.request_data['file_name']:
                    # logger.info('Приводим в соответствие регистр символов')
                    new_name = os.path.join(exist_digital_file.folder.folder_path, self.request_data['file_name'])
                    try:
                        os.rename(exist_digital_file.file_path, new_name)
                    except:
                        return Response(
                            {"message": f'Ошибка переименования {exist_digital_file.file_path} в {new_name}'},
                            status=status.HTTP_400_BAD_REQUEST)
                    # Изменяем запись в базе данных
                    exist_digital_file.file_name = self.request_data['file_name']
                    exist_digital_file.edt_sess = self.request_data['crtd_sess']
                    exist_digital_file.save()
                self.request_data['document_version'] = exist_digital_file.document_version.pk
        # Файловый документ
        result, message = self.fn_file_document()
        if not result:
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)
        # Версия файлового документа
        result, message = self.fn_document_version()
        if not result:
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)
        # Если передан файл и не найден существующий
        if self.request_data['file_was_received'] and not exist_digital_file:
            result, message = self.fn_digital_file()
            if not result:
                return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)
        # Связь с разработчиком
        result, message = self.fn_design_role()
        if not result:
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)
        # Связь с объектом
        result, message = self.fn_entity_document_version()
        if not result:
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)


class UploadArcdocsList(ListAPIView):
    queryset = UploadArcdoc.objects.all()
    serializer_class = UploadArcdocsSerializerList
    name = 'upload-arcdocs-list'
    paginator = None  # Отключение пагинации

    # Поля фильтрации
    filterset_fields = (
        'file_upload',
    )


class NoticeLinkDocView(ListAPIView):
    queryset = DocumentVersion.objects.filter(
        digital_files__dlt_sess=0
    ).order_by(
        'digital_files__file_name'
    ).values(
        'digital_files__pk',
        'change_num',
        'change_type__list_value',
        'document__doc_type__list_value',
        'is_done',
        'version_num',
        'digital_files__file_name'
    )
    serializer_class = NoticeLinkDocSerializerList
    name = 'notice-link-doc-list'
    paginator = None  # Отключение пагинации

    # Поля фильтрации
    filterset_fields = (
        'notice',
    )
