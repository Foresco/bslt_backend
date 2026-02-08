CREATE OR REPLACE FUNCTION rep_specif(
  IN _object_id integer,
  IN _group_var smallint,
  OUT top_code character varying,
  OUT div_name character varying,
  OUT draft_format text,
  OUT draft_zone character varying,
  OUT "position" smallint,
  OUT object_code character varying,
  OUT object_name character varying,
  OUT quantity double precision,
  OUT short_name character varying,
  OUT to_replace text,
  OUT remark text,
  OUT mater_code character varying,
  OUT mater_size text,
  OUT weight double precision,
  OUT weight_unit character varying,
  OUT section_id integer
) RETURNS SETOF record
LANGUAGE plpgsql
AS $function$
DECLARE
  a_object_code CHARACTER VARYING(230); -- Обозначение объектов
  a_var_count INT; -- Количество исполнений объекта
  a_tract_id INT; -- Идентификатор транзакции для поиска непроведенных вариантов
  a_notice_id INT; -- Идентификатор извещения, по которому выпускается объект
BEGIN
  -- Таблицы для временных выборок
  CREATE TEMPORARY TABLE a_parts (c_top_id INT, c_draft_zone CHARACTER VARYING(5), c_position SMALLINT, c_child_id INT, c_quantity FLOAT, c_remark TEXT, c_to_replace TEXT, c_first_use BOOLEAN, c_section_id INT) ON COMMIT DROP;
  CREATE TEMPORARY TABLE a_parts_res (c_top_id INT, c_draft_zone CHARACTER VARYING(5), c_position SMALLINT, c_child_id INT, c_quantity FLOAT, c_remark TEXT, c_to_replace TEXT, c_first_use BOOLEAN, c_section_id INT) ON COMMIT DROP;
  -- Получение идентификатора извещения
  SELECT nl.notice_id INTO a_notice_id
  FROM vw_notice_links nl WHERE (nl.object_id = _object_id) AND (nl.dlt_sess = 0) LIMIT 1;

  IF (_group_var = 1) THEN -- Указан групповой вариант формирования
    -- Получение фильтра обозначений объектов
    SELECT OVERLAY(o.code placing '-(0|1|2)(1|2|3|4|5|6|7|8|9|0)' FROM fnIf(STRPOS(o.code, ' ') = 0, CHAR_LENGTH(o.code)+1, STRPOS(o.code, ' ')) FOR 0), o.dlt_sess
    INTO a_object_code, a_tract_id
    FROM core_entity o WHERE (o.id = _object_id);

    -- Получение количества вариантов
    SELECT COUNT(*) INTO a_var_count
	FROM core_entity o
	INNER JOIN pdm_partobject po ON (po.entity_ptr_id = o.id)
    WHERE ((o.code SIMILAR TO a_object_code) AND (po.part_type_id IN ('assembly', 'complect')) AND NOT (o.dlt_sess IS DISTINCT FROM a_tract_id) AND (o.state_id < 6)) OR (o.id = _object_id);

    -- Ввод состава объектов в промежуточную таблицу
    INSERT INTO a_parts(c_top_id, c_draft_zone, c_position, c_child_id, c_quantity, c_remark, c_to_replace, c_first_use, c_section_id)
    SELECT p.parent_id, p.draft_zone, p.position, fn_notice_object_get(a_notice_id, p.child_id), p.quantity, p.comment, p.to_replace, p.first_use, p.section_id
    FROM vw_parts p
    WHERE (p.parent_id IN (SELECT o.id
	FROM core_entity o
	INNER JOIN pdm_partobject po ON (po.entity_ptr_id = o.id)
	WHERE ((o.code SIMILAR TO a_object_code) AND (po.part_type_id IN ('assembly', 'complect')) AND NOT (o.dlt_sess IS DISTINCT FROM a_tract_id) AND (o.state_id < 6)) OR (o.id = _object_id)))
    AND (p.dlt_sess = 0);

    -- Выборка общих вариантов
    INSERT INTO a_parts_res (c_draft_zone, c_position, c_child_id, c_quantity, c_remark, c_to_replace, c_first_use, c_section_id)
    SELECT c_draft_zone, c_position, c_child_id, c_quantity, c_remark, c_to_replace, c_first_use, c_section_id
    FROM a_parts
    GROUP BY c_draft_zone, c_position, c_child_id, c_quantity, c_remark, c_to_replace, c_first_use, c_section_id
    HAVING (COUNT(*) = a_var_count);
    -- Выборка отличных вариантов
    INSERT INTO a_parts_res (c_top_id, c_draft_zone, c_position, c_child_id, c_quantity, c_remark, c_to_replace, c_first_use, c_section_id)
    SELECT a.c_top_id, a.c_draft_zone, a.c_position, a.c_child_id, a.c_quantity, a.c_remark, a.c_to_replace, a.c_first_use, a.c_section_id
    FROM a_parts a
    LEFT JOIN a_parts_res r ON (r.c_draft_zone IS NOT DISTINCT FROM a.c_draft_zone) AND (r.c_position IS NOT DISTINCT FROM a.c_position)
    AND (r.c_child_id = a.c_child_id) AND (r.c_quantity IS NOT DISTINCT FROM a.c_quantity)
    AND (r.c_remark IS NOT DISTINCT FROM a.c_remark) AND (r.c_to_replace IS NOT DISTINCT FROM a.c_to_replace) AND NOT (r.c_section_id = a.c_section_id)
    WHERE (r.c_child_id IS NULL);
  ELSE
    -- Ввод состава объекта
    INSERT INTO a_parts_res(c_draft_zone, c_position, c_child_id, c_quantity, c_remark, c_to_replace, c_first_use, c_section_id)
    SELECT p.draft_zone, p.position, fn_notice_object_get(a_notice_id, p.child_id), p.quantity, p.comment, p.to_replace, p.first_use, p.section_id
    FROM vw_parts p
    WHERE (p.parent_id = _object_id) AND (p.dlt_sess = 0);
  END IF;

  -- Отображение полученных данных
  RETURN QUERY SELECT COALESCE(tp.code, '') AS tc, pt.div_name, fn_format_string(o.id) AS draft_format, p.c_draft_zone, p.c_position,
  CASE WHEN (et.doc_key) THEN o.code || COALESCE(' ' || d.code, '') ELSE o.code END AS key_code,
  po.title, p.c_quantity, u.short_name, p.c_to_replace, p.c_remark,
  CASE WHEN mt.doc_key THEN (mo.code || COALESCE(' ' || md.code, '')) ELSE mo.code END, o.description,
  CASE WHEN (po.unit_id = wu.numerator_id) THEN CASE WHEN COALESCE(po.weight)>0 THEN 1/po.weight END ELSE po.weight END,
  CASE WHEN (po.unit_id = wu.numerator_id) THEN wu.denominator ELSE wu.numerator END,
  p.c_section_id
  FROM a_parts_res p
  INNER JOIN core_entity o ON (o.id = p.c_child_id)
  INNER JOIN core_entitytype et ON (et.type_key = o.type_key_id)
  INNER JOIN pdm_partobject po ON (po.entity_ptr_id = o.id)
  INNER JOIN pdm_parttype pt ON (pt.part_type = po.part_type_id)
  LEFT JOIN core_measureunit u ON (u.id = po.unit_id)
  LEFT JOIN vw_weignt_units wu ON (wu.id = po.weight_unit_id)
  LEFT JOIN core_entity d ON (d.id = o.parent_id) AND NOT (d.type_key_id = 'stage') -- Стадии не пристыковываются
  LEFT JOIN core_entity tp ON (tp.id = p.c_top_id)
  LEFT JOIN core_classification g ON (g.entity_ptr_id = o.group_id)
  LEFT JOIN core_link m ON (m.parent_id = o.id) AND (m.link_class = 'designmater') AND (m.dlt_sess = 0)
  LEFT JOIN core_entity mo ON (mo.id = m.child_id)
  LEFT JOIN core_entitytype mt ON mt.type_key = o.type_key_id
  LEFT JOIN core_entity md ON md.id = o.parent_id
  ORDER BY tc, p.c_section_id, fn_if(o.type_key_id = 'exemplar', 7, pt.order_num), p.c_position, p.c_first_use DESC,
    g.order_num, key_code, d.code, po.title; -- Экземпляры сортаментов сортируются как материалы
END $function$
;