from rest_framework import serializers
# Классы, подлежащие сериализации
from jsonserv.core.models import UserProfile
from jsonserv.staff.models import (StaffPosition, Person, PersonStaffPosition)


class PersonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Person
        fields = (
            'pk',
            'person_profile',
            'person',
            'person_short',
            'person_r',
            'person_d',
            'person_phone',
            'person_mail',
            'person_category',
            'work_rank',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class PersonProfileRefSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='user_name')

    class Meta:
        model = UserProfile
        fields = ('pk', 'value')


class PersonSerializerDetailed(serializers.ModelSerializer):
    work_rank = serializers.ChoiceField(Person.WORKRANKCHOICES)
    person_profile = PersonProfileRefSerializer(read_only=True)
    person_category = serializers.SlugRelatedField(read_only=True, slug_field='list_value')

    class Meta:
        model = Person
        fields = (
            'pk',
            'person_profile',
            'person',
            'person_short',
            'person_r',
            'person_d',
            'person_phone',
            'person_mail',
            'person_category',
            'work_rank',
        )


class PersonSerializerList(serializers.ModelSerializer):
    person_profile = serializers.SlugRelatedField(read_only=True, slug_field='user_name')

    class Meta:
        model = Person
        fields = (
            'pk',
            'person_profile',
            'person'
        )


class PersonStaffPositionSerializer(serializers.ModelSerializer):

    class Meta:
        model = PersonStaffPosition
        fields = (
            'pk',
            'person',
            'staff_position',
            'place',
            'is_main',
            'edt_sess',
            'crtd_sess',
            'dlt_sess')


class PersonStaffPositionSerializerDetailed(serializers.ModelSerializer):

    class Meta:
        model = PersonStaffPosition
        fields = (
            'pk',
            'person',
            'staff_position',
            'place',
            'is_main'
        )


class PersonStaffPositionSerializerList(serializers.ModelSerializer):
    person = serializers.SlugRelatedField(read_only=True, slug_field='person')
    place = serializers.SlugRelatedField(read_only=True, slug_field='code')
    staff_position = serializers.SlugRelatedField(read_only=True, slug_field='position_name')

    class Meta:
        model = PersonStaffPosition
        fields = (
            'pk',
            'person',
            'staff_position',
            'place'
        )


class StaffPositionSerializer(serializers.ModelSerializer):

    class Meta:
        model = StaffPosition
        fields = (
            'pk',
            'position_name',
            'edt_sess',
            'crtd_sess',
            'dlt_sess')


class StaffPositionSerializerDetailed(serializers.ModelSerializer):

    class Meta:
        model = StaffPosition
        fields = (
            'pk',
            'position_name'
        )
