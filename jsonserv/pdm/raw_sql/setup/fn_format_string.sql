CREATE OR REPLACE FUNCTION fn_format_string(
  _part_object_id INTEGER
) RETURNS TEXT
AS $$
DECLARE
  a_temp TEXT;
  a_list_value CHARACTER VARYING;
  a_list_quantity INTEGER;
  a_cursor CURSOR FOR
    SELECT f.list_value, pof.list_quantity
    FROM pdm_partobjectformat pof
    INNER JOIN pdm_partformat f ON (f.id = pof.format_id)
    WHERE (pof.part_object_id = _part_object_id) AND (pof.dlt_sess = 0)
    ORDER BY pof.order_num;
BEGIN
  OPEN a_cursor;
  FETCH a_cursor INTO a_list_value, a_list_quantity;
  WHILE FOUND LOOP
    IF a_list_quantity>1 THEN
      a_temp := CONCAT_WS(', ', a_temp, CAST(a_list_quantity AS CHARACTER VARYING) || 'x' || a_list_value);
    ELSE
      a_temp := CONCAT_WS(', ', a_temp, a_list_value);
    END IF;
    FETCH a_cursor INTO a_list_value, a_list_quantity;
  END LOOP;
  CLOSE a_cursor;
  RETURN a_temp;
END $$ LANGUAGE plpgsql;