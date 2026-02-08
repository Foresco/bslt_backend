from rest_framework import serializers

from jsonserv.docarchive.models import EntityDocumentVersion, FileDocument


class FileObjectsSerializer(serializers.Serializer):
    """Сериализатор файлов у объекта
    Не используется!!!"""
    id = serializers.IntegerField(source='entity__pk')
    code = serializers.CharField(source='entity__code')


class FileObjectsList(serializers.Field):
    """Отображение списка файлов объекта
    Не используется!!!"""
    def to_representation(self, value):
        objs = EntityDocumentVersion.objects.filter(
            document_version=value,
            old_version=False
        ).values(
            'pk',
            'entity__pk',
            'entity__code',
        ).order_by(
            'entity__code',
        )
        if objs:
            serializer = FileObjectsSerializer(objs, many=True)
            return serializer.data
        return None


class FileSuggestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileDocument
        fields = (
            'pk',
            'doc_code',
        )
    

class SearchFilesSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='document_versions__pk')
    version_num = serializers.IntegerField(source='document_versions__version_num')
    notice_num = serializers.SerializerMethodField()
    file_name = serializers.CharField(source='document_versions__digital_files__file_name')
    url = serializers.SerializerMethodField()    
    objects = serializers.CharField()
    # objects = FileObjectsList(source='document_versions__pk')

    def get_url(self, instance):
        return f'file/{instance["document_versions__digital_files__pk"]}/'

    def get_notice_num(self, instance):
        # Форматируем строку ссылки
        if instance["document_versions__notice__code"]:
            notice_num = instance["document_versions__notice__code"]
            if instance["document_versions__change_num"]:
                notice_num += ' изм.' + str(instance["document_versions__change_num"])
                if instance["document_versions__change_type__list_value"]:
                    notice_num += ' ' + instance["document_versions__change_type__list_value"]
            return notice_num
        return ''

    
    # "id": 9,
	# 	"version_num": 2,
	# 	"notice_num": "082-23 изм.1 Зам",
	# 	"file_name": "CPM3500_03_03_01_000_sp.pdf",
	# 	"objects": "CPM3500.03.03.01.000",
	# 	"url": "/file/9/",
