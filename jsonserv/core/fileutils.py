# Функционал для работы с файлами
from shutil import copyfile, move
import hashlib  # Для расчета контрольной суммы файла
import os
import urllib
import mimetypes
from wsgiref.util import FileWrapper
from django.http import HttpResponse, StreamingHttpResponse
from django.conf import settings  # для обращения к настройкам
from django.db import connection

import logging

logger = logging.getLogger('basalta')


def prepare_filename(filename):
    """Формирование корректного имени файла"""
    map_s = str.maketrans('"/\'\\', '____')  # Заменяемые, заменяющие
    return filename.translate(map_s)  # Замена символов, недопустимых в имени файла


def handle_uploaded_file(file_obj, file_name):
    """Потоковая загрузка файла в архив"""
    try:
        with open(file_name, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)
    except (OSError, FileNotFoundError) as err:
        logger.info(f'Ошибка копирования файла: {str(err)}')
        return False

    return True


def copy_file_to_folder(src_file_name, dst_file_name):
    logger.info(f'Начинаем копирование {src_file_name} {dst_file_name}')
    try:
        copyfile(src_file_name, dst_file_name)
        return True
    # except (OSError, FileNotFoundError) as err:
    except Exception as err:  # Перехват любой ошибки
        logger.info(f'Ошибка копирования файла: {str(err)}')
        return False


def move_file_to_folder(src_file_name, dst_file_name):
    logger.info(f'Начинаем перемещение {src_file_name} {dst_file_name}')
    try:
        move(src_file_name, dst_file_name)
        return True
    # except (OSError, FileNotFoundError) as err:
    except Exception as err:  # Перехват любой ошибки
        logger.info(f'Ошибка перемещения файла: {str(err)}')
        return False


def compute_check_sum(file_path):
    """Вычисление контрольной суммы для указанного файла"""
    if os.path.isfile(file_path):
        return hashlib.md5(open(file_path, 'rb').read()).hexdigest()
    return None


def get_sql_file_path(app, file_name):
    """Формирование полного пути к файлу запроса"""
    if connection.vendor != 'postgresql':
        db = connection.vendor  # На случай, если БД отличная от PostgreSQLБ то для нее подкаталог
    else:
        db = ''
    return os.path.join(
        getattr(settings, 'BASE_DIR', ''),
        'jsonserv',
        app,
        'raw_sql',  # Так называется каталог для sql во всех моделях
        db,
        file_name
    )


def get_report_template_path(app, template_name):
    """Формирование полного пути к файлу шаблона отчета"""
    return os.path.join(
        getattr(settings, 'BASE_DIR', ''),
        'jsonserv',
        app,
        'reports',  # Так называется каталог для отчетов во всех моделях
        'templates',  # Так называется каталог для шаблонов отчетов во всех моделях
        template_name
    )


def get_temp_file_path(file_name):
    """Формирование полного пути ко временному файлу"""
    return os.path.join(
        getattr(settings, 'TEMP_DIR', 'temp'),
        file_name
    )


def get_log_file_path(file_name):
    """Формирование полного пути к лог-файлу"""
    return os.path.join(
        getattr(settings, 'LOG_DIR', 'log'),
        file_name
    )


def get_watermark_file_path(file_name):
    """Формирование полного пути к файлу c вотемаркой"""
    return os.path.join(
        getattr(settings, 'TEMP_DIR', 'temp'),
        'watermark',
        file_name
    )


def delete_file(file_path):
    """Физическое Удаление файла"""
    if os.path.exists(file_path):
        os.remove(file_path)


def read_txt_file(file_path):
    """Чтение текстового файла"""
    print(file_path)
    with open(file_path, "r", encoding='utf-8') as f:
        return f.read()


def http_unload_file(file_path, file_name, content_type):
    """Выгрузка файла по http-протоколу"""
    with open(file_path, 'rb') as fh:
        response = HttpResponse(fh.read(), content_type=content_type)
        response['Content-Description'] = 'File Transfer'
        response['Content-Length'] = os.path.getsize(file_path)
        # Ухищрения для передачи кириллических имен файлов
        response['Content-Disposition'] = "attachment; filename*=UTF-8'ru-ru'" + urllib.parse.quote(file_name)
        return response


def http_unload_big_file(file_path, file_name, content_type):
    """Выгрузка большого файла по http-протоколу"""
    chunk_size = 8192  # Размер кусочка при передаче
    response = StreamingHttpResponse(FileWrapper(open(file_path, 'rb'), chunk_size),
                                     content_type=mimetypes.guess_type(file_path)[0])
    response['Content-Length'] = os.path.getsize(file_path)
    # Ухищрения для передачи кириллических имен файлов
    response['Content-Disposition'] = "attachment; filename*=UTF-8'ru-ru'" + urllib.parse.quote(file_name)
    return response


def get_mime_type(file_name):
    """Получение mime type файла"""
    mime_types = {  # Соответствия расширений и типов файлов
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.dwg': 'application/dwg',
        '.dwf': 'application/dwf',
        '.sldasm': 'application/sldworks',
        '.sldprt': 'application/sldworks',
        '.slddrw': 'application/sldworks'
    }
    name, ext = os.path.splitext(file_name)
    return mime_types.get(ext.lower(), 'unknown')
