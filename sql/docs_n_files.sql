SELECT * FROM docarchive_filedocument df

SELECT * FROM docarchive_digitalfile dd 

SELECT * FROM docarchive_documentversion dd 

SELECT * FROM docarchive_entitydocumentversion de 

DELETE FROM docarchive_entitydocumentversion

SELECT edv.document_version_id 
FROM docarchive_entitydocumentversion edv 
INNER JOIN docarchive_documentversion dv ON (dv.id = edv.document_version_id)
INNER JOIN docarchive_filedocument fd ON (fd.id = dv.document_id)
INNER JOIN docarchive_digitalfile dd2 ON (dd2.document_version_id = edv.document_version_id)

SELECT edv.id, dv.id, fd.id, edv.document_version_id
FROM docarchive_entitydocumentversion edv
INNER JOIN docarchive_documentversion dv ON (dv.id = edv.document_version_id)
INNER JOIN docarchive_filedocument fd ON (fd.id = dv.document_id)
-- INNER JOIN docarchive_digitalfile dd2 ON (dd2.document_version_id = edv.document_version_id)
WHERE edv.entity_id = 588275 AND edv.document_version_id < 108307

SELECT * FROM docarchive_filedocument ORDER BY id DESC LIMIT 4

DELETE FROM docarchive_entitydocumentversion WHERE id IN (514679,
514678,
514677);

DELETE FROM docarchive_documentversion WHERE id IN (108306,
108305,
108304);

DELETE FROM docarchive_filedocument WHERE id IN (107541,
107540,
107539);

-- Все файлы и сущности с ними связанные
SELECT ce.id, ce.code, ce.type_key_id, ev.dlt_sess, df.file_name 
FROM docarchive_digitalfile df
INNER JOIN docarchive_documentversion dv ON (dv.id = df.document_version_id) 
INNER JOIN docarchive_entitydocumentversion ev ON (ev.document_version_id = dv.id) 
INNER JOIN core_entity ce ON (ce.id = ev.entity_id)

SELECT edv.id, dv.id, edv.document_version_id, fd.id, fd.doc_code, ar.archive_name, f.folder_name, dd2.id, f.archive_id 
FROM docarchive_entitydocumentversion edv 
INNER JOIN docarchive_documentversion dv ON (dv.id = edv.document_version_id)
INNER JOIN docarchive_filedocument fd ON (fd.id = dv.document_id)
INNER JOIN docarchive_digitalfile dd2 ON (dd2.document_version_id = edv.document_version_id)
INNER JOIN docarchive_folder f ON (f.id = dd2.folder_id)
INNER JOIN docarchive_filearchive ar ON (ar.id = f.archive_id) 
WHERE dd2.id IN (68942, 114551)
AND edv.entity_id = 572318

-- Создание копий файловых документов 114542
INSERT INTO docarchive_filedocument(doc_code, description, doc_type_id, crtd_sess_id, edt_sess, dlt_sess, archive_id)
SELECT fd.doc_code, fd.description, fd.doc_type_id, fd.crtd_sess_id, fd.edt_sess, fd.dlt_sess, 2
FROM docarchive_arcdocument da 
INNER JOIN docarchive_entitydocumentversion edv ON (edv.entity_id = da.entity_ptr_id)
INNER JOIN docarchive_documentversion dv ON (dv.id = edv.document_version_id)
INNER JOIN docarchive_filedocument fd ON (fd.id = dv.document_id)
WHERE NOT edv.entity_id = 572318;

-- Создание версий документов 116810
INSERT INTO docarchive_documentversion(document_id, description, version_num, archive_cell_id, notice_id, change_num, change_type_id, is_done, crtd_sess_id, edt_sess, dlt_sess)
SELECT fd2.id, dv.description, dv.version_num, dv.archive_cell_id, dv.notice_id, dv.change_num, dv.change_type_id, dv.is_done, dv.crtd_sess_id, dv.edt_sess, dv.dlt_sess
FROM docarchive_arcdocument da 
INNER JOIN docarchive_entitydocumentversion edv ON (edv.entity_id = da.entity_ptr_id)
INNER JOIN docarchive_documentversion dv ON (dv.id = edv.document_version_id)
INNER JOIN docarchive_filedocument fd ON (fd.id = dv.document_id) AND (fd.archive_id = 1)
INNER JOIN docarchive_digitalfile dd2 ON (dd2.document_version_id = edv.document_version_id)
INNER JOIN docarchive_folder f ON (f.id = dd2.folder_id) AND (f.archive_id = 2)
INNER JOIN docarchive_filedocument fd2 ON (fd2.doc_code = fd.doc_code) AND (fd2.archive_id = 2)
WHERE NOT edv.entity_id = 572318;

-- Связывание созданных версий с соотвествующими файлами
UPDATE docarchive_digitalfile
SET document_version_id = a.dv_id
FROM (
SELECT dd2.id AS df_id, dv2.id AS dv_id
FROM docarchive_arcdocument da 
INNER JOIN docarchive_entitydocumentversion edv ON (edv.entity_id = da.entity_ptr_id)
INNER JOIN docarchive_documentversion dv ON (dv.id = edv.document_version_id)
INNER JOIN docarchive_filedocument fd ON (fd.id = dv.document_id) AND (fd.archive_id = 1)
INNER JOIN docarchive_digitalfile dd2 ON (dd2.document_version_id = edv.document_version_id)
INNER JOIN docarchive_folder f ON (f.id = dd2.folder_id) AND (f.archive_id = 2)
INNER JOIN docarchive_filedocument fd2 ON (fd2.doc_code = fd.doc_code) AND (fd2.archive_id = 2)
INNER JOIN docarchive_documentversion dv2 ON (dv2.document_id = fd2.id)
WHERE NOT edv.entity_id = 572318
) a
WHERE (id = a.df_id);

-- Связывание созданных версий с соответствующими архивными документами
UPDATE docarchive_entitydocumentversion
SET document_version_id = a.dv_id
FROM (
SELECT edv.id AS edv_id, dv2.id AS dv_id
FROM docarchive_arcdocument da 
INNER JOIN docarchive_entitydocumentversion edv ON (edv.entity_id = da.entity_ptr_id)
INNER JOIN docarchive_documentversion dv ON (dv.id = edv.document_version_id)
INNER JOIN docarchive_filedocument fd ON (fd.id = dv.document_id) AND (fd.archive_id = 1)
INNER JOIN docarchive_filedocument fd2 ON (fd2.doc_code = fd.doc_code) AND (fd2.archive_id = 2)
INNER JOIN docarchive_documentversion dv2 ON (dv2.document_id = fd2.id)
WHERE NOT da.entity_ptr_id = 572318
) a
WHERE (id = a.edv_id);

-- Удаление повторов файловых документов
UPDATE docarchive_documentversion SET document_id = a.min_id
FROM (
SELECT max(id) AS max_id, min(id) min_id
FROM docarchive_filedocument df GROUP BY doc_code, archive_id 
HAVING count(*)>1
) a
WHERE document_id = a.max_id

DELETE FROM docarchive_filedocument WHERE id IN (
SELECT max(id)
FROM docarchive_filedocument df GROUP BY doc_code, archive_id 
HAVING count(*)>1
)

-- Чистка ошибок импорта
-- Удаление связей с версиями документов, не имеющими цифровых файлов
DELETE FROM docarchive_entitydocumentversion
WHERE NOT EXISTS (
  SELECT 1 FROM docarchive_digitalfile WHERE document_version_id = docarchive_entitydocumentversion.document_version_id
);

-- Удаление ролей у версий документов, не имеющих цифровых файлов
DELETE FROM docarchive_versiondesignrole
WHERE NOT EXISTS (
  SELECT 1 FROM docarchive_digitalfile WHERE document_version_id = docarchive_versiondesignrole.document_version_id
);

-- Удаление версий документов, не имеющих цифровых файлов
DELETE FROM docarchive_documentversion
WHERE NOT EXISTS (
  SELECT 1 FROM docarchive_digitalfile WHERE document_version_id = docarchive_documentversion.id
);

-- Удаление файловых документов без версий 
DELETE FROM docarchive_arcdocument
WHERE NOT EXISTS (
  SELECT 1 FROM docarchive_documentversion WHERE document_id = docarchive_arcdocument.id
);

-- Перенос пометок удаления на связь с объектом
SELECT * FROM docarchive_documentversion WHERE dlt_sess = 0;