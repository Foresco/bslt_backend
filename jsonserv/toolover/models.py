from django.db import models
from django.core.exceptions import ValidationError  # Ошибка проверки полей модели при записи

# Базовые модели
from jsonserv.core.models import (List, CodedList, Entity, MeasureSystem, Property, Language, Place,
                                  HistoryTrackingMixin, NotDeletedObjects, GraphicFile, EntityType)


class TranslateProperty(models.Model):
    """Свойства для перевода на разные языки"""
    value_pattern = models.CharField(max_length=50, null=False, blank=False, unique=True,
                                     verbose_name="Схема принадлежности значения")

    class Meta:
        verbose_name = 'Свойство перевода'
        verbose_name_plural = 'Свойства переводов'
        default_permissions = ()
        permissions = [('change_translateproperty', 'Свойство перевода. Редактирование'),
                       ('view_translateproperty', 'Свойство перевода. Просмотр')]


class LanguageValue(HistoryTrackingMixin, models.Model):
    """Значения свойств на разных языках"""
    property = models.ForeignKey(to='TranslateProperty', on_delete=models.CASCADE,
                                 verbose_name='Идентификатор свойства')
    language = models.ForeignKey(Language, related_name='lng', on_delete=models.CASCADE, verbose_name='Идентификатор языка')
    property_value = models.CharField(max_length=255, blank=True, verbose_name="Значение на указанном языке")

    class Meta:
        verbose_name = 'Значение свойства на языках'
        verbose_name_plural = 'Значения свойств на языках'
        default_permissions = ()
        permissions = [('change_languagevalue', 'Значение свойства на языках. Редактирование'),
                       ('view_languagevalue', 'Значение свойства на языках. Просмотр')]


class GtcPackage(HistoryTrackingMixin):
    """Загруженные GTC-пакеты"""
    gtc_package_id = models.CharField(max_length=36, null=False, blank=False,
                                      verbose_name='Уникальный идентификатор пакета')
    supported_gtc_generic_versions = models.CharField(max_length=50, verbose_name='Supported GTC generic versions')
    vendor_hierarchy_version = models.CharField(max_length=10, null=False, verbose_name='Vendor hierarchy version')
    vendor_name = models.CharField(max_length=100, null=False, verbose_name='Vendor name')
    vendor_acronym = models.CharField(max_length=100, verbose_name='Vendor acronym')
    gtc_package_creation_date = models.DateTimeField(verbose_name='GTC package creation_date')
    logo = models.ForeignKey(GraphicFile, on_delete=models.SET_DEFAULT, default=None, null=True,
                             verbose_name='Файл логотипа')
    download_security = models.CharField(max_length=100, verbose_name='Download security')
    vendor_system_version = models.CharField(max_length=10, verbose_name='Vendor System version')
    short_description = models.CharField(max_length=255, null=True, verbose_name='Short description')

    class Meta:
        verbose_name = 'GTC-пакет'
        verbose_name_plural = 'GTC-пакеты'
        default_permissions = ()
        permissions = [('change_gtcpackage', 'GTC-пакет. Редактирование'),
                       ('view_gtcpackage', 'GTC-пакет. Просмотр')]

    def __str__(self):
        return "Пакет от {}, {} ({})".format(self.vendor_name, self.gtc_package_creation_date, self.gtc_package_id)

    @classmethod
    def get_or_create_item(cls, prop_dict):
        return GtcPackage.objects.get_or_create(gtc_package_id=prop_dict['gtc_package_id'], defaults=prop_dict)


class ToolClass(HistoryTrackingMixin, models.Model):
    """Классы инструмента"""
    class_id = models.CharField(max_length=50, null=False, unique=True, verbose_name='Идентификатор класса')
    parent = models.ForeignKey(to='ToolClass', on_delete=models.SET_DEFAULT, default=None, related_name='sub_classes',
                               null=True, verbose_name='Родительский класс')
    class_name = models.CharField(max_length=100, null=False, blank=False, verbose_name="Наименование класса")
    preferred_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Предпочтительное имя класса")
    russian_name = models.CharField(max_length=200, null=True, blank=True, verbose_name="Русскоязычное имя класса")
    icon = models.ForeignKey(GraphicFile, on_delete=models.SET_DEFAULT, default=None, null=True,
                             related_name='icon_for_classes', verbose_name='Файл иконки')
    drawing = models.ForeignKey(GraphicFile, on_delete=models.SET_DEFAULT, default=None, null=True,
                                related_name='drawing_for_classes', verbose_name='Файл чертежа')
    mapping_rule = models.CharField(max_length=255, null=True, blank=True, verbose_name="Правило маппинга")
    modified_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата изменения")

    # Менеджер по умолчанию
    objects = NotDeletedObjects()

    class Meta:
        ordering = ['class_id', 'preferred_name', 'class_name']
        verbose_name = "Класс инструмента"
        verbose_name_plural = "Классы инструмента"
        default_permissions = ()
        permissions = [('change_toolclass', 'Класс инструмента. Редактирование'),
                       ('view_toolclass', 'Класс инструмента. Просмотр')]

    def __str__(self):
        return "{}, {} ({})".format(self.class_name, self.preferred_name, self.class_id)

    @classmethod
    def get_or_create_item(cls, prop_dict):
        return ToolClass.objects.get_or_create(class_id=prop_dict['class_id'], defaults=prop_dict)

    def save(self, *args, **kwargs):
        cnt = ToolClass.objects.filter(class_id=self.class_id).exclude(pk=self.pk).count()
        if cnt:
            raise ValidationError("head_key is not unique")
        super(ToolClass, self).save(*args, **kwargs)

    def delete(self, dlt_sess):
        # при удалении запись в поле dlt_sess идентификатора сессии
        super(ToolClass, self).save(dlt_sess=dlt_sess)

    def has_children(self):
        """Определение наличия потомков по полю parent"""
        return 1 if self.sub_classes.count() else 0


class ToolPropsFile(models.Model):
    """Файл со свойствами экземпляра инструмента (*.p21)"""
    file_name = models.CharField(max_length=150, null=False, blank=False, verbose_name='Имя файла')
    package = models.ForeignKey(to='GtcPackage', on_delete=models.CASCADE, default=None, related_name='files',
                                null=True, verbose_name='GTC-пакет')
    description = models.CharField(max_length=255, null=True, blank=True, verbose_name='Описание файла')
    implementation_level = models.CharField(max_length=10, null=False, blank=False,
                                            verbose_name='Обозначение требований')
    time_stamp = models.DateTimeField(verbose_name='Дата создания')
    author = models.TextField(null=True, blank=True, verbose_name='Имя и почтовый адрес ответственного')
    organization = models.CharField(max_length=255, null=True, blank=True, verbose_name='Организация автора')
    preprocessor_version = models.CharField(max_length=100, null=False, blank=False,
                                            verbose_name='Использованная система и версия')
    originating_system = models.CharField(max_length=100, null=True, blank=True, verbose_name='Выдавшая система')
    authorization = models.CharField(max_length=100, null=True, blank=True, verbose_name='Имя и адрес уполномоченного')
    file_schema = models.CharField(max_length=50, null=False, blank=False, verbose_name='Имя EXPRESS-схемы')

    class Meta:
        verbose_name = "Файлы со свойствами экземпляров инструмента (*.p21)"
        verbose_name_plural = "Файл со свойствами экземпляров инструмента (*.p21)"
        default_permissions = ()
        permissions = [('change_toolpropsfile', 'Файл со свойствами инструмента. Редактирование'),
                       ('view_toolpropsfile', 'Файл со свойствами инструмента. Просмотр')]


class ToolObject(Entity):
    """Справочник инструмента"""
    state = models.ForeignKey(to='ToolState', on_delete=models.SET_NULL, null=True, verbose_name='Состояние')
    source = models.ForeignKey(to='ToolSource', on_delete=models.SET_NULL, null=True,
                               verbose_name='Источник поступления')
    preference = models.ForeignKey(to='ToolPreference', on_delete=models.SET_NULL, null=True,
                                   verbose_name='Предпочтительность')

    @staticmethod
    def get_or_create_item(prop_dict):
        prop_dict['type_key'] = EntityType.objects.get(pk='toolobject')  # Значение всегда такое
        return ToolProduct.objects.get_or_create(code=prop_dict['code'], defaults=prop_dict)

    class Meta:
        verbose_name = "Инструмент"
        verbose_name_plural = "Инструменты"
        default_permissions = ()
        permissions = [('change_toolobject', 'Инструмент. Редактирование'),
                       ('view_toolobject', 'Инструмент. Просмотр')]


class ExternalLibrary(models.Model):
    """Ссылки на внешние библиотеки"""
    external_id = models.CharField(max_length=100, unique=True, null=False, verbose_name='Идентификатор библиотеки')
    library_type = models.CharField(max_length=10, null=False, verbose_name='Тип библиотеки')
    description = models.CharField(max_length=255, null=True, verbose_name='Описание')

    def __str__(self):
        return f'Внешняя библиотека {self.external_id}'

    @staticmethod
    def get_or_create_item(prop_dict):
        return ExternalLibrary.objects.get_or_create(external_id=prop_dict['external_id'],
                                                              defaults=prop_dict)

    class Meta:
        verbose_name = "Внешняя библиотека"
        verbose_name_plural = "Внешние библиотеки"
        default_permissions = ()
        permissions = [('change_externallibrary', 'Внешняя библиотека. Редактирование'),
                       ('view_externallibrary', 'Внешняя библиотека. Просмотр')]


class ToolProduct(Entity):
    """Продукция поставщиков"""
    # parent = tool_object = models.ForeignKey(ToolObject, null=True, on_delete=models.CASCADE,
    #                                 verbose_name="Инструмент из справочника")
    product_id = models.PositiveIntegerField(null=True, blank=True, default=None,
                                             verbose_name="Идентификатор продукции")
    # code = name = models.CharField(max_length=255, null=True, verbose_name='Наименование продукции')
    # description = models.CharField(max_length=255, null=True, blank=True, verbose_name='Описание продукции')
    generic_class = models.ForeignKey(ToolClass, on_delete=models.SET_DEFAULT, default=None, null=True,
                                      related_name='generic_class_tools', verbose_name='GTC GENERIC CLASS')
    gtc_vendor_class = models.ForeignKey(ToolClass, on_delete=models.SET_DEFAULT, default=None, null=True,
                                         related_name='vendor_class_tools', verbose_name='GTC VENDOR CLASS')
    p21_value_change_timestamp = models.DateTimeField(null=True, blank=True, default=None,
                                                      verbose_name="Момент изменения значений")
    p21_structure_change_timestamp = models.DateTimeField(null=True, blank=True, default=None,
                                                          verbose_name="Момент изменения структуры")
    generic_version = models.CharField(max_length=10, null=True, blank=True, default=None,
                                       verbose_name='GTC GENERIC VERSION')
    unit_system = models.ForeignKey(MeasureSystem, on_delete=models.SET_DEFAULT, default=None, null=True,
                                    verbose_name='Система измерения')  # TODO: Может measure_system?
    external_library_reference = models.ForeignKey(ExternalLibrary, null=True, on_delete=models.SET_NULL,
                                                   verbose_name="Ссылка на внешнюю библиотеку")

    def __str__(self):
        return f'{self.code} ({self.product_id})'

    class Meta:
        verbose_name = "Инструмент от поставщика"
        verbose_name_plural = "Инструменты от поставщика"
        default_permissions = ()
        permissions = [('change_toolproduct', 'Инструмент от поставщика. Редактирование'),
                       ('view_toolproduct', 'Инструмент от поставщика. Просмотр')]


class SpecificClass(List):
    """Класс из SPECIFIC_ITEM_CLASSIFICATION"""
    class Meta:
        verbose_name = "Спецификационный класс"
        verbose_name_plural = "Спецификационные классы"
        default_permissions = ()
        permissions = [('change_specificclass', 'Спецификацонный класс. Редактирование'),
                       ('view_specificclass', 'Спецификацонный класс. Просмотр')]


class SpecificClassification(models.Model):
    """Классификация классов инструмента по SPECIFIC_ITEM_CLASSIFICATION"""
    tool_product = models.ForeignKey(ToolProduct, null=False, on_delete=models.CASCADE,
                                     verbose_name="Продукция постащика")
    specific_class = models.ForeignKey(SpecificClass, null=False, on_delete=models.CASCADE,
                                       verbose_name="Спецификационный класс")

    def __str__(self):
        return f'{self.tool_product} относится к {self.specific_class}'

    @staticmethod
    def get_or_create_item(prop_dict):
        return SpecificClassification.objects.get_or_create(tool_product=prop_dict['tool_product'],
                                                            specific_class=prop_dict['specific_class'],
                                                            defaults=prop_dict)

    class Meta:
        verbose_name = "Спецификационная классификация"
        verbose_name_plural = "Спецификационные классификации"
        default_permissions = ()
        permissions = [('change_specificclassification', 'Спецификационная классификация. Редактирование'),
                       ('view_specificclassification', 'Спецификационная классификация. Просмотр')]


class ToolState(List):
    """Варианты значений состояний инструмента"""
    class Meta:
        verbose_name = "Состояние инструмента"
        verbose_name_plural = "Состояния инструмента"
        default_permissions = ()
        permissions = [('change_toolstate', 'Состояние инструмента. Редактирование'),
                       ('view_toolstate', 'Состояние инструмента. Просмотр')]


class ToolSource(List):
    """Варианты значений источников поступления инструмента"""
    class Meta:
        verbose_name = "Источник поступления инструмента"
        verbose_name_plural = "Источники поступления инструмента"
        default_permissions = ()
        permissions = [('change_toolsource', 'Источник поступления инструмента. Редактирование'),
                       ('view_toolsource', 'Источник поступления инструмента. Просмотр')]


class ToolPreference(List):
    """Варианты значений предпочтительности инструмента"""
    class Meta:
        verbose_name = "Предпочтительность инструмента"
        verbose_name_plural = "Предпочтительности инструмента"
        default_permissions = ()
        permissions = [('change_toolpreference', 'Предпочтительность инструмента. Редактирование'),
                       ('view_toolpreference', 'Предпочтительность инструмента. Просмотр')]


class PlibClass(models.Model):
    """PLIB Класс инструмента"""
    code = models.CharField(max_length=10, unique=True, null=False, verbose_name='Код класса')
    parent = models.ForeignKey(to='PlibClass', null=True, on_delete=models.CASCADE, verbose_name='Родительскй класс')
    symbol_key = models.CharField(max_length=20, null=False, blank=False, verbose_name='Символьный ключ')
    class_name = models.CharField(max_length=150, null=False, blank=False, verbose_name='Наименование класса')
    class_name_rus = models.CharField(max_length=150, null=True, blank=True, verbose_name='Наименование класса')
    external_library_reference = models.ForeignKey(ExternalLibrary, null=True, on_delete=models.SET_NULL,
                                                   verbose_name="Ссылка на внешнюю библиотеку")

    def __str__(self):
        return f'{self.class_name} ({self.code})'

    @staticmethod
    def get_or_create_item(prop_dict):
        return PlibClass.objects.get_or_create(code=prop_dict['code'], defaults=prop_dict)

    class Meta:
        verbose_name = "PLIB Класс инструмента (PLIB_CLASS_REFERENCE)"
        verbose_name_plural = "PLIB Классы инструмента (PLIB_CLASS_REFERENCE)"
        default_permissions = ()
        permissions = [('change_plibclass', 'PLIB Класс инструмента (PLIB_CLASS_REFERENCE). Редактирование'),
                       ('view_plibclass', 'PLIB Класс инструмента (PLIB_CLASS_REFERENCE). Просмотр')]


class VendorPlibClass(models.Model):
    """PLIB класс продукции поставщика (вендора)"""
    plib_class = models.ForeignKey(PlibClass, null=False, on_delete=models.CASCADE, verbose_name='PLIB Класс')
    tool_product = models.ForeignKey(ToolProduct, null=False, on_delete=models.CASCADE,
                                     verbose_name="Продукция постащика")
    supplier_bsu = models.CharField(max_length=8, verbose_name='Обозначение библиотеки PLib-классов')
    version = models.CharField(max_length=3, verbose_name='Версия')

    def __str__(self):
        return f'{self.plib_class} Bp {self.supplier_bsu} версия {self.version}'

    @staticmethod
    def get_or_create_item(prop_dict):
        return VendorPlibClass.objects.get_or_create(plib_class=prop_dict['plib_class'],
                                                     tool_product=prop_dict['tool_product'],
                                                     supplier_bsu=prop_dict['supplier_bsu'],
                                                     version=prop_dict['version'],
                                                     defaults=prop_dict)

    class Meta:
        verbose_name = "Библиотека поставщика PLIB_CLASS_REFERENCE"
        verbose_name_plural = "Библиотеки поставщиков PLIB_CLASS_REFERENCE"
        default_permissions = ()
        permissions = [('change_vendorplibclass', 'Библиотека поставщика PLIB_CLASS_REFERENCE. Редактирование'),
                       ('view_vendorplibclass', 'Библиотека поставщика PLIB_CLASS_REFERENCE. Просмотр')]


class PlibProperty(models.Model):
    """PLIB свойство инструмента"""
    code = models.CharField(max_length=10, unique=True, null=False, verbose_name='Код класса')
    symbol_key = models.CharField(max_length=10, null=False, blank=False, verbose_name='Символьный ключ')
    property_name = models.CharField(max_length=100, unique=True, null=False, verbose_name='Наименование свойства')
    name_scope = models.ForeignKey(PlibClass, null=True, on_delete=models.SET_NULL, verbose_name='PLib класс свойства')

    def __str__(self):
        return f'{self.property_name} ({self.code})'

    @staticmethod
    def get_or_create_item(prop_dict):
        # print(prop_dict)
        return PlibProperty.objects.get_or_create(code=prop_dict['code'], defaults=prop_dict)

    class Meta:
        verbose_name = "Библиотека PLIB_PROPERTY_REFERENCE"
        verbose_name_plural = "Библиотеки PLIB_PROPERTY_REFERENCE"
        default_permissions = ()
        permissions = [('change_plibproperty', 'Библиотека PLIB_PROPERTY_REFERENCE. Редактирование'),
                       ('view_plibproperty', 'Библиотека PLIB_PROPERTY_REFERENCE. Просмотр')]


class PropertySource(models.Model):
    """Связи свойств и источников"""
    property = models.OneToOneField(Property, null=False, on_delete=models.CASCADE,
                                         verbose_name='Свойство основное')
    plib_property = models.ForeignKey(PlibProperty, null=True, on_delete=models.SET_NULL,
                                      verbose_name="Ссылка на PLib-свойство")
    external_library_reference = models.ForeignKey(ExternalLibrary, null=True, on_delete=models.SET_NULL,
                                                   verbose_name="Ссылка на внешнюю библиотеку")

    def __str__(self):
        src = f'из PLIb {self.plib_property}' if self.plib_property else f'из библиотеки {self.external_library_reference}'
        return f'{self.property} {src}'

    @staticmethod
    def get_or_create_item(prop_dict):
        if 'plib_property' in prop_dict:
            return PropertySource.objects.get_or_create(property=prop_dict['property'],
                                                        plib_property=prop_dict['plib_property'],
                                                        defaults=prop_dict)
        else:
            return PropertySource.objects.get_or_create(property=prop_dict['property'],
                                                        external_library_reference=prop_dict[
                                                            'external_library_reference'],
                                                        defaults=prop_dict)

    class Meta:
        verbose_name = "Связь свойства и источника"
        verbose_name_plural = "Связи свойств и источников"
        default_permissions = ()
        permissions = [('change_propertysource', 'Связь свойства и источника. Редактирование'),
                       ('view_propertysource', 'Связь свойства и источника. Просмотр')]


class VendorPlibProperty(models.Model):
    """Связь plib классов и свойств в библиотеке вендора"""
    plib_property = models.ForeignKey(PlibProperty, null=False, on_delete=models.CASCADE,
                                      verbose_name='PLIB Свойство')
    name_scope = models.ForeignKey(PlibClass, null=False, on_delete=models.CASCADE,
                                   verbose_name='PLIB Класс')
    version = models.CharField(max_length=3, verbose_name='Версия')
    # TODO: делать составной ключ

    def __str__(self):
        return f'{self.plib_property} для {self.name_scope}'

    @staticmethod
    def get_or_create_item(prop_dict):
        return VendorPlibProperty.objects.get_or_create(plib_property=prop_dict['plib_property'],
                                                        name_scope=prop_dict['name_scope'],
                                                        version=prop_dict['version'],
                                                        defaults=prop_dict)

    class Meta:
        verbose_name = "Библиотека поставщика PLIB_PROPERTY_REFERENCE"
        verbose_name_plural = "Библиотеки поставщиков PLIB_PROPERTY_REFERENCE"
        default_permissions = ()
        permissions = [('change_vendorplibproperty', 'Библиотека поставщика PLIB_PROPERTY_REFERENCE. Редактирование'),
                       ('view_vendorplibproperty', 'Библиотека поставщика PLIB_PROPERTY_REFERENCE. Просмотр')]


class MainGtcPropertyClass(List):
    """Варианты значения признака Основной класс свойства"""
    class Meta:
        verbose_name = "Основной класс свойства"
        verbose_name_plural = "Основные классы свойств"
        default_permissions = ()
        permissions = [('change_maingtcpropertyclass', 'Основной класс свойства. Редактирование'),
                       ('view_maingtcpropertyclass', 'Основной класс свойства. Просмотр')]


class GtcPropertyClass(CodedList):
    """Варианты значения Класс GTC свойства"""
    class Meta:
        verbose_name = "Класс свойства"
        verbose_name_plural = "Классы свойств"
        default_permissions = ()
        permissions = [('change_gtcpropertyclass', 'Класс свойства. Редактирование'),
                       ('view_gtcpropertyclass', 'Класс свойства. Просмотр')]


class GtcProperty(models.Model):
    """GTC-свойства"""
    MAINLOCATIONS = (
        ('mach', 'mach'),
        ('wkps', 'wkps')
    )

    gtc_application = models.ForeignKey(ToolClass, null=False, on_delete=models.CASCADE,
                                         related_name='application_properties', verbose_name='GTC application класс')
    gtc_generic = models.ForeignKey(ToolClass, null=False, on_delete=models.CASCADE,
                                    related_name='generic_properties', verbose_name='GTC generic класс')
    main_class = models.ForeignKey(MainGtcPropertyClass, null=False, on_delete=models.CASCADE,
                                   verbose_name='Основной класс свойства')
    property_class = models.ForeignKey(GtcPropertyClass, null=False, on_delete=models.CASCADE,
                                       verbose_name='Класс свойства')
    plib_property = models.ForeignKey(PlibProperty, null=True, on_delete=models.SET_NULL, verbose_name='PLIB свойство')
    property_index = models.CharField(max_length=2, null=True, blank=True, verbose_name='Индекс свойства')
    main_location = models.CharField(max_length=4, null=True, default=None, choices=MAINLOCATIONS,
                                     verbose_name='Расположение свойства')
    item_type = models.CharField(max_length=20, null=True, blank=True, verbose_name='Тип элемента')
    taxonomy_application = models.CharField(max_length=255, null=True, blank=True,
                                            verbose_name='Классификационный путь application')
    taxonomy_generic= models.CharField(max_length=255, null=True, blank=True,
                                       verbose_name='Классификационный путь generic')
    class_top = models.CharField(max_length=5, null=True, blank=True, verbose_name='Поле непонятного назначения')

    def __str__(self):
        return f'Свойство {self.plib_property} класса {self.gtc_application}'

    @staticmethod
    def get_or_create_item(prop_dict):
        return GtcProperty.objects.get_or_create(plib_property=prop_dict['plib_property'],
                                                 property_class=prop_dict['property_class'],
                                                 gtc_application=prop_dict['gtc_application'],
                                                 main_location=prop_dict['main_location'],
                                                 property_index=prop_dict['plib_property'],
                                                 defaults=prop_dict)

    class Meta:
        verbose_name = "Свойство из GTC-библиотеки"
        verbose_name_plural = "Свойства из GTC-библиотеки"
        default_permissions = ()
        permissions = [('change_gtcproperty', 'Свойство из GTC-библиотеки. Редактирование'),
                       ('view_gtcproperty', 'Свойство из GTC-библиотеки. Просмотр')]


class ToolProductAlias(models.Model):
    """Алиасы продукции инструмента"""
    tool_product = models.ForeignKey(ToolProduct, blank=False, on_delete=models.CASCADE,
                                     verbose_name="Ссылка на продукцию")
    supplier = models.ForeignKey(Place, null=False, on_delete=models.CASCADE, verbose_name="Поставщик")
    alias_name = models.CharField(max_length=100, null=False, verbose_name='Наименование алиаса')
    alias = models.CharField(max_length=100, null=False, verbose_name='Значение алиаса')

    def __str__(self):
        return f'{self.tool_product} это {self.alias_name} {self.alias} у {self.supplier}'

    @staticmethod
    def get_or_create_item(prop_dict):
        return ToolProductAlias.objects.get_or_create(tool_product=prop_dict['tool_product'],
                                                      supplier=prop_dict['supplier'],
                                                      alias_name=prop_dict['alias_name'],
                                                      defaults=prop_dict)

    class Meta:
        verbose_name = "Алиас продукции у поставщика"
        verbose_name_plural = "Алиасы продукции у поставщиков"
        default_permissions = ()
        permissions = [('change_toolproductalias', 'Алиас продукции у поставщика. Редактирование'),
                       ('view_toolproductalias', 'Алиас продукции у поставщика. Просмотр')]


class Effectivity(models.Model):
    """Сроки действия данных"""
    tool_product = models.ForeignKey(ToolProduct, null=False, on_delete=models.CASCADE,
                                     verbose_name="Инструмент производителя")
    indicator = models.BooleanField(default=True, null=False, verbose_name='Индикатор срока')
    role = models.CharField(max_length=50, null=False, blank=False, verbose_name='Роль срока')
    limit = models.DateTimeField(null=False, verbose_name='Срок действия')

    def __str__(self):
        return f'{self.tool_product} {self.role} {self.limit}'

    @staticmethod
    def get_or_create_item(prop_dict):
        # TODO: Сделать механизм обновления дат
        return Effectivity.objects.get_or_create(tool_product=prop_dict['tool_product'],
                                                 indicator=prop_dict['indicator'],
                                                 role=prop_dict['role'],
                                                 defaults=prop_dict)

    class Meta:
        verbose_name = "Срок действия продукции у поставщика"
        verbose_name_plural = "Сроки действия продукции у поставщиков"
        default_permissions = ()
        permissions = [('change_effectivity', 'Срок действия продукции у поставщика. Редактирование'),
                       ('view_effectivity', 'Срок действия продукции у поставщика. Просмотр')]
