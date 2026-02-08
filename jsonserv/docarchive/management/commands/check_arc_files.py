# Команда проверки корректности ссылок на файлы в архиве
from datetime import datetime
import os.path
from django.core.management.base import BaseCommand
from jsonserv.core.fileutils import get_log_file_path
from jsonserv.docarchive.models import DigitalFile


class Command(BaseCommand):
    help = 'Check files in archives'

    def add_arguments(self, parser):
        parser.add_argument('--archive_name', type=str, help='Идентификатор архива для проверки')
        parser.add_argument('--delete_rows', action='store_true',  help='Указание об удалении ошибочных ссылок')

    def handle(self, *args, **options):
        # archive_name = options['archive_name']
        delete_rows = options['delete_rows']
        files = DigitalFile.all_files.all()
        err_links = list()
        for fl in files:
            file_path = fl.file_path
            # Проверяем существование файла
            if not os.path.isfile(file_path):
                err_links.append(file_path)
                if delete_rows:
                    fl.delete_row()  # Физическое удаление записи из базы данных

        # Если были найдены ошибочные ссылки
        if err_links:
            err_list_file = f'wrong file links {datetime.now().strftime("%Y%m%d-%H%M%S")}.log'
            err_list_file = get_log_file_path(err_list_file)
            with open(err_list_file, 'w') as f:
                f.write('\n'.join(err_links))
            print('Ошибочные ссылки сохранены в файл', err_list_file)
        else:
            print('Ошибочные ссылки не обнаружены')