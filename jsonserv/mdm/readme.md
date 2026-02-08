Приложение для обработки и выверки справочных данных (MDM)
Для работы необходимо приложение **core**.

Перед началом работы желательно импортировать специфически данные приложения.
```cmd
python manage.py loaddata mdm_type_settings.json
```

Это:
* Настройки дашбородов типов mdm_type_settings.json

## Пункты меню
```cmd
python manage.py import_json 1 0 mdm/fixtures/menu_items.json
```
## Панели интерфейса
```cmd
python manage.py import_json 1 0 mdm/fixtures/panels.json
```
## Панели типов
```cmd
python manage.py import_json 1 0 mdm/fixtures/type_panels.json
```