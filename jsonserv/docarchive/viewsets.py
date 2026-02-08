import django_filters  # Специальные фильтры
from django.db.models import Q

from jsonserv.core.models import fn_head_key
from jsonserv.core.viewsets import CommonViewSet, DateEqualFilter, EqualFilter, ListViewSet

from jsonserv.docarchive.models import (ArcDocument, ArcDocumentObject, CodePrefix, FileDocument, FileUpload, Delivery,
                                        DeliveryArcdoc, DocumentType, DocumentVersion, EntityDocumentVersion, Incident)
from jsonserv.docarchive.serializers import (CodePrefixSerializer,
                                             FileDocumentSerializer, FileDocumentSerializerDetailed,
                                             FileDocumentSerializerList,
                                             FileUploadSerializer, FileUploadSerializerDetailed,
                                             FileUploadSerializerList,
                                             ArcDocumentSerializer, ArcDocumentSerializerDetailed,
                                             ArcDocumentSerializerList,
                                             ArcDocumentObjectSerializer, ArcDocumentObjectSerializerList,
                                             DeliverySerializer, DeliverySerializerDetailed, DeliverySerializerList,
                                             DeliveryArcdocSerializer, DeliveryArcdocSerializerList,
                                             DocumentTypeSerializer, DocumentVersionSerializer,
                                             EntityDocumentVersionSerializer, DocumentVersionDetailed, EntityDocumentVersionSerializerList,
                                             IncidentSerializer, IncidentSerializerDetailed, IncidentSerializerList)


class DeliveryFilter(django_filters.FilterSet):
    """Особые фильтры для списка извещений"""
    min_date = django_filters.DateFilter(
        field_name="delivery_date", lookup_expr='gte')
    max_date = django_filters.DateFilter(
        field_name="delivery_date", lookup_expr='lte')
    equal_date = DateEqualFilter(field_name="delivery_date")
    place = EqualFilter(field_name="receiver")

    class Meta:
        model = Delivery
        fields = ['equal_date', 'min_date', 'max_date']


class DeliveryViewSet(CommonViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer
    serializer_class_detailed = DeliverySerializerDetailed
    serializer_class_list = DeliverySerializerList
    filterset_class = DeliveryFilter  # Особые настройки фильтрации

    # Поля поиска
    search_fields = (
        'comment',
    )


class DeliveryArcdocViewSet(CommonViewSet):
    queryset = DeliveryArcdoc.objects.all().order_by('arc_doc__code')
    serializer_class = DeliveryArcdocSerializer
    serializer_class_list = DeliveryArcdocSerializerList
    paginator = None  # Отключение пагинации

    # Поля фильтрации
    filterset_fields = (
        'delivery',
        'arc_doc'
    )


class DocumentTypeViewSet(ListViewSet):
    queryset = DocumentType.objects.all().order_by(
        'order_num', 'value_code', 'list_value')
    serializer_class = DocumentTypeSerializer

    # Поля фильтрации
    filterset_fields = (
        's_key',
    )
    # Поля поиска
    search_fields = (
        'list_value',
    )


class DocumentVersionViewSet(CommonViewSet):
    queryset = DocumentVersion.objects.all()
    serializer_class = DocumentVersionSerializer
    serializer_class_detailed = DocumentVersionDetailed

    # Поля фильтрации
    filterset_fields = (
        'document',
    )
    
    def get_queryset(self):
        if self.action == 'retrieve':
            return DocumentVersion.objects.all().values(
                'pk',
                'version_num',
                'document__doc_code',
            )
        return DocumentVersion.objects.all()


class EntityDocumentVersionViewSet(CommonViewSet):
    queryset = EntityDocumentVersion.objects.all()
    serializer_class = EntityDocumentVersionSerializer
    serializer_class_list = EntityDocumentVersionSerializerList
    paginator = None  # Отключение пагинации

    # Поля фильтрации
    filterset_fields = (
        'entity',
        'document_version'
    )


class FileDocumentViewSet(CommonViewSet):
    queryset = FileDocument.objects.all()
    serializer_class = FileDocumentSerializer
    serializer_class_detailed = FileDocumentSerializerDetailed
    serializer_class_list = FileDocumentSerializerList

    # Поля фильтрации
    filterset_fields = (
        'doc_type',
    )
    # Поля поиска
    search_fields = (
        'doc_code',
    )


class FileUploadViewSet(CommonViewSet):
    queryset = FileUpload.objects.all().order_by('-upload_date')
    serializer_class = FileUploadSerializer
    serializer_class_detailed = FileUploadSerializerDetailed
    serializer_class_list = FileUploadSerializerList

    # Поля поиска
    search_fields = (
        'file_name',
    )


class ArcDocumentFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search')  # Особая обработка поискового запроса

    class Meta:
        model = ArcDocument
        # Поля поиска
        fields = (
            'search',
        )

    def filter_search(self, queryset, name, value):
        key_value = fn_head_key(str(value))  # Ключ для поиска в поле head_key
        # Комбинация поиска по полям, в т.ч. по head_key
        return queryset.filter(
            Q(code__icontains=value) |
            Q(document_num__icontains=value) |
            Q(head_key__icontains=key_value)
        )


class ArcDocumentViewSet(CommonViewSet):
    queryset = ArcDocument.objects.all()
    serializer_class = ArcDocumentSerializer
    serializer_class_detailed = ArcDocumentSerializerDetailed
    serializer_class_list = ArcDocumentSerializerList

    def get_queryset(self):
        if self.action == 'list':  # Для списков
            # Применяем другой фильтр
            self.filter = ArcDocumentFilter(self.request.GET, queryset=ArcDocumentViewSet.queryset)
            # print(self.filter.qs.query)
            return self.filter.qs
        return ArcDocumentViewSet.queryset  # Иначе по умолчанию


class ArcDocumentObjectViewSet(CommonViewSet):
    queryset = ArcDocumentObject.objects.all().order_by('child__code')
    serializer_class = ArcDocumentObjectSerializer
    serializer_class_list = ArcDocumentObjectSerializerList
    paginator = None  # Отключение пагинации

    # Поля фильтрации
    filterset_fields = (
        'parent',
        'child'
    )


class CodePrefixViewSet(CommonViewSet):
    queryset = CodePrefix.objects.all()
    serializer_class = CodePrefixSerializer

    # Поля поиска
    search_fields = (
        'prefix_code',
        'project_code',
        'description'
    )


class IncidentFilter(django_filters.FilterSet):
    """Особые фильтры для списка извещений"""
    min_date = django_filters.DateFilter(
        field_name="incident_date", lookup_expr='gte')
    max_date = django_filters.DateFilter(
        field_name="incident_date", lookup_expr='lte')
    equal_date = DateEqualFilter(field_name="incident_date")

    class Meta:
        model = Incident
        fields = ['parent', 'equal_date', 'min_date', 'max_date']


class IncidentViewSet(CommonViewSet):
    queryset = Incident.objects.all().order_by('-incident_num')
    serializer_class = IncidentSerializer
    serializer_class_detailed = IncidentSerializerDetailed
    serializer_class_list = IncidentSerializerList
    filterset_class = IncidentFilter  # Особые настройки фильтрации

    # Поля поиска
    search_fields = (
        'code',
        'plant_number',
        'description'
    )
