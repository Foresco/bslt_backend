from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import ExternalID
from .serializers import ExternalIDSerializer


@api_view(['GET', ])
def get_external(request, pk):
    """Предоставление информации о ссылках во внешних системах"""
    external_links = ExternalID.objects.filter(
        internal_id=pk
       ).values(
            'pk',
            'external_id',
            'partner__pk',
            'partner__partner_name',
            'partner__header_url'
        ).order_by(
            'partner__partner_name'
        )
    serializer = ExternalIDSerializer(external_links, many=True)
    return Response(serializer.data)
