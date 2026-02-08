-- Список через запятую все замен объекта с обозначением
CREATE FUNCTION fn_replace_codes(
  @code CHARACTER VARYING(200)
) RETURNS CHARACTER VARYING(2000)
BEGIN
  DECLARE
    @a_code CHARACTER VARYING(200),
    @a_temp CHARACTER VARYING(2000);
  DECLARE a_cursor CURSOR FAST_FORWARD READ_ONLY LOCAL FOR
    SELECT DISTINCT e.code
    FROM pdm_partlink p
    INNER JOIN core_link cl ON (cl.id = p.link_ptr_id) AND (cl.dlt_sess = 0)
    INNER JOIN core_entity e ON (e.id = cl.child_id)
    WHERE (p.to_replace = @code)
    ORDER BY e.code;

  OPEN a_cursor
  FETCH NEXT FROM a_cursor INTO @a_code
  WHILE @@FETCH_STATUS=0
    BEGIN
      SET @a_temp = CONCAT_WS(', ', @a_temp, @a_code);
      FETCH NEXT FROM a_cursor INTO @a_code;
    END
  CLOSE a_cursor
  DEALLOCATE a_cursor
  IF (@a_temp IS NOT NULL) RETURN CONCAT_WS('', ' (', @a_temp, ')');
  RETURN ''
END