# Приложение для управления информацией о составе трудового коллектива

```commandline
python manage.py loaddata person_category.json staff_form_fields.json
python manage.py loaddata staff_type_settings.json
```

Это:
* Категории сотрудников person_category.json
* Поля форм свойств staff_form_fields.json
* Настройки дашбородов типов staff_type_settings.json

## Панели
```cmd
python manage.py import_json 1 0 staff/fixtures/panels.json
```

## Панели типов
```cmd
python manage.py import_json 1 0 staff/fixtures/type_panels.json
```