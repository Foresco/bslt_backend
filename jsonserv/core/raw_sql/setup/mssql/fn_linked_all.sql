CREATE FUNCTION fn_linked_all_device(
  @object_id INTEGER, -- Идентификатор родительского объекта
  @quantity FLOAT, -- Количество объекта родителя
  @link_classes CHARACTER VARYING -- Список классов связей для отбора
) RETURNS @res_table TABLE
(
  top_id INTEGER, -- Идентификатор изделия
  child_id INTEGER, -- Идентификатор входящего объекта
  quantity FLOAT, -- Количество входящих
  quantity_ratio FLOAT, -- Количество входящих с учетом коэффициента
  level_max INTEGER -- Максимальный уровень развертывания
)
AS
BEGIN
  DECLARE @a_level INTEGER
  SET @a_level = 1
  DECLARE @a_links TABLE (c_top_id INT, c_child_id INT, c_quantity FLOAT, c_quantity_ratio FLOAT, c_level INT)

  -- Ввод состава самого родительского объекта
  INSERT INTO @a_links(c_top_id, c_child_id, c_quantity, c_quantity_ratio, c_level)
  SELECT @object_id, l.child_id, l.quantity*@quantity, l.quantity*@quantity, @a_level
  FROM core_link l WHERE (l.parent_id = @object_id) AND (l.dlt_sess = 0)
  AND ((@link_classes IS NULL) OR (l.link_class IN (
    SELECT value FROM STRING_SPLIT(@link_classes, ', ')
    )))

  WHILE (@@ROWCOUNT>0)
  BEGIN
    SET @a_level = @a_level + 1
    -- Заполнение составом
    INSERT INTO @a_links(c_top_id, c_child_id, c_quantity, c_quantity_ratio, c_level)
    SELECT a.c_top_id, l.child_id, l.quantity*a.c_quantity,
    CASE WHEN l.link_class = 'tpresource'
      THEN l.quantity*a.c_quantity_ratio*COALESCE(l.ratio, 1)
      ELSE l.quantity*a.c_quantity*COALESCE(l.ratio, 1) END
    ,
    @a_level
    FROM @a_links a
    INNER JOIN core_link l ON (l.parent_id = a.c_child_id) AND (l.dlt_sess = 0)
    WHERE (a.c_level = @a_level - 1)
    AND ((@link_classes IS NULL) OR (l.link_class IN (
      SELECT value FROM STRING_SPLIT(@link_classes, ', ')
      )))
  END

  INSERT INTO @res_table(top_id, child_id, quantity, quantity_ratio, level_max)
  SELECT p.c_top_id, p.c_child_id, SUM(p.c_quantity), SUM(p.c_quantity_ratio), @a_level
  FROM @a_links p
  GROUP BY p.c_top_id, p.c_child_id
  RETURN
END