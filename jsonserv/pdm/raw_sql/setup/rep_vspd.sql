CREATE OR REPLACE FUNCTION rep_vspd(
  _object_id integer,
  _var smallint,
  _group_var smallint,
  _notice_id integer,
  OUT top_code character varying,
  OUT div_name character varying,
  OUT object_code character varying,
  OUT object_name character varying,
  OUT parent_code character varying,
  OUT quantity double precision,
  OUT total_quantity double precision,
  OUT short_name character varying,
  OUT remark text,
  OUT to_replace text
)  RETURNS SETOF record
LANGUAGE plpgsql
AS $function$
DECLARE
  a_critery INT := 1;
  a_object_code CHARACTER VARYING(200); -- Обозначение объектов
  a_var_count INT; -- Количество исполнений объекта
  a_tract_id INT; -- Идентификатор транзакции для поиска непроведенных вариантов
  a_doc_name CHARACTER VARYING(110); -- Имя документа
BEGIN
  -- Таблицы для временных выборок
  CREATE TEMPORARY TABLE a_parts (c_top_id INT, c_child_id INT, c_parent_id INT, c_quantity FLOAT, c_total_quantity FLOAT, c_remark TEXT, c_to_replace TEXT, critery INT) ON COMMIT DROP;
  CREATE TEMPORARY TABLE a_parts_res (c_ved BOOLEAN DEFAULT false, c_top_id INT, c_child_id INT, c_parent_id INT, c_quantity FLOAT, c_total_quantity FLOAT, c_remark TEXT, c_to_replace TEXT) ON COMMIT DROP;
  -- Для последующей фильтрации
  a_doc_name := fn_if(_var = 1, CAST('Ведомость спецификаций' AS CHARACTER VARYING), CAST('Ведомость деталей' AS CHARACTER VARYING));

  IF (_group_var = 1) THEN -- Указан групповой вариант формирования
    -- Получение обозначения объекта
    SELECT OVERLAY(o.code placing '-(0|1|2)(1|2|3|4|5|6|7|8|9|0)' FROM fn_if(STRPOS(o.code, ' ') = 0, CHAR_LENGTH(o.code)+1, STRPOS(o.code, ' ')) FOR 0), o.dlt_sess
    INTO a_object_code, a_tract_id
    FROM core_entity o WHERE (o.id = _object_id);
    -- Получение количества вариантов
    SELECT COUNT(*) INTO a_var_count
	FROM core_entity o
	INNER JOIN pdm_partobject po ON (po.entity_ptr_id = o.id)
	WHERE ((o.code SIMILAR TO a_object_code) AND (po.part_type_id IN ('assembly', 'complect')) AND NOT (o.dlt_sess IS DISTINCT FROM a_tract_id))
	OR (o.id = _object_id);

    -- Ввод состава родительских объектов
    INSERT INTO a_parts(c_top_id, c_child_id, c_parent_id, c_quantity, c_total_quantity, c_remark, c_to_replace, critery)
    SELECT p.parent_id, fn_notice_object_get(_notice_id, p.child_id), NULL, p.quantity, p.quantity, p.comment, p.to_replace, a_critery
    FROM vw_parts p
	INNER JOIN pdm_partobject po ON (po.entity_ptr_id = p.child_id) AND (po.part_type_id IN ('assembly', 'complect'))
    WHERE (p.parent_id IN (SELECT fn_notice_object_get(_notice_id, o.id)
	FROM core_entity o
	INNER JOIN pdm_partobject po ON (po.entity_ptr_id = o.id)
	WHERE ((o.code SIMILAR TO a_object_code) AND (po.part_type_id IN ('assembly', 'complect')) AND NOT (o.dlt_sess IS DISTINCT FROM a_tract_id)) OR (o.id = _object_id)))
    AND (p.dlt_sess = 0);
  ELSE
    -- Ввод состава родительского объекта
    INSERT INTO a_parts(c_child_id, c_parent_id, c_quantity, c_total_quantity, c_remark, c_to_replace, critery)
    SELECT fn_notice_object_get(_notice_id, p.child_id), NULL, p.quantity, p.quantity, p.comment, p.to_replace, a_critery
    FROM vw_parts p
    INNER JOIN pdm_partobject po ON (po.entity_ptr_id = p.child_id) AND (po.part_type_id IN ('assembly', 'complect'))
    WHERE (p.parent_id = _object_id) AND (p.dlt_sess = 0);
  END IF;
  -- Перебор нижних уровней
  LOOP
    INSERT INTO a_parts(c_top_id, c_child_id, c_parent_id, c_quantity, c_total_quantity, c_remark, c_to_replace, critery)
    SELECT a.c_top_id, fn_notice_object_get(_notice_id, p.child_id), p.parent_id, p.quantity, p.quantity*a.c_total_quantity,
    p.comment, p.to_replace, a_critery + 1
    FROM a_parts a
    INNER JOIN vw_parts p ON (p.parent_id = a.c_child_id) AND (p.dlt_sess = 0)
    INNER JOIN pdm_partobject po ON (po.entity_ptr_id = p.child_id) AND (po.part_type_id IN ('assembly', 'complect'))
    WHERE (a.critery = a_critery) AND NOT EXISTS(
      SELECT 1 FROM vw_parts pt
      INNER JOIN pdm_partobject ot ON (ot.entity_ptr_id = pt.child_id) AND (ot.part_type_id = 'document') AND (ot.title = a_doc_name) -- Где нет ведомостей в составе
      WHERE (pt.parent_id = a.c_child_id) AND (pt.dlt_sess = 0)
    );
    -- выход по завершению перебора
    EXIT WHEN NOT FOUND;
    a_critery := a_critery + 1;
  END LOOP;
  -- Разбор вариантов
  IF (_var = 1) THEN -- Ведомость спецификаций
    IF (_group_var = 1) THEN -- Указан групповой вариант формирования
      -- Выборка общих вариантов
      INSERT INTO a_parts_res (c_child_id, c_parent_id, c_quantity, c_total_quantity, c_to_replace, c_remark)
      SELECT c_child_id, c_parent_id, c_quantity, c_total_quantity, c_to_replace, c_remark
      FROM a_parts
      GROUP BY c_child_id, c_parent_id, c_quantity, c_total_quantity, c_to_replace, c_remark
      HAVING (COUNT(*) >= a_var_count); -- Бывает не только равно, но и несколько раз в одном
      -- Выборка отличных вариантов
      INSERT INTO a_parts_res (c_top_id, c_child_id, c_parent_id, c_quantity, c_total_quantity, c_to_replace, c_remark)
      SELECT a.c_top_id, a.c_child_id, a.c_parent_id, a.c_quantity, a.c_total_quantity, a.c_to_replace, a.c_remark
      FROM a_parts a
      LEFT JOIN a_parts_res r ON (r.c_child_id = a.c_child_id) AND (r.c_parent_id IS NOT DISTINCT FROM a.c_parent_id) AND (r.c_quantity = a.c_quantity)
      AND (r.c_total_quantity = a.c_total_quantity)
      WHERE (r.c_child_id IS NULL);
    ELSE
      INSERT INTO a_parts_res (c_child_id, c_parent_id, c_quantity, c_total_quantity, c_to_replace, c_remark)
      SELECT c_child_id, c_parent_id, c_quantity, c_total_quantity, c_to_replace, c_remark FROM a_parts;
    END IF;
  ELSE -- Ведомость деталей
    IF (_group_var = 1) THEN -- Указан групповой вариант формирования
      -- Выборка общих вариантов
      INSERT INTO a_parts_res (c_child_id, c_parent_id, c_quantity, c_total_quantity, c_remark, c_to_replace)
      SELECT fn_notice_object_get(_notice_id, p.child_id), p.parent_id, p.quantity, p.quantity*a.c_total_quantity AS tc, p.comment, p.to_replace
      FROM a_parts a
      INNER JOIN vw_parts p ON (p.parent_id = a.c_child_id) AND (p.dlt_sess = 0)
	  INNER JOIN pdm_partobject po ON (po.entity_ptr_id = p.child_id) AND (po.part_type_id IN ('complex', 'detail', 'standart', 'other', 'material', 'exemplar'))
      GROUP BY p.child_id, p.parent_id, p.quantity, tc, p.comment, p.to_replace
      HAVING (COUNT(*) >= a_var_count); -- Бывает не только равно, но и несколько раз в одном
      -- Ввод общего состава родительских объектов
      INSERT INTO a_parts_res (c_child_id, c_quantity, c_total_quantity, c_remark, c_to_replace)
      SELECT p.child_id, p.quantity, p.quantity, p.comment, p.to_replace
      FROM vw_parts p
      INNER JOIN pdm_partobject po ON (po.entity_ptr_id = p.child_id) AND (po.part_type_id IN ('complex', 'detail', 'standart', 'other', 'material', 'exemplar'))
      WHERE (p.parent_id IN (SELECT fn_notice_object_get(_notice_id, o.id)
	  FROM core_entity o
	  INNER JOIN pdm_partobject po ON (po.entity_ptr_id = o.id)
	  WHERE ((o.code SIMILAR TO a_object_code) AND (po.part_type_id IN ('assembly', 'complect')) AND NOT (o.dlt_sess IS DISTINCT FROM a_tract_id)) OR (o.id = _object_id)))
      AND (p.dlt_sess = 0)
      GROUP BY p.child_id, p.quantity, p.comment, p.to_replace
      HAVING (COUNT(*) >= a_var_count); -- Бывает не только равно, но и несколько раз в одном
      -- Выборка отличных вариантов
      INSERT INTO a_parts_res (c_top_id, c_child_id, c_parent_id, c_quantity, c_total_quantity, c_remark, c_to_replace)
      SELECT a.c_top_id, fn_notice_object_get(_notice_id, p.child_id), p.parent_id, p.quantity, p.quantity*a.c_total_quantity AS tc, p.comment, p.to_replace
      FROM a_parts a
      INNER JOIN vw_parts p ON (p.parent_id = a.c_child_id) AND (p.dlt_sess = 0)
      INNER JOIN pdm_partobject po ON (po.entity_ptr_id = p.child_id) AND (po.part_type_id IN ('complex', 'detail', 'standart', 'other', 'material', 'exemplar'))
      LEFT JOIN a_parts_res r ON (r.c_child_id = p.child_id) AND (r.c_parent_id IS NOT DISTINCT FROM p.parent_id) AND (r.c_quantity = p.quantity)
      AND (r.c_total_quantity = p.quantity*a.c_total_quantity)
      WHERE (r.c_child_id IS NULL);
      -- Ввод состава родительских объектов отличных вариантов
      INSERT INTO a_parts_res (c_top_id, c_child_id, c_quantity, c_total_quantity, c_remark, c_to_replace)
      SELECT p.parent_id, p.child_id, p.quantity, p.quantity, p.comment, p.to_replace
      FROM vw_parts p
      INNER JOIN pdm_partobject po ON (po.entity_ptr_id = p.child_id) AND (po.part_type_id IN ('complex', 'detail', 'standart', 'other', 'material', 'exemplar'))
      LEFT JOIN a_parts_res r ON (r.c_child_id = p.child_id) AND (r.c_parent_id IS NULL) AND (r.c_quantity = p.quantity)
      AND (r.c_total_quantity = p.quantity)
      WHERE (p.parent_id IN (SELECT fn_notice_object_get(_notice_id, o.id)
      FROM core_entity o
	  INNER JOIN pdm_partobject po ON (po.entity_ptr_id = o.id)
	  WHERE ((o.code SIMILAR TO a_object_code) AND (po.part_type_id IN ('assembly', 'complect')) AND NOT (o.dlt_sess IS DISTINCT FROM a_tract_id)) OR (o.id = _object_id)))
      AND (p.dlt_sess = 0) AND (r.c_child_id IS NULL);
    ELSE
      INSERT INTO a_parts_res (c_child_id, c_parent_id, c_quantity, c_total_quantity, c_remark, c_to_replace)
      SELECT fn_notice_object_get(_notice_id, p.child_id), p.parent_id, p.quantity, p.quantity*a.c_total_quantity, p.comment, p.to_replace
      FROM a_parts a
      INNER JOIN vw_parts p ON (p.parent_id = a.c_child_id) AND (p.dlt_sess = 0)
      INNER JOIN pdm_partobject po ON (po.entity_ptr_id = p.child_id) AND (po.part_type_id IN ('complex', 'detail', 'standart', 'other', 'material', 'exemplar'));
      -- Вставка состава самого объекта
      INSERT INTO a_parts_res (c_child_id, c_quantity, c_total_quantity, c_remark, c_to_replace)
      SELECT p.child_id, p.quantity, p.quantity, p.comment, p.to_replace
      FROM vw_parts p
      INNER JOIN pdm_partobject po ON (po.entity_ptr_id = p.child_id) AND (po.part_type_id IN ('complex', 'detail', 'standart', 'other', 'material', 'exemplar'))
      WHERE (p.parent_id = _object_id) AND (p.dlt_sess = 0);
    END IF;
  END IF;

  -- Добавление ведомостей от элементов состава
  INSERT INTO a_parts_res (c_ved, c_top_id, c_child_id, c_parent_id, c_quantity, c_total_quantity, c_remark, c_to_replace)
  SELECT true, a.c_top_id, p.child_id, p.parent_id, NULL, NULL, p.comment, p.to_replace
  FROM a_parts_res a
  INNER JOIN vw_parts p ON (p.parent_id = a.c_child_id) AND (p.dlt_sess = 0)
  INNER JOIN pdm_partobject ot ON (ot.entity_ptr_id = p.child_id) AND (ot.part_type_id = 'document') AND (ot.title = a_doc_name)
  WHERE NOT (p.child_id = _object_id); -- Ведомость самого объекта не берем

  -- Вывод обработанной информации
  RETURN QUERY SELECT COALESCE(tp.code, '') AS tc, pt.div_name, o.object_code, ot.title, COALESCE(po.code, '') AS pc,
  p.c_quantity, p.c_total_quantity, u.short_name, p.c_remark, p.c_to_replace
  FROM (SELECT c_ved, c_top_id, c_child_id, c_parent_id, MAX(c_quantity) AS c_quantity, SUM(c_total_quantity) AS c_total_quantity, c_remark, c_to_replace
    FROM a_parts_res GROUP BY c_ved, c_top_id, c_child_id, c_parent_id, c_remark, c_to_replace) p
  INNER JOIN vw_objects_doc_only o ON (o.id = p.c_child_id)
  INNER JOIN pdm_parttype pt ON (pt.part_type = o.type_id)
  LEFT JOIN core_measureunit u ON (u.id = o.unit_id)
  LEFT JOIN core_entity po ON (po.id = p.c_parent_id)
  LEFT JOIN pdm_partobject ot ON (ot.entity_ptr_id = p.c_child_id)
  LEFT JOIN core_entity tp ON (tp.id = p.c_top_id)
  ORDER BY c_ved, tc, fn_if(o.type_id = 'exemplar', 7, pt.order_num), o.object_code, pc; -- Экземпляры сортаментов сортируются как материалы
END $function$
;
