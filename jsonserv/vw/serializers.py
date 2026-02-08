from rest_framework import serializers

from jsonserv.docarchive.models import EntityDocumentVersion
from jsonserv.vw.models import StaffRoot, StaffTree


class FilesListList(serializers.Serializer):
    id = serializers.IntegerField(source='document_version__digital_files__pk')
    file_name = serializers.CharField(source='document_version__digital_files__file_name')
    type_class = serializers.CharField(source='document_version__document__doc_type__value_class', default='')


class FilesList(serializers.Field):
    """Отображение всех файлов объекта"""

    def to_representation(self, value):
        files = EntityDocumentVersion.objects.filter(
            entity=value, old_version=False,
            document_version__digital_files__dlt_sess=0
        ).values(
            'document_version__digital_files__pk',
            'document_version__digital_files__file_name',
            'document_version__document__doc_type__value_class'
        ).order_by(
            'document_version__digital_files__file_name'
        )

        if files:
            serializer = FilesListList(files, many=True)
            return serializer.data
        return None


class StaffTreeSerializer(serializers.ModelSerializer):
    files = FilesList(source='child_id')

    class Meta:
        model = StaffTree
        fields = ('id', 'parent', 'child', 'part_type_id', 'code', 'title', 'quantity', 'position', 'format_string', 'weight',
                  'designer', 'des_state', 'material', 'notice', 'has_staff', 'can_has_staff', 'label', 'has_arcdocs',
                  'ratio', 'to_replace', 'files', 'outdated')


class StaffRootSerializer(serializers.ModelSerializer):
    files = FilesList(source='child_id')

    class Meta:
        model = StaffRoot
        fields = ('id', 'child', 'part_type_id', 'code', 'title', 'quantity', 'position', 'format_string', 'weight',
                  'designer', 'des_state', 'material', 'notice', 'has_staff', 'can_has_staff', 'label', 'has_arcdocs',
                  'ratio', 'to_replace', 'files', 'outdated')
