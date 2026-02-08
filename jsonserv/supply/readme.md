# Приложение, реализующее фукционал учета цен, заказов и поставок
Информация о поставщиках товарно-материальных ценностей
* Ценах
* Условиях поставки
* Заказах на поставку

Использует в работе данные из приложения **manufacture**

Перед началом работы желательно импортировать специфически данные приложения.

```commandline
python manage.py loaddata supply_entity_types.json supply_form_fields.json
python manage.py loaddata supply_type_settings.json
```

Это:
* Типы сущностей supply_entity_types.json
* Поля форм свойств supply_form_fields.json
* Настройки дашбородов типов supply_type_settings.json 

## Пункты меню
```cmd
python manage.py import_json 1 0 supply/fixtures/menu_items.json
```
## Панели
```cmd
python manage.py import_json 1 0 supply/fixtures/panels.json
```

## Панели типов
```cmd
python manage.py import_json 1 0 supply/fixtures/type_panels.json
```