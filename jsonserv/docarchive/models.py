import os.path
from django.db import models
from django.db.models import Q, OuterRef, Subquery
from django.db.models.functions import Lower
from django.core.exceptions import ObjectDoesNotExist

import logging

from jsonserv.core.models import (List, StructuredList, Entity, EntityType, Link, CreateTrackingMixin,
                                  HistoryTrackingMixin, Place, RightMixin, UserProfile)
from jsonserv.pdm.models import ChangeType, Designer, Notice, Rendition, Role, Stage, PartState
from jsonserv.core.fileutils import copy_file_to_folder, compute_check_sum
from jsonserv.docarchive.file_prepare import prepare_file_for_store

logger = logging.getLogger('basalta')


class FileArchive(RightMixin, models.Model):
    """Информация об архивах документов"""
    archive_name = models.CharField(max_length=25, null=False, blank=False, unique=True,
                                    verbose_name="Наименование архива")
    core_directory = models.CharField(max_length=255, null=False, blank=False, unique=True,
                                      verbose_name="Корневой каталог архива")
    description = models.TextField(blank=True, null=True, verbose_name='Описание')

    def __str__(self):
        return f'{self.archive_name} в каталоге {self.core_directory}'

    @staticmethod
    def get_or_create_item(prop_dict):
        return FileArchive.objects.get_or_create(archive_name=prop_dict['archive_name'], defaults=prop_dict)

    @staticmethod
    def get_archive_path(pk):
        """Получение адреса архива по идентификатору"""
        return FileArchive.objects.get(pk=pk).core_directory

    class Meta:
        verbose_name = "Файловый архив"
        verbose_name_plural = "Файловые архивы"
        default_permissions = ()
        # permissions = [('change_filearchive', 'Файловый архив. Редактирование'),
        #                ('view_filearchive', 'Файловый архив. Просмотр')]


class EntityTypeFileArchive(models.Model):
    """Информация об архивах, используемых для каждого типа сущности"""
    entity_type = models.OneToOneField(EntityType, null=False, related_name='file_archive',
                                       on_delete=models.CASCADE, verbose_name='Тип сущности')
    archive = models.ForeignKey(FileArchive, null=False, verbose_name='Архив', on_delete=models.CASCADE)

    @staticmethod
    def get_archive_id(entity_id):
        """Получение идентификатора архива для сохранения связанных с сущностью файлов
        entity_id - идентификатор экземпляра сущности"""
        ent = Entity.objects.get(pk=entity_id)
        try:
            a = EntityTypeFileArchive.objects.get(entity_type=ent.type_key)
            if a:
                return a.archive.id
        except ObjectDoesNotExist:
            pass
        return 1  # Идентификатор архива по умолчанию

    def __str__(self):
        return f'{self.entity_type} хранятся в архиве {self.archive}'

    class Meta:
        verbose_name = "Файловый архив для сущности"
        verbose_name_plural = "Файловые архивы для сущностей"
        default_permissions = ()


class Folder(models.Model):
    """Информация о каталогах файловых архивов"""
    archive = models.ForeignKey(FileArchive, null=False, verbose_name='Архив', on_delete=models.CASCADE)
    folder_name = models.CharField(max_length=25, null=False, blank=False, verbose_name="Наименование каталога")
    folder_num = models.IntegerField(null=False, blank=False, default=1, verbose_name='Номер каталога')

    def __str__(self):
        return f'Каталог {self.folder_name} в архиве {self.archive}'

    @property
    def folder_path(self):
        return os.path.join(self.archive.core_directory, self.folder_name)

    @staticmethod
    def get_or_create_item(prop_dict):
        return Folder.objects.get_or_create(folder_name=prop_dict['folder_name'], archive=prop_dict['archive'],
                                            defaults=prop_dict)

    class Meta:
        verbose_name = "Каталог файлового архива"
        verbose_name_plural = "Каталоги файловых архивов"
        default_permissions = ()
        # permissions = [('change_folder', 'Каталог файлового архива. Редактирование'),
        #                ('view_folder', 'Каталог файлового архива. Просмотр')]


class ArchiveCell(HistoryTrackingMixin):
    """Информация о ячейках архива"""
    cell_name = models.CharField(max_length=25, null=False, blank=False, unique=True,
                                 verbose_name="Наименование ячейки")
    parent = models.ForeignKey(to='ArchiveCell', null=True, verbose_name='Родительская ячейка',
                               on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True, verbose_name='Описание назначения ячейки')

    def __str__(self):
        return f'Ячейка {self.cell_name} в ячейке {self.parent}'

    class Meta:
        verbose_name = "Ячейка архива"
        verbose_name_plural = "Ячейки архива"
        default_permissions = ()
        permissions = [('change_archivecell', 'Ячейка архива. Редактирование'),
                       ('view_archivecell', 'Ячейка архива. Просмотр')]


class DocumentType(RightMixin, StructuredList):
    """Типы документов"""

    class Meta:
        verbose_name = "Тип файлового документа"
        verbose_name_plural = "Типы файловых документов"
        default_permissions = ()
        permissions = [('change_documenttype', 'Тип файлового документа. Редактирование'),
                       ('view_documenttype', 'Тип файлового документа. Просмотр')]


class FileDocument(HistoryTrackingMixin):
    """Файловый документы. Заголовки файлов, хранящихся в файловых архивах"""
    doc_code = models.CharField(max_length=200, null=False, blank=False, verbose_name='Обозначение документа')
    doc_name = models.CharField(max_length=250, blank=True, null=True, verbose_name="Наименование документа")
    doc_type = models.ForeignKey(DocumentType, null=True, blank=True, on_delete=models.SET_NULL,
                                 verbose_name="Вид файлового документа")
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    archive = models.ForeignKey(FileArchive, null=False, verbose_name='Архив', on_delete=models.CASCADE)

    def __str__(self):
        return self.doc_code

    @staticmethod
    def get_or_create_item(prop_dict):
        return FileDocument.objects.get_or_create(doc_code=prop_dict['doc_code'], archive=prop_dict['archive'],
                                                  defaults=prop_dict)

    def get_next_version_num(self):
        """Получение номера версии документа"""
        logger.info(f'Получение номера версии документа.')
        vc = self.document_versions.aggregate(
            version_num_max=models.Max('version_num'),
            cnt=models.Count('version_num')
        )
        if vc['cnt']:
            version_num_max = vc['version_num_max']
            logger.info(f'Получение номера версии документа. Текущая версия номер {version_num_max}')
            return version_num_max + 1  # Следующий номер версии
        else:
            logger.info(f'Это первая версия документа.')
            return 1  # Первый номер по умолчанию

    class Meta:
        verbose_name = "Файловый документ"
        verbose_name_plural = "Файловые документы"
        default_permissions = ()
        permissions = [('change_filedocument', 'Файловый документ. Редактирование'),
                       ('view_filedocument', 'Файловый документ. Просмотр')]


class DocumentVersion(HistoryTrackingMixin):
    """Версии файловых документов"""
    document = models.ForeignKey(FileDocument, related_name='document_versions', on_delete=models.CASCADE,
                                 blank=False, null=False, verbose_name='Ссылка на документ')
    archive_cell = models.ForeignKey(ArchiveCell, null=True, on_delete=models.SET_NULL,
                                     verbose_name="Место хранения (ячейка)")
    description = models.TextField(blank=True, null=True, verbose_name='Описание версии')
    version_num = models.PositiveIntegerField(default=1, verbose_name="Номер версии")
    notice = models.ForeignKey(Notice, related_name='notice_document_versions', on_delete=models.SET_NULL,
                               blank=True, null=True, verbose_name='Ссылка на извещение')
    change_num = models.PositiveIntegerField(blank=True, null=True, verbose_name='Номер изменения')
    change_type = models.ForeignKey(ChangeType, on_delete=models.SET_NULL, blank=True, null=True,
                                    verbose_name='Тип изменения')
    is_done = models.BooleanField(blank=False, null=False, default=False, verbose_name='Признак проведения изменений')
    version_stage = models.ForeignKey(Stage, blank=True, null=True, related_name='staged_versions',
                                       on_delete=models.SET_NULL, verbose_name="Стадия")

    def __str__(self):
        return f'Версия {self.version_num} документа {self.document}'

    @staticmethod
    def get_or_create_item(prop_dict):
        if 'version_num' not in prop_dict:
            # Вычисление номера следующей версии
            prop_dict['version_num'] = prop_dict['document'].get_next_version_num()

        return DocumentVersion.objects.get_or_create(document=prop_dict['document'],
                                                     version_num=prop_dict['version_num'],
                                                     defaults=prop_dict)

    def delete(self, *args, **kwargs):
        # Удаление всей связанной с версией информации
        # Роли разработчиков
        roles = self.document_roles.filter(dlt_sess=0)
        roles.update(dlt_sess=self.dlt_sess)
        # Файлы
        files = self.digital_files.filter(dlt_sess=0)
        files.update(dlt_sess=self.dlt_sess)
        # Связи с сущностями
        e_links = self.version_objects.filter(dlt_sess=0)
        e_links.update(dlt_sess=self.dlt_sess)

        super().delete()

    def up_order_version(self, order, edt_sess):
        """Подключение версии к объектам из заказа"""
        # Получение всех версий данного документа
        edv = EntityDocumentVersion.objects.filter(
            document_version__document=self.document,  # Относится к тому же документу
            entity__partobject__prod_order=order,  # Связана с объектом из указанного заказа
            document_version__version_num__lt=self.version_num  # Версия меньше текущей
        )
        if edv:  # Если что-то нашлось
            for v in edv:
                v.document_version = self  # Переключаем на текущую версию
                v.edt_sess = edt_sess
                v.save()

    class Meta:
        verbose_name = "Версия файлового документа"
        verbose_name_plural = "Версии файловых документов"
        default_permissions = ()
        permissions = [('change_documentversion', 'Версия файлового документа. Редактирование'),
                       ('view_documentversion', 'Версия файлового документа. Просмотр')]


class DigitalFile(HistoryTrackingMixin):
    """Файлы документов"""
    document_version = models.ForeignKey(DocumentVersion, null=True, verbose_name='Версия документа',
                                         related_name='digital_files', on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255, null=False, blank=False, verbose_name="Наименование файла")
    folder = models.ForeignKey(Folder, null=False, verbose_name='Каталог', on_delete=models.CASCADE)
    data_format = models.CharField(max_length=200, null=True, blank=True, verbose_name='Описание формата данных файла')
    character_code = models.CharField(max_length=50, null=True, blank=True, verbose_name='Описание кодировки файла')
    file_number = models.PositiveIntegerField(default=1, null=True, verbose_name='Номер файла')
    check_sum = models.CharField(max_length=32, null=True, blank=True, verbose_name='Контрольная сумма MD5')

    all_files = models.Manager()  # Отключаем менеджер, полученный от родителя. Здесь все файлы, включая удаленные

    def __str__(self):
        return f'Файл {self.file_name} версии {self.document_version} номер {self.file_number}'

    @property
    def file_path(self):
        """Получение пути к файлу в хранилище"""
        return os.path.join(self.folder.folder_path, self.file_name)

    def update_check_sum(self, edt_sess):
        """Обновление контрольной суммы если файл изменился"""
        self.check_sum = compute_check_sum(self.file_path)
        self.edt_sess = edt_sess
        self.save()

    @property
    def url(self):
        return 'file/%i/' % self.id

    @staticmethod
    def get_path_for_file(file_name, archive_id=1):
        """Получение полного пути для помещения указанного файла в архив"""
        # Определяем максимальный текущий каталог (с учетом удаленных файлов)
        df = DigitalFile.all_files.filter(file_name=file_name, folder__archive_id=archive_id).order_by(
            '-folder__folder_num'
        ).first()
        if df:
            folder_num = df.folder.folder_num + 1  # Следующая по порядку папка
        else:
            folder_num = 1
        folder_name = "{:08d}".format(folder_num)
        folder_obj, created = Folder.get_or_create_item(dict(folder_name=folder_name, folder_num=folder_num,
                                                             archive=FileArchive.objects.get(pk=archive_id)))
        target_folder = os.path.join(FileArchive.get_archive_path(archive_id), folder_name)

        # Создаем каталог при необходимости
        if created:
            os.makedirs(target_folder, exist_ok=True)
        # Возвращаем полный путь
        return folder_obj, os.path.join(target_folder, file_name)

    @staticmethod
    def get_or_create_item(prop_dict):
        logger.info('Создание файла на основе словаря')
        logger.info(prop_dict)
        src = prop_dict.pop('src', '')  # Исходное расположение
        watermark_date = prop_dict.pop('watermark_date', '')  # Дата для метки
        if watermark_date:
            # Вставляем метку
            result, src = prepare_file_for_store(src, watermark_date)
        # Расчет контрольной суммы
        if 'check_sum' not in prop_dict:
            prop_dict['check_sum'] = compute_check_sum(src)
        # Проверка наличия файла с такой же контрольной суммой
        if not prop_dict['check_sum']:  # Файл не найден
            None, False
        # Получение места для хранения файла
        archive_id = prop_dict.pop('archive', 1)  # Ссылка на архив
        # Проверка существования файла Уникального по имени, контрольной сумме и архиву
        logger.info('Проверка существования файла Уникального по имени, контрольной сумме и архиву')
        # Проверять и удаленные файлы (dlt_sess>0)
        exist = DigitalFile.all_files.filter(file_name=prop_dict['file_name'], check_sum=prop_dict['check_sum'],
                                             folder__archive_id=archive_id)
        if exist:  # Если найден существующий
            logger.info('Найден существующий')
            return exist[0], False
        # Копирование исходного файла
        folder_obj, file_path = DigitalFile.get_path_for_file(prop_dict['file_name'], archive_id)
        if copy_file_to_folder(src, file_path):  # Копирование файла из из первоисточника
            # Создание записи в БД
            logger.info('Создание записи в БД')
            logger.info(prop_dict)
            return DigitalFile.objects.get_or_create(file_name=prop_dict['file_name'], folder=folder_obj,
                                                     defaults=prop_dict)
        else:
            logger.info(f'Копирование {src} {file_path} неудачное')
            return None, None

    class Meta:
        verbose_name = "Электронный файл"
        verbose_name_plural = "Электронные файлы"
        default_permissions = ()
        permissions = [('change_digitalfile', 'Электронный файл. Редактирование'),
                       ('view_digitalfile', 'Электронный файл. Просмотр'),
                       ('no_watermark', 'Электронный файл. Скачать без марки')]


class VersionDesignRole(HistoryTrackingMixin):
    """Роли, выполненные пользователями"""
    document_version = models.ForeignKey(DocumentVersion, related_name='document_roles', on_delete=models.CASCADE,
                                         null=False, verbose_name='Ссылка на версию документа')
    role = models.ForeignKey(Role, related_name='role_documents', on_delete=models.CASCADE,
                             null=False, verbose_name='Выполненная роль')
    designer = models.ForeignKey(Designer, null=False, on_delete=models.CASCADE, verbose_name="Разработчик")
    role_date = models.DateField(null=True, blank=True, verbose_name="Дата выполнения роли")
    comment = models.TextField(null=True, blank=True, verbose_name="Примечание")

    def __str__(self):
        return f'{self.designer} выполнил {self.role} для версии {self.document_version}'

    @staticmethod
    def get_or_create_item(prop_dict):
        return VersionDesignRole.objects.get_or_create(document_version=prop_dict['document_version'],
                                                       role=prop_dict['role'], defaults=prop_dict)

    class Meta:
        verbose_name = "Выполненная роль в разработке"
        verbose_name_plural = "Выполненные роли в разработке"
        default_permissions = ()
        permissions = [('change_versiondesignrole', 'Выполненная роль в разработке. Редактирование'),
                       ('view_versiondesignrole', 'Выполненная роль в разработке. Просмотр')]


class EntityDocumentVersion(HistoryTrackingMixin):
    """Связь объектов и документов"""
    entity = models.ForeignKey(Entity, related_name='object_documents', on_delete=models.CASCADE,
                               blank=False, null=False, verbose_name='Ссылка на владельца документа')
    document_version = models.ForeignKey(DocumentVersion, on_delete=models.CASCADE, related_name='version_objects',
                                         blank=False, null=False, verbose_name='Ссылка на документ')
    document_role = models.CharField(max_length=50, null=True, blank=True,
                                     verbose_name="Роль документа по отношению к объекту")
    old_version = models.BooleanField(null=False, default=False, verbose_name="Признак старой версии")

    def __str__(self):
        if self.document_role:
            return f'{self.document_version} связан с {self.entity} как {self.document_role}'
        return f'{self.document_version} связан с {self.entity}'

    @staticmethod
    def get_or_create_item(prop_dict):
        return EntityDocumentVersion.objects.get_or_create(entity=prop_dict['entity'],
                                                           document_version=prop_dict['document_version'],
                                                           defaults=prop_dict)

    @staticmethod
    def mark_old_versions(entity_id, document_id, actual_version_id):
        """Пометка устаревших версий"""
        # Список всех объектов
        rends = Rendition.get_renditions(entity_id)
        if rends:
            # Добавляем все исполнения объекта
            obj_lis = list(map(lambda x: x['rendition'], rends.values('rendition')))
        else:
            obj_lis = list()
        obj_lis.append(entity_id)  # Сам объект
        # Пометка старых версий у объекта и его исполнений
        EntityDocumentVersion.objects.filter(entity_id__in=obj_lis, document_version__document_id=document_id).exclude(
            document_version_id=actual_version_id).update(old_version=True)

    def save(self, *args, **kwargs):
        """Добавление ссылки всем исполнениям базового исполнения"""
        link_dict = dict(document_version=self.document_version, document_role=self.document_role,
                         old_version=self.old_version, crtd_sess=self.crtd_sess)
        rends = Rendition.get_renditions(self.entity.pk)  # Получаем все исполнения объекта
        if rends:
            for row in rends:  # Присоединение ко всем исполнениям
                link_dict['entity'] = row.rendition
                lnk, result = EntityDocumentVersion.get_or_create_item(link_dict)  # Копируем связь
        super(EntityDocumentVersion, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Удаление связи у всех исполнений базового исполнения"""
        rends = Rendition.get_renditions(self.entity.pk)  # Получаем все исполнения объекта
        if rends:
            for row in rends:  # Удаление у всех исполнений
                EntityDocumentVersion.objects.filter(entity=row.rendition,
                                                     document_version=self.document_version).update(
                    dlt_sess=self.dlt_sess)
        super(EntityDocumentVersion, self).delete(*args, **kwargs)

    @staticmethod
    def get_documents_queryset(all_versions=False):
        """Возвращает QuerySet с документами для последующей выборки нужных"""
        next_version_id = DocumentVersion.objects.filter(
            document=OuterRef('document_version__document__pk'),
            version_num__gt=OuterRef('document_version__version_num')
        ).order_by('version_num')
        a = EntityDocumentVersion.objects if all_versions else EntityDocumentVersion.objects.filter(
            old_version=False)  # По умолчанию только текущие версии
        return a.filter(
            Q(document_version__digital_files__dlt_sess=0),
            Q(document_version__document_roles__role_id=1) | Q(document_version__document_roles__role_id__isnull=True)
        ).annotate(
            next_version_id=Subquery(
                next_version_id.values('pk')[:1]
            )
        ).values(
            'pk',
            'old_version',
            'document_version__digital_files__pk',
            'document_version__document__pk',
            'document_version__pk',
            'document_version__version_num',
            'document_version__notice',
            'document_version__change_type',
            'document_version__change_type__list_value',
            'document_version__change_num',
            'document_version__notice__code',
            'document_version__version_stage__code',
            'document_version__digital_files__file_name',
            'document_version__document__description',
            'document_version__document__doc_type',
            'document_version__document__doc_code',
            'document_version__document__doc_name',
            'document_version__document__doc_type__list_value',
            'document_version__document__doc_type__value_right',
            'document_version__document_roles__pk',
            'document_version__document_roles__designer_id',
            'document_version__document_roles__designer__designer',
            'document_version__digital_files__crtd_sess__session_datetime',
            'document_version__digital_files__crtd_sess__user__username',
            'next_version_id'
        ).order_by(
            Lower('document_version__digital_files__file_name'),
            'document_version__version_num',
        )

    @staticmethod
    def update_documents_in_order(target_id, source_id, user_session_id, mess_txt):
        """Изменение набора файлов объекта-копии"""
        edt_count = 0  # Счетчик выполненных изменений
        # Получаем файлы копии
        obj_files = dict((d['document_version_id'], d) for d in
                         EntityDocumentVersion.objects.filter(entity=target_id).values('document_version_id',
                                                                                       'old_version',
                                                                                       'pk'))
        # Получаем файлы исходного объекта
        origin_files = dict((d['document_version_id'], d) for d in
                            EntityDocumentVersion.objects.filter(entity=source_id).values('document_version_id',
                                                                                          'old_version', 'pk'))
        # Находим недостающие записи
        difference = list(set(origin_files.keys()) - set(obj_files.keys()))
        for r in difference:  # Добавляем то, чего нет в копии
            # Создаем связь на основе существующей
            src = EntityDocumentVersion.objects.get(pk=origin_files[r]['pk'])
            # Создаем связь
            src.entity = Entity.objects.get(pk=target_id)  # Относится к объекту-получателю
            src.pk = None
            src.crtd_sess_id = user_session_id
            src.save()
            edt_count += 1

            if edt_count:
                mess_txt.append(f'Добавлено файлов {edt_count}')
                edt_count = 0

        # Удаляем то, чего нет в исходном
        difference = list(set(obj_files.keys()) - set(origin_files.keys()))
        for r in difference:
            # Удаляем строку
            d = EntityDocumentVersion.objects.get(pk=obj_files[r]['pk'])
            d.dlt_sess = user_session_id
            d.save()
            # Удаляем запись из массива
            del obj_files[r]
            edt_count += 1

        if edt_count:
            mess_txt.append(f'Удалено файлов {edt_count}')

        # Корректируем признак "старая версия"
        for r in obj_files.keys():
            if obj_files[r]['old_version'] != origin_files[r]['old_version']:
                d = EntityDocumentVersion.objects.get(pk=obj_files[r]['pk'])
                d.old_version = origin_files[r]['old_version']
                d.edt_sess = user_session_id
                d.save()

    class Meta:
        verbose_name = "Версия документа у объекта"
        verbose_name_plural = "Версии документов у объектов"
        default_permissions = ()
        permissions = [('change_entitydocumentversion', 'Версия документа у объекта. Редактирование'),
                       ('view_entitydocumentversion', 'Версия документа у объекта. Просмотр')]


class DocumentVersionDateType(List):
    """Виды дат версий документов"""

    class Meta:
        verbose_name = "Вид даты версии документа"
        verbose_name_plural = "Виды дат версий документов"
        default_permissions = ()
        permissions = [('change_documentversiondatetype', 'Вид даты версии документа. Редактирование'),
                       ('view_documentversiondatetype', 'Вид даты версии документа. Просмотр')]


class DocumentVersionDate(HistoryTrackingMixin):
    """Даты документов"""
    document_version = models.ForeignKey(DocumentVersion, null=False, on_delete=models.CASCADE,
                                         verbose_name='Версия документа')
    date_type = models.ForeignKey(DocumentVersionDateType, null=False, on_delete=models.CASCADE,
                                  verbose_name='Вид даты')
    date = models.DateField(null=False, verbose_name='Дата')

    def __str__(self):
        return f'{self.document_version} {self.date_type} {self.date}'

    @staticmethod
    def get_or_create_item(prop_dict):
        return DocumentVersionDate.objects.get_or_create(document_version=prop_dict['document_version'],
                                                         date_type=prop_dict['date_type'],
                                                         defaults=prop_dict)

    class Meta:
        verbose_name = "Дата версии документа"
        verbose_name_plural = "Даты версий документов"
        default_permissions = ()
        permissions = [('change_documentversiondate', 'Дата версии документа. Редактирование'),
                       ('view_documentversiondate', 'Дата версии документа. Просмотр')]


class CodePrefix(HistoryTrackingMixin):
    """Префиксы обозначений"""
    prefix_code = models.CharField(max_length=15, null=False, blank=False, unique=True,
                                   verbose_name='Префикс обозначения')
    project_code = models.CharField(max_length=15, null=False, blank=False, verbose_name='Обозначение проекта')
    description = models.TextField(null=True, blank=True, verbose_name='Описание префикса обозначения')

    def get_caption(self):
        """Формирование понятной надписи для разных целей"""
        return f'{self.prefix_code}  ({self.project_code}) | Префикс'

    @staticmethod
    def get_or_create_item(prop_dict):
        return CodePrefix.objects.get_or_create(prefix_code=prop_dict['prefix_code'], defaults=prop_dict)

    @staticmethod
    def suggest(user, str_filter, int_limit, init_filter):
        """Формирование набора значений для списка подстановки"""
        if str_filter:  # Фильтрацию применяем, если указан фильтр
            items = CodePrefix.objects.filter(prefix_code__icontains=str_filter)
        else:
            items = CodePrefix.objects.all()
        items = items.order_by('prefix_code')[0:int(int_limit)]

        return list(
            map(lambda x: dict(pk=x['pk'], value=x['prefix_code']), items.values('pk', 'prefix_code')))

    class Meta:
        verbose_name = "Префикс, применяемый в обозначениях"
        verbose_name_plural = "Префиксы, применяемые в обозначениях"
        ordering = ['prefix_code', ]
        default_permissions = ()
        permissions = [('change_codeprefix', 'Префикс, применяемый в обозначениях. Редактирование'),
                       ('view_codeprefix', 'Префикс, применяемый в обозначениях. Просмотр')]


class ArcDocument(Entity):
    """Архивные документы. Учетные единицы документации в архиве"""
    doc_type = models.ForeignKey(DocumentType, null=True, blank=True, on_delete=models.SET_NULL,
                                 verbose_name="Вид документа")
    document_name = models.CharField(max_length=250, blank=True, null=True, verbose_name="Наименование документа")
    document_num = models.CharField(max_length=50, blank=True, null=True, verbose_name="Инвентарный номер документа")
    reg_date = models.DateField(blank=True, null=True, verbose_name="Дата поступления документа в архив")
    list_count = models.SmallIntegerField(blank=True, null=True, verbose_name="Количество листов в документе")
    document_state = models.ForeignKey(PartState, blank=True, null=True, on_delete=models.SET_NULL,
                                       verbose_name="Состояние")
    # document_stage = models.ForeignKey(Stage, blank=True, null=True, related_name='staged_documents',
    #                                    on_delete=models.SET_NULL, verbose_name="Стадия")  # TODO: Удалить? Используется parent
    document_place = models.ForeignKey(Place, blank=True, null=True, on_delete=models.SET_NULL,
                                       verbose_name="Место хранения документа")
    prefix = models.ForeignKey(CodePrefix, null=True, blank=True, on_delete=models.SET_NULL,
                               verbose_name='Префикс инвентарного номера')

    @property
    def formats(self):
        """Формирование списка форматов объекта"""
        frm = self.object_formats.values_list('list_quantity', 'format__list_value')
        return ', '.join("%sx%s" % x for x in frm)

    class Meta:
        verbose_name = "Документ архива"
        verbose_name_plural = "Документы архивов"
        default_permissions = ()
        permissions = [('change_arcdocument', 'Документ архива. Редактирование'),
                       ('view_arcdocument', 'Документ архива. Просмотр')]


class ArcDocumentObject(Link):
    """Объекты архивных документов"""

    def __str__(self):
        return f"{self.parent} относится к {self.child}"

    class Meta:
        verbose_name = "Объект архивного документа"
        verbose_name_plural = "Объекты архивных документов"
        default_permissions = ()
        permissions = [('change_arcdocumentobject', 'Объект архивного документа. Редактирование'),
                       ('view_arcdocumentobject', 'Объект архивного документа. Просмотр')]


class FileUpload(CreateTrackingMixin):
    """Загрузки документов"""
    file_name = models.CharField(max_length=200, null=False, blank=False,
                                 verbose_name='Наименование загруженного файла')
    upload_date = models.DateField(null=False, blank=False, verbose_name='Дата загрузки'
                                   , auto_now=True
                                   )

    def get_caption(self):
        """Формирование понятной надписи для разных целей"""
        return f'{self.file_name} от {self.upload_date.strftime("%d.%m.%Y")} | Загрузка архивных документов'

    @staticmethod
    def get_or_create_item(prop_dict):
        return FileUpload.objects.get_or_create(file_name=prop_dict['file_name'], defaults=prop_dict)

    class Meta:
        verbose_name = "Загрузка архивных документов"
        verbose_name_plural = "Загрузки архивных документов"
        default_permissions = ()
        permissions = [('change_fileupload', 'Загрузка архивных документов. Редактирование'),
                       ('view_fileupload', 'Загрузка архивных документов. Просмотр')]


class UploadArcdoc(CreateTrackingMixin):
    """Загруженные файловые документы"""
    file_upload = models.ForeignKey(FileUpload, null=False, blank=False, on_delete=models.CASCADE,
                                    verbose_name='Загрузка файлов')
    arc_doc = models.ForeignKey(ArcDocument, null=False, blank=False, on_delete=models.CASCADE,
                                verbose_name='Загруженный архивный документ')

    @staticmethod
    def get_or_create_item(prop_dict):
        return UploadArcdoc.objects.get_or_create(file_upload=prop_dict['file_upload'], arc_doc=prop_dict['arc_doc'],
                                                  defaults=prop_dict)

    class Meta:
        verbose_name = "Загруженный документ"
        verbose_name_plural = "Загруженные документы"
        default_permissions = ()
        permissions = [('change_uploadarcdoc', 'Загруженный документ. Редактирование'),
                       ('view_uploadarcdoc', 'Загруженный документ. Просмотр')]


class Delivery(HistoryTrackingMixin):
    """Выдачи архивных документов"""
    delivery_num = models.IntegerField(null=False, blank=False, verbose_name='Номер выдачи')
    receiver = models.ForeignKey(Place, null=False, blank=False, on_delete=models.CASCADE,
                                 verbose_name='Подразделение-получатель')
    delivery_date = models.DateField(null=False, blank=False, verbose_name='Дата выдачи')
    comment = models.TextField(blank=True, null=True, verbose_name='Примечание')

    @staticmethod
    def get_delivery_num():
        # Генерация номера выдачи
        dc = Delivery.objects.aggregate(
            delivery_num_max=models.Max('delivery_num'),
            cnt=models.Count('delivery_num'))
        if dc['cnt']:
            # Следующий номер
            return dc['delivery_num_max'] + 1
        return 1

    @staticmethod
    def get_or_create_item(prop_dict):
        return Delivery.objects.get_or_create(delivery_num=prop_dict['delivery_num'], defaults=prop_dict)

    def save(self, *args, **kwargs):
        # Генерация следующего номера выдачи
        if not self.delivery_num:
            self.delivery_num = Delivery.get_delivery_num()  # Следующий номер по порядку
        super().save(*args, **kwargs)

    def get_caption(self):
        """Формирование понятной надписи для разных целей"""
        return f'{self.delivery_num} от {self.delivery_date.strftime("%d.%m.%Y")} | Выдача документов'

    class Meta:
        verbose_name = "Выдача документов"
        verbose_name_plural = "Выдачи документов"
        ordering = ['-delivery_date', '-delivery_num']
        default_permissions = ()
        permissions = [('change_delivery', 'Выдача документов. Редактирование'),
                       ('view_delivery', 'Выдача документов. Просмотр')]


class DeliveryArcdoc(HistoryTrackingMixin):
    """Состав выдач архивных документов"""
    delivery = models.ForeignKey(Delivery, null=False, blank=False, on_delete=models.CASCADE,
                                 verbose_name='Выдача')
    arc_doc = models.ForeignKey(ArcDocument, null=False, blank=False, on_delete=models.CASCADE,
                                verbose_name='Архивный документ')
    exemplar_num = models.CharField(max_length=20, blank=True, null=True, verbose_name="Номер выданного экземпляра")
    comment = models.TextField(blank=True, null=True, verbose_name="Примечание")

    @staticmethod
    def get_or_create_item(prop_dict):
        return DeliveryArcdoc.objects.get_or_create(delivery=prop_dict['delivery'], arc_doc=prop_dict['arc_doc'],
                                                    defaults=prop_dict)

    class Meta:
        verbose_name = "Документ архива в выдаче документов"
        verbose_name_plural = "Документ архива в выдачах документов"
        default_permissions = ()
        permissions = [('change_deliveryarcdoc', 'Документ архива в выдаче документов. Редактирование'),
                       ('view_deliveryarcdoc', 'Документ архива в выдаче документов. Просмотр')]


class Incident(Entity):
    """Инциденты"""
    incident_date = models.DateField(blank=True, null=True, verbose_name="Дата инцидента")
    incident_num = models.IntegerField(null=False, blank=False, verbose_name='Номер инцидента')
    # inc_project = models.ForeignKey(PartObject, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="Проект")
    plant_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Заводской номер изделия")

    @staticmethod
    def get_incident_num():
        dc = Incident.objects.aggregate(
            incident_num_max=models.Max('incident_num'),
            cnt=models.Count('incident_num'))
        if dc['cnt']:
            # Следующий номер версии
            return dc['incident_num_max'] + 1
        return 1

    def save(self, *args, **kwargs):
        if not self.code:
            self.incident_num = Incident.get_incident_num()  # Следующий номер по порядку
            self.code = str(self.incident_num)
        super(Incident, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Инцидент"
        verbose_name_plural = "Инциденты"
        default_permissions = ()
        permissions = [('change_incident', 'Инцидент. Редактирование'),
                       ('view_incident', 'Инцидент. Просмотр')]


class DownloadCounter(models.Model):
    """Счетчик скачиваний"""
    user_profile = models.ForeignKey(ArcDocument, null=False, blank=False, on_delete=models.CASCADE,
                                verbose_name='Архивный документ')
    last_date = models.DateField(null=False, verbose_name="Дата последнего скачивания")
    download_count_day = models.IntegerField(null=False, default=0, verbose_name='Счетчик скачиваний в день')
    download_count_month = models.IntegerField(null=False, default=0, verbose_name='Счетчик скачиваний в месяц')
    download_count_year = models.IntegerField(null=False, default=0, verbose_name='Счетчик скачиваний в год')

    def __str__(self):
        return f'{self.user_profile} на {self.last_date} {self.download_count_day}/{self.download_count_month}/{self.download_count_year}'

    class Meta:
        verbose_name = "Счетчик скачивания пользователем"
        verbose_name_plural = "Счетчики скачивания пользователем"
        default_permissions = ()

# Функции обработки сигналов
def copy_file_links(sender, **kwargs):
    """Функция копирования связей с файлами от одного объекта другому"""
    print("Request finished!")
