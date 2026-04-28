-- Создание сессии пользователя перед импортом
INSERT INTO core_usersession(session_datetime, user_ip, user_id)
VALUES('2020-11-19 13:13:33', '127.0.0.1', 1);

-- Снятие активности у прошлых установок норм драгметаллов
UPDATE treasure_weightnorm SET is_active = False
WHERE norm_set_id IN
(
SELECT ws1.id
FROM (
SELECT ws.entity_id, ws.material_id, MIN(dd.date) AS dt
FROM treasure_weightnormset ws
INNER JOIN docarchive_documentversiondate dd ON (dd.document_version_id = ws.norm_document_id)
WHERE EXISTS (SELECT 1 FROM treasure_weightnorm wn WHERE (wn.norm_set_id = ws.id) AND wn.is_active = True)
GROUP BY ws.entity_id, ws.material_id
HAVING count(*)>1) a
INNER JOIN treasure_weightnormset ws1 ON (ws1.entity_id = a.entity_id) AND (ws1.material_id = a.material_id)
INNER JOIN docarchive_documentversiondate dd1 ON (dd1.document_version_id = ws1.norm_document_id)
AND (dd1.date = a.dt)
)

-- Установка активности у самых свежих установок норм драгметаллов
-- у которых нет активных записей
UPDATE treasure_weightnorm SET is_active = True
WHERE norm_set_id IN
(
SELECT ws1.id
FROM (
SELECT ws.entity_id, ws.material_id, MAX(dd.date) AS dt
FROM treasure_weightnormset ws
INNER JOIN docarchive_documentversiondate dd ON (dd.document_version_id = ws.norm_document_id)
INNER JOIN treasure_weightnorm wn ON (wn.norm_set_id = ws.id) 
GROUP BY ws.entity_id, ws.material_id
HAVING MAX(wn.is_active::int) = 0
) a
INNER JOIN treasure_weightnormset ws1 ON (ws1.entity_id = a.entity_id) AND (ws1.material_id = a.material_id)
INNER JOIN docarchive_documentversiondate dd1 ON (dd1.document_version_id = ws1.norm_document_id)
AND (dd1.date = a.dt)
)
;

-- Нормы драгметаллов
SELECT
cdse.code AS "ДСЕ",
pt.type_name AS "Тип ДСЕ",
po.title AS "Наименование",
d.doc_type AS "Тип документа",
cdoc.code AS "Документ",
dd.date AS "Дата утверждения",
cm.code AS "Лигатура или чистота",
pm.nom_code AS "Номенклатурный код",
wt.list_value AS "Вид нормы",
wn.norm AS "Значение",
wn.is_total AS "Сводная",
wns.remark AS "Примечание",
wn.begin_date AS "Дата_выгрузки",
wn.is_active AS "Активность"
FROM treasure_weightnorm wn
INNER JOIN treasure_weightnormset wns ON (wns.id = wn.norm_set_id)
INNER JOIN core_entity cdse ON (cdse.id = wns.entity_id)
INNER JOIN pdm_partobject po ON (po.entity_ptr_id = cdse.id)
INNER JOIN core_entity cm ON (cm.id = wns.material_id)
INNER JOIN pdm_partobject pm ON (pm.entity_ptr_id = cm.id)
INNER JOIN pdm_parttype pt ON (pt.type_key = po.part_type_id)
INNER JOIN docarchive_documentversion dv ON (dv.id = wns.norm_document_id)
INNER JOIN docarchive_document d ON (d.entity_ptr_id = dv.document_id)
INNER JOIN core_entity cdoc ON (cdoc.id = d.entity_ptr_id)
INNER JOIN docarchive_documentversiondate dd ON (dd.document_version_id = dv.id) AND (dd.date_type_id = 1)
INNER JOIN treasure_weightnormtype wt ON (wt.id = wn.norm_type_id)
LIMIT 1000;

-- Группы без родителей
SELECT id, code FROM core_entity WHERE type_key_id = 'classification' AND group_id IS NULL ORDER BY code DESC;

UPDATE core_entity set group_id = 616578 WHERE id IN (175, 176, 177);

-- Манипуляции панелями
INSERT INTO core_typepanel (type_key, in_list, in_single, start_params, panel_id)
SELECT 'other', in_list, in_single, start_params, panel_id
FROM core_typepanel ct WHERE type_key = 'complex';

INSERT INTO core_typepanel(type_key, in_list, in_single, edit_right_id, panel_id, view_right_id)
SELECT  'psib', in_list, in_single, edit_right_id, panel_id, view_right_id
FROM core_typepanel WHERE type_key = 'tpun';

INSERT INTO core_typepanel (type_key, in_list, in_single, panel_id)
VALUES
('assembly', false, true, 44),
('detail', false, true, 44),
('standart', false, true, 44),
('other', false, true, 44),
('order', false, true, 44);

-- Копирование набора полей
INSERT INTO core_formfield(form_name, field_name, order_num, caption, read_only, max_size, required, list_keys, default_value, hide_in_create, target)
SELECT 'psib', field_name, order_num, caption, read_only, max_size, required, list_keys, default_value, hide_in_create, target
FROM core_formfield WHERE form_name = 'tpun';

-- Вставка рейтинга разработчиков
INSERT INTO pdm_designerrating(role_id, designer_id, rating)
SELECT role_id, designer_id, count(*)
FROM pdm_designrole pd
WHERE dlt_sess = 0
GROUP BY role_id, designer_id

-- Обновление рейтинга
UPDATE pdm_designerrating b
SET rating = a.rating
FROM (
SELECT role_id,  designer_id, COUNT(*) AS rating
FROM
pdm_designrole pd
WHERE dlt_sess = 0
GROUP BY role_id, designer_id
) a
WHERE b.role_id = a.role_id AND b.designer_id = a.designer_id

-- Удаление исполнений, ссылающихся на удаленные объекты
UPDATE
pdm_rendition SET dlt_sess = a.dlt FROM (
SELECT pr.id AS rid, ce.dlt_sess AS dlt
FROM pdm_rendition pr
INNER JOIN core_entity ce ON (ce.id = pr.rendition_id)
WHERE ce.dlt_sess > 0 AND pr.dlt_sess = 0) a
WHERE id = a.rid

-- Удаление лишних прав
DELETE FROM auth_permission
WHERE codename in (
'add_measuresystem',
'delete_measuresystem',
'add_usagestatistic',
'change_usagestatistic',
'delete_usagestatistic',
'view_usagestatistic',
'add_systemuser',
'delete_systemuser',
'add_externallibrary',
'delete_externallibrary',
'add_gtcpackage',
'delete_gtcpackage',
'add_gtcpropertyclass',
'delete_gtcpropertyclass',
'add_maingtcpropertyclass',
'delete_maingtcpropertyclass',
'add_plibclass',
'delete_plibclass',
'add_plibproperty',
'delete_plibproperty',
'add_specificclass',
'delete_specificclass',
'add_toolclass',
'delete_toolclass',
'add_toolpreference',
'delete_toolpreference',
'add_toolproduct',
'delete_toolproduct',
'add_toolsource',
'delete_toolsource',
'add_toolstate',
'delete_toolstate',
'add_translateproperty',
'delete_translateproperty',
'add_vendorplibproperty',
'delete_vendorplibproperty',
'add_vendorplibclass',
'delete_vendorplibclass',
'add_toolpropsfile',
'delete_toolpropsfile',
'add_toolproductalias',
'delete_toolproductalias',
'add_toolobject',
'delete_toolobject',
'add_specificclassification',
'delete_specificclassification',
'add_propertysource',
'delete_propertysource',
'add_languagevalue',
'delete_languagevalue',
'add_gtcproperty',
'delete_gtcproperty',
'add_effectivity',
'delete_effectivity',
'add_price',
'delete_price',
'add_changetype',
'delete_changetype',
'add_noticereason',
'delete_noticereason',
'add_noticerecipient',
'delete_noticerecipient',
'add_noticereserve',
'delete_noticereserve',
'add_noticetype',
'delete_noticetype',
'add_partformat',
'delete_partformat',
'add_partlitera',
'delete_partlitera',
'add_partobject',
'delete_partobject',
'can_view_partobject',
'add_partpreference',
'delete_partpreference',
'add_partsource',
'delete_partsource',
'add_partstate',
'delete_partstate',
'add_paymentsystem',
'delete_paymentsystem',
'add_renditiontail',
'delete_renditiontail',
'add_role',
'delete_role',
'add_routestate',
'delete_routestate',
'add_section',
'delete_section',
'add_tprowlitera',
'delete_tprowlitera',
'add_tprowtype',
'delete_tprowtype',
'add_workrank',
'delete_workrank',
'add_designerrating',
'delete_designerrating',
'add_ordermaker',
'delete_ordermaker',
'add_prodorderlink',
'delete_prodorderlink',
'add_prodorderlinkworker',
'delete_prodorderlinkworker',
'add_prodorderstate',
'delete_prodorderstate',
'add_workshift',
'delete_workshift',
'add_workerreportconsist',
'delete_workerreportconsist',
'add_prodorder',
'delete_prodorder',
'add_weightnormtype',
'delete_weightnormtype',
'add_weightnormset',
'delete_weightnormset',
'add_weightnorm',
'delete_weightnorm',
'add_comment',
'delete_comment'
);

-- Назначение прав группе пользователей
INSERT INTO auth_group_permissions(group_id, permission_id)
SELECT 1, id FROM auth_permission ap WHERE codename in (
'view_classification', 'view_classification', 'view_designer', 'view_designmater', 'view_designrole', 'view_historylog', 'view_entity_list', 'view_noticelink', 'view_noticelink', 'view_notice', 'view_filedocument', 'view_incident', 'view_operation', 'view_place', 'view_userprofile', 'view_property', 'view_rendition', 'view_partlink', 'view_partlink', 'view_task', 'view_taskrefer', 'view_taskrefer', 'view_typesizemater', 'view_typesizesort', 'view_logentry', 'view_group', 'view_user', 'view_arcdocument', 'view_delivery', 'view_role', 'view_letter', 'view_taskuser', 'view_arcdocumentobject', 'view_noticerecipient', 'view_entity_props'
)
AND id NOT IN (476, 369, 385);

-- Удаление задвоений ссылок на файлы
UPDATE docarchive_entitydocumentversion
SET dlt_sess = 77
WHERE id IN (
SELECT MAX(id)
FROM docarchive_entitydocumentversion
WHERE (dlt_sess = 0)
GROUP BY entity_id, document_version_id
HAVING COUNT(*)>1
);

-- Удаление задвоений касающихся
UPDATE core_link
SET dlt_sess = 77
WHERE id IN (
SELECT MAX(id)
FROM core_link
WHERE (link_class = 'arcdocumentobject') AND (dlt_sess = 0)
GROUP BY parent_id, child_id
HAVING COUNT(*)>1
);

-- Удаление задвоений форматов
UPDATE pdm_partobjectformat
SET dlt_sess = 77
WHERE id IN (
SELECT MAX(id)
FROM pdm_partobjectformat
WHERE (dlt_sess = 0)
GROUP BY part_object_id, format_id, list_quantity
HAVING COUNT(*)>1
);

-- Удаление задвоений разработчиков
DELETE FROM pdm_designrole WHERE id IN (
SELECT max(id)
FROM pdm_designrole WHERE dlt_sess = 0
GROUP BY subject_id, role_id
HAVING count(*)>1);

-- Пользователи без профиля
SELECT u.username, u.last_name
FROM auth_user u
LEFT JOIN core_userprofile cu ON (cu.user_id = u.id)
WHERE cu.id IS NULL;

-- Вставка ролей в состав
INSERT INTO pdm_designrole(subject_id, role_id, designer_id, crtd_sess_id, edt_sess, dlt_sess)
SELECT a.child_id, 3, 1, 3441, 0, 0
FROM fn_linked_all(672943, 1, 'partlink') a
INNER JOIN pdm_partobject pp ON (pp.entity_ptr_id = a.child_id)
AND (pp.part_type_id IN ('assembly', 'detail'))
LEFT JOIN pdm_designrole pd ON (pd.subject_id = a.child_id)
AND (pd.role_id = 3) AND (pd.dlt_sess = 0)
WHERE pd.id IS NULL;

-- Добавление записей в историю
INSERT INTO core_historylog(table_name, object_id, changes, edt_sess_id)
SELECT 'partobject', ce.id, '{"source": 3}', 36198
FROM core_entity ce 
INNER JOIN pdm_partobject pp ON (pp.entity_ptr_id = ce.id)
WHERE ce.dlt_sess = 0
AND (pp.part_type_id IN ('standart', 'other', 'material', 'exemplar'))
AND (pp.source_id = 1);

-- Изменение источника поступления
UPDATE pdm_partobject SET source_id = 3 WHERE entity_ptr_id IN (
SELECT ce.id
FROM core_entity ce 
INNER JOIN pdm_partobject pp ON (pp.entity_ptr_id = ce.id)
WHERE ce.dlt_sess = 0
AND (pp.part_type_id IN ('standart', 'other', 'material', 'exemplar'))
AND (pp.source_id = 1)
);

-- Изменение редактирующей сессии
UPDATE core_entity SET edt_sess = 11468 WHERE id IN (
SELECT object_id
FROM core_historylog
WHERE edt_sess_id = 11468
)

-- Удаление повторов в истории
DELETE FROM core_historylog WHERE id IN (
SELECT MAX(id) 
FROM core_historylog 
GROUP BY table_name, object_id, changes, edt_sess_id
HAVING count(*)>1)

-- Изменение ЕИ массы
UPDATE pdm_partobject
SET weight_unit_id = 15
WHERE entity_ptr_id IN (
SELECT c.id
FROM pr_all_objects(802425, 1) a
INNER JOIN core_entity c ON (c.id = a.child_id)
INNER JOIN pdm_partobject p ON (p.entity_ptr_id = c.id)
WHERE c.type_key_id = 'partobject'
AND p.part_type_id IN ('assembly', 'detail')
AND c.dlt_sess = 0
AND (NOT (p.weight_unit_id = 15) OR p.weight_unit_id IS NULL)
)

INSERT INTO core_historylog(table_name, object_id, changes, edt_sess_id)
SELECT 'partobject', c.id, ch.changes, ch.edt_sess_id
FROM pr_all_objects(802425, 1) a
INNER JOIN core_entity c ON (c.id = a.child_id)
INNER JOIN pdm_partobject p ON (p.entity_ptr_id = c.id),
core_historylog ch
WHERE c.type_key_id = 'partobject'
AND p.part_type_id IN ('assembly', 'detail')
AND c.dlt_sess = 0
AND (NOT (p.weight_unit_id = 15) OR p.weight_unit_id IS NULL)
AND ch.edt_sess_id = 15375

-- Удаление объектов из состава заказа
-- Удаление объектов
UPDATE core_entity SET dlt_sess = 15415
WHERE id IN (
SELECT c.id
FROM pr_all_objects(806788, 1) a
INNER JOIN core_entity c ON (c.id = a.child_id)
INNER JOIN pdm_partobject p ON (p.entity_ptr_id = c.id) AND (p.prod_order_id = 705455)
WHERE c.type_key_id = 'partobject'
-- AND p.part_type_id IN ('assembly', 'detail')
AND c.dlt_sess = 0
)

-- Удаление родительских связей объектов
UPDATE core_link SET dlt_sess = 15415
WHERE parent_id IN (
SELECT c.id
FROM pr_all_objects(806788, 1) a
INNER JOIN core_entity c ON (c.id = a.child_id)
INNER JOIN pdm_partobject p ON (p.entity_ptr_id = c.id) AND (p.prod_order_id = 705455)
WHERE c.type_key_id = 'partobject'
-- AND p.part_type_id IN ('assembly', 'detail')
AND c.dlt_sess = 15415
)
AND dlt_sess = 0

-- Корректировка ссылок на маршруты у строк техпроцессов
UPDATE pdm_tprow
SET route_id = a.rid
FROM
(
SELECT tpr.id AS tid, rp.route_id AS rid FROM
pdm_routepoint rp
INNER JOIN pdm_tprow tpr ON (tpr.route_point_id = rp.id)
AND NOT rp.route_id = tpr.route_id
) a
WHERE id = a.tid;

-- Установка ссылок на маршруты у связей с заказами
UPDATE manufacture_prodorderlink
SET route_id = a.rid
FROM (
SELECT m.link_ptr_id AS mid, r.id AS rid
FROM core_link l
INNER JOIN manufacture_prodorderlink m ON m.link_ptr_id = l.id
INNER JOIN pdm_route r ON (r.subject_id = l.child_id) AND (r.is_active) AND (r.dlt_sess = 0)
WHERE
l.parent_id = 1683
	AND (m.route_id IS NULL OR NOT m.route_id = r.id)
) a
WHERE link_ptr_id = a.mid;

-- Повторы обозначений материалов
SELECT e.id, e.code, ep.code, pt.type_name, o.code, a.cnt
FROM
(SELECT c.head_key, count(*) cnt
FROM core_entity c
INNER JOIN pdm_partobject p ON (p.entity_ptr_id = c.id)
WHERE p.part_type_id IN ('material', 'sortament', 'exemplar')
AND (c.dlt_sess = 0)
GROUP BY c.head_key
HAVING count(*)>1) a
INNER JOIN core_entity e  ON (e.head_key = a.head_key)
INNER JOIN pdm_partobject pp ON (pp.entity_ptr_id = e.id)
INNER JOIN pdm_parttype pt ON (pt.part_type = pp.part_type_id)
LEFT JOIN core_entity o ON (o.id = pp.prod_order_id)
LEFT JOIN core_entity ep ON (ep.id = e.parent_id)
WHERE (e.dlt_sess = 0)
ORDER BY a.cnt DESC, e.code, o.code, e.id;

-- Повторы обозначений материалов не из
SELECT e.id, fn_if(pt.doc_key, concat_ws(' ', e.code, ep.code), e.code::TEXT) AS icode, pt.type_name, a.cnt, 'http://192.168.0.220/' || e.id || '/'
FROM
(SELECT e.head_key, count(*)  cnt
FROM core_entity e
INNER JOIN pdm_partobject p ON (p.entity_ptr_id = e.id)
WHERE type_key_id = 'partobject'
AND e.dlt_sess = 0
AND p.prod_order_id IS NULL
AND p.part_type_id IN ('material', 'exemplar')
-- AND e.head_key = 'KAHAT30.5.Г.BK.H.T.1670Г0CT2688.80'
GROUP BY e.head_key
HAVING count(*) > 1) a
INNER JOIN core_entity e  ON (e.head_key = a.head_key)
INNER JOIN pdm_partobject pp ON (pp.entity_ptr_id = e.id)
INNER JOIN pdm_parttype pt ON (pt.part_type = pp.part_type_id)
LEFT JOIN core_entity ep ON (ep.id = e.parent_id)
WHERE (e.dlt_sess = 0)
AND pp.prod_order_id IS NULL
ORDER BY a.cnt DESC, e.head_key, icode, pt.type_name, e.id;

-- Поиск всех позиций по ключу head_key
SELECT * FROM core_entity ce
INNER JOIN pdm_partobject pp ON (pp.entity_ptr_id = ce.id)
WHERE ce.head_key = 'Y.01.00.00.001'
AND pp.prod_order_id IS NULL

-- Копирование настроек дашборда
INSERT INTO core_typepanel(type_key, in_list, in_single, start_params, edit_right_id, panel_id, view_right_id)
SELECT 'prodorderdashrib', in_list, in_single, start_params, edit_right_id, panel_id, view_right_id 
FROM core_typepanel WHERE type_key = 'prodorderdash';

-- Добавление ссылок на файлы от исходной версии
INSERT INTO docarchive_entitydocumentversion(entity_id, document_version_id, old_version, crtd_sess_id, edt_sess, dlt_sess)
SELECT a.child_id, de.document_version_id, de.old_version, 25164, 0, 0
FROM fn_linked_all(604683, 1, 'partlink') a
INNER JOIN pdm_partobject po ON (po.entity_ptr_id = a.child_id)
INNER JOIN docarchive_entitydocumentversion de ON (de.entity_id = po.origin_id) AND (de.dlt_sess = 0)
LEFT JOIN docarchive_entitydocumentversion det ON (det.entity_id = a.child_id) AND (det.document_version_id = de.document_version_id) AND (det.dlt_sess = 0)
WHERE det.id IS NULL;

-- Альтернативный вариант, создающий связи
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

  IF NOT FOUND THEN -- Если не найден - создаем
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
  END IF;

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

  RETURN a_object_id;
END $$ LANGUAGE plpgsql;

-- Удаление связей состава
BEGIN TRANSACTION;

  DELETE FROM pdm_partlink WHERE link_ptr_id IN (
  SELECT id FROM core_link WHERE child_id IN (
  SELECT entity_ptr_id FROM pdm_partobject WHERE prod_order_id = 108881
  ) AND link_class = 'partlink');

  DELETE FROM core_link WHERE child_id IN (
  SELECT entity_ptr_id FROM pdm_partobject WHERE prod_order_id = 108881
  ) AND link_class = 'partlink';

COMMIT TRANSACTION;

-- Установка источника поступления Покупка
-- Записываем в историю
INSERT INTO core_historylog(table_name, object_id, changes, edt_sess_id)
SELECT 'partobject', entity_ptr_id, '{"source": 3}', 26475
FROM pdm_partobject WHERE entity_ptr_id IN (SELECT
e.id
FROM core_entity e
INNER JOIN pdm_partobject p ON (p.entity_ptr_id = e.id)
WHERE (p.part_type_id = 'material') AND (e.dlt_sess = 0)
AND (p.source_id = 1));

UPDATE pdm_partobject SET source_id = 3 WHERE entity_ptr_id IN (SELECT
e.id
FROM core_entity e
INNER JOIN pdm_partobject p ON (p.entity_ptr_id = e.id)
WHERE (p.part_type_id = 'material') AND (e.dlt_sess = 0)
AND (p.source_id = 1));

-- Удаление повторов связей с версиями файлов
UPDATE docarchive_entitydocumentversion
SET dlt_sess = 27395 WHERE id IN (
SELECT MAX(id)
FROM docarchive_entitydocumentversion
WHERE dlt_sess = 0
GROUP BY entity_id, document_version_id
HAVING COUNT(*)>1
);

-- Обновление сессий на основе сессий связей
UPDATE core_entity SET edt_sess = ess
FROM
(SELECT greatest(MAX(crtd_sess_id), MAX(edt_sess)) AS ess, parent_id AS pid
FROM core_link cl
WHERE (dlt_sess = 0)
GROUP BY parent_id) a
WHERE id = pid AND edt_sess < ess;

-- Замена объекта
UPDATE core_link SET child_id = 80062 WHERE child_id = 80889 AND dlt_sess = 0;
UPDATE pdm_partobject SET origin_id = 80062 WHERE origin_id = 80889;
-- Проверка наличия повторов
SELECT * FROM core_link cl WHERE child_id = 80062 AND dlt_sess = 0;

-- Функция, не разворачивающая состав некоторых узлов
CREATE OR REPLACE FUNCTION fn_linked_all_del(
  IN _object_id INT, -- Идентификатор родительского объекта
  IN _quantity FLOAT, -- Количество объекта родителя
  IN _link_classes TEXT, -- Список классов связей для отбора
  OUT child_id INT, -- Идентификатор входящего объекта
  OUT quantity FLOAT, -- Количество входящих
  OUT level_max INT -- Максимальный уровень развертывания
) RETURNS SETOF RECORD
AS $$
DECLARE
  a_level INT := 1;
BEGIN
  DROP TABLE IF EXISTS a_links; -- Защита от конфликтов при повторном вызове

  -- Таблицы для временных выборок
  CREATE TEMPORARY TABLE a_links (c_child_id INT, c_quantity FLOAT, c_level INT) ON COMMIT DROP;

  -- Ввод самого родительского объекта
  INSERT INTO a_links(c_child_id, c_quantity, c_level) VALUES (_object_id, _quantity, a_level);

  LOOP
    -- Заполнение составом
    INSERT INTO a_links(c_child_id, c_quantity, c_level)
    SELECT l.child_id, l.quantity*a.c_quantity, a_level + 1
    FROM a_links a
    INNER JOIN core_link l ON (l.parent_id = a.c_child_id) AND (l.dlt_sess = 0)
    WHERE (a.c_level = a_level)
    AND ((_link_classes IS NULL) OR (l.link_class IN (
      SELECT CAST(SPLIT_PART(_link_classes, ', ', GENERATE_SERIES) AS TEXT)
      FROM GENERATE_SERIES(1, (CHAR_LENGTH(_link_classes) - CHAR_LENGTH(REPLACE(_link_classes, ', ', '')))/2 + 1)
    )))
    AND l.child_id NOT IN (819836, 875131, 838190, 832874, 832875);
    -- выход по завершению перебора
    EXIT WHEN (NOT FOUND);
    a_level := a_level + 1;
  END LOOP;

  RETURN QUERY SELECT p.c_child_id, SUM(p.c_quantity), a_level
  FROM a_links p
  GROUP BY p.c_child_id;
END $$ LANGUAGE plpgsql;

-- Замена удаленных исходных объектов верными
UPDATE pdm_partobject SET origin_id = a.orid
FROM (
SELECT pp.entity_ptr_id AS pid, cer.id AS orid
FROM core_entity ce
INNER JOIN pdm_partobject pp ON (pp.origin_id = ce.id) AND (pp.part_type_id IN ('assembly', 'detail'))
INNER JOIN core_entity cep  ON (pp.entity_ptr_id = cep.id) AND (cep.dlt_sess = 0)
INNER JOIN core_entity cer  ON (cer.head_key = ce.head_key) AND (cer.dlt_sess = 0)
INNER JOIN pdm_partobject ppo ON (ppo.entity_ptr_id = cer.id) AND (ppo.prod_order_id IS NULL)
WHERE ce.dlt_sess > 0
) a
WHERE entity_ptr_id = a.pid

-- Замена удаленных первоисточников на неудаленные
UPDATE pdm_partobject SET origin_id = oid
FROM (
SELECT ce.id AS pid, fn_origin_id_get(ce.head_key) AS oid
FROM core_entity ce
INNER JOIN pdm_partobject pp ON (pp.entity_ptr_id = ce.id) AND (pp.prod_order_id IS NOT NULL) -- Все объекты из заказов
INNER JOIN core_entity ceo ON (ceo.id = pp.origin_id) AND (ceo.dlt_sess > 0) -- Первоисточник удален
WHERE (ce.dlt_sess = 0)) a
WHERE entity_ptr_id = pid
AND pid IS NOT NULL;
