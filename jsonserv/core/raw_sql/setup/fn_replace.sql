CREATE FUNCTION fn_replace(
  IN _source_id INTEGER,
  IN _target_id INTEGER,
  IN _edt_sess INTEGER
) RETURNS INTEGER
AS $$
BEGIN
  -- Изменение вхождений
  UPDATE core_link
  SET child_id = _target_id, edt_sess = _edt_sess
  WHERE (child_id = _source_id) AND (dlt_sess = 0)
  AND NOT EXISTS ( -- Защита от повторов
    SELECT 1 FROM core_link t
    WHERE t.parent_id = core_link.parent_id
    AND t.child_id = _target_id
    AND t.link_class = core_link.link_class
    AND (t.dlt_sess = 0)
  );

  -- Удаление оставшихся связей
  UPDATE core_link
  SET dlt_sess = _edt_sess
  WHERE (child_id = _source_id) AND (dlt_sess = 0);

  -- Изменение исходников у позиций в заказах
  UPDATE pdm_partobject SET origin_id = _target_id
  WHERE (origin_id = _source_id);

  -- Замена связей с документами
  UPDATE docarchive_entitydocumentversion
  SET entity_id = _target_id, edt_sess = _edt_sess
  WHERE (entity_id = _source_id) AND (dlt_sess = 0)
  AND NOT EXISTS ( -- Защита от повторов
    SELECT 1 FROM docarchive_entitydocumentversion t
    WHERE t.document_version_id = docarchive_entitydocumentversion.document_version_id
    AND t.entity_id = _target_id
    AND (t.dlt_sess = 0)
  );

  -- Удаление оставшихся связей с документами
  UPDATE docarchive_entitydocumentversion
  SET dlt_sess = _edt_sess
  WHERE (entity_id = _source_id) AND (dlt_sess = 0);

  -- Замена связей со свойствами
  UPDATE core_propertyvalue
  SET entity_id = _target_id, edt_sess = _edt_sess
  WHERE (entity_id = _source_id) AND (dlt_sess = 0)
  AND NOT EXISTS ( -- Защита от повторов
    SELECT 1 FROM core_propertyvalue t
    WHERE t.property_id = core_propertyvalue.property_id
    AND t.entity_id = _target_id
    AND (t.dlt_sess = 0)
  );

  -- Удаление оставшихся связей со свойствами
  UPDATE core_propertyvalue
  SET dlt_sess = _edt_sess
  WHERE (entity_id = _source_id) AND (dlt_sess = 0);

  -- Замена базовых объектов в исполнениях
  UPDATE pdm_rendition SET parent_id = _target_id, edt_sess = _edt_sess
  WHERE (parent_id = _source_id) AND (dlt_sess = 0);

  -- Замена исполнений
  UPDATE pdm_rendition SET rendition_id = _target_id, edt_sess = _edt_sess
  WHERE (rendition_id = _source_id) AND (dlt_sess = 0)
  AND NOT EXISTS ( -- Защита от повторов
    SELECT 1 FROM pdm_rendition WHERE (rendition_id = _target_id) AND (dlt_sess = 0)
  );

  -- Замена в ролях
  UPDATE pdm_designrole
  SET subject_id = _target_id, edt_sess = _edt_sess
  WHERE (subject_id = _source_id) AND (dlt_sess = 0)
  AND NOT EXISTS ( -- Защита от повторов
    SELECT 1 FROM pdm_designrole t
    WHERE t.role_id = pdm_designrole.role_id
    AND t.subject_id = _target_id
    AND (t.dlt_sess = 0)
  );

  -- Замена в идентификаторах
  UPDATE exchange_externalid SET internal_id = _target_id
  WHERE (internal_id = _source_id)
  AND NOT EXISTS ( -- Защита от повторов
    SELECT 1 FROM exchange_externalid WHERE (internal_id = _target_id)
  );

  -- Замена в метках
  UPDATE core_entitylabel SET entity_id = _target_id
  WHERE (entity_id = _source_id)
  AND NOT EXISTS ( -- Защита от повторов
    SELECT 1 FROM core_entitylabel WHERE (entity_id = _target_id)
  );

  RETURN 1;
END $$ LANGUAGE plpgsql;