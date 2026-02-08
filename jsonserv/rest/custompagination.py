# Доработанный класс пагинации
from rest_framework.pagination import LimitOffsetPagination


class LimitOffsetPaginationWithUpperBound(LimitOffsetPagination):
    """Пользовательский класс пагинации
    Используется в настройках (settings.py)"""
    max_limit = 30  # Set the maximum limit value to 30
