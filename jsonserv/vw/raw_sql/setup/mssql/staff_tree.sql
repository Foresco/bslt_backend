CREATE FUNCTION fn_last_notice_get(
  @object_id INTEGER
) RETURNS CHARACTER VARYING(200)
AS
BEGIN
DECLARE @return varchar(200)
SELECT TOP 1 @return = e.code
FROM core_link cl
INNER JOIN pdm_noticelink nl ON (nl.link_ptr_id = cl.id)
INNER JOIN pdm_notice n ON (n.entity_ptr_id = cl.parent_id)
INNER JOIN core_entity e ON (e.id = cl.parent_id)
WHERE (cl.child_id = $1) AND (cl.dlt_sess = 0)
ORDER BY n.notice_date DESC
RETURN @return
END

CREATE FUNCTION fn_files_str(
  @entity_id INTEGER
) RETURNS CHARACTER VARYING
BEGIN
DECLARE
  @a_temp CHARACTER VARYING, -- Результирующая строка
  @a_id INTEGER, -- Идентификатор текущего файла
  @a_file_name CHARACTER VARYING(255); -- Обозначение текущего файла
DECLARE a_cursor CURSOR FAST_FORWARD READ_ONLY LOCAL FOR
    SELECT f.id, f.file_name
    FROM vw_partobject_files f
    WHERE (f.entity_id = @entity_id)
    ORDER BY f.file_name;

  OPEN a_cursor
  FETCH NEXT FROM a_cursor INTO @a_id, @a_file_name
  WHILE @@FETCH_STATUS=0
  BEGIN
    SET @a_temp = CONCAT_WS('/ ', @a_temp, CAST(@a_id AS CHARACTER VARYING), @a_file_name); -- / точно не будет в имени файла
    FETCH NEXT FROM a_cursor INTO @a_id, @a_file_name;
  END
  CLOSE a_cursor
  DEALLOCATE a_cursor
  RETURN @a_temp
END

CREATE FUNCTION fn_has_parts(
  @object_id INTEGER
)
RETURNS BIT
BEGIN
DECLARE @return BIT
SELECT @return = CAST(CASE WHEN EXISTS (
SELECT 1
FROM core_link cl
INNER JOIN pdm_partlink pl ON (pl.link_ptr_id = cl.id)
WHERE (cl.parent_id = @object_id) AND (cl.dlt_sess = 0)
) THEN 1 ELSE 0 END AS BIT);
RETURN @return
END

CREATE FUNCTION fn_has_arcdocs(
  @object_id INTEGER
) RETURNS BIT
BEGIN
DECLARE @return BIT
SELECT @return = CAST(CASE WHEN EXISTS (
SELECT 1
FROM core_link cl
INNER JOIN docarchive_arcdocumentobject da ON (da.link_ptr_id = cl.id)
WHERE (cl.child_id = @object_id) AND (cl.dlt_sess = 0)
) THEN 1 ELSE 0 END AS BIT);
RETURN @return
END

CREATE VIEW vw_staff_tree AS
SELECT
  l.parent_id,
  l.id,
  l.child_id,
  po.part_type_id,
  e.code,
  po.title,
  l.quantity,
  pl.position,
  dbo.fn_format_string(l.child_id) AS format_string,
  po.weight,
  d.designer,
  ps.list_value AS des_state,
  em.code AS material,
  dbo.fn_last_notice_get(l.child_id) AS notice,
  dbo.fn_has_parts(l.child_id) AS has_staff,
  dbo.fn_files_str(l.child_id) AS files,
  pt.has_staff AS can_has_staff,
  el.label,
  dbo.fn_has_arcdocs(l.child_id) AS has_arcdocs,
  l.ratio,
  pl.to_replace
FROM pdm_partlink pl
INNER JOIN core_link l ON (l.id = pl.link_ptr_id) AND (l.dlt_sess = 0)
INNER JOIN core_entity e ON (e.id = l.child_id)
INNER JOIN pdm_partobject po ON (po.entity_ptr_id = e.id)
INNER JOIN pdm_parttype pt ON (pt.part_type = po.part_type_id)
LEFT JOIN pdm_designrole dr ON (dr.subject_id = l.child_id) AND (dr.role_id = 1) AND (dr.dlt_sess = 0)
LEFT JOIN pdm_designer d ON (d.id = dr.designer_id)
LEFT JOIN vw_designmater dm ON (dm.parent_id = l.child_id)
LEFT JOIN core_entity em ON (em.id = dm.child_id)
LEFT JOIN pdm_partstate ps ON (ps.id = po.state_id)
LEFT JOIN core_entitylabel el ON (el.entity_id = l.child_id);

CREATE VIEW vw_root_tree AS
SELECT
  e.id,
  e.id AS child_id,
  po.part_type_id,
  e.code,
  po.title,
  1 AS quantity,
  0 AS "position",
  dbo.fn_format_string(e.id) AS format_string,
  po.weight,
  d.designer,
  ps.list_value AS des_state,
  em.code AS material,
  dbo.fn_last_notice_get(e.id) AS notice,
  dbo.fn_has_parts(e.id) AS has_staff,
  dbo.fn_files_str(e.id) AS files,
  pt.has_staff AS can_has_staff,
  el.label,
  dbo.fn_has_arcdocs(e.id) AS has_arcdocs,
  1 AS ratio,
  '' AS to_replace
FROM core_entity e
INNER JOIN pdm_partobject po ON (po.entity_ptr_id = e.id)
INNER JOIN pdm_parttype pt ON (pt.part_type = po.part_type_id)
LEFT JOIN pdm_designrole dr ON (dr.subject_id = e.id) AND (dr.role_id = 1) AND (dr.dlt_sess = 0)
LEFT JOIN pdm_designer d ON (d.id = dr.designer_id)
LEFT JOIN vw_designmater dm ON (dm.parent_id = e.id)
LEFT JOIN core_entity em ON (em.id = dm.child_id)
LEFT JOIN pdm_partstate ps ON (ps.id = po.state_id)
LEFT JOIN core_entitylabel el ON (el.entity_id = e.id);
