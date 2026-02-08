CREATE FUNCTION fn_into_codes(
  @part_object_id INTEGER,
  @link_classes CHARACTER VARYING(100) -- Список классов связей для отбора
) RETURNS CHARACTER VARYING(2000)
BEGIN
  DECLARE
    @a_temp CHARACTER VARYING(2000),
    @a_list_value CHARACTER VARYING(200);
  DECLARE a_cursor CURSOR FAST_FORWARD READ_ONLY LOCAL FOR
    SELECT DISTINCT o.object_code
    FROM core_link l
    INNER JOIN vw_objects o ON (o.id = l.parent_id)
    WHERE (l.child_id = @part_object_id) AND (l.dlt_sess = 0)
    AND ((@link_classes IS NULL) OR (l.link_class IN (
      SELECT value FROM STRING_SPLIT(@link_classes, ', ')
      )))
    ORDER BY o.object_code;

  OPEN a_cursor
  FETCH NEXT FROM a_cursor INTO @a_list_value
  WHILE @@FETCH_STATUS=0
    BEGIN
      SET @a_temp = CONCAT_WS(', ', @a_temp, @a_list_value);
      FETCH NEXT FROM a_cursor INTO @a_list_value;
    END
  CLOSE a_cursor
  DEALLOCATE a_cursor
  RETURN @a_temp
END