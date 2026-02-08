CREATE USER bslt PASSWORD 'bslt';
CREATE SCHEMA testb AUTHORIZATION bslt;
GRANT CONNECT ON DATABASE postgres to bslt;
GRANT USAGE ON SCHEMA testb to bslt;
GRANT ALL ON SCHEMA testb to bslt;

CREATE USER basauser PASSWORD 'basauser_pas_1';
CREATE USER basalta PASSWORD 'basalta_pas_1';
CREATE USER archive PASSWORD 'archive_pas_1';

GRANT CONNECT ON DATABASE postgres to basauser;
GRANT USAGE ON SCHEMA basalta2 to basauser;

GRANT CONNECT ON DATABASE postgres to basalta;
GRANT USAGE ON SCHEMA basalta2 to basalta;

GRANT CONNECT ON DATABASE postgres to archive;
GRANT USAGE ON SCHEMA archive to archive;

GRANT ALL ON SCHEMA basalta2 to basauser;
GRANT ALL ON SCHEMA basalta2 to basalta;
GRANT ALL ON SCHEMA archive to archive;

ALTER USER basalta SET SEARCH_PATH TO basalta2;
ALTER USER basauser SET SEARCH_PATH TO basalta2;
ALTER USER archive SET SEARCH_PATH TO archive;
