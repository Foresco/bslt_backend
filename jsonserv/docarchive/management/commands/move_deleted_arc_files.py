# Команда перемещения помеченных как удаленные файлов в другой каталог

from datetime import datetime
import os
from shutil import move
from django.core.management.base import BaseCommand
from jsonserv.core.fileutils import get_log_file_path
from jsonserv.docarchive.models import DigitalFile


class Command(BaseCommand):
    help = 'Move deleted files from archive'

    def add_arguments(self, parser):
        parser.add_argument('target', help='Каталог для перемещения файлов')
        parser.add_argument('--archive_name', type=str, nargs='?', help='Идентификатор архива для обработки')

    def handle(self, *args, **options):
        target = options['target']
        archive_name = options['archive_name']
        files = DigitalFile.all_files.exclude(dlt_sess=0)  # Отбираем только удаленные
        if archive_name:
            files = files.filter(folder__archive__archive_name=archive_name)
        moved_files = list()
        for fl in files:
            file_path = fl.file_path
            # Проверяем существование файла
            if os.path.isfile(file_path):
                # Формируем новое имя файла
                new_path = os.path.join(target, fl.folder.archive.archive_name, fl.folder.folder_name)
                if not os.path.isdir(new_path):
                    # Создаем каталог, если его не существует
                    os.makedirs(new_path)
                new_file_path = os.path.join(new_path, fl.file_name)
                try:
                    move(file_path, new_file_path)
                    moved_files.append(file_path)
                except Exception as err:  # Перехват любой ошибки
                    print(f'Ошибка перемещения файла {file_path} {new_file_path}: {str(err)}')

        # Если были найдены удаленные файлы
        if moved_files:
            err_list_file = f'moved files {datetime.now().strftime("%Y%m%d-%H%M%S")}.log'
            err_list_file = get_log_file_path(err_list_file)
            with open(err_list_file, 'w') as f:
                f.write('\n'.join(moved_files))
            print('Адреса перемещенных файлов сохранены в файл', err_list_file)
        else:
            print('Удаленные файлы не обнаружены')