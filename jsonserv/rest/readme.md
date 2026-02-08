# Принципы построения API

Запросы, защищенные авторизацией
Запросы, не защищенные автризацией

REST-ветка находится под уровнем rest/
Соедражание описывается в файле rest/urls.py

Входная точка REST-запросов
http://localhost:8000/rest/

url-адреса запросов регистрируются в файле rest/urls.py


Примеры запросов:

Запрос объектов типа Инструмент (tool)
http://localhost:8000/rest/objects/?type_key=tool

При запросе из ARC необходимо добавить параметр cookie следующего содержания
csrftoken=LWKGCKCJLVfnzQ5tPPH4cR7H2aIcwQyXrK0U4tq5DHyW8XOzwybh46cdCrSstECG; sessionid=glalnxewvikg2c3vboxivi7ql4sbbunc
где:
* csrftoken
* sessionid
параметры, переданные сервером при аутентификации (можно посмотреть в cookies консоли)