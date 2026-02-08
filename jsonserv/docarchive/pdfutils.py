# Утилиты для работы с pdf-файлами
import os.path
from PyPDF2 import PdfFileWriter, PdfFileReader #, PdfReader, PdfWriter
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from jsonserv.core.fileutils import get_watermark_file_path
import logging

logger = logging.getLogger('basalta')


def insert_text_to_pdf(file_name, text, x, y, red=True, new_file_name=''):
    """Вставка текста в pdf-фай с сохранением во временный каталог"""

    def get_width_height():
        """Вычисление ширины и высоты листа"""
        # mb = page.mediaBox
        mb = page.mediabox
        # return mb.getWidth(), mb.getHeight(), page.get('/Rotate')
        return mb.width, mb.height, page.get('/Rotate')

    def write_vertical_text(page_width, page_height, rotate_angle):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
        can.setFont('Arial', 12)
        if red:
            can.setFillColorRGB(200, 0, 0)
        can.saveState()
        logger.info(f'page_width={page_width}, page_height={page_height}, x={x}, y={y}, r={rotate_angle}')
        if rotate_angle == 90:  # Если применено вращение страницы (90)
            # Высота и ширина поменяны местами чтобы учесть дальнейшее вращение
            can.setPageSize((page_width, page_height))
            can.rotate(180)
            can.drawString(x - round(page_width), y - round(page_height), text)  # без round ошибка
        elif rotate_angle:  # Если применено вращение страницы (предполагается 270)
            can.drawString(x, y, text)
        else:
            # Высота и ширина поменяны местами чтобы учесть дальнейшее вращение
            can.setPageSize((page_width, page_height))
            can.rotate(90)
            can.drawString(x, y - round(page_width), text)  # без round ошибка
        can.restoreState()
        can.save()
        # Переходим в начало StringIO буфера
        packet.seek(0)
        # Генерируем новый pdf
        # return PdfFileReader(packet)
        return PdfFileReader(packet)
    
    logger.info(f'Читаем существующий pdf-файл {file_name}')
    # existing_pdf = PdfFileReader(open(file_name, "rb"), strict=False)
    existing_pdf = PdfFileReader(open(file_name, "rb"), strict=False)
    # output = PdfFileWriter()
    output = PdfFileWriter()
    # logger.info('Перебираем страницы')
    # for page_num in range(existing_pdf.getNumPages()):
    for page_num in range(len(existing_pdf.pages)):
        # logger.info('Вставка на первую страницу')
        page = existing_pdf.pages[page_num]
        if page_num == 0:   # Вставка только на первой странице
            # Определяем ширину и высоту страницы
            w, h, r = get_width_height()
            # Создаем образ с меткой
            wm = write_vertical_text(w, h, r)
            # Совмещаем страницы
            try:
                # page.mergePage(wm.getPage(0))
                page.merge_page(wm.pages[0])
            except Exception as e:
                logger.error(e)
            # Сжимаем для оптимизации размера
            try:
                # page.compressContentStreams()
                page.compress_content_streams()
            except Exception as e:
                logger.error(e)
        # output.addPage(page)
        output.add_page(page)
    # Записываем в новый файл
    if not new_file_name:
        # Имя нового файла не передано в параметрах
        new_file_name = get_watermark_file_path(os.path.basename(file_name))
    output_stream = open(new_file_name, "wb")
    output.write(output_stream)
    output_stream.close()
    logger.info('Запись файла успешно завершена')
    return new_file_name
