Приложение, реализующее управление файловым архивом и архивом документов

Для корректной работы приложения необходимо установить приложение **pdm**

Перед началом работы желательно импортировать специфически данные приложения.
## Фикстуры с данными
```cmd
python manage.py loaddata docarchive_entity_types.json archives_and_folders.json
python manage.py loaddata document_types.json docarchive_form_fields.json
python manage.py loaddata docarchive_type_settings.json
```
Это:
* Типы сущностей docarchive_entity_types.json
* Архивы и Каталоги archives_and_folders.json
* Типы документов document_types.json
* Поля форм свойств docarchive_form_fields.json
* Настройки дашбородов типов docarchive_type_settings.json

## Пункты меню
```cmd
python manage.py import_json 1 0 docarchive/fixtures/menu_items.json
```

## Панели
```cmd
python manage.py import_json 1 0 docarchive/fixtures/panels.json
```

## Панели типов
```cmd
python manage.py import_json 1 0 docarchive/fixtures/type_panels.json
```

## Единицы измерения
```cmd
python manage.py import_json 1 0 docarchive/fixtures/measure_units.json
```

После импорта информации об архиве необходимо настроить адрес расположения файловго архива в модуле администрирования
Управление архивом документации › Файловые архивы