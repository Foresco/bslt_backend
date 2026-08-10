# Функции подготовки файлов для манипуляций
import os.path
from datetime import date
from django.conf import settings  # для обращения к настройкам
from jsonserv.docarchive.pdfutils import insert_text_to_pdf

import logging

logger = logging.getLogger('basalta')


def prepare_file_for_unload(request, file):
    """Подготовка файла к выгрузке. Здесь находятся обработки файла перед его выдачей пользователю"""
    file_name = os.path.basename(file.file_name)
    name, ext = os.path.splitext(file_name)
    if ext.lower() == '.pdf':  # Проверка, что расширение pdf
        if getattr(settings, 'INSERT_WATERMARK', False):  # Проверка необходимости вставки метки
            # if 1 == 2 and not request.user.has_perm('no_watermark'):  # Проверка права скачивания файла без метки
            if not file.document_version.document.doc_type or file.document_version.document.doc_type.s_key == 0:
                # Только для документов без типа и типа из нулевого раздела
                user = request.user
                # Формирование текста метки
                if hasattr(user, 'userprofile') and user.userprofile.user_name:
                    receiver = user.userprofile.user_name  # Имя из профиля текущего пользователя
                else:
                    receiver = user.last_name
                receive_date = date.today().strftime("%d.%m.%Y")  # Текущая дата
                mark = f"Экземпляр {receiver}: {receive_date}"
                # Формируем новый файл с меткой во временном каталоге
                file_path = insert_text_to_pdf(file.file_path, mark, 240, 3)
                # Если была указана вставка метки с датой
                watemark_date = request.GET.get('watemark_date')
                if watemark_date:
                    file_path = prepare_file_for_store(file_path, watemark_date)
                return file_path, file_name, file.data_format
    # Возвращаем словарь из трех параметров
    return file.file_path, file_name, file.data_format


def prepare_file_for_store(src_file, watemark_date):
    """Подготовка файла к помещению в архив. Здесь находятся обработки файла перед его переносом в каталог архива"""
    file_name = os.path.basename(src_file)
    name, ext = os.path.splitext(file_name)
    if watemark_date and ext.lower() == '.pdf':  # Проверка, что расширение pdf
        enterprise = getattr(settings, 'ENTERPRISE', '')
        mark = f"{enterprise} {watemark_date}"
        logger.info(f'Вставка в файл метки {mark}')
        # Формируем новый файл с меткой во временном каталоге
        result_file = insert_text_to_pdf(src_file, mark, 15, 3)
        return True, result_file
    # Возвращаем результат выполнения
    return True, src_file

