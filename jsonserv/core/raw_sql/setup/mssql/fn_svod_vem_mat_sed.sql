CREATE OR ALTER FUNCTION fn_svod_vem_mat_sed(
  @object_id INTEGER, -- Идентификатор родительского объекта
  @quantity FLOAT, -- Количество объекта родителя
  @link_classes CHARACTER VARYING -- Список классов связей для отбора
) RETURNS @res_table TABLE
(
  child_id INTEGER, -- Идентификатор входящего объекта
  quantity FLOAT, -- Количество входящих
  quantity_ratio FLOAT, -- Количество входящих с учетом коэффициента
  replaced_id INT -- Идентификатор заменяемой строки
)
AS
BEGIN
  DECLARE @a_level INTEGER
  SET @a_level = 1
  DECLARE @a_links TABLE (c_child_id INT, c_quantity FLOAT, c_quantity_ratio FLOAT, c_replaced_id INT DEFAULT NULL, c_level INT)

  -- Ввод самого родительского объекта
  INSERT INTO @a_links(c_child_id, c_quantity, c_quantity_ratio, c_level)
  VALUES (@object_id, @quantity, @quantity, @a_level)

  WHILE (@@ROWCOUNT>0)
  BEGIN
    SET @a_level = @a_level + 1
    -- Заполнение составом
    INSERT INTO @a_links(c_child_id, c_quantity, c_quantity_ratio, c_replaced_id, c_level)
    SELECT l.child_id, l.quantity*a.c_quantity,
    CASE WHEN l.link_class = 'tpresource'
      THEN l.quantity*a.c_quantity_ratio*COALESCE(l.ratio, 1) 
      ELSE l.quantity*a.c_quantity*COALESCE(l.ratio, 1) END
    ,
	tpr.replaced_id,
    @a_level
    FROM @a_links a
    INNER JOIN core_link l ON (l.parent_id = a.c_child_id) AND (l.dlt_sess = 0)
	LEFT JOIN pdm_tpresource rs ON (rs.link_ptr_id = l.id)
	LEFT JOIN pdm_tprow tpr ON (tpr.id = rs.tp_row_id)
    WHERE (a.c_level = @a_level - 1)
    AND ((@link_classes IS NULL) OR (l.link_class IN (
      SELECT value FROM STRING_SPLIT(@link_classes, ', ')
      )))
  END

  INSERT INTO @res_table(child_id, quantity, quantity_ratio, replaced_id)
  SELECT p.c_child_id, SUM(p.c_quantity), SUM(p.c_quantity_ratio), MAX(c_replaced_id)
  FROM @a_links p
  GROUP BY p.c_child_id
  RETURN
END