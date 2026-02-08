CREATE OR REPLACE VIEW vw_files_for_upload
AS SELECT
  df.id,
  edv.entity_id AS object_id,
  df.file_name AS doc_code,
  df.folder_id,
  "left"(f.folder_name::text, 1) AS prefix_char,
  f.folder_name,
  dv.version_num,
  fd.doc_type_id,
  dt.list_value AS doc_type,
  edv.dlt_sess AS del_tract_id,
  'd'::text AS source,
  f.archive_id,
  fa.archive_name
FROM docarchive_entitydocumentversion edv
JOIN docarchive_documentversion dv ON dv.id = edv.document_version_id
JOIN docarchive_filedocument fd ON fd.id = dv.document_id
JOIN docarchive_digitalfile df ON df.document_version_id = edv.document_version_id
JOIN docarchive_folder f ON f.id = df.folder_id
JOIN docarchive_filearchive fa ON fa.id = f.archive_id
LEFT JOIN docarchive_documenttype dt ON dt.id = fd.doc_type_id
WHERE edv.dlt_sess = 0 AND df.dlt_sess = 0 AND edv.old_version = false;