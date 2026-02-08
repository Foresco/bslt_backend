# Команда вставки метки в pdf-файл

from datetime import date
from django.core.management.base import BaseCommand
from jsonserv.docarchive.pdfutils import insert_text_to_pdf


class Command(BaseCommand):
    help = 'Insert watermark into pdf file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к файлу для вставки метки')
        parser.add_argument('res_path', type=str, help='Путь к файлу с вставленной меткой')
        parser.add_argument('watermark', type=str, help='Текст метки')

    def handle(self, *args, **options):
        file_path = options['file_path']
        res_path = options['res_path']
        watermark = options['watermark']
        # Формируем новый файл с меткой во временном каталоге
        new_file_path = insert_text_to_pdf(file_path, watermark, 25, 3, False, res_path)
