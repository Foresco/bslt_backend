CREATE OR REPLACE FUNCTION fn_notice_object_get(
  _notice_id integer,
  _object_id integer
) RETURNS integer
LANGUAGE sql
AS $function$
  SELECT COALESCE(nl.object_id, o.id)
  FROM core_entity o
  LEFT JOIN vw_notice_links nl ON (nl.notice_id = $1) AND (nl.old_id = o.id) AND (nl.dlt_sess = 0)
  WHERE (o.id = $2) LIMIT 1;
$function$
;
