# Утилиты для работы с pdf-файлами
import os.path
import io
from pypdf import PdfReader, PdfWriter
# from pypdf.generic import Destination, NumberObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from jsonserv.core.fileutils import get_watermark_file_path
import logging

import sys
sys.setrecursionlimit(5000)  # Default is usually 1000

logger = logging.getLogger('basalta')


def insert_text_to_pdf(file_name, text, x, y, red=True, new_file_name=''):
    """Вставка текста в pdf-фай с сохранением во временный каталог"""

    def get_width_height(page):
        """Вычисление ширины и высоты листа"""
        mb = page.mediabox
        return mb.width, mb.height, page.get('/Rotate', 0)

    def write_vertical_text(page_width, page_height, rotate_angle):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
        can.setFont('Arial', 12)
        if red:
            can.setFillColorRGB(200, 0, 0)
        can.saveState()

        if rotate_angle == 90:  # Если применено вращение страницы (90)
            can.setPageSize((page_width, page_height))
            can.rotate(180)
            can.drawString(x - round(page_width), y - round(page_height), text)
        elif rotate_angle:  # Если применено вращение страницы (предполагается 270)
            can.drawString(x, y, text)
        else:
            can.setPageSize((page_width, page_height))
            can.rotate(90)
            can.drawString(x, y - round(page_width), text)

        can.restoreState()
        can.save()
        packet.seek(0)
        return PdfReader(packet)
    
    logger.info(f'Читаем существующий pdf-файл {file_name}')
    existing_pdf = PdfReader(open(file_name, "rb"), strict=False)
    output = PdfWriter()
    # logger.info('Перебираем страницы')
    for page_num, page in enumerate(existing_pdf.pages):
        # logger.info(f'Страница {page_num}')
        if page_num > 1000:
            continue
        if page_num == 0:   # Вставка только на первой странице
            logger.info('Вставка на первую страницу')
            # Определяем ширину и высоту страницы
            w, h, r = get_width_height(page)
            # Создаем образ с меткой
            wm = write_vertical_text(w, h, r)
            # Совмещаем страницы
            try:
                page.merge_page(wm.pages[0])
            except Exception as e:
                logger.error(e)
            # Сжимаем для оптимизации размера
            # try:
            #     page.compress_content_streams()
            # except Exception as e:
            #     logger.error(e)

        output.add_page(page)

    # Сжатие страниц для оптимизации размера
    compressed = False  # Для контроля сжатия только первой страницы
    for page in output.pages:
        if compressed:  # Значит страница не первая
            break
        page.compress_content_streams(level=9)  # Works correctly
        compressed = True  # Первую страницу обработали

    # Копирование оглавления    
    if existing_pdf.outline:
        # Функция для рекурсивного копирования закладок
        def copy_outline_items(outline_items, parent):
            parent_loc = None
            for item in outline_items:
                if isinstance(item, list):
                    # Если это список элементов оглавления
                    copy_outline_items(item, parent_loc)
                else:
                    # Это элемент оглавления - создаем его
                    if hasattr(item, 'page'):
                        # print(item.page)
                        # Определяем номер страницы для закладки
                        page_number = existing_pdf.get_destination_page_number(item)
                        # Создаем новую закладку
                        parent_loc = output.add_outline_item(
                                    title=item.title,
                                    page_number=page_number,
                                    parent=parent
                                )
        # Получаем корневые закладки
        outline_root = existing_pdf.outline
        copy_outline_items(outline_root, None)

    # Записываем в новый файл
    if not new_file_name:
        # Имя нового файла не передано в параметрах
        new_file_name = get_watermark_file_path(os.path.basename(file_name))
    output_stream = open(new_file_name, "wb")
    output.write(output_stream)
    output_stream.close()
    logger.info('Запись файла успешно завершена')
    return new_file_name
