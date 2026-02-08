CREATE FUNCTION fn_repl_nom_code(
  @row_id INTEGER,
  @replaced_id INTEGER,
  @repl_num INTEGER
) RETURNS CHARACTER VARYING(15)
BEGIN
  DECLARE
    @a_temp CHARACTER VARYING(15);
  SELECT @a_temp = po.nom_code
  FROM pdm_tprow tpr
  INNER JOIN pdm_tpresource rs ON (rs.tp_row_id = tpr.id)
  INNER JOIN core_link cl ON (cl.id = rs.link_ptr_id)
  INNER JOIN pdm_partobject po ON (po.entity_ptr_id = cl.child_id)
  WHERE (((tpr.replaced_id = @replaced_id) AND NOT (tpr.id = @row_id)) 
  OR ((@row_id != @replaced_id) AND (tpr.id = @replaced_id)))
  AND (tpr.dlt_sess = 0)
  ORDER BY tpr.id
  OFFSET (@repl_num - 1) ROWS
  FETCH NEXT 1 ROWS ONLY ;
  RETURN @a_temp
END