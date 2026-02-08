CREATE OR REPLACE VIEW vw_notice_links
AS
SELECT
  cl.id,
  cl.parent_id AS notice_id,
  cl.child_id AS object_id,
  cl.crtd_sess_id,
  cl.comment,
  cl.edt_sess,
  cl.dlt_sess,
  nl.change_num,
  nl.is_done,
  nl.change_type_id,
  nl.old_id
FROM core_link cl
JOIN pdm_noticelink nl ON nl.link_ptr_id = cl.id;