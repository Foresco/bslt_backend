CREATE OR REPLACE FUNCTION pr_object_id_get_by_code(
  _object_code character varying,
  _object_type character varying
) RETURNS basalta2old.probjectidgetbycode_result
LANGUAGE plpgsql
AS $function$
DECLARE
  res prObjectIdGetByCode_result;
BEGIN
  SELECT o.id, fn_if(o.del_tract_id = 0, 0, 1), o.type_id, o.object_code, o.object_name, o.object_doc, o.unit_id, o.short_name, o.form_name
  INTO res.object_id, res.result_id, res.type_id, res.object_code, res.object_name, res.object_doc, res.unit_id, res.short_name, res.form_name
  FROM vw_objects_wide o
  WHERE (UPPER(o.key_code) = UPPER(_object_code)) AND ((_object_type IS NULL) OR (o.type_name = _object_type)) ORDER BY o.del_tract_id DESC LIMIT 1;
  IF (res.object_id IS NULL) THEN
    -- Объект не найден
    res.object_id := 0;
    res.type_id := 0;
    res.result_id := 2;
  END IF;
  RETURN res;
END $function$
;