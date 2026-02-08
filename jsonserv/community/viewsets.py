import django_filters  # Специальные фильтры
from django.db.models import Exists, OuterRef
from jsonserv.core.viewsets import CommonViewSet, DateEqualFilter, EqualFilter

from jsonserv.community.models import (Comment, Letter, Task, TaskRefer, TaskUser)

from jsonserv.community.serializers import (CommentSerializer, CommentSerializerList,
                                            LetterSerializer, LetterSerializerDetailed, LetterSerializerList,
                                            ObjectTaskSerializerList,
                                            TaskSerializer, TaskSerializerDetailed, TaskSerializerList,
                                            TaskReferSerializer, TaskReferSerializerList,
                                            TaskUserSerializer, TaskUserSerializerList)


class CommentViewSet(CommonViewSet):
    queryset = Comment.objects.all().order_by('-comment_datetime')
    serializer_class = CommentSerializer
    # serializer_class_detailed = CommentSerializerDetailed
    serializer_class_list = CommentSerializerList
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    # Поля фильтрации
    filterset_fields = (
        'entity',
    )


class LetterFilter(django_filters.FilterSet):
    """Особые фильтры для списка писем"""
    min_date = django_filters.DateFilter(field_name="reg_date", lookup_expr='gte')
    max_date = django_filters.DateFilter(field_name="reg_date", lookup_expr='lte')
    equal_date = DateEqualFilter(field_name="reg_date")

    class Meta:
        model = Letter
        fields = ['equal_date', 'min_date', 'max_date', 'direction', 'letter_type', 'sender', 'receiver']


class LetterViewSet(CommonViewSet):
    queryset = Letter.objects.all().order_by('-reg_date', '-code')
    filterset_class = LetterFilter  # Особые настройки фильтрации
    serializer_class = LetterSerializer
    serializer_class_detailed = LetterSerializerDetailed
    serializer_class_list = LetterSerializerList

    # Поля поиска
    search_fields = (
        'code',
        'letter_theme',
        'letter_num',
        'description'
    )


class ObjectTaskViewSet(CommonViewSet):
    queryset = TaskRefer.objects.all().order_by('parent__code')
    serializer_class = TaskReferSerializer
    serializer_class_list = ObjectTaskSerializerList
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    # Поля фильтрации
    filterset_fields = (
        'child',
    )


class ReferFilter(django_filters.Filter):
    """Фильтрация по признаку связи задания с указанным объектом"""
    def filter(self, qs, value):
        if value not in (None, ''):
            return qs.filter(Exists(TaskRefer.objects.filter(parent=OuterRef(self.field_name), dlt_sess=0,
                                                             child=value)))
        return qs


class ReceiverFilter(django_filters.Filter):
    """Фильтрация по признаку выдачи задания указанному пользователю"""
    def filter(self, qs, value):
        if value not in (None, ''):
            return qs.filter(Exists(TaskUser.objects.filter(task=OuterRef(self.field_name), dlt_sess=0, user=value)))
        return qs


class TakerFilter(django_filters.Filter):
    """Фильтрация по признаку взятия задания указанным пользователем"""

    def filter(self, qs, value):
        if value not in (None, ''):
            return qs.filter(Exists(TaskUser.objects.filter(
                task=OuterRef(self.field_name), dlt_sess=0, user=value
            ).exclude(taker_sess=0)))
        return qs


class ExecutorFilter(django_filters.Filter):
    """Фильтрация по признаку выполнения задания указанным пользователем"""

    def filter(self, qs, value):
        if value not in (None, ''):
            return qs.filter(Exists(TaskUser.objects.filter(
                task=OuterRef(self.field_name), dlt_sess=0, user=value
            ).exclude(executor_sess=0)))
        return qs


class TaskFilter(django_filters.FilterSet):
    """Особые фильтры для списка извещений"""
    min_date = django_filters.DateFilter(field_name="task_date", lookup_expr='gte')
    max_date = django_filters.DateFilter(field_name="task_date", lookup_expr='lte')
    equal_date = DateEqualFilter(field_name="task_date")
    author = django_filters.NumberFilter(field_name="crtd_sess__user")
    refer = ReferFilter(field_name='pk')  # Фильтр Касается
    receiver = ReceiverFilter(field_name='pk')  # Фильтр Получено
    taker = TakerFilter(field_name='pk')  # Фильтр Взято
    executor = ExecutorFilter(field_name='pk')  # Фильтр Выполнено

    class Meta:
        model = Task
        fields = ['task_type', 'equal_date', 'min_date', 'max_date']


class TaskViewSet(CommonViewSet):
    queryset = Task.objects.all().order_by('-order_num', 'task_type')
    serializer_class = TaskSerializer
    serializer_class_detailed = TaskSerializerDetailed
    serializer_class_list = TaskSerializerList
    filterset_class = TaskFilter  # Особые настройки фильтрации

    # Поля поиска
    search_fields = (
        'code',
        'income_number',
        'task_theme',
        'description'
    )


class TaskReferViewSet(CommonViewSet):
    queryset = TaskRefer.objects.all().order_by('child__code')
    serializer_class = TaskReferSerializer
    serializer_class_list = TaskReferSerializerList

    # Поля фильтрации
    filterset_fields = (
        'parent',
    )


class TaskUserViewSet(CommonViewSet):
    queryset = TaskUser.objects.all().order_by('deadline')
    serializer_class = TaskUserSerializer
    serializer_class_list = TaskUserSerializerList
    paginator = None  # Отключение пагинации (выводить весь список сразу)

    # Поля фильтрации
    filterset_fields = (
        'task',
    )

    def partial_update(self, request, *args, **kwargs):
        action_id = request.data.get('action_id', 'no')
        if action_id == 'take':
            # Добавление в свойства записи взявшей сессии
            request.data['taker_sess'] = request.session.get('user_session_id', 1)
        elif action_id == 'untake':
            # Исключение из свойств записи взявшей сессии
            request.data['taker_sess'] = 0
        elif action_id == 'execute':
            # Добавление в свойства записи выполнившей сессии
            request.data['executor_sess'] = request.session.get('user_session_id', 1)
        elif action_id == 'unexecute':
            # Исключение из свойств записи выполнившей сессии
            request.data['executor_sess'] = 0
        return super().partial_update(request, *args, **kwargs)
