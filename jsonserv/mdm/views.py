from rest_framework.decorators import api_view

from jsonserv.rest.views import JSONResponse

from jsonserv.mdm.models import RawRow, RawProperty


@api_view(['GET', ])
def rawrow_prop_values_get(request, pk=''):
    """Получение списка значений свойств сырой строки"""
    if pk:
        props = RawProperty.get_id_names()
        rr = RawRow.objects.get(pk=pk)
        p = {props[int(id)]: val for id, val in rr.properties.items()}
        return JSONResponse(p)
