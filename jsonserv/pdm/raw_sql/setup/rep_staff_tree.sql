CREATE OR REPLACE FUNCTION rep_staff_tree(
  _object_id integer,
  _quantity double precision,
  _levels integer,
  OUT child_id integer,
  OUT parent_id integer,
  OUT quantity double precision,
  OUT level_num integer,
  OUT order_num character varying
) RETURNS SETOF record
LANGUAGE plpgsql
AS $function$
DECLARE
  a_critery INT := 1;
BEGIN
  -- Таблицы для временных выборок
  CREATE TEMPORARY TABLE a_parts (c_child_id INT, c_parent_id INT, c_quantity FLOAT, c_order CHARACTER VARYING(255), critery INT) ON COMMIT DROP;

  -- Ввод самого родительского объекта
  INSERT INTO a_parts(c_child_id, c_quantity, c_order, critery) VALUES (_object_id, _quantity, '', a_critery);

  LOOP
    INSERT INTO a_parts(c_child_id, c_parent_id, c_quantity, c_order, critery)
    SELECT p.child_id, p.parent_id, (p.quantity + COALESCE(p.reg_quantity, 0))*a.c_quantity,
    a.c_order || LPAD(CAST(row_number() over() AS CHARACTER VARYING), 3, '0'), a_critery + 1
    FROM a_parts a
    INNER JOIN vw_parts p ON (p.parent_id = a.c_child_id) AND (p.dlt_sess = 0) AND (p.to_replace IS NULL)
    INNER JOIN core_entity o ON (o.id = a.c_child_id)
    WHERE (a.critery = a_critery)
    ORDER BY p.position, o.code;
    -- выход по завершению перебора
    EXIT WHEN (a_critery = _levels) OR NOT FOUND;
    a_critery := a_critery + 1;
  END LOOP;

  RETURN QUERY SELECT p.c_child_id, p.c_parent_id, p.c_quantity, p.critery, p.c_order
  FROM a_parts p ORDER BY p.c_order;
END $function$
;
