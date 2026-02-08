CREATE OR REPLACE FUNCTION fn_all_objects_level(
  _object_id integer,
  _quantity double precision,
  _levels integer,
  OUT child_id integer,
  OUT quantity double precision,
  OUT parents text
) RETURNS SETOF record
LANGUAGE plpgsql
AS $function$
DECLARE
  a_critery INT := 1;
BEGIN
  -- Таблицы для временных выборок
  CREATE TEMPORARY TABLE a_parts (c_child_id INT, c_quantity FLOAT, c_parent_code CHARACTER VARYING(200), critery INT) ON COMMIT DROP;

  -- Ввод самого родительского объекта
  INSERT INTO a_parts(c_child_id, c_quantity, critery) VALUES (_object_id, _quantity, a_critery);

  LOOP
    INSERT INTO a_parts(c_child_id, c_quantity, c_parent_code, critery)
    SELECT p.child_id, (p.quantity + COALESCE(p.reg_quantity, 0))*a.c_quantity, o.code, a_critery + 1
    FROM a_parts a
    INNER JOIN vw_parts p ON (p.parent_id = a.c_child_id) AND (p.dlt_sess = 0) AND (p.to_replace IS NULL)
    INNER JOIN core_entity o ON (o.id = a.c_child_id)
    WHERE (a.critery = a_critery);
    -- выход по завершению перебора
    EXIT WHEN (a_critery = _levels) OR NOT FOUND;
    a_critery := a_critery + 1;
  END LOOP;

  RETURN QUERY SELECT p.c_child_id, SUM(p.c_quantity), agg_concat(p.c_parent_code) FROM a_parts p GROUP BY p.c_child_id;
END $function$
;
