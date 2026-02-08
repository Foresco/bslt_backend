CREATE OR REPLACE FUNCTION fn_last_notice_get(
  IN _object_id INT
) RETURNS CHARACTER VARYING(200)
AS $$
SELECT e.code
FROM core_link cl
INNER JOIN pdm_noticelink nl ON (nl.link_ptr_id = cl.id)
INNER JOIN pdm_notice n ON (n.entity_ptr_id = cl.parent_id)
INNER JOIN core_entity e ON (e.id = cl.parent_id)
WHERE (cl.child_id = $1) AND (cl.dlt_sess = 0)
ORDER BY n.notice_date DESC LIMIT 1;
$$ LANGUAGE sql;

CREATE OR REPLACE FUNCTION fn_files_str(
  _entity_id INT
) RETURNS TEXT
AS $$
DECLARE
  a_temp TEXT; -- Результирующая строка
  a_id INT; -- Идентификатор текущего файла
  a_file_name CHARACTER VARYING(255); -- Обозначение текущего файла
  a_cursor CURSOR FOR
    SELECT f.id, f.file_name
    FROM vw_partobject_files f
    WHERE (f.entity_id = _entity_id)
    ORDER BY f.file_name;
BEGIN
  OPEN a_cursor;
  FETCH a_cursor INTO a_id, a_file_name;
  WHILE FOUND LOOP
    a_temp := CONCAT_WS('/ ', a_temp, CAST(a_id AS TEXT), CAST(a_file_name AS TEXT)); -- / точно не будет в имени файла
    FETCH a_cursor INTO a_id, a_file_name;
  END LOOP;
  CLOSE a_cursor;
  RETURN a_temp;
END $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_has_parts(
  _object_id integer
)
RETURNS boolean
AS $$
SELECT EXISTS (
SELECT 1
FROM core_link cl
INNER JOIN pdm_partlink pl ON (pl.link_ptr_id = cl.id)
WHERE (cl.parent_id = $1) AND (cl.dlt_sess = 0)
);
$$ LANGUAGE sql;

CREATE OR REPLACE FUNCTION fn_has_arcdocs(
  _object_id integer
)
RETURNS boolean
AS $$
SELECT EXISTS (
SELECT 1
FROM core_link cl
INNER JOIN docarchive_arcdocumentobject da ON (da.link_ptr_id = cl.id)
WHERE (cl.child_id = $1) AND (cl.dlt_sess = 0)
);
$$ LANGUAGE sql;

CREATE OR REPLACE VIEW vw_staff_tree AS
SELECT
  l.parent_id,
  l.id,
  l.child_id,
  po.part_type_id,
  e.code,
  po.title,
  l.quantity,
  pl.position,
  fn_format_string(l.child_id) AS format_string,
  po.weight,
  d.designer,
  ps.list_value AS des_state,
  em.code AS material,
  fn_last_notice_get(l.child_id) AS notice,
  fn_has_parts(l.child_id) AS has_staff,
  pt.has_staff AS can_has_staff,
  el.label,
  fn_has_arcdocs(l.child_id) AS has_arcdocs,
  l.ratio,
  pl.to_replace,
  COALESCE(se.edt_sess, 0) > GREATEST(e.edt_sess, e.crtd_sess_id) AS outdated
FROM pdm_partlink pl
INNER JOIN core_link l ON (l.id = pl.link_ptr_id) AND (l.dlt_sess = 0)
INNER JOIN core_entity e ON (e.id = l.child_id)
INNER JOIN pdm_partobject po ON (po.entity_ptr_id = e.id)
INNER JOIN pdm_parttype pt ON (pt.part_type = po.part_type_id)
LEFT JOIN core_entity se ON (se.id = po.origin_id)
LEFT JOIN pdm_designrole dr ON (dr.subject_id = l.child_id) AND (dr.role_id = 1) AND (dr.dlt_sess = 0)
LEFT JOIN pdm_designer d ON (d.id = dr.designer_id)
LEFT JOIN vw_designmater dm ON (dm.parent_id = l.child_id)
LEFT JOIN core_entity em ON (em.id = dm.child_id)
LEFT JOIN pdm_partstate ps ON (ps.id = po.state_id)
LEFT JOIN core_entitylabel el ON (el.entity_id = l.child_id);

CREATE OR REPLACE VIEW vw_root_tree AS
SELECT
  e.id,
  e.id AS child_id,
  po.part_type_id,
  e.code,
  po.title,
  1 AS quantity,
  0 AS "position",
  fn_format_string(e.id) AS format_string,
  po.weight,
  d.designer,
  ps.list_value AS des_state,
  em.code AS material,
  fn_last_notice_get(e.id) AS notice,
  fn_has_parts(e.id) AS has_staff,
  pt.has_staff AS can_has_staff,
  el.label,
  fn_has_arcdocs(e.id) AS has_arcdocs,
  1 AS ratio,
  '' AS to_replace,
  COALESCE(se.edt_sess, 0) > GREATEST(e.edt_sess, e.crtd_sess_id) AS outdated
FROM core_entity e
INNER JOIN pdm_partobject po ON (po.entity_ptr_id = e.id)
INNER JOIN pdm_parttype pt ON (pt.part_type = po.part_type_id)
LEFT JOIN core_entity se ON (se.id = po.origin_id)
LEFT JOIN pdm_designrole dr ON (dr.subject_id = e.id) AND (dr.role_id = 1) AND (dr.dlt_sess = 0)
LEFT JOIN pdm_designer d ON (d.id = dr.designer_id)
LEFT JOIN vw_designmater dm ON (dm.parent_id = e.id)
LEFT JOIN core_entity em ON (em.id = dm.child_id)
LEFT JOIN pdm_partstate ps ON (ps.id = po.state_id)
LEFT JOIN core_entitylabel el ON (el.entity_id = e.id);
