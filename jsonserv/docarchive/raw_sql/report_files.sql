SELECT
  a.doc_code,
  a.folder_name,
  ad.code AS document_num,
  t.session_datetime AS tract_datetime
FROM pr_all_docs(%(object_id)s, %(doc_types)s, %(notices)s::SMALLINT, %(archive)s) a
LEFT JOIN core_entity ad ON (ad.id = a.arcdoc_id)
LEFT JOIN core_usersession t ON (t.id = ad.crtd_sess_id);