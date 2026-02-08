# Загрузка файлов из внешних источников во внутренне хранилище
from shutil import copyfile, move
import wget
from urllib.error import URLError
import ssl
import os.path

from django.conf import settings  # для обращения к настройкам

from jsonserv.core.fileutils import compute_check_sum


class FileUploader:
    """Класс, отвечающий за перемещение внешних файлов во внутренний архив"""

    def __init__(self, dir_name=''):
        self.error_message = ''  # Текст ошибки
        self.is_error = False
        self.file_name = ''  # Имя исходного файла
        self.temp_dir_name = getattr(settings, 'TEMP_DIR', 'temp')
        self.tmp_file_path = ''  # Имя файла во временном каталоге
        self.file_ext = ''  # Расширение файла
        self.regime = 'move'  # Режим обращения с временным файлом (move/copy)

    def file_download(self, source_file_name):
        """Загрузка/копирование исходного файла"""
        # Определение источника (каталог или веб)
        if source_file_name.startswith('http'):
            ssl._create_default_https_context = ssl._create_unverified_context  # Защита от ошибки с ssl-сертификатом
            try:
                # print(source_file_name, self.tmp_file_path)
                wget.download(source_file_name, self.tmp_file_path)
            except URLError as err:
                self.error_message = str(err)
                self.is_error = True
            self.regime = 'copy'  # Чтобы не скачивать повторно в случае чего...
        else:
            if os.path.isfile(source_file_name):
                # Копирование файла во временное хранилище
                try:
                    copyfile(source_file_name, self.tmp_file_path)
                except OSError as err:
                    self.error_message = str(err)
                    self.is_error = True
            else:
                self.error_message = "По указанному пути файл не обнаружен"
                self.is_error = True
            self.regime = 'move'

    def file_get(self, source_file_name):
        """Получение файла во временное хранилище"""
        if not source_file_name:
            self.error_message = 'Не указано имя файла'
            self.is_error = True
            return ''
        # Определение имени файла
        self.file_name = os.path.basename(source_file_name)
        # Вычисление пути назначения
        self.tmp_file_path = os.path.join(self.temp_dir_name, self.file_name)

        if not os.path.isfile(self.tmp_file_path):  # Проверка наличия такого файла в папке
            self.file_download(source_file_name)
        if self.is_error:  # Если при загрузки произошла ошибка
            return ''
        # Расчет контрольной суммы
        check_sum = compute_check_sum(self.tmp_file_path)
        # Определение расширения файла
        self.file_ext = os.path.splitext(self.file_name)[1]
        # Формирование имени файла
        file_name = check_sum + self.file_ext
        return file_name

    def file_put(self, file_name, dest_arc='grapfic'):
        """Помещение файла в основное хранилище"""
        # Определяем архив для сохранения (графика/файлы и т.п.)
        if dest_arc == 'grapfic':
            dst_name = os.path.join(getattr(settings, 'GRAPHIC_DIR', 'graphic'), file_name)
        else:
            # Этот вариант пока не рабочий
            dst_name = os.path.join(self.temp_dir_name, file_name)
        try:
            # print(self.regime, self.tmp_file_path, dst_name)
            if self.regime == 'move':
                move(self.tmp_file_path, dst_name)
            else:
                copyfile(self.tmp_file_path, dst_name)
        except OSError as err:
            self.error_message = str(err)
            self.is_error = True

    def file_name_get(self):
        return self.file_name

    def error_check(self):
        return self.is_error

    def error_get(self):
        return self.error_message

    def file_ext_get(self):
        return self.file_ext.strip('.')
