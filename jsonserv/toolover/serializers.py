from rest_framework import serializers
# Классы для ссылок на них
from jsonserv.core.serializers import GraphicFileSerializer, EntityRefSerializer
# Классы, подлежащие сериализации
from .models import ToolClass, ToolObject


class ToolClassRefSerializer(serializers.ModelSerializer):
    """Класс для сериализации ссылок на Класс инструмента"""
    value = serializers.CharField(source='__str__')  # Дополнительное поле для отображения в формах свойств

    class Meta:
        model = ToolClass
        fields = ('pk', 'class_id', 'value')


class ToolSerializer(serializers.ModelSerializer):
    """Сериализатор полного описания инструмента"""
    group = EntityRefSerializer(read_only=True)

    class Meta:
        model = ToolObject
        fields = (
            'pk',
            'code',
            'description',
            'group')


class ToolClassSerializer(serializers.ModelSerializer):

    class Meta:
        model = ToolClass
        fields = (
            'pk',
            'class_id',
            'parent',
            'class_name',
            'preferred_name',
            'icon',
            'drawing',
            'mapping_rule',
            'modified_date',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class ToolClassSerializerDetailed(serializers.ModelSerializer):

    parent = ToolClassRefSerializer(read_only=True)
    icon = GraphicFileSerializer(read_only=True)
    drawing = GraphicFileSerializer(read_only=True)

    class Meta:
        model = ToolClass
        fields = (
            'pk',
            'class_id',
            'parent',
            'class_name',
            'preferred_name',
            'icon',
            'drawing',
            'mapping_rule',
            'modified_date'
        )


class ToolClassSerializerList(serializers.ModelSerializer):

    class Meta:
        model = ToolClass
        fields = (
            'pk',
            'class_id',
            'parent',
            'class_name',
            'preferred_name',
            'icon',
            'drawing',
            'mapping_rule',
            'modified_date'
        )


class ToolClassTreeSerializer(serializers.ModelSerializer):
    """Сериализатор частичного описания класса инструмента для дерева"""

    class Meta:
        model = ToolClass
        fields = (
            'pk',
            'class_id',
            'parent',
            'class_name',
            'preferred_name',
            'has_children'
        )
