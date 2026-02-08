Приложение содержит базовый функционал системы
* Абстарктные классы
* Миксины
* Модели, используемые более чем в одном приложении

Перед началом работы желательно импортировать специфически данные приложения.
## Фикстуры с данными
```cmd
python manage.py loaddata place_types.json entity_types.json
python manage.py loaddata essences.json property_types.json core_form_fields.json
python manage.py loaddata core_type_settings.json
python manage.py loaddata core_reports.json
```
Это:
* Типы производственных подразделений place_types.json 
* Типы сущностей entity_types.json
* Измеряемые сущности essences.json
* Типы дополнительных свойств property_types.json
* Поля форм свойств form_fields.json
* Отчеты core_reports.json
* Настройки дашбородов типов core_type_settings.json

Перед загрузкой следующих пунктов должен быть осуществлен хотя бы один вход в систему.
Чтобы была сессия с идентификатором 1.

## Пункты меню
```cmd
python manage.py import_json 1 0 core/fixtures/menu_items.json
```
## Панели интерфейса
```cmd
python manage.py import_json 1 0 core/fixtures/panels.json
```
## Панели типов
```cmd
python manage.py import_json 1 0 core/fixtures/type_panels.json
```

## Единицы измерения
```cmd
python manage.py import_json 1 0 core/fixtures/measure_units.json
```
