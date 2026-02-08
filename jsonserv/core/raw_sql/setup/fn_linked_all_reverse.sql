CREATE OR REPLACE FUNCTION fn_linked_all_reverse(
  IN _object_id INT, -- Идентификатор родительского объекта
  IN _quantity FLOAT, -- Количество объекта родителя
  IN _link_classes TEXT, -- Список классов связей для отбора
  OUT parent_id INT, -- Идентификатор родительского объекта
  OUT top_id INT,  -- Идентификатор объекта верхнего уровня
  OUT quantity FLOAT, -- Количество входящих
  OUT quantity_ratio FLOAT, -- Количество входящих с учетом коэффициента
  OUT max_level INT -- Уровень вхождения максимальный
) RETURNS SETOF RECORD
AS $$
DECLARE
  a_level INT := 1;
BEGIN
  DROP TABLE IF EXISTS a_links; -- Защита от конфликтов при повторном вызове

  -- Таблицы для временных выборок
  CREATE TEMPORARY TABLE a_links (c_parent_id INT, c_top_id INT, c_child_id INT, c_quantity FLOAT, c_quantity_ratio FLOAT, c_level INT) ON COMMIT DROP;

  -- Ввод ввод состава первого уровня
  INSERT INTO a_links(c_parent_id, c_top_id, c_child_id, c_quantity, c_quantity_ratio, c_level)
  SELECT l.parent_id, l.parent_id, l.child_id, l.quantity*_quantity, l.quantity*_quantity*COALESCE(l.ratio, 1), a_level
  FROM core_link l
  WHERE (l.child_id = _object_id) AND (l.dlt_sess = 0)
  AND ((_link_classes IS NULL) OR (l.link_class IN (
    SELECT CAST(SPLIT_PART(_link_classes, ', ', GENERATE_SERIES) AS TEXT)
    FROM GENERATE_SERIES(1, (CHAR_LENGTH(_link_classes) - CHAR_LENGTH(REPLACE(_link_classes, ', ', '')))/2 + 1)
  )));

  LOOP
    -- Заполнение составом
    INSERT INTO a_links(c_parent_id, c_top_id, c_child_id, c_quantity, c_quantity_ratio, c_level)
    SELECT a.c_parent_id, l.parent_id, l.child_id, l.quantity*a.c_quantity, l.quantity*a.c_quantity*COALESCE(l.ratio, 1), a_level + 1
    FROM a_links a
    INNER JOIN core_link l ON (l.child_id = a.c_top_id) AND (l.dlt_sess = 0)
    WHERE (a.c_level = a_level)
    AND ((_link_classes IS NULL) OR (l.link_class IN (
      SELECT CAST(SPLIT_PART(_link_classes, ', ', GENERATE_SERIES) AS TEXT)
      FROM GENERATE_SERIES(1, (CHAR_LENGTH(_link_classes) - CHAR_LENGTH(REPLACE(_link_classes, ', ', '')))/2 + 1)
    )));
    -- выход по завершению перебора
    EXIT WHEN (NOT FOUND);
    a_level := a_level + 1;
  END LOOP;

  RETURN QUERY SELECT p.c_parent_id, p.c_top_id, SUM(p.c_quantity), SUM(p.c_quantity_ratio), MAX(p.c_level)
  FROM a_links p
  WHERE p.c_top_id NOT IN (SELECT DISTINCT c_child_id FROM a_links) -- Только объекты, которые сами никуда не входят
  GROUP BY p.c_parent_id, p.c_top_id;  
END $$ LANGUAGE plpgsql;
