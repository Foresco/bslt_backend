CREATE OR REPLACE VIEW vw_parts
AS SELECT cl.id,
  cl.parent_id,
  cl.child_id,
  cl.crtd_sess_id,
  cl.comment,
  cl.edt_sess,
  cl.dlt_sess,
  cl.quantity,
  pl.link_ptr_id,
  pl.draft_zone,
  pl."position",
  pl.reg_quantity,
  pl.to_replace,
  pl.first_use,
  pl.not_buyed,
  pl.section_id,
  pl.unit_id
FROM core_link cl
JOIN pdm_partlink pl ON pl.link_ptr_id = cl.id
WHERE cl.dlt_sess = 0;