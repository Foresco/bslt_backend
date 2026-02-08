CREATE OR REPLACE FUNCTION fn_linked_all_w_renditions(
  IN _object_id INT, -- Идентификатор родительского объекта
  IN _quantity FLOAT, -- Количество объекта родителя
  IN _link_classes TEXT, -- Список классов связей для отбора
  OUT child_id INT, -- Идентификатор входящего объекта
  OUT quantity FLOAT, -- Количество входящих
  OUT level_max INT -- Максимальный уровень развертывания
) RETURNS SETOF RECORD
AS $$
DECLARE
  a_level INT := 1;
BEGIN
  DROP TABLE IF EXISTS a_links; -- Защита от конфликтов при повторном вызове

  -- Таблицы для временных выборок
  CREATE TEMPORARY TABLE a_links (c_child_id INT, c_quantity FLOAT, c_level INT) ON COMMIT DROP;

  -- Ввод самого родительского объекта
  INSERT INTO a_links(c_child_id, c_quantity, c_level) VALUES (_object_id, _quantity, a_level);

  LOOP
    -- добавление исполнений
    INSERT INTO a_links(c_child_id, c_quantity, c_level)
    SELECT r.rendition_id, a.c_quantity, a_level
    FROM a_links a
    INNER JOIN pdm_rendition r ON (r.parent_id = a.c_child_id) AND (r.dlt_sess = 0)
    LEFT JOIN a_links ta ON (ta.c_child_id = r.rendition_id)
    WHERE (a.c_level = a_level)
    AND (ta.c_child_id IS NULL); -- Проверка, что ранее не был добавлен
    -- Заполнение составом
    INSERT INTO a_links(c_child_id, c_quantity, c_level)
    SELECT l.child_id, l.quantity*a.c_quantity, a_level + 1
    FROM a_links a
    INNER JOIN core_link l ON (l.parent_id = a.c_child_id) AND (l.dlt_sess = 0)
    WHERE (a.c_level = a_level)
    AND ((_link_classes IS NULL) OR (l.link_class IN (
      SELECT CAST(SPLIT_PART(_link_classes, ', ', GENERATE_SERIES) AS TEXT)
      FROM GENERATE_SERIES(1, (CHAR_LENGTH(_link_classes) - CHAR_LENGTH(REPLACE(_link_classes, ', ', '')))/2 + 1)
    )));
    -- выход по завершению перебора
    EXIT WHEN (NOT FOUND);
    a_level := a_level + 1;
  END LOOP;

  -- Внимание, количество бессмысленно, так как есть исполнения!
  RETURN QUERY SELECT p.c_child_id, SUM(p.c_quantity), a_level
  FROM a_links p
  GROUP BY p.c_child_id;
END $$ LANGUAGE plpgsql;
