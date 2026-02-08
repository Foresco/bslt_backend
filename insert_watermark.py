# Команда вставки метки в pdf файл
import argparse  # Пакет для парсинга аргументов
from PyPDF2 import PdfWriter, PdfReader
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import logging
logger = logging.getLogger('php_python')

logging.basicConfig(filename='/home/administrator/basalta/logs/php_python.log', level=logging.INFO)
logger.info('Started')



def parse_args():
    parser = argparse.ArgumentParser(description='Разбор аргументов команды вставки метки')
    parser.add_argument('file_path', type=str, help='Путь к файлу для вставки метки')
    parser.add_argument('res_path', type=str, help='Путь к файлу с вставленной меткой')
    parser.add_argument('watermark', type=str, help='Текст метки')

    # Возвращаем набор распарсенных аргументов
    return parser.parse_args()


def insert_text_to_pdf(file_name, text, x, y, red=True, new_file_name=''):
    """Вставка текста в pdf-фай с сохранением во временный каталог"""

    def get_width_height():
        """Вычисление ширины и высоты листа"""
        mb = page.mediabox
        return mb.width, mb.height, page.get('/Rotate')

    def write_vertical_text(page_width, page_height, rotate_angle):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
        can.setFont('Arial', 12)
        if red:
            can.setFillColorRGB(200, 0, 0)
        can.saveState()
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
        return PdfReader(packet)

    logger.info(f'открываем файл {file_name}')
    existing_pdf = PdfReader(open(file_name, "rb"), strict=False)
    output = PdfWriter()
    logger.info('Перебираем страницы')
    for page_num in range(len(existing_pdf.pages)):
        logger.info('Вставка на первую страницу')
        page = existing_pdf.pages[page_num]
        if page_num == 0:  # Вставка только на первой странице
            # Определяем ширину и высоту страницы
            w, h, r = get_width_height()
            # Создаем образ с меткой
            wm = write_vertical_text(w, h, r)
            # Совмещаем страницы
            try:
                page.merge_page(wm.pages[0])
            except Exception as e:
                print('Ошибка 1')
            # Сжимаем для оптимизации размера
            try:
                page.compress_content_streams()
            except Exception as e:
                print('Ошибка 2')
        output.add_page(page)
    # Записываем в новый файл
    logger.info(f'записываем файл {new_file_name}')
    output_stream = open(new_file_name, "wb")
    output.write(output_stream)
    output_stream.close()
    logger.info('Успешно!')
    return new_file_name


def main():
    # Разбираем переданные параметры и формируем
    logger.info('Разбор параметров')
    command_args = parse_args()  # Парсинг параметров запуска
    file_path = command_args.file_path
    res_path = command_args.res_path
    watermark = command_args.watermark
    # Формируем новый файл с меткой во временном каталоге
    new_file_path = insert_text_to_pdf(file_path, watermark, 25, 3, False, res_path)
    print(new_file_path)


if __name__ == '__main__':
    main()
