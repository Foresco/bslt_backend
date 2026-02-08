CREATE OR REPLACE FUNCTION fn_create_order_part (
  IN _origin_id INT, -- Идентификатор объекта-источника
  IN _prod_order_id INT, -- Идентификатор заказа
  IN _crtd_sess_id INT -- Идентификатор сессии
) RETURNS INT
-- Возвращает идентификатор найденного или созданного объекта
AS $$
DECLARE
  a_object_id INT; -- Идентификатор объекта
  a_id INT; -- Идентификатор строки
  a_child_id INT; -- Идентификатор входящего
  a_new_child_id INT; -- Идентификатор нового входящего
  a_new_link_id INT; -- Идентификатор новой связи
BEGIN
  -- Поиск уже существующего объекта
  SELECT e.id INTO a_object_id
  FROM pdm_partobject p
  INNER JOIN core_entity e ON (e.id = p.entity_ptr_id) AND (e.dlt_sess = 0)
  WHERE ((p.origin_id = _origin_id) AND (p.prod_order_id = _prod_order_id)) -- Объект из заказа
  OR ((p.entity_ptr_id = _origin_id) AND (p.source_id = 3)) -- Покупной объект
  LIMIT 1;

  IF FOUND THEN -- Если найден - возвращаем
    RETURN a_object_id;
  END IF;

  -- Создаем entity
  INSERT INTO core_entity(code, auto_code, description, head_key, rating, guid, parent_id, type_key_id, group_id, crtd_sess_id, edt_sess, dlt_sess)
  SELECT code, auto_code, description, head_key, 0,
  uuid_in(md5(random()::text || clock_timestamp()::text)::cstring), -- Генерация guid
  parent_id, type_key_id, group_id, _crtd_sess_id, 0, 0
  FROM core_entity WHERE (id = _origin_id);

  a_object_id := currval('core_entity_id_seq');

  -- Создаем partobject
  INSERT INTO pdm_partobject(entity_ptr_id, title, abbr, is_top, nom_code, weight, surface, litera_id,
  origin_id, part_type_id, preference_id, prod_order_id, source_id, state_id, unit_id, weight_unit_id)
  SELECT a_object_id, title, abbr, is_top, nom_code, weight, surface, litera_id,
  _origin_id, part_type_id, preference_id, _prod_order_id, source_id, state_id, unit_id, weight_unit_id
  FROM pdm_partobject WHERE (entity_ptr_id = _origin_id);

  -- Копируем состав объекта
  FOR a_id, a_child_id IN SELECT id, child_id
  FROM core_link WHERE (parent_id = _origin_id) AND (link_class = 'partlink') AND (dlt_sess = 0) LOOP
    -- Создание нового объекта
    SELECT fn_create_order_part ( a_child_id, _prod_order_id, _crtd_sess_id) INTO a_new_child_id;

    -- Создание связи core_link
    INSERT INTO core_link (parent_id, child_id, quantity, comment, link_class, crtd_sess_id, edt_sess, dlt_sess)
    SELECT a_object_id, a_new_child_id, quantity, comment, link_class, _crtd_sess_id, edt_sess, dlt_sess
    FROM core_link WHERE (id = a_id);
    a_new_link_id := currval('core_link_id_seq');
    -- Создание связи pdm_partlink
    INSERT INTO pdm_partlink (link_ptr_id, draft_zone, position, reg_quantity, to_replace, first_use,	not_buyed, section_id, unit_id)
    SELECT a_new_link_id, draft_zone, position, reg_quantity, to_replace, first_use,	not_buyed, section_id, unit_id
    FROM pdm_partlink WHERE (link_ptr_id = a_id);
  END LOOP;

  -- Копирование конструкторского материала
  INSERT INTO core_link (parent_id, child_id, link_class, crtd_sess_id, edt_sess, dlt_sess)
  SELECT a_object_id, child_id, link_class, _crtd_sess_id, edt_sess, dlt_sess
  FROM core_link WHERE (parent_id = _origin_id) AND (link_class = 'designmater') AND (dlt_sess = 0);
  IF FOUND THEN
    a_new_link_id := currval('core_link_id_seq');
    INSERT INTO pdm_designmater(link_ptr_id) VALUES(a_new_link_id);
  END IF;

  -- Копирование ссылок на файлы
  INSERT INTO docarchive_entitydocumentversion (document_role, document_version_id, entity_id, old_version, crtd_sess_id, edt_sess, dlt_sess)
  SELECT document_role, document_version_id, a_object_id, old_version, _crtd_sess_id, edt_sess, dlt_sess
  FROM docarchive_entitydocumentversion
  WHERE (entity_id = _origin_id) AND (dlt_sess = 0) AND NOT (old_version);

  -- Копирование форматов
  INSERT INTO pdm_partobjectformat(part_object_id, format_id, order_num, list_quantity, crtd_sess_id, edt_sess, dlt_sess)
  SELECT a_object_id, format_id, order_num, list_quantity, crtd_sess_id, 0, 0
  FROM pdm_partobjectformat
  WHERE (part_object_id = _origin_id) AND (dlt_sess = 0);

  RETURN a_object_id;
END $$ LANGUAGE plpgsql;