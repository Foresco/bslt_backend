CREATE OR REPLACE FUNCTION fn_pia_update()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
  IF (new.state_id = 6) AND NOT EXISTS ( -- Такой строки еще нет
    SELECT 1 FROM core_entitylabel t
    WHERE (t.entity_id = new.entity_ptr_id)
  ) THEN
    INSERT INTO core_entitylabel(entity_id, label)
    VALUES (new.entity_ptr_id, 'Сдано в архив');
  END IF;
  RETURN new;
END; $function$
;
