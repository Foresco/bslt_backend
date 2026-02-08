CREATE OR REPLACE FUNCTION fn_group_tree(
  IN _group_id INT -- Идентификатор корневой группы
) RETURNS SETOF INT
AS $$
DECLARE
  a_level INT := 1;
BEGIN
  DROP TABLE IF EXISTS a_groups; -- Защита от конфликтов при повторном вызове

  -- Таблицы для временных выборок
  CREATE TEMPORARY TABLE a_groups (c_group_id INT, c_level INT) ON COMMIT DROP;

  -- Ввод самого родительского объекта
  INSERT INTO a_groups(c_group_id, c_level) VALUES (_group_id, a_level);

  LOOP
    -- Заполнение составом
    INSERT INTO a_groups(c_group_id, c_level)
    SELECT g.id, a_level + 1
    FROM a_groups a
    INNER JOIN core_entity g ON (g.group_id = a.c_group_id) AND (g.type_key_id = 'classification') AND (g.dlt_sess = 0)
    WHERE (a.c_level = a_level);
    -- выход по завершению перебора
    EXIT WHEN (NOT FOUND);
    a_level := a_level + 1;
  END LOOP;

  RETURN QUERY SELECT g.c_group_id
  FROM a_groups g
  ORDER BY g.c_group_id;
END $$ LANGUAGE plpgsql;