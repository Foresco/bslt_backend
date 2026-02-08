CREATE OR REPLACE FUNCTION fn_concat(
character varying,
character varying
) RETURNS text
LANGUAGE sql
AS $function$
  SELECT COALESCE($1 || ' ' || $2, '');
$function$
;
