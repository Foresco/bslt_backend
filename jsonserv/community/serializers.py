from rest_framework import serializers

from jsonserv.core.serializers import EntityRefSerializer, UserSessionUserField
from jsonserv.docarchive.serializers import ObjectFilesList

# Классы, подлежащие сериализации
from jsonserv.community.models import (Comment, Letter, Task, TaskType, TaskRefer, TaskUser)


class CommentSerializer (serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = (
            'pk',
            'entity',
            'comment_type',
            'parent',
            'comment_datetime',
            'comment_text',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class CommentSerializerList (serializers.ModelSerializer):
    crtd_user = UserSessionUserField(source='crtd_sess')
    comment_datetime = serializers.DateTimeField(format="%d.%m.%Y %H:%M")

    class Meta:
        model = Comment
        fields = (
            'pk',
            'comment_type',
            'parent',
            'comment_datetime',
            'comment_text',
            'crtd_user'
        )


class LetterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Letter
        fields = (
            'pk',
            'code',
            'description',
            'direction',
            'reg_date',
            'letter_num',
            'letter_date',
            'letter_type',
            'sender',
            'receiver',
            'letter_theme',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class LetterSerializerDetailed(serializers.ModelSerializer):
    sender = EntityRefSerializer(read_only=True)
    receiver = EntityRefSerializer(read_only=True)

    class Meta:
        model = Letter
        fields = (
            'pk',
            'code',
            'description',
            'direction',
            'reg_date',
            'letter_num',
            'letter_date',
            'letter_type',
            'letter_theme',
            'sender',
            'receiver',
        )


class LetterSerializerList(serializers.ModelSerializer):
    direction = serializers.SlugRelatedField(read_only=True, slug_field='list_value')
    letter_type = serializers.SlugRelatedField(read_only=True, slug_field='list_value')
    reg_date = serializers.DateField(format="%d.%m.%Y")
    letter_date = serializers.DateField(format="%d.%m.%Y")
    sender = serializers.SlugRelatedField(read_only=True, slug_field='code')
    receiver = serializers.SlugRelatedField(read_only=True, slug_field='code')
    files = ObjectFilesList(source='pk')

    class Meta:
        model = Letter
        fields = (
            'pk',
            'code',
            'direction',
            'reg_date',
            'letter_num',
            'letter_date',
            'letter_type',
            'sender',
            'receiver',
            'letter_theme',
            'description',
            'files'
        )


class TaskTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskType
        fields = ('pk', 'list_value')


class TaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = Task
        fields = (
            'pk',
            # За поле code отвечает встроенный нумератор в модели
            'description',
            'task_date',
            'task_type',
            'income_number',
            'task_from',
            'task_theme',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )
        # extra_kwargs = {
        #     'code': {
        #         # Указание, что поле код указывать не надо
        #         'required': False,
        #         'allow_blank': True,
        #     }
        # }


class TaskSerializerDetailed(serializers.ModelSerializer):
    # task_type = TaskTypeSerializer()

    class Meta:
        model = Task
        fields = (
            'pk',
            'code',
            'description',
            'task_date',
            'task_type',
            'income_number',
            'task_from',
            'task_theme',
            'next'
        )


class TaskSerializerList(serializers.ModelSerializer):
    task_type = serializers.SlugRelatedField(read_only=True, slug_field='list_value')
    task_date = serializers.DateField(format="%d.%m.%Y")
    highlighted = serializers.BooleanField(source='is_expired')  # Необходимо, чтобы вычисляемое свойство отображалось

    class Meta:
        model = Task
        fields = (
            'pk',
            'code',
            'task_date',
            'task_type',
            'task_theme',
            'income_number',
            'order_num',
            'highlighted'
        )


class ObjectTaskSerializerList(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(read_only=True, slug_field='code')

    class Meta:
        model = TaskRefer
        fields = (
            'pk',
            'parent',
            'parent_id',
            'comment'
        )


class TaskReferSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskRefer
        fields = (
            'pk',
            'parent',
            'child',
            'comment',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class TaskReferSerializerList(serializers.ModelSerializer):
    child = serializers.SlugRelatedField(read_only=True, slug_field='key_code')

    class Meta:
        model = TaskRefer
        fields = (
            'pk',
            'child',
            'child_id',
            'comment'
        )


class TaskUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = TaskUser
        fields = (
            'pk',
            'task',
            'user',
            'deadline',
            'time_norm',
            'unit',
            'taker_sess',
            'executor_sess',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class TaskUserSerializerList(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(read_only=True, slug_field='user_name')
    deadline = serializers.DateField(format="%d.%m.%Y")
    unit = serializers.SlugRelatedField(read_only=True, slug_field='short_name')

    class Meta:
        model = TaskUser
        fields = (
            'pk',
            'task',
            'user',
            'deadline',
            'time_norm',
            'unit',
            'taker_sess',
            'executor_sess',
        )
