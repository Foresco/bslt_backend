CREATE OR REPLACE FUNCTION fn_quantity(
	IN _parent_id integer,
	IN _child_id integer,
	IN _quantity double precision
) RETURNS double precision
AS $$
BEGIN
  IF (_parent_id = _child_id) THEN -- Вхождение в самого себя
    RETURN _quantity;
  END IF;
  DROP TABLE IF EXISTS a_parts; -- Защита от конфликтов при повторном вызове
  -- Перебор всех родителей
  RETURN SUM(a.quantity) FROM fn_linked_all(_parent_id, _quantity, ''::TEXT) a
  WHERE (a.child_id = _child_id);
END $$ LANGUAGE plpgsql;
