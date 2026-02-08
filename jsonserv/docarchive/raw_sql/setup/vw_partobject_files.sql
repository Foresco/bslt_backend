CREATE OR REPLACE VIEW vw_partobject_files
AS 
SELECT ev.entity_id,
  df.id,
  df.file_name
FROM docarchive_entitydocumentversion ev
JOIN docarchive_digitalfile df ON df.document_version_id = ev.document_version_id AND df.dlt_sess = 0
WHERE ev.dlt_sess = 0;