CREATE OR REPLACE FUNCTION fn_if(
  boolean,
  anyelement,
  anyelement
) RETURNS anyelement
LANGUAGE sql
AS $function$
  SELECT CASE WHEN $1 THEN $2 ELSE $3 END;
$function$
;