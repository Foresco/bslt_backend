CREATE FUNCTION fn_format_string(
  @part_object_id INTEGER
) RETURNS CHARACTER VARYING(2000)
BEGIN
  DECLARE
    @a_temp CHARACTER VARYING(2000),
    @a_list_value CHARACTER VARYING(2),
    @a_list_quantity INTEGER;
  DECLARE a_cursor CURSOR FAST_FORWARD READ_ONLY LOCAL FOR
    SELECT f.list_value, pof.list_quantity
    FROM pdm_partobjectformat pof
    INNER JOIN pdm_partformat f ON (f.id = pof.format_id)
    WHERE (pof.part_object_id = @part_object_id) AND (pof.dlt_sess = 0)
    ORDER BY pof.order_num;

  OPEN a_cursor
  FETCH NEXT FROM a_cursor INTO @a_list_value, @a_list_quantity
  WHILE @@FETCH_STATUS=0
    BEGIN
      IF @a_list_quantity>1
        SET @a_temp = CONCAT_WS(', ', @a_temp, CAST(@a_list_quantity AS CHARACTER VARYING) + 'x' + @a_list_value)
      ELSE
	  BEGIN
        SET @a_temp = CONCAT_WS(', ', @a_temp, @a_list_value);
      END;
      FETCH NEXT FROM a_cursor INTO @a_list_value, @a_list_quantity;
    END
  CLOSE a_cursor
  DEALLOCATE a_cursor
  RETURN @a_temp
END