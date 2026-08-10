# Модуль Управление производством
Позволяет управлять производственными заказами. 
Требует наличия приложениий **pdm**, **docarchive**

Перед началом работы желательно импортировать специфические данные приложения.
## Фикстуры с данными
```cmd
python manage.py loaddata manufacture_entity_types.json manufacture_form_fields.json
python manage.py loaddata prodorder_states.json work_shifts.json
python manage.py loaddata supply_states.json link_worker_states.json order_link_tp_row_states.json
python manage.py loaddata spec_account_states.json payment_states.json
python manage.py loaddata manufacture_type_settings.json manufacture_panels.json
```
Это:
* Типы сущностей manufacture_entity_types.json
* Поля форм manufacture_form_fields.json
* Состояния производственных заказов prodorder_states.json
* Список рабочих смен work_shifts.json
* Панели интерфейса manufacture_panesl.json
* Состояния поставки supply_states.json
* Состояния заданий исполнителям link_worker_states.json
* Состояния свойств операции у позиции производственного заказа order_link_tp_row_states.json
* Состояния открытия спецсчета spec_account_states.json
* Состояния оплаты заказа payment_states.json
* Настройки дашбородов типов manufacture_type_settings.json
* Панели manufacture_panels.json

Настройки типов!
Группы пользователей!

## Пункты меню
```cmd
python manage.py import_json 1 0 manufacture/fixtures/menu_items.json
```
## Панели интерфейса
```cmd
python manage.py import_json 1 0 manufacture/fixtures/panels.json
```
## Панели типов
```cmd
python manage.py import_json 1 0 manufacture/fixtures/type_panels.json
```
## Состояния операции в составе заказа
```cmd
python manage.py import_json 1 0 manufacture/fixtures/order_link_tp_row_states.json
```
