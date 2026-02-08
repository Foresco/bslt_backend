Приложение, реализующее взаимодествие между сотрудниками

Перед началом работы желательно импортировать специфически данные приложения.
## Фикстуры с данными
```cmd
python manage.py loaddata community_entity_types.json letter_types.json
python manage.py loaddata letter_directions.json task_types.json
python manage.py loaddata community_form_fields.json community_type_settings.json
```
Это:
* Типы сущностей community_entity_types.json
* Типы писем letter_types.json
* Направления писем letter_directions.json
* Типы заданий task_types.json
* Поля форм свойств community_form_fields.json
* Настройки дашбородов типов community_type_settings.json

## Пункты меню
```cmd
python manage.py import_json 1 0 community/fixtures/menu_items.json
```

## Панели
```cmd
python manage.py import_json 1 0 community/fixtures/panels.json
```

## Панели типов
```cmd
python manage.py import_json 1 0 community/fixtures/type_panels.json
```