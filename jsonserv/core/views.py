from importlib import import_module
import os.path
from itertools import chain
from django.utils.safestring import mark_safe # Для защиты текста json от порчи при шаблонизации
from django.conf import settings  # для обращения к настройкам
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView
from django.views.decorators.cache import cache_page
from django.contrib.auth.models import Group
from django.db.models import JSONField, F, Value
from django.db.models.fields.related import ForeignKey
from django.db.models.functions import JSONObject


# Инструментарий фильтрации
from django_filters import rest_framework as filters
from django_filters import BooleanFilter

from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status

from jsonserv.core.models import (Classification, Entity, EntityType, HistoryLog, Link, List, CodedList, MenuItem,
                                  FormField, GraphicFile, UserSession, TypePanel, TypeExtraLink, ActionLog,
                                  TypeSetting, Report, UserProfile, UserSettings, check_access, children)
from jsonserv.core.serializers import (ClassificationTreeSerializer, EntitySerializer, ExtraLinkSerializer,
                                       HistorySerializerList, UserActionLogSerializer, ActionLogSerializer,
                                       LinkedSerializerList, ReportParamSerializer,
                                       UserGroupListSerializer, UserSessionSerializer)

from jsonserv.core.models_dispatcher import ModelsDispatcher

from jsonserv.pdm.models import Notice, PartObject, PartType, TpRowType
from jsonserv.docarchive.models import EntityDocumentVersion
from jsonserv.core.fileutils import (get_mime_type, http_unload_big_file, http_unload_file,
                                     handle_uploaded_file, delete_file)
from jsonserv.rest.views import JSONResponse


def get_host_url(request):
    """Определение адреса бэкенда"""
    if request.is_secure():
        return f'https://{request.get_host()}'
    return f'http://{request.get_host()}'


class ApplicationView(TemplateView):
    """Общий класс для всех форм приложения, за исключением формы входа и выхода.
    Формы-потомки доступны только авторизованным пользователям"""
    app_dir = getattr(settings, 'APP_DIR', 'app')  # Каталог, в котором находятся подключаемы стили и скрипты

    def __init__(self):
        self.template_name = 'dashboard.html'  # Шаблон по умолчанию

        self.user = None  # Текущий пользователь
        # Список подключаемых файлов с js-скриптами
        self.scripts = ['chunk-common', 'chunk-vendors']
        # Список подключаемых файлов стилей
        self.styles = ['main', 'chunk-common']  # , 'chunk-vendors'
        self.panels_key = ''  # Ключ для поиска панелей
        self.panels_list = list()  # Список панелей
        self.editable_panels_list = list()  # Список панелей, допускающих редактирование
        # Параметры отображения дашборда
        self.title = ''  # Заголовок страницы
        self.message = ''  # Сообщение пользователю

        # Дополнительные ключи для передачи js-скриптам
        # Возможные значения:
        # type_key - Название отображаемого класса
        # part_type - Тип элемента конструкции
        # object_id - Идентификатор отображаемого объекта
        self.keys = dict()

    def set_key_value(self, key, value):
        self.keys[key] = value

    def set_title(self, title):
        self.title = title
        # Заголовок также передается в параметры для JS
        self.set_key_value('caption', title)

    def add_to_title(self, title):
        # Набор данных в заголовок страницы
        if title:
            if self.title:  # Вариант с накоплением
                self.title = self.title + '. ' + title
            else:
                self.title = title
        # Заголовок также передается в параметры для JS
        self.set_key_value('caption', self.title)

    def links_get(self):
        """Формирование списка описаний подключаемых файлов"""
        links = list()
        # Ссылки на общие файлы скриптов
        for script in self.scripts:
            links.append(
                dict(href=f'{self.app_dir}/js/{script}.js', rel='preload', las='script'))
        # Ссылки на общие файлы стилей
        for style in self.styles:
            links.append(
                dict(href=f'{self.app_dir}/css/{style}.css', rel='stylesheet', las=''))
        return links

    def scripts_get(self):
        """Формирование списка подключаемых скриптов"""
        return list(map(lambda s: f'{self.app_dir}/js/{s}.js', self.scripts))

    def user_session_get(self):
        """Получение параметров сессии пользователя"""
        user_session_id = self.request.session.get('user_session_id', 0)
        # TODO: Сделать нормальную обработку нулевого значения user_session_id
        user_session = UserSession.objects.get(pk=user_session_id)
        # Текущий пользователь может использоваться для получения прав
        self.user = self.request.user
        # Логирование действий пользователя
        ActionLog.log_action('C', self.request.path, self.request.session)
        dashboard = UserProfile.get_user_dashboard(self.user)
        return dict(username=user_session.user_profile_user_name, session_datetime=user_session.session_datetime,
                    user_session_id=user_session_id, home=dashboard)

    def panels_and_params_get(self):
        """Формирование массива панелей дашборда и набора уникальных параметров"""
        start_params = list()  # Список начальных параметров для панелей
        # Получения списка панелей дашборда
        panels = TypePanel.type_panels(self.panels_key, self.in_single)
        # Перебор всех панелей типа
        for panel in panels:
            # Проверка уровня доступа к панели
            can_view = max(
                # Если право не выдано - доступа нет
                check_access(panel.view_right, self.user, False),
                # Если право не выдано - доступа нет
                check_access(panel.panel.view_right, self.user, False)
            )
            if panel.panel.check_state:
                # Если для панели контролируется доступ по состоянию
                can_view = min(can_view, self.state_can_view)
            if not can_view:
                continue  # Если нет доступа, панель не отображается
            can_edit = max(
                # Если право не выдано - редактировать нельзя
                check_access(panel.edit_right, self.user, False),
                # Если право не выдано - редактировать нельзя
                check_access(panel.panel.edit_right, self.user, False)
            )

            if panel.panel.check_state:
                can_edit = min(can_edit, self.state_can_edit)
            if can_edit:
                # Добавляем в список редактируемых панелей
                self.editable_panels_list.append(panel.panel.panel_name)
            self.panels_list.append(panel.panel.panel_name)
            area = panel.panel.area  # Область тоже надо добавить в список
            if area and area not in self.panels_list:
                self.panels_list.append(area)
            if panel.start_params:  # У панели есть параметры
                start_params.append(mark_safe(panel.start_params))

        # Добавление дополнительных ключей из предварительно собранного набора
        for key in self.keys:
            if isinstance(self.keys[key], str):
                # Пометка двойных кавычек эскейпами
                a = self.keys[key].translate(str.maketrans({'"': r'\"', }))
                start_params.append(mark_safe(f'{key} = "{a}";'))
            else:
                start_params.append(mark_safe(f'{key} = "{self.keys[key]}";'))

        result = dict()
        # Добавление общего списка панелей
        result['panels'] = "['" + "', '".join(self.panels_list) + "']"
        result['epanels'] = "['" + \
            "', '".join(self.editable_panels_list) + "']"
        # Уникальные параметры
        result['unique_js'] = start_params
        return result

    def context_dict_get(self):
        """Инициализатор словаря с исходным набором параметров"""
        context_dict = dict(
            session=self.user_session_get(),
            links=self.links_get(),
            params=self.panels_and_params_get(),
            scripts=self.scripts_get(),
            title=self.title  # Последним, потому что заголовок должен быть сформирован
        )
        if self.message:
            context_dict['message'] = self.message
        return context_dict

    def set_error(self, error_message):
        """Переключение на дашборд с ошибкой в случае ошибки"""
        self.message = error_message
        self.template_name = 'error.html'

    def set_host_url(self):
        """Определение адреса бэкенда для передачи в параметры фронтенда"""
        self.keys['host_url'] = get_host_url(self.request)

    def fill_keys(self, **kwargs):
        """Наполнение уникальной части содержимого дашборда из настроек"""
        self.set_host_url()  # Заполняем адрес сервера
        # Получение описания дашборда
        scr, tlt, vr, extra_js = TypeSetting.get_dashboard(self.panels_key)
        if vr:  # Если указаны права доступа для дашборда
            if not check_access(vr, self.user, True):
                self.add_to_title(self.panels_key)
                self.set_error(
                    f'У Вас нет прав доступа к типу {self.panels_key}!')
                return
        # Добавление в скрипты уникального скрипта дашборда для типа
        self.scripts.append(scr)
        # Добавление дополнительных скриптов из настроек типа
        if extra_js:
            for js in extra_js.split(','): # Разбиение производится по запятой
                self.scripts.append(js)
        # Указание заголовка из настроек
        if tlt:
            self.add_to_title(tlt)

    def params_read(self, **kwargs):
        """Разбор переданных параметров запроса"""
        return False  # В дочерних классах переопределяется

    def get_context_data(self, **kwargs):
        """Главная функция, формирующая словарь context для заполнения шаблона"""
        if not self.params_read(**kwargs):  # Разбор входных параметров
            # Заполнение параметров (в дочерних классах свои варианты)
            self.fill_keys(**kwargs)
        return self.context_dict_get()  # Словарь с наполнением для шаблона


class ModelApplicationView(ApplicationView):
    """Класс для дашбордов, завязанных на конкретную модель"""
    in_single = False
    # Диспетчер, для поиска моделей по наименованию
    ModelsDispatcher = ModelsDispatcher()

    def __init__(self):
        super().__init__()
        self.model_class = None  # Класс модели объектов, отображаемых на дашборде
        self.part_type_class = None  # Класс объекта конструкции
        self.panels_key = ''  # Ключ для поиска панелей
        self.state_can_view = True  # Право чтения к состоянию объекта
        self.state_can_edit = True  # Право редактирования к состоянию объекта

    def set_type_key(self, type_key):
        """Обработка типа первого уровня"""
        self.set_key_value('type_key', type_key)
        try:
            self.model_class = ModelsDispatcher.get_entity_class_by_entity_name(
                type_key)
        except KeyError:
            # Запрошен список неизвестных сущностей
            self.add_to_title(type_key)
            self.set_error(f'Сущность {type_key} не обнаружена в базе данных!')
            return True
        # Проверяем права доступа к типу сущности
        if not type_key == 'entity':  # Только если тип объекта известен
            try:
                etype = EntityType.objects.get(pk=type_key)
                if not check_access(etype.value_right, self.user, True):
                    self.add_to_title(type_key)
                    self.set_error(
                        f'У Вас нет прав доступа к типу {type_key}!')
                    return True
            except:
                pass
        self.panels_key = type_key
        if not self.in_single:
            # Для списочного дашборда
            # Заголовок страницы
            self.set_title(self.model_class._meta.verbose_name_plural.title())
        return False

    def set_sub_type_key(self, sub_type_key):
        """Обработка типа второго уровня"""
        if sub_type_key:
            self.set_key_value('sub_type_key', sub_type_key)
            try:
                # Получение описания типа объекта конструкции
                self.part_type_class = PartType.objects.get(pk=sub_type_key)
            except PartType.DoesNotExist:
                self.add_to_title(sub_type_key)
                self.set_error(
                    f'Тип {sub_type_key} не обнаружен в базе данных!')
                return True
            self.panels_key = sub_type_key
            if not self.in_single:  # Если это список объектов
                # Заголовок страницы
                self.set_title(self.part_type_class.div_name)
        return False

    def get_state_rights(self, obj):
        if obj.state:
            # Запоминание прав на состояние для последующей проверки прав
            # Если право не выдано - доступ есть (раньше было - нет)
            self.state_can_view = check_access(
                obj.state.view_right, self.user, True)
            self.state_can_edit = check_access(
                obj.state.edit_right, self.user, True)

    def set_object_id(self, object_id, type_key):
        self.set_key_value('object_id', object_id)
        # Получение свойств экземпляра
        try:
            exemplar = self.model_class.objects.get(
                pk=object_id)  # Экземпляр объекта
            if hasattr(exemplar, 'type_key'):  # Если это наследник Entity
                exemplar_type_key = exemplar.type_key.type_key
                # Уточняем класс объекта
                self.model_class = ModelsDispatcher.get_entity_class_by_entity_name(
                    exemplar_type_key)
            else:
                exemplar_type_key = type_key

            exemplar = self.model_class.objects.get(
                pk=object_id)  # Экземпляр объекта

            # Уточняем ссылку на класс модели
            if self.set_type_key(exemplar_type_key):
                return
            if exemplar_type_key == 'partobject':  # Для этого типа дополнительные условия
                # Указание подтипа
                # Получаем права доступа к состоянию
                self.get_state_rights(exemplar)
                self.set_sub_type_key(exemplar.part_type.part_type)
                # Указание, что это базовое исполнение
                if exemplar.is_base_rendition():
                    self.keys['base_rendition'] = True
                # Дополнительный признак заказа, Чтобы отрабатывать при создании объектов
                if exemplar.part_type.part_type == 'order':
                    self.set_key_value('order_id', object_id)
                elif exemplar.prod_order:
                    self.set_key_value('order_id', exemplar.prod_order_id)
            elif exemplar_type_key == 'notice':  # Для этого типа есть достyп к состоянию
                notice_object = Notice.objects.get(pk=object_id)
                # Получаем права доступа к состоянию
                self.get_state_rights(notice_object)
            # else:
            # Вывод специализированного заголовка из модели
            self.add_to_title(exemplar.get_caption())

        except self.model_class.DoesNotExist:
            # Запрошенному идентификатору не соответствует ни одна сущность
            self.set_error(
                f'Объект с идентификатором {object_id} не обнаружен в базе данных!')
            return True
        return False


class DashboardView(ModelApplicationView):
    """Форма приложения, отображающая специализированный дашборд"""
    in_single = True

    def set_dashboard_name(self, dashboard_name):
        if dashboard_name:
            self.panels_key = dashboard_name  # Набор панелей будем искать по имени дашборда
            self.styles.append(dashboard_name)  # У дашборда есть стили
        else:
            self.add_to_title('Не указан дашборд')
            self.set_error(f'Дашборд не обнаружен в адресной строке!')
            return True
        return False

    def params_read(self, **kwargs):
        """Разбор переданных параметров запроса"""
        err = self.set_dashboard_name(kwargs.get('dashboard_name', ''))
        if err:
            return err
        object_id = kwargs.get('id', '')  # Идентификатор экземпляра
        if object_id:
            # Модель для первичного поиска
            type_key = kwargs.get('type_key', 'partobject')
            self.set_key_value('type_key', type_key)
            self.set_key_value('object_id', object_id)
        return err


class ReportView(ApplicationView):
    """Форма приложения, отображающая форму запуска формирования отчета"""
    in_single = False
    report_name = ''  # Наименование отчета
    mode = ''  # Режим формирования
    app = ''  # Приложение, к которому относится отчет

    def set_report_form_params(self, report_name):
        """Указание всех параметров отчета"""
        if report_name:
            report_obj = Report.objects.get(report_name=report_name)
            if report_obj:
                self.set_title(report_obj.title)  # Заголовок страницы
                self.panels_key = 'report'
                self.scripts.append('report')
                self.set_key_value('report_name', report_name)
                if report_obj.module_url:  # Если указана ссылка на внешний модуль формирования
                    # Передаем ссылку на модуль формирования
                    self.set_key_value('module_url ', report_obj.module_url)
                if report_obj.file_name:  # Если указано наименование файла-отчета
                    self.set_key_value('file_name ', report_obj.file_name)
                if report_obj.only_format:  # Если указан единственный возможный формат файла-отчета
                    self.set_key_value('only_format ', report_obj.only_format)
            else:
                self.add_to_title('Отчет не найден')
                self.set_error(
                    f'Отчет с именем {report_name} не найден в настройках!')
                return True
        else:
            self.add_to_title('Не указано имя отчета')
            self.set_error('Имя отчета не обнаружено в адресной строке!')
            return True
        # Если был передан идентификатор объетка, то передаем его в дополнительные параметры
        object_id = self.request.GET.get('object_id', 0)
        if object_id:
            self.set_key_value('object_id ', object_id)
        return False

    def params_read(self, **kwargs):
        """Разбор переданных параметров запроса"""
        self.report_name = kwargs.get('report_name', '')
        err = self.set_report_form_params(self.report_name)
        return err

    def fill_keys(self, **kwargs):
        self.set_host_url()  # Заполняем адрес сервера


class SearchView(ApplicationView):
    """Форма поиска"""
    in_single = False

    def fill_keys(self, **kwargs):
        self.set_host_url()  # Заполняем адрес сервера
        self.scripts.append('search')  # Добавление уникальных скриптов
        self.add_to_title('Поиск')  # Заголовок


class ListView(ModelApplicationView):
    """Форма приложения, отображающая список объектов"""
    in_single = False  # Это Форма списка

    def params_read(self, **kwargs):
        """Разбор переданных параметров запроса"""
        self.user = self.request.user  # Текущий пользователь может использоваться для получения прав
        err = self.set_type_key(kwargs.get('type_key', ''))
        err |= self.set_sub_type_key(kwargs.get('sub_type_key', ''))
        return err


class DetailView(ModelApplicationView):
    """Форма приложения, отображающая свойства экземпляра (объекта)"""
    in_single = True  # Это единичный дашборд

    def params_read(self, **kwargs):
        """Разбор переданных параметров запроса"""
        self.user = self.request.user  # Текущий пользователь может использоваться для получения прав
        # Модель для первичного поиска
        err = self.set_type_key(kwargs.get('type_key', 'entity'))
        if err:
            return err
        object_id = kwargs.get('id', '')  # Идентификатор экземпляра
        type_key = kwargs.get('type_key', 'entity')
        return self.set_object_id(object_id, type_key)


class ClassificationTreeRootFilter(filters.FilterSet):
    root = BooleanFilter(field_name='group', lookup_expr='isnull')

    class Meta:
        model = Classification
        fields = (
            'id',
            'group',
        )


class ClassificationStaff(ListAPIView):
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer
    name = 'classification-staff'
    paginator = None  # Отключение пагинации (в дереве не нужна)
    # Поля фильтрации
    filterset_fields = (
        'group',
    )


class ClassificationTree(ListAPIView):
    queryset = Classification.objects.all()
    serializer_class = ClassificationTreeSerializer
    name = 'classification-branch'
    # Дополнительный фильтра для корневого элемента
    filterset_class = ClassificationTreeRootFilter
    paginator = None  # Отключение пагинации (в дереве не нужна)
    # Поля фильтрации
    filterset_fields = (
        'id',
        'group',
    )
    # Поля поиска
    search_fields = (
        'code',
        'name'
    )


class EntityList(RetrieveAPIView):
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer
    name = 'object-list'


class GraphicUploadView(APIView):
    """Представление для работы с графическими файлами экземпляров сущностей"""
    name = 'graphic-upload'
    name_del = 'graphic-delete'
    parser_classes = (MultiPartParser,)
    file_params = ('file_name', 'file', 'entity')

    def __init__(self):
        self.file_data = dict()  # Информация о загружаемом файле

    def check_data(self, data):
        """Проверка полноты переданных параметров"""
        for param in self.file_params:
            if param not in data:
                # Проверка не пройдена
                return False, f'отсутствует параметр файла {param}'
            if not data[param]:
                # Проверка не пройдена
                return False, f'отсутствует значение параметра файла {param}'
            self.file_data[param] = data[param]

        return True, ''

    def post(self, request):
        result, message = self.check_data(request.data)

        if result:
            # Каталог и имя для временного сохранения файла
            temp_name = os.path.join(
                getattr(settings, 'TEMP_DIR', 'temp'), self.file_data['file_name'])

            # Если перенос файла прошел удачно, то
            if handle_uploaded_file(self.file_data['file'], temp_name):
                # Записываем информацию о графическом файле в базу данных
                crtd_sess = request.session.get('user_session_id', 1)
                graphic_obj, created = GraphicFile.get_or_create_item(dict(file_name=temp_name,
                                                                           crtd_sess_id=crtd_sess))
                # указание объекту ссылки на иллюстрацию
                if 'entity' in self.file_data:
                    entity = Entity.objects.filter(pk=self.file_data['entity'])
                    entity.update(picture=graphic_obj, edt_sess=crtd_sess)
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                # Удаляем остатки неудачного файла из архива
                delete_file(temp_name)
                return Response({'message': 'Ошибка переноса файла в хранилище'}, status=status.HTTP_304_NOT_MODIFIED)
        else:
            return Response({'message': message}, status=status.HTTP_304_NOT_MODIFIED)

        # return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def get(request):
        graphic_file, message = '', ''
        entity_id = request.GET.get("id", None)
        if entity_id:
            entity = Entity.objects.get(pk=entity_id)
            if entity:
                if entity.picture:
                    graphic_file = entity.picture.file_name
                else:
                    graphic_file = ''
            else:
                message = f'Не удалось найти объект по id ({entity_id})'
        else:
            message = 'Не указан идентификатор объекта'
        return Response({'message': message, 'graphic_file': graphic_file})

    @staticmethod
    def delete(request, id):
        entity_id = id
        if entity_id:
            entity = Entity.objects.filter(pk=entity_id)
            if entity:
                entity.update(picture=None, edt_sess=request.session.get('user_session_id', 1))
            else:
                return Response({'message': f'Не удалось найти объект по id ({entity_id})'},
                                status=status.HTTP_304_NOT_MODIFIED)
        else:
            return Response({'message': 'Не указан идентификатор объекта'}, status=status.HTTP_304_NOT_MODIFIED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class HistoryList(ListAPIView):
    """Отображение истории редактирования"""
    serializer_class = HistorySerializerList
    paginator = None
    name = 'history-list'

    def get_queryset(self):
        """Список обязательно фильтруется по исполнителю"""
        table_name = self.kwargs['table_name']
        object_id = self.kwargs['object']
        # Создание объекта
        creator = Entity.objects.filter(pk=object_id).annotate(
            pk=-1 * F('pk'),  # Чтобы точно было уникальным
            edt_sess__id=F('crtd_sess_id'),
            edt_sess__user__username=F('crtd_sess__user__username'),
            edt_sess__session_datetime=F('crtd_sess__session_datetime'),
            changes=Value(dict(create=""), JSONField())
        ).values('pk',
                 'edt_sess__id',
                 'edt_sess__user__username',
                 'edt_sess__session_datetime',
                 'changes')
        # История редактирования
        history = HistoryLog.objects.filter(
            table_name=table_name, object_id=object_id
        ).values('pk',
                 'edt_sess__id',
                 'edt_sess__user__username',
                 'edt_sess__session_datetime',
                 'changes'
                 ).order_by(
            'edt_sess__session_datetime', 'pk'
        )
        # История файлов
        files_history = EntityDocumentVersion.objects.filter(
            entity_id=object_id
        ).annotate(
            pk=-1 * F('pk'),  # Чтобы точно было уникальным
            edt_sess__id=F('crtd_sess_id'),
            edt_sess__user__username=F('crtd_sess__user__username'),
            edt_sess__session_datetime=F('crtd_sess__session_datetime'),
            changes=JSONObject(title=F('document_version__document__doc_code'))
        ).values('pk',
                 'edt_sess__id',
                 'edt_sess__user__username',
                 'edt_sess__session_datetime',
                 'changes')
        return chain(creator, history, files_history)  # Соединяем результаты запросов


class LinkList(ListAPIView):
    """Отображение всех связанных объектов"""
    queryset = Link.objects.all().order_by('child__code', 'parent__code')
    serializer_class = LinkedSerializerList
    paginator = None  # Отключение пагинации
    name = 'link-list'

    # Поля фильтрации
    filterset_fields = (
        'parent',
        'child',
        'link_class',  # Можно отобрать связи по классу
    )


@api_view(['GET', ])
def search_list(request):
    md = ModelsDispatcher()  # Диспетчер, для поиска моделей по наименованию
    # Получение переданных параметров фильтрации
    filters = request.GET
    search = filters.get('search', '')
    filter_args = dict(code__icontains=search)  # Поиск регистронезависимый
    part_type = filters.get('part_type', '')
    title = filters.get('title', '')
    parent = filters.get('parent', 0)
    design_mater = filters.get('design_mater', 0)
    # При наличии дополнительных параметров поиска ищем среди PartObject
    if part_type or parent or design_mater or title:
        if part_type:
            # Фильтр по типу
            filter_args['part_type'] = part_type
        if parent:
            # Выборка объектов состава
            children_ids = list(
                map(lambda x: x[0], children(parent, 'partlink')))[0:30]
            filter_args['pk__in'] = children_ids
        if design_mater:
            # Изготавливается из
            filter_args['child_objects__child'] = design_mater
        if title:
            filter_args['title__icontains'] = title
        rows = PartObject.objects.filter(**filter_args)[0:30]
    else:
        rows = Entity.objects.filter(**filter_args)[0:30]
    result = list()
    for row in rows:  # Обработка результатов
        item_model = md.get_entity_class_by_entity_name(row.type_key.type_key)
        pk = row.id
        item = item_model.objects.get(pk=pk)
        description = item.get_description()
        result.append(dict(pk=pk, code=item.code,
                      description=description, type_key=row.type_key))

    serializer = EntitySerializer(result, many=True)
    return Response(serializer.data)


class ReportParamsList(ListAPIView):
    """Получение списка параметров формирования отчета"""
    serializer_class = ReportParamSerializer
    name = 'report-param-list'
    pagination_class = None

    def get_queryset(self):
        report_name = self.kwargs['report_name']
        return Report.objects.filter(
            report_name=report_name
        ).values(
            'report_params__pk',
            'report_params__param_name',
            'report_params__caption',
            'report_params__param_type',
            'report_params__default_value',
            'report_params__required',
            'report_params__order_num',
            'report_params__values_list',
            'report_params__list_keys',
            'report_params__extra_value',
            'report_params__is_file_name'
        ).order_by('report_params__order_num')


class UserGroupList(ListAPIView):
    queryset = Group.objects.all().order_by('name')
    serializer_class = UserGroupListSerializer
    name = 'user-groups-list'


class ActionLogList(ListAPIView):
    serializer_class = ActionLogSerializer
    name = 'action-log-list'

    def get_queryset(self):
        user_id = self.request.GET.get('user_id', 0)
        # Фильтрация данных о действиях пользователя
        return ActionLog.objects.filter(session__user_id=user_id)


class UserSessionList(ListAPIView):
    serializer_class = UserSessionSerializer
    name = 'user-session-list'

    def get_queryset(self):
        user_id = self.kwargs.get('pk', 1)
        # Фильтрация данных о сессиях по пользователю
        # Последние 5 входов
        return UserSession.objects.filter(user_id=user_id)[:5]


def model_field(f, caption):
    """Формирование описания поля из модели"""
    # Перевод типов из модели Django в типы элементов EasyUI
    easyui = {
        "CharField": "TextBox",
        "IntegerField": "NumberBoxInt",
        "SmallIntegerField": "NumberBoxInt",
        "PositiveIntegerField": "NumberBox",
        # {"type": "NumberBox", "options": {"precision": 1}},
        "FloatField": "NumberBox",
        "DateField": "DateBox",
        "BooleanField": "CheckBox",
        # {"type": "textbox", "options": {"multiline": True}}
        "TextField": "TextBoxMultiline",
    }

    item = dict(name=f.name)
    # Если указана уникальная подпись - передаем ее, иначе подпись из модели
    item['label'] = caption if caption else f.verbose_name
    if isinstance(f, ForeignKey):
        item['target'] = f.related_model.__name__.lower()
        if issubclass(f.related_model, List) or issubclass(f.related_model, CodedList):
            # Если у класса родитель List, CodedList
            item['type'] = 'List'
            item['data'] = f.related_model.values_list()
        else:  # В остальных случаях
            item['type'] = 'Link'
            item['data'] = list()
    else:
        # Преобразуем на основе массива
        if f.name == 'password': # Для пароля отдельный тип поля
            item['type'] = 'PasswordBox'
        else:
            item['type'] = easyui.get(f.__class__.__name__, f.__class__.__name__)

    # Проверка обязательности заполнения поля
    if not (f.null or f.blank):
        if f.__class__.__name__ != 'BooleanField':  # Для boolean контроль обязательности в элементе интерфейса
            item['required'] = True
    # Значение по умолчанию
    item['default'] = f.get_default()
    return item


@api_view(['GET', ])
def caption_get(request, type_key='', id=''):
    if type_key and id:
        instance = ModelsDispatcher.get_entity_class_by_entity_name(type_key)
        item = instance.objects.get(pk=id)
        description = item.get_description()
        result = dict(pk=id, code=item.code,
                      description=description, type_key=item.type_key)

        serializer = EntitySerializer(result)
        return Response(serializer.data)
    return Response({"message": "Исходный объект не найден"}, status=status.HTTP_404_NOT_FOUND)


# Поля с особым функционалом редактирования
extra_fields = {
    # TODO: костыльный функционал - желательно облагородить
    'formats': {  # Форма редактирования списка форматов
        'label': 'Форматы',
        'type': "FormatFrom",
        'read_only': True
    },
    'design_mater': {  # Ссылка на конструкторский материал
        'label': 'Конструкторский материал',
        'type': "Link",
        'target': 'partobject'
    },
    'crtd_user': {  # Пользователь создавшей сессии
        'label': 'Создавший пользователь',
        'type': "TextBox"
    },
    'entity_label': {  # Внутренняя метка сущности
        'label': 'Метка',
        'type': "EntityLabel",
        'read_only': True
    },
    'row_type': {  # Тип строки ресурса
        'label': 'Тип строки',
        'type': "List",
        'related_model': TpRowType
    },
    'password_chk': { # Пароль для проверки
        'label': 'Пароль повторно',
        'type': "PasswordBox"
    }
}


def extra_field(ex_f, caption):
    """Формирование описания поля с внешним редактором"""
    item = dict(name=ex_f)
    f = extra_fields[ex_f]
    item['label'] = caption if caption else f['label']
    item['type'] = f['type']
    if 'target' in f:
        item['target'] = f['target']
    if 'related_model' in f:
        item['data'] = f['related_model'].values_list()
    return item


def type_fields(type_key, sub_type_key, user):
    """Получение словаря с перечнем полей-свойств указанного типа"""
    # Перечень полей, исключаемых из массива свойств
    except_list_update = ('entity_ptr', 'type_key',
                          )
    # Перечень свойств поля, передаваемых в его описании
    add_values_list = ('order_num', 'read_only', 'leave_func', 'field_style',
                       'hide_in_create', 'list_keys', 'required', 'default')

    def add_values(fld_props):
        for val in add_values_list:
            if val in fld_props:
                item[val] = fld_props[val]

    if type_key:
        # Получение отсортированного списка описаний полей для типа
        form_fields = FormField.type_fields_list(sub_type_key)
        # Получаем набор свойств сущности
        try:
            instance = ModelsDispatcher.get_entity_class_by_entity_name(type_key)
        except ObjectDoesNotExist as e:
            raise ObjectDoesNotExist(f"Tип {type_key} не найден") from e

        opts = instance._meta

        fields = list()

        for f in opts.concrete_fields:
            if f.name not in form_fields:  # Поля, не выводимые в форму, не отображаются
                continue
            if f.name in except_list_update:  # Не отображаются поля из списка исключений
                continue
            # Проверяем поля с контролем доступа
            if form_fields[f.name]['value_right'] and not check_access(form_fields[f.name]['value_right'], user): 
                continue
            # Формируем начальный набор полей на основе модели
            item = model_field(f, form_fields[f.name]['caption'])
            # Добавляем свойства из описания поля
            add_values(form_fields[f.name])
            if item['read_only'] and item['type'] == 'Link':
                # Только для чтения списки для выбора меняем на ссылки
                item['type'] = 'Ref'
            if form_fields[f.name]['target']:
                # Тоже может быть указан в свойствах
                item['target'] = form_fields[f.name]['target']

            if item['type'] == 'TextBoxMultiline' and item['field_style'] is None:
                # print(item)
                # Установка значения стиля по умолчанию для многострочных полей
                item['field_style'] = 'height: 50px'
            fields.append(item)

        for ex_f in extra_fields:  # Добавляем дополнительные поля, которых нет в моделях
            if ex_f in form_fields:
                item = extra_field(ex_f, form_fields[ex_f]['caption'])
                # Добавляем свойства из описания поля
                add_values(form_fields[ex_f])
                fields.append(item)

        # Сортировка полей по порядку следования
        return sorted(fields, key=lambda itm: itm['order_num'])
    else:
        return dict(error='Не указан тип сущности (entity)')

@api_view(['GET', ])
# @cache_page(60*15)  # Кэшируем запрос на 15 мин
def entity_properties_get(request, type_key='', sub_type_key=''):
    """Получение списка свойств сущности type_key для построения формы редактирования"""

    result = type_fields(type_key, sub_type_key, request.user)

    return JSONResponse(result)


@api_view(['GET', ])
def main_menu_get(request):
    """Получение массива с главным меню"""
    result = list()
    user = request.user
    head = MenuItem.objects.get(pk=1)  # Головной пункт меню
    # Все его подпункты
    items = head.subitems.filter(is_active=True).order_by('order_num')
    for item in items:
        # Добавляем всех потомков, проверяя доступ
        if check_access(item.item_right, user):  # Если доступ есть
            result.append(item.item_with_children(user))

    return JSONResponse(result)


@api_view(['GET', ])
def report_get(request, report_name, mode):
    report_obj = Report.objects.get(report_name=report_name)

    # Импортируем модуль формирования отчета
    module_path = report_obj.get_module_path()
    report_module = import_module(module_path)

    # Запускаем типовой метод формирования файла отчета
    report = report_module.ReportClass(request)
    file_path = report.prepare_report_file()
    file_name = os.path.basename(file_path)
    content_type = get_mime_type(file_name)
    if os.path.getsize(file_path) > 10000000:  # Выгружаем другим способом
        return http_unload_big_file(file_path, file_name, content_type)
    return http_unload_file(file_path, file_name, content_type)


class ExtraLinkList(ListAPIView):
    """Получение списка дополнительных ссылок
    Не используется. Оставил ради примера get_serializer_context"""
    serializer_class = ExtraLinkSerializer
    name = 'extra-link-list'
    paginator = None

    def get_queryset(self):
        type_key = self.kwargs['type_key']
        return TypeExtraLink.objects.filter(
            type_key=type_key
        ).values(
            'extra_link__link_pattern',
            'extra_link__caption',
        )

    def get_serializer_context(self):
        # Метод дополнения контекста сериализатора для передачи ему переменной
        context = super().get_serializer_context()
        context["id"] = self.kwargs['id']  # Переданный идентификатор объекта
        context["host"] = get_host_url(self.request)  # Адрес сервера
        return context


@api_view(['GET', ])
def extra_links_get(request, type_key='', id=''):
    if type_key and id:
        result = list()
        host = get_host_url(request)
        for lnk in TypeExtraLink.objects.filter(type_key=type_key):
            if check_access(lnk.extra_link.value_right, user=request.user):  # Если доступ есть
                result.append(dict(
                    link=lnk.extra_link.link_pattern.format(id=id, host=host),
                    caption=lnk.extra_link.caption
                ))

        return JSONResponse(result)
    return Response('', status=status.HTTP_404_NOT_FOUND)


@api_view(['POST', ])
def save_user_settings(request):
    """Сохранение настройки пользователя"""
    user = request.user
    setting_id = request.data.get('setting_id', '')
    setting_value = request.data.get('setting_value', '')
    if user.id is not None:
        cur_set = UserSettings.save_settings(user, setting_id, setting_value)
        return Response({"message": "Настройки сохранены"}, status=status.HTTP_200_OK)
    return Response({"message": "Настройки не переданы"}, status=status.HTTP_204_NO_CONTENT)
