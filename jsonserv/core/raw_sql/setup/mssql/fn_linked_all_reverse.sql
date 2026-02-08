CREATE OR ALTER FUNCTION fn_linked_all_reverse(
  @object_id INT, -- Идентификатор родительского объекта
  @quantity FLOAT, -- Количество объекта родителя
  @link_classes CHARACTER VARYING -- Список классов связей для отбора
) RETURNS @res_table TABLE
(
  parent_id INT, -- Идентификатор родительского объекта
  top_id INT,  -- Идентификатор объекта верхнего уровня
  quantity FLOAT, -- Количество входящих
  quantity_ratio FLOAT, -- Количество входящих с учетом коэффициента
  max_level INT -- Уровень вхождения максимальный
)
AS
BEGIN
  DECLARE @a_level INT 
  SET @a_level = 1

  -- Таблицы для временных выборок
  DECLARE @a_links TABLE (c_parent_id INT, c_top_id INT, c_child_id INT, c_quantity FLOAT, c_quantity_ratio FLOAT, c_level INT)

  -- Ввод ввод состава первого уровня
  INSERT INTO @a_links(c_parent_id, c_top_id, c_child_id, c_quantity, c_quantity_ratio, c_level)
  SELECT l.parent_id, l.parent_id, l.child_id, l.quantity*@quantity, l.quantity*@quantity*COALESCE(l.ratio, 1), @a_level
  FROM core_link l
  WHERE (l.child_id = @object_id) AND (l.dlt_sess = 0)
  AND ((@link_classes IS NULL) OR (l.link_class IN (
    SELECT value FROM STRING_SPLIT(@link_classes, ', ')
  )))

  WHILE (@@ROWCOUNT>0) -- AND (@a_level < 500)
  BEGIN
    SET @a_level = @a_level + 1
    -- Заполнение составом
    INSERT INTO @a_links(c_parent_id, c_top_id, c_child_id, c_quantity, c_quantity_ratio, c_level)
    SELECT a.c_parent_id, l.parent_id, l.child_id, l.quantity*a.c_quantity, l.quantity*a.c_quantity*COALESCE(l.ratio, 1), @a_level
    FROM @a_links a
    INNER JOIN core_link l ON (l.child_id = a.c_top_id) AND (l.dlt_sess = 0)
    WHERE (a.c_level = @a_level - 1)
    AND ((@link_classes IS NULL) OR (l.link_class IN (
      SELECT value FROM STRING_SPLIT(@link_classes, ', ')
    )))
  END

  INSERT INTO @res_table(parent_id, top_id, quantity, quantity_ratio, max_level)
  SELECT p.c_parent_id, p.c_top_id, SUM(p.c_quantity), SUM(p.c_quantity_ratio), MAX(p.c_level)
  FROM @a_links p
  WHERE p.c_top_id NOT IN (SELECT DISTINCT c_child_id FROM @a_links) -- Только объекты, которые сами никуда не входят
  GROUP BY p.c_parent_id, p.c_top_id
  RETURN
END
