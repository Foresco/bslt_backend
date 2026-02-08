# Настрока системы

## База данных
По умолчанию предполагается использование СУБД PostgreSQL
### Создание пользователя
```postgres-sql
CREATE USER basauser PASSWORD 'basauser_pas_1';
GRANT CONNECT ON DATABASE postgres to basauser;
```
### Создение схемы для данного пользователя
```postgres-sql
CREATE SCHEMA bslt AUTHORIZATION basauser;
ALTER USER basauser SET SEARCH_PATH TO bslt;
```

## Настройки Django
### Прописываем свойства соединения и пользователя в settings.py

### Создаем и выполняем миграции
```commandline
python manage.py makemigrations
python manage.py migrate
```

### Создаем суперпользователя
```commandline
python manage.py createsuperuser
```

Запускаем сервер и делаем первый вход
```commandline
python manage.py runserver
```
http://127.0.0.1:8000/login/

Для проверки дистанционного доступа допускается запуск встроенного сервера Django командой
```commandline
python manage.py runserver 0.0.0.0:8000
```
Предвариательно необходимо в настройках указать параметр ALLOWED_HOSTS, например


Далее выполняем инструкции из файла readme каждой подключенной модели

По умолчанию на сервере используется вариант аутентификации **SessionAuthentication**, использующий типовые встроенные механизмы Django.


Перед установкой возможна очистка миграций командой
```commandline
python manage.py reset_migrations core docarchive manufacture pdm price staff toolover treasure
```


