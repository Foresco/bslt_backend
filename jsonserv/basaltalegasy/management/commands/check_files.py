# Команда проверки целостности архива
# Результаты проверки сохраняются в лог-файл
import logging
from datetime import datetime as dt
import os.path
from django.conf import settings  # для обращения к настройкам
from django.core.management.base import BaseCommand
import psycopg2


class Command(BaseCommand):
    help = 'Check files in archives exist'

    def handle(self, *args, **options):
        date_time = dt.now().strftime("%Y%m%d-%H%M%S")
        log_file_name = date_time + '.log'
        log_target_dir = getattr(settings, 'LOG_DIR', 'jsonserv/logs')
        log_file_name = os.path.join(log_target_dir, log_file_name)
        logging.basicConfig(level=logging.INFO,
                            handlers=[logging.FileHandler(log_file_name, 'w', 'utf-8')],
                            format='%(message)s',
                            )

        conn = psycopg2.connect(host="192.168.0.209", database="postgres", user="test2", password="test2_pas_!")

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM vwDocsND")
        row = cursor.fetchone()
        while row:
            file_path = os.path.join('/mnt/uploaded', row['folder_name'], row['doc_code'])
            if not os.path.isfile(file_path):
                logging.info(file_path)
            row = cursor.fetchone()
        # print('Done')
