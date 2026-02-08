from rest_framework import serializers
from jsonserv.core.serializers import EntityRefSerializer

from jsonserv.mdm.models import RawRow


class RawRowSerializerDetailed(serializers.ModelSerializer):
    group = EntityRefSerializer(read_only=True)

    class Meta:
        model = RawRow
        fields = (
            'pk',
            'code',
            'description',
            'group',
            'title',
            'properties'
        )


class RawRowSerializerList(serializers.ModelSerializer):

    class Meta:
        model = RawRow
        fields = (
            'pk',
            'code',
            'title'
        )


class RawRowSerializer(serializers.ModelSerializer):

    class Meta:
        model = RawRow
        fields = (
            'pk',
            'code',
            'title',
            'description',
            'group',
            'properties',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )
