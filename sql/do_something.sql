-- Удаление повторов архивных документов с переносом связей
CREATE OR REPLACE FUNCTION doSomething(
  IN _edt_sess INT -- идентификатор сессии
) RETURNS INT
AS $$
DECLARE
  a_counter INT := 0; -- Счетчик
  a_target INT; -- Идентификатор документа хорошего
  a_source INT; -- Идентификатор документа плохого
BEGIN
  -- Получение всех задвоений
  FOR a_target, a_source IN 
  SELECT max(id), min(id)
  FROM core_entity
  WHERE (type_key_id = 'arcdocument') AND (dlt_sess = 0)
  GROUP BY head_key
  HAVING COUNT(*)>1
  LOOP
    -- Перенос файлов
    UPDATE docarchive_entitydocumentversion
    SET entity_id = a_target
    WHERE (entity_id = a_source);
    
    -- Перенос касается
    UPDATE core_link 
    SET parent_id = a_target
    WHERE (link_class = 'arcdocumentobject')
    AND (parent_id = a_source);
    
    -- Перенос форматов
    UPDATE pdm_partobjectformat
    SET part_object_id = a_target
    WHERE (part_object_id = a_source);
	
	-- Перенос состава загрузок
    UPDATE docarchive_uploadarcdoc
    SET arc_doc_id = a_target
    WHERE (arc_doc_id = a_source);
    
    -- Удаление документа
    UPDATE core_entity
    SET dlt_sess = _edt_sess
    WHERE (id = a_source);
    
    a_counter := a_counter + 1;
  END LOOP;
  RETURN a_counter;
END $$ LANGUAGE plpgsql;

-- Удаление повторов объектов с переносом связей
CREATE OR REPLACE FUNCTION doSomething(
  IN _edt_sess INT -- идентификатор сессии
) RETURNS INT
AS $$
DECLARE
  a_counter INT := 0; -- Счетчик
  a_target INT; -- Идентификатор документа хорошего
  a_source INT; -- Идентификатор документа плохого
BEGIN
  -- Получение всех задвоений
  FOR a_target, a_source IN
  SELECT max(id), min(id)
  FROM core_entity ce
  INNER JOIN pdm_partobject pp ON (pp.entity_ptr_id = ce.id)
  WHERE (ce.dlt_sess = 0) AND (pp.prod_order_id IS NOT NULL)
  -- AND (ce.id IN (712443, 710689))
  GROUP BY head_key, pp.prod_order_id HAVING count(*)>1
  LOOP
    -- Перенос файлов
    UPDATE docarchive_entitydocumentversion
    SET entity_id = a_target
    WHERE (entity_id = a_source)
    AND (dlt_sess = 0)
    AND NOT EXISTS ( -- Защита от повторов
      SELECT 1 FROM docarchive_entitydocumentversion t
      WHERE t.document_version_id = docarchive_entitydocumentversion.document_version_id
      AND t.entity_id = a_target
      AND (t.dlt_sess = 0)
    );

    -- Удаление оставшихся связей с файлами
    UPDATE docarchive_entitydocumentversion
    SET dlt_sess = _edt_sess
    WHERE (entity_id = a_source)
    AND (dlt_sess = 0);

    -- Перенос связей с потомками
    UPDATE core_link
    SET parent_id = a_target
    WHERE (parent_id = a_source)
    AND (dlt_sess = 0)
    AND NOT EXISTS ( -- Защита от повторов
      SELECT 1 FROM core_link t
      WHERE t.child_id = core_link.child_id
      AND t.parent_id = a_target
      AND t.link_class = core_link.link_class
      AND (t.dlt_sess = 0)
    );

    -- Перенос связей с родителями
    UPDATE core_link
    SET child_id = a_target
    WHERE (child_id = a_source)
    AND NOT EXISTS ( -- Защита от повторов
      SELECT 1 FROM core_link t
      WHERE t.parent_id = core_link.parent_id
      AND t.child_id = a_target
      AND t.link_class = core_link.link_class
      AND (t.dlt_sess = 0)
    );

    -- Удаление оставшихся связей с родителями
    UPDATE core_link
    SET dlt_sess = _edt_sess
    WHERE (child_id = a_source) AND (dlt_sess = 0);

    -- Перенос форматов
    UPDATE pdm_partobjectformat
    SET part_object_id = a_target
    WHERE (part_object_id = a_source)
    AND (dlt_sess = 0)
    AND NOT EXISTS ( -- Защита от повторов
      SELECT 1 FROM pdm_partobjectformat t
      WHERE t.format_id = pdm_partobjectformat.format_id
      AND t.part_object_id = a_target
      AND (t.dlt_sess = 0)
    );

    -- Удаление оставшихся связей состава
    UPDATE core_link
    SET dlt_sess = _edt_sess
    WHERE (parent_id = a_source) AND (dlt_sess = 0);

    -- Удаление объекта
    UPDATE core_entity
    SET dlt_sess = _edt_sess
    WHERE (id = a_source);

    a_counter := a_counter + 1;
  END LOOP;
  RETURN a_counter;
END $$ LANGUAGE plpgsql;

-- Удаление повторов связей
CREATE OR REPLACE FUNCTION doSomething(
  IN _edt_sess INT -- идентификатор сессии
) RETURNS INT
AS $$
DECLARE
  a_counter INT := 0; -- Счетчик
  a_link_id INT;
BEGIN
  -- Получение всех задвоений
  FOR a_link_id IN
  SELECT min(id)
  FROM core_link cl
  WHERE dlt_sess = 0
  GROUP BY parent_id, child_id, link_class
  HAVING count(*)>1
  LOOP
    -- Удаление связи
    UPDATE core_link
    SET dlt_sess = _edt_sess
    WHERE (id = a_link_id);

    a_counter := a_counter + 1;
  END LOOP;
  RETURN a_counter;
END $$ LANGUAGE plpgsql;

-- Удаление повторов со стадиями
CREATE OR REPLACE FUNCTION dosomething(_edt_sess integer)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
  a_counter INT := 0; -- Счетчик
  a_target INT; -- Идентификатор хорошего
  a_source INT; -- Идентификатор плохого
BEGIN
  -- Получение всех задвоений
  FOR a_target, a_source IN
  SELECT c.id, cw.id
  FROM core_entity c
  INNER JOIN pdm_partobject p ON (p.entity_ptr_id = c.id) AND (p.prod_order_id IS NULL) -- не является частью заказа
  INNER JOIN core_entity cw ON (cw.code = c.code) AND (cw.parent_id IS NULL) AND (cw.dlt_sess = 0)
  INNER JOIN pdm_partobject pw ON (pw.entity_ptr_id = cw.id) AND (pw.prod_order_id IS NULL) -- не является частью заказа
  WHERE c.parent_id = 92743 -- ТП
  -- 92742 -- РКД
  AND c.type_key_id = 'partobject'
  -- AND p.part_type_id IN ('assembly', 'detail')
  AND p.part_type_id = pw.part_type_id
  AND c.dlt_sess = 0
  ORDER BY c.code
  LOOP
    -- Изменение вхождений
    UPDATE core_link
    SET child_id = a_target, edt_sess = _edt_sess
    WHERE (child_id = a_source) AND (dlt_sess = 0)
    AND NOT EXISTS ( -- Защита от повторов
      SELECT 1 FROM core_link t
      WHERE t.parent_id = core_link.parent_id
      AND t.child_id = a_target
      AND t.link_class = core_link.link_class
      AND (t.dlt_sess = 0)
    );

    -- Удаление оставшихся связей
    UPDATE core_link
    SET dlt_sess = _edt_sess
    WHERE (child_id = a_source) AND (dlt_sess = 0);

    -- Изменение исходников у позиций в заказах
    UPDATE pdm_partobject SET origin_id = a_target
    WHERE (origin_id = a_source);

    -- Замена связей с документами
    UPDATE docarchive_entitydocumentversion
    SET entity_id = a_target, edt_sess = _edt_sess
    WHERE (entity_id = a_source) AND (dlt_sess = 0)
    AND NOT EXISTS ( -- Защита от повторов
      SELECT 1 FROM docarchive_entitydocumentversion t
      WHERE t.document_version_id = docarchive_entitydocumentversion.document_version_id
      AND t.entity_id = a_target
      AND (t.dlt_sess = 0)
    );

    -- Удаление оставшихся связей с документами
    UPDATE docarchive_entitydocumentversion
    SET dlt_sess = _edt_sess
    WHERE (entity_id = a_source) AND (dlt_sess = 0);

   -- Замена связей со свойствами
    UPDATE core_propertyvalue
    SET entity_id = a_target, edt_sess = _edt_sess
    WHERE (entity_id = a_source) AND (dlt_sess = 0)
    AND NOT EXISTS ( -- Защита от повторов
      SELECT 1 FROM core_propertyvalue t
      WHERE t.property_id = core_propertyvalue.property_id
      AND t.entity_id = a_target
      AND (t.dlt_sess = 0)
    );

    -- Удаление оставшихся связей со свойствами
    UPDATE core_propertyvalue
    SET dlt_sess = _edt_sess
    WHERE (entity_id = a_source) AND (dlt_sess = 0);

    -- Замена базовых объектов в исполнениях
    UPDATE pdm_rendition SET parent_id = a_target, edt_sess = _edt_sess
    WHERE (parent_id = a_source) AND (dlt_sess = 0);

    -- Замена исполнений
    UPDATE pdm_rendition SET rendition_id = a_target, edt_sess = _edt_sess
    WHERE (rendition_id = a_source) AND (dlt_sess = 0)
    AND NOT EXISTS ( -- Защита от повторов
      SELECT 1 FROM pdm_rendition WHERE (rendition_id = a_target) AND (dlt_sess = 0)
    );

    -- Замена в ролях
    UPDATE pdm_designrole
    SET subject_id = a_target, edt_sess = _edt_sess
    WHERE (subject_id = a_source) AND (dlt_sess = 0)
    AND NOT EXISTS ( -- Защита от повторов
      SELECT 1 FROM pdm_designrole t
      WHERE t.role_id = pdm_designrole.role_id
      AND t.subject_id = a_target
      AND (t.dlt_sess = 0)
    );

    -- Замена в идентификаторах
    UPDATE exchange_externalid SET internal_id = a_target
    WHERE (internal_id = a_source)
    AND NOT EXISTS ( -- Защита от повторов
      SELECT 1 FROM exchange_externalid WHERE (internal_id = a_target)
    );

    -- Замена в метках
    UPDATE core_entitylabel SET entity_id = a_target
    WHERE (entity_id = a_source)
    AND NOT EXISTS ( -- Защита от повторов
      SELECT 1 FROM core_entitylabel WHERE (entity_id = a_target)
    );

    -- Удаление связей, где объект родитель
    UPDATE core_link
    SET dlt_sess = _edt_sess
    WHERE (parent_id = a_source) AND (dlt_sess = 0);

    -- Удаление исполнений
    UPDATE pdm_rendition SET dlt_sess = _edt_sess
    WHERE (rendition_id = a_source) AND (dlt_sess = 0);

    -- Удаление объектов
    UPDATE core_entity
    SET dlt_sess = _edt_sess
    WHERE (id = a_source);

    a_counter := a_counter + 1;
  END LOOP;
  RETURN a_counter;
END $function$
;

-- Восстановление ошибочно удаленных объектов
CREATE OR REPLACE FUNCTION dosomething(_edt_sess integer)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
  a_counter INT := 0; -- Счетчик
  a_target INT; -- Идентификатор хорошего
  a_source INT; -- Идентификатор плохого
BEGIN
  -- Получение всех задвоений
  FOR a_source, a_target IN
  SELECT e.id, ee.id
  FROM fn_linked_all(819507, 1, NULL) a
  INNER JOIN core_entity e ON (e.id = a.child_id) AND e.parent_id = 92743 -- ТП
  INNER JOIN core_entity ee ON (ee.code = e.code) AND ee.dlt_sess = 19586
  LOOP
    -- Замена объекта
    PERFORM pr_replace_new (
      a_source, -- Что заменить
      a_target, -- Чем заменить
      _edt_sess -- Транзакция, изменения по которой отменяются
    );
    -- Замена в ролях
    UPDATE pdm_designrole
    SET subject_id = a_target, edt_sess = _edt_sess
    WHERE (subject_id = a_source) AND (dlt_sess = 0)
    AND NOT EXISTS ( -- Защита от повторов
      SELECT 1 FROM pdm_designrole t
      WHERE t.role_id = pdm_designrole.role_id
      AND t.subject_id = a_target
      AND (t.dlt_sess = 0)
    );

    a_counter := a_counter + 1;
  END LOOP;
  RETURN a_counter;
END $function$

-- Удаление стадии ТП
CREATE OR REPLACE FUNCTION dosomething(_edt_sess integer)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
  a_counter INT := 0; -- Счетчик
  a_id INT;
BEGIN
  FOR a_id IN
  SELECT e.id
  FROM fn_linked_all(819507, 1, NULL) a
  INNER JOIN core_entity e ON (e.id = a.child_id) AND e.parent_id = 92743
  LOOP
    UPDATE core_entity SET parent_id = NULL, edt_sess = _edt_sess WHERE id = a_id;

    INSERT INTO core_historylog(table_name, object_id, changes, edt_sess_id)
    VALUES ('partobject', a_id, '{"parent": ""}', _edt_sess);

    a_counter := a_counter + 1;
  END LOOP;
  RETURN a_counter;
END $function$

-- Замена ошибочно созданных материалов и стандартных изделий в составе заказов
CREATE OR REPLACE FUNCTION doSomething(
  IN _edt_sess INT -- идентификатор сессии
) RETURNS INT
AS $$
DECLARE
  a_counter INT := 0; -- Счетчик
  a_target INT; -- Идентификатор объекта хорошего
  a_source INT; -- Идентификатор объекта плохого
BEGIN
  -- Получение всех задвоений
  FOR a_target, a_source IN
  SELECT pp.origin_id, ce.id
  FROM core_entity ce
  INNER JOIN pdm_partobject pp ON (pp.entity_ptr_id = ce.id)
  -- Выбираем все объекты типа материал, стандартное изделие, прочее изделие, экземпляр сортамента
  AND (pp.part_type_id IN ('material', 'standart', 'other', 'exemplar'))
  INNER JOIN core_entity ceo ON (ceo.id = pp.origin_id) AND (ceo.code = ce.code) AND (ceo.dlt_sess = 0)
  WHERE (ce.dlt_sess = 0) AND
  (pp.origin_id IS NOT NULL) AND (pp.prod_order_id IS NOT NULL) -- Имеющие ссылку на исходный объект и на заказ
  AND NOT (pp.source_id = 2) -- Имеющие источник поступления отличный от Самостоятельное изготовление
  -- AND pp.origin_id = 17988
  LOOP
    -- Перенос файлов
    UPDATE docarchive_entitydocumentversion
    SET entity_id = a_target
    WHERE (entity_id = a_source);

    -- Заменяем копию оригиналом
    -- Перенос связей
    UPDATE core_link
    SET parent_id = a_target
    WHERE (parent_id = a_source);

    UPDATE core_link
    SET child_id = a_target
    WHERE (child_id = a_source);

    -- Удаление копии
    UPDATE core_entity
    SET dlt_sess = _edt_sess
    WHERE (id = a_source);

    -- Устанавливаем у оригинала источник поступления Покупка
    -- Записываем в историю
    INSERT INTO core_historylog(table_name, object_id, changes, edt_sess_id)
    SELECT 'partobject', entity_ptr_id, '{"source": 3}', _edt_sess
    FROM pdm_partobject WHERE entity_ptr_id = a_target AND source_id IS DISTINCT FROM 3;

    UPDATE pdm_partobject SET source_id = 3 WHERE entity_ptr_id = a_target AND source_id IS DISTINCT FROM 3;

    a_counter := a_counter + 1;
  END LOOP;
  RETURN a_counter;
END $$ LANGUAGE plpgsql;
