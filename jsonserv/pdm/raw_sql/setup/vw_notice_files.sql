CREATE OR REPLACE VIEW vw_notice_files
AS
SELECT
  dv.id,
  dv.notice_id,
  df.id AS file_id,
  dv.crtd_sess_id,
  dv.edt_sess,
  dv.dlt_sess,
  dv.change_num,
  dv.is_done,
  dv.change_type_id
FROM docarchive_digitalfile df
JOIN docarchive_documentversion dv ON dv.id = df.document_version_id;