# Утилиты работы с базой данных
from django.db import connection
from jsonserv.core.fileutils import read_txt_file


def execute_sql(sql, params):
    """Получение результата запроса"""
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def execute_sql_to_dict(sql, params):
    """Выполнение запроса из sql-файла с преобразованием данных в словарь"""
    with connection.cursor() as cursor:
        if connection.vendor == 'postgresql':
            cursor.execute(sql, params)
        else:  # Пока только MS SQL
            # Не поддерживает именованные параметры (словари)
            import sqlparams
            # Преобразуем запрос и параметры
            query = sqlparams.SQLParams('pyformat', 'format')
            s, p = query.format(sql, params)
            cursor.execute(s, p)

        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]


def execute_sql_from_file(file_path, params, to_dict=False):
    """Выполнение запроса из sql-файла"""
    sql = read_txt_file(file_path)
    if to_dict:
        return execute_sql_to_dict(sql, params)
    return execute_sql(sql, params)
