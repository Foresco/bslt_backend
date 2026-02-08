-- Функция вычисления количества вхождения объекта в объект
CREATE FUNCTION fn_quantity (
  @parent_id INT, -- Идентификатор родителя
  @child_id INT, -- Идентификатор потомка
  @quantity FLOAT -- Количество родителей
) RETURNS FLOAT
-- Варианты значений: 0 - входит с нулевым количеством, NULL - не входит
BEGIN
  DECLARE @return FLOAT;
  IF (@parent_id = @child_id) -- Вхождение в самого себя
  BEGIN
    SET @return = @quantity
  END
  ELSE
  BEGIN
    SELECT @return = SUM(a.quantity)
    FROM dbo.fn_linked_all(@parent_id, @quantity, NULL) a
    WHERE (a.child_id = @child_id)
  END
  RETURN @return
END