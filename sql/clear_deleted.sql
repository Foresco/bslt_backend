-- Физическое удаление удаленныйх записей
CREATE FUNCTION fn_deleted_clear(
  IN _dlt_sess_id INTEGER -- Самая свежая удалившая сессия
) RETURNS INTEGER
AS $$
BEGIN
  START TRANSACTION -- Все в рамках одной транзакции, так как данные взаимосвязаны
  -- Удаление связей
  -- Удаление связей состава

  -- Удаление связей Изготавливается из

  -- Удаление основы связей
  DELETE FROM core_links WHERE (dlt_sess_id <= _dlt_sess_id);

  -- Удаление объектов состава

  -- Удаление сущностей

  -- Удаление ролей


  COMMIT;
END $$
LANGUAGE plsql;