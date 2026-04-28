from rest_framework import serializers

from jsonserv.docarchive.models import (CodePrefix, DocumentVersion, EntityDocumentVersion, FileDocument, FileUpload,
                                        ArcDocument, ArcDocumentObject, Delivery, DeliveryArcdoc, Incident,
                                        UploadArcdoc, VersionDesignRole, DocumentType)

from jsonserv.core.serializers import EntityRefSerializer, UserSessionUserField, EntityChildObjectSerializer


class DocumentsList(serializers.Serializer):
    pk = serializers.IntegerField()
    old_version = serializers.BooleanField()
    file_document_id = serializers.IntegerField(source='document_version__document__pk')
    document_version_id = serializers.IntegerField(source='document_version__pk')
    version_num = serializers.IntegerField(source='document_version__version_num')
    notice_id = serializers.IntegerField(source='document_version__notice')
    notice_num = serializers.CharField(source='document_version__notice__code')
    version_stage = serializers.CharField(source='document_version__version_stage__code')
    change_type_id = serializers.IntegerField(source='document_version__change_type')
    change_type = serializers.CharField(source='document_version__change_type__list_value')
    doc_code = serializers.CharField(source='document_version__document__doc_code')
    doc_name = serializers.CharField(source='document_version__document__doc_name')
    change_num = serializers.IntegerField(source='document_version__change_num')
    file_name = serializers.CharField(source='document_version__digital_files__file_name')
    description = serializers.CharField(source='document_version__document__description')
    doc_type_id = serializers.IntegerField(source='document_version__document__doc_type')
    doc_type = serializers.CharField(source='document_version__document__doc_type__list_value')
    design_role_id = serializers.IntegerField(source='document_version__document_roles__pk')
    designer_id = serializers.IntegerField(source='document_version__document_roles__designer_id')
    designer = serializers.CharField(source='document_version__document_roles__designer__designer')
    file_id = serializers.IntegerField(source='document_version__digital_files__pk')
    session_datetime = serializers.DateTimeField(source='document_version__digital_files__crtd_sess__session_datetime',
                                                 format="%d.%m.%Y")
    username = serializers.CharField(source='document_version__digital_files__crtd_sess__user__username')
    url = serializers.SerializerMethodField()
    next_version_id = serializers.IntegerField()

    def get_url(self, instance):
        return f'/file/{instance["document_version__digital_files__pk"]}/'


class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = ('pk', 'list_value', 'order_num', 'value_code', 'is_default', 's_key')


class DocumentTypeSerializerList(serializers.Serializer):
    pk = serializers.IntegerField()
    list_value = serializers.CharField()


class DocumentVersionSerializer(serializers.ModelSerializer):

    class Meta:
        model = DocumentVersion
        fields = (
            'pk',
            'document',
            'archive_cell',
            'description',
            'version_num',
            'notice',
            'change_num',
            'change_type',
            'is_done',
            'version_stage',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class DocumentVersionDetailed(serializers.Serializer):
    pk = serializers.IntegerField(read_only=True)
    doc_code = serializers.CharField(source='document__doc_code')
    version_num = serializers.IntegerField()


class DeliverySerializer(serializers.ModelSerializer):

    class Meta:
        model = Delivery
        fields = (
            'pk',
            'receiver',
            'delivery_date',
            'comment',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class DeliverySerializerDetailed(serializers.ModelSerializer):
    receiver = EntityRefSerializer(read_only=True)

    class Meta:
        model = Delivery
        fields = (
            'pk',
            'receiver',
            'delivery_date',
            'comment',
            'delivery_num'
        )


class DeliverySerializerList(serializers.ModelSerializer):
    receiver = serializers.SlugRelatedField(read_only=True, slug_field='code')
    delivery_date = serializers.DateField(format="%d.%m.%Y")

    class Meta:
        model = Delivery
        fields = (
            'pk',
            'receiver',
            'delivery_date',
            'comment',
            'delivery_num'
        )


class DeliveryArcdocSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeliveryArcdoc
        fields = (
            'pk',
            'delivery',
            'arc_doc',
            'exemplar_num',
            'comment',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class DeliveryArcdocSerializerList(serializers.ModelSerializer):
    arc_doc = EntityRefSerializer(read_only=True)
    delivery = DeliverySerializerList(read_only=True)

    class Meta:
        model = DeliveryArcdoc
        fields = (
            'pk',
            'delivery',
            'arc_doc',
            'exemplar_num',
            'comment'
        )


class FileDocumentVersionsList(serializers.Serializer):
    pk = serializers.IntegerField(source='document_version_id')
    file_name = serializers.CharField()
    doc_type = serializers.CharField(source='document_version__document__doc_type__list_value')
    version_id = serializers.IntegerField(source='document_version_id')
    version_num = serializers.IntegerField(source='document_version__version_num')
    notice_id = serializers.IntegerField(source='document_version__notice')
    notice_num = serializers.CharField(source='document_version__notice__code')
    change_num = serializers.IntegerField(source='document_version__change_num')
    change_type = serializers.CharField(source='document_version__change_type__list_value')
    description = serializers.CharField(source='document_version__document__description')
    designer = serializers.CharField(source='document_version__document_roles__designer__designer')
    session_datetime = serializers.DateTimeField(source='crtd_sess__session_datetime', format="%d.%m.%Y")
    username = serializers.CharField(source='crtd_sess__user__username')
    url = serializers.SerializerMethodField()

    def get_url(self, instance):
        return f'/file/{instance["pk"]}/'


class EntityDocumentVersionSerializer(serializers.ModelSerializer):

    class Meta:
        model = EntityDocumentVersion
        fields = (
            'pk',
            'entity',
            'document_version',
            'old_version',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class EntityDocumentVersionSerializerList(serializers.ModelSerializer):
    entity = EntityChildObjectSerializer()

    class Meta:
        model = EntityDocumentVersion
        fields = (
            'pk',
            'entity',
            'document_version',
            'old_version',
        )


class FileDocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = FileDocument
        fields = (
            'pk',
            'doc_code',
            'doc_name',
            'description',
            'doc_type',
            'archive',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class FileDocumentSerializerDetailed(serializers.ModelSerializer):
    doc_type = serializers.SlugRelatedField(read_only=True, slug_field='list_value')

    class Meta:
        model = FileDocument
        fields = (
            'pk',
            'doc_code',
            'description',
            'doc_type',
        )


class FileDocumentSerializerList(serializers.ModelSerializer):

    doc_type = serializers.SlugRelatedField(read_only=True, slug_field='list_value')

    class Meta:
        model = FileDocument
        fields = (
            'pk',
            'doc_code',
            'doc_type'
        )


class FileUploadSerializer(serializers.ModelSerializer):

    class Meta:
        model = FileUpload
        fields = (
            'pk',
            'file_name',
            'crtd_sess'
        )


class FileUploadSerializerDetailed(serializers.ModelSerializer):
    crtd_user = UserSessionUserField(source='crtd_sess')

    class Meta:
        model = FileUpload
        fields = (
            'pk',
            'file_name',
            'upload_date',
            'crtd_user'
        )


class FileUploadSerializerList(serializers.ModelSerializer):
    upload_date = serializers.DateField(format="%d.%m.%Y")
    upload_user = UserSessionUserField(source='crtd_sess')

    class Meta:
        model = FileUpload
        fields = (
            'pk',
            'file_name',
            'upload_date',
            'upload_user'
        )


class ArcDocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = ArcDocument
        fields = (
            'pk',
            'prefix',
            'code',
            'parent',
            'description',
            'group',
            'doc_type',
            'document_name',
            'document_num',
            'reg_date',
            'list_count',
            'document_state',
            # 'document_stage',
            'document_place',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )

    def create(self, validated_data):
        if 'prefix' in validated_data and validated_data['prefix']:
            # Формирование инвентарного номера с учетом префикса
            validated_data['document_num'] = f"{validated_data['prefix'].prefix_code}/{validated_data['document_num']}"
        return super().create(validated_data)


class ArcDocumentSerializerDetailed(serializers.ModelSerializer):
    group = EntityRefSerializer(read_only=True)
    parent = EntityRefSerializer(read_only=True)
    # document_stage = EntityRefSerializer(read_only=True)
    document_place = EntityRefSerializer(read_only=True)

    class Meta:
        model = ArcDocument
        fields = (
            'pk',
            'prefix',
            'code',
            'parent',
            'group',
            'description',
            'doc_type',
            'document_name',
            'document_num',
            'reg_date',
            'list_count',
            'document_state',
            # 'document_stage',
            'document_place',
            'formats'
        )


class ArcDocumentSerializerList(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(read_only=True, slug_field='code')
    doc_type = serializers.SlugRelatedField(read_only=True, slug_field='list_value')

    class Meta:
        model = ArcDocument
        fields = (
            'pk',
            'code',
            'parent',
            'doc_type',
            'document_name',
            'document_num'
        )


class ArcDocumentObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArcDocumentObject
        fields = (
            'pk',
            'parent',
            'child',
            'comment',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class ArcDocumentObjectSerializerList(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(read_only=True, slug_field='key_code')
    child = serializers.SlugRelatedField(read_only=True, slug_field='key_code')

    class Meta:
        model = ArcDocumentObject
        fields = (
            'pk',
            'parent',
            'parent_id',
            'child',
            'child_id',
            'comment'
        )


class CodePrefixSerializer(serializers.ModelSerializer):

    class Meta:
        model = CodePrefix
        fields = (
            'pk',
            'prefix_code',
            'project_code',
            'description',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class IncidentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Incident
        fields = (
            'pk',
            'parent',
            'incident_date',
            'plant_number',
            'description',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class IncidentSerializerDetailed(serializers.ModelSerializer):
    parent = EntityRefSerializer(read_only=True)

    class Meta:
        model = Incident
        fields = (
            'pk',
            'code',
            'parent',
            'incident_date',
            'plant_number',
            'description'
        )


class IncidentSerializerList(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(read_only=True, slug_field='code')
    incident_date = serializers.DateField(format="%d.%m.%Y")

    class Meta:
        model = Incident
        fields = (
            'pk',
            'code',
            'parent',
            'incident_date',
            'plant_number'
        )


class ObjectFilesList(serializers.Field):
    """Отображение списка файлов объекта"""
    def to_representation(self, value):
        files = EntityDocumentVersion.objects.filter(
            entity_id=value,
            dlt_sess=0,
            document_version__digital_files__dlt_sess=0,
            old_version=False
        ).values(
            'pk',
            'document_version__digital_files__pk',
            'document_version__digital_files__file_name',
            'document_version__document__doc_type__value_class'
        ).order_by(
            'document_version__digital_files__file_name',
        )
        if files:
            serializer = ObjectFilesSerializer(files, many=True)
            return serializer.data
        return None


class UploadArcdocsSerializerList(serializers.ModelSerializer):
    arc_doc = EntityRefSerializer(read_only=True)
    files = ObjectFilesList(source='arc_doc_id')

    class Meta:
        model = UploadArcdoc
        fields = (
            'pk',
            'file_upload',
            'arc_doc',
            'files'
        )


class VersionDesignRoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = VersionDesignRole
        fields = (
            'pk',
            'document_version',
            'role',
            'designer',
            'role_date',
            'comment',
            'edt_sess',
            'crtd_sess',
            'dlt_sess'
        )


class ObjectFilesSerializer(serializers.Serializer):
    """Сериализатор файлов у объекта"""
    id = serializers.IntegerField(source='document_version__digital_files__pk')
    file_name = serializers.CharField(source='document_version__digital_files__file_name')
    type_class = serializers.CharField(source='document_version__document__doc_type__value_class')


class NoticeLinkDocSerializerList(serializers.Serializer):
    """Сериализатор файлов у извещения"""
    id = serializers.IntegerField(source='digital_files__pk')
    file_name = serializers.CharField(source='digital_files__file_name')
    doc_type = serializers.CharField(source='document__doc_type__list_value')
    change_type = serializers.CharField(source='change_type__list_value')
    change_num = serializers.IntegerField()
    version_num = serializers.IntegerField()
    is_done = serializers.BooleanField()
    url = serializers.SerializerMethodField()

    def get_url(self, instance):
        return f'/file/{instance["digital_files__pk"]}/'
