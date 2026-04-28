-- Основная база данных
CREATE USER basauser PASSWORD 'basauser_pas_1';
GRANT CONNECT ON DATABASE postgres to basauser;

CREATE SCHEMA basalta2 AUTHORIZATION basauser;

ALTER USER basauser SET SEARCH_PATH TO basalta2;

GRANT USAGE ON SCHEMA archive TO archive2;

-- База данных для наследования
CREATE USER basalta PASSWORD 'basalta_pas_1';
GRANT CONNECT ON DATABASE postgres to basalta;

CREATE SCHEMA test AUTHORIZATION basalta;

ALTER USER basalta SET SEARCH_PATH TO test;

-- Нечеткий поиск
CREATE EXTENSION fuzzystrmatch;

SELECT object_code, levenshtein('Б0ЛTM24X60.TZNDIN6914', check_code) aa, check_code
FROM objects WHERE type_id = 5
AND check_code ILIKE 'Б0ЛTM24%'
ORDER BY aa DESC;
