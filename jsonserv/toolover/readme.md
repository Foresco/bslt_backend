Приложение, реализующее фукникционал инструментооборота
Хранение произвольных данных об используемом предприятием инструменте

Для управления информацией о хранении инструмента необходима установка приложения **Storehouse** (ссылка)


Перед началом работы желательно импортировать специфически данные приложения.
## Фикстуры с данными
```cmd
python manage.py loaddata toolover_entity_types.json toolover_sources.json toolover_preferences.json toolover_states.json
python manage.py loaddata toolover_fields.json
```
Это:
* Типы сущностей toolover_entity_types.json
* Панели интерфейса toolover_panels.json
* Источники поступления toolover_sources.json
* Предпочтительности toolover_preferences.json
* Состояния toolover_states.json
* Имена полей форм toolover_fields.json

## Пункты меню
```cmd
python manage.py import_json 1 0 toolover/fixtures/menu_items.json
```


## Демонстрационные данные
При необходимости можно добавить в базу данных демоснстрационные данные.
Классификационные группы
```cmd
python manage.py import_json 1 0 toolover/demodata/classifications.json
```
Классы режущего инструмента
```cmd
python manage.py import_json 1 0 toolover/fixtures/tool_classes.json
```
Класификационная структура Sandvik
```cmd
python manage.py import_json 1 0 toolover/fixtures/gtc_application_properties.json
```

## Команды, доступные в приложении
Загрузка данных из GTC-пакета
Содержимое GTC-пакета должно быть предварительно распаковано в каталог, имя которого передается команде на импорт, например C:/PackageDir
```cmd
python manage.py import_package 1 D:/temp/gtc/Demo_Catalog
```
Допололнительно команде можно передать параметр
**--prepare**
Означающий, что импорта производить не нужно, достаточно сформировать пакеты для импорта