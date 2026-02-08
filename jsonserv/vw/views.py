from django.db.models import F
from django.db.models.functions import Coalesce

from jsonserv.vw.models import StaffTree, StaffRoot
from jsonserv.vw.serializers import StaffTreeSerializer, StaffRootSerializer
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response


@api_view(['GET',])
def get_root(request, pk):
    """Предоставление информации корневого элемента для дерева состава"""
    try:
        root = StaffRoot.objects.get(pk=pk)
    except StaffRoot.DoesNotExist:
        return Response({'message': f'Элемент [{pk}] не найден'}, status=status.HTTP_404_NOT_FOUND)
    serializer = StaffRootSerializer(root)
    return Response(serializer.data)


@api_view(['GET',])
def get_tree(request, pk):
    """Предоставление информации для дерева состава"""
    try:
        # Позиции без номера позиции помещаем в начало списка
        tree = StaffTree.objects.filter(parent_id=pk).order_by(Coalesce(
            F('position'), 0), 'child__part_type__order_num', 'child__code')
    except StaffTree.DoesNotExist:
        return Response({'message': f'Состав элемента [{pk}] не найден'}, status=status.HTTP_404_NOT_FOUND)
    serializer = StaffTreeSerializer(tree, many=True)
    return Response(serializer.data)
