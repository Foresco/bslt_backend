Приложение, организующее обмен информацие с внешними системами

Перед началом работы желательно импортировать специфически данные приложения.
## Фикстуры с данными
```cmd
python manage.py loaddata external_partners.json
```
Это:
* Внешние системы для обмена external_partners.json

## Панели
```cmd
python manage.py import_json 1 0 exchange/fixtures/panels.json
```