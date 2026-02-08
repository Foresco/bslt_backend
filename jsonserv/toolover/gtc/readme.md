# Порядок загрузки данных из GTC-пакета
Перед загрузкой собственно GTC-пакета необходимо загрузить (если ранее эта информация не была загружена)
## Информацию об измеряемых сущностях
```commandline
python manage.py loaddata jsonserv/core/fixtures/essences.json
```
## Информацию о единицах измерения
```commandline
python manage.py import_json 1 core/fixtures/measure_units.json
```
## Информацию о свойствах, классах инструмента, PLIB-свойствах и PLIB-классах, а также их связях
```commandline
python manage.py import_json 1 toolover/fixtures/properties.json
python manage.py import_json 1 toolover/fixtures/tool_classes.json
python manage.py import_json 1 toolover/fixtures/plib_properties.json
python manage.py import_json 1 toolover/fixtures/plib_classes.json
```

## Загрузка данных из пакета запускается командой
```commandline
python manage.py import_package 1 D:/temp/gtc/Demo_Catalog
```
**Первый параметр** команды - идентификатор загрузочной сессии (обычно 1)

**Второй параметр** команды - полный путь к каталогу, в который распаковано содержимое GTC-пакета

Команда может содержать дополнительную опцию _--prepare_, это указание не выполнять загрузку, 
а только сформировать файлы с данными. В этом случае загрузочные json-пакеты будут помещены 
в каталог для временных файлов (параметр TEMP_DIR в настройках)

## Основные места доработок и корректировок
* schema_dictionary.py - Шаблоны разбора строк с параметрами из файла *.p21
* p21builder.py - построитель массива для импорта в БД. Массив имеет json-подобную структуру 
и может быть сохранен в json-файл.
в методе __init__ p21builder указывается обработчик для каждого варианта параметра.
Параметры предварительно разбираются p21parser
