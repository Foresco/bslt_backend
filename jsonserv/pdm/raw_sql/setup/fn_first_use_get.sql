CREATE OR REPLACE FUNCTION fn_first_use_get(
  _object_id integer
) RETURNS character varying
 LANGUAGE sql
AS $function$
  SELECT o.code
  FROM vw_parts p
  INNER JOIN core_entity o ON (o.id = p.parent_id)
  INNER JOIN pdm_partobject po ON (po.entity_ptr_id = o.id) AND (po.part_type_id = 'assembly')
  WHERE (p.child_id = $1) AND (p.dlt_sess = 0)
  ORDER BY p.first_use, p.id LIMIT 1;
$function$
;