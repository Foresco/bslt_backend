CREATE OR REPLACE FUNCTION fn_repl_nom_code(_row_id integer, _repl_num integer)
 RETURNS character varying
 LANGUAGE sql
AS $$
  SELECT po.nom_code
  FROM pdm_tprow tpr
  INNER JOIN pdm_tpresource rs ON (rs.tp_row_id = tpr.id)
  INNER JOIN core_link cl ON (cl.id = rs.link_ptr_id)
  INNER JOIN pdm_partobject po ON (po.entity_ptr_id = cl.child_id)
  WHERE (tpr.replaced_id = _row_id) AND (tpr.dlt_sess = 0)
  ORDER BY tpr.id
  LIMIT 1 OFFSET (_repl_num - 1);
$$
;