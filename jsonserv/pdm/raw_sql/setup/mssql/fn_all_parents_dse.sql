CREATE OR ALTER FUNCTION fn_all_parents_dse(
  @object_id INTEGER, -- Идентификатор родительского объекта
  @quantity FLOAT, -- Количество объекта родителя
  @link_classes CHARACTER VARYING -- Список классов связей для отбора
) RETURNS @res_table TABLE
(
  child_id INTEGER, -- Идентификатор входящего объекта
  dse_id INTEGER, -- Идентификатор входящей сборочной единицы или детали
  quantity FLOAT, -- Количество входящих
  quantity_ratio FLOAT, -- Количество входящих с учетом коэффициента
  level_max INTEGER -- Максимальный уровень развертывания
)
AS
BEGIN
  DECLARE @a_level INTEGER
  SET @a_level = 1
  DECLARE @a_links TABLE (c_child_id INT, c_dse_id INT, c_quantity FLOAT, c_quantity_ratio FLOAT, c_level INT)

  -- Ввод самого родительского объекта
  INSERT INTO @a_links(c_child_id, c_dse_id, c_quantity, c_quantity_ratio, c_level)
  VALUES (@object_id, @object_id, @quantity, @quantity, @a_level)

  WHILE (@@ROWCOUNT>0)
  BEGIN
    SET @a_level = @a_level + 1
    -- Заполнение составом
    INSERT INTO @a_links(c_child_id, c_dse_id, c_quantity, c_quantity_ratio, c_level)
    SELECT l.child_id,
    CASE WHEN p.part_type_id IN ('detail', 'assembly', 'device')
      THEN a.c_child_id
      ELSE a.c_dse_id END
    ,
    l.quantity*a.c_quantity,
    CASE WHEN l.link_class = 'tpresource'
      THEN l.quantity*a.c_quantity_ratio*COALESCE(l.ratio, 1)
      ELSE l.quantity*a.c_quantity*COALESCE(l.ratio, 1) END
    ,
    @a_level
    FROM @a_links a
    INNER JOIN core_link l ON (l.parent_id = a.c_child_id) AND (l.dlt_sess = 0)
    INNER JOIN pdm_partobject p ON (p.entity_ptr_id = a.c_child_id)
    WHERE (a.c_level = @a_level - 1)
    AND ((@link_classes IS NULL) OR (l.link_class IN (
      SELECT value FROM STRING_SPLIT(@link_classes, ', ')
      )))
  END

  INSERT INTO @res_table(child_id, dse_id, quantity, quantity_ratio, level_max)
  SELECT p.c_child_id, p.c_dse_id, SUM(p.c_quantity), SUM(p.c_quantity_ratio), @a_level
  FROM @a_links p
  GROUP BY p.c_child_id, p.c_dse_id
  RETURN
END