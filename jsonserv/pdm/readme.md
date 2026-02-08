Приложение, реализующее фукникционал **Product Data Management** (**PDM**)
Управление даными опродукте, а именно:
Состав

Требует наличия подключенных приложений:
* staff

Перед началом работы желательно импортировать специфические данные приложения. 
Если пользователи не готовы вводить их самостоятельно.
## Фикстуры с данными
```cmd
python manage.py loaddata pdm_entity_types.json rendition_tails.json part_types.json
python manage.py loaddata sources.json preferences.json formats.json
python manage.py loaddata change_types.json notice_reasons.json notice_types.json
python manage.py loaddata roles.json norm_units.json route_states.json
python manage.py loaddata tp_row_types.json pdm_form_fields.json
python manage.py loaddata pdm_type_settings.json
```
Это:
* Типы сущностей pdm_entity_types.json
* Приращения исполнений rendition_tails.json
* Типы элементов состава part_types.json
* Источники поступления sources.json
* Предпочтительности preferences.json
* Типы изменений по извещению change_types.json
* Причины изменений в извещениях notice_reasons.json 
* Типы извещений notice_types.json
* Форматы листов formats.json
* Роли в разработке roles.json
* Единицы нормирования norm_units.json
* Состояния маршрутов route_states.json
* Типы строк технологических процессов tp_row_types.json
* Поля форм свойств pdm_form_fields.json
* Настройки дашбородов типов pdm_type_settings.json

## Пункты меню
```cmd
python manage.py import_json 1 0 pdm/fixtures/menu_items.json
```
## Панели интерфейса
```cmd
python manage.py import_json 1 0 pdm/fixtures/panels.json
```
## Панели типов
```cmd
python manage.py import_json 1 0 pdm/fixtures/type_panels.json
```
## Состояния объектов
```cmd
python manage.py import_json 1 0 pdm/fixtures/part_states.json
```

## Демонстрационные данные
При необходимости можно добавить в базу данных демоснстрационные данные.
Классификационные группы
```cmd
python manage.py import_json 1 0 pdm/demodata/classifications.json
```