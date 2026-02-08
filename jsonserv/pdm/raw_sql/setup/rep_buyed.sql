CREATE OR REPLACE FUNCTION rep_buyed(
  _object_id integer,
  _quantity double precision,
  OUT row_num text,
  OUT group_name character varying,
  OUT object_code text,
  OUT nom_code character varying,
  OUT object_doc character varying,
  OUT remark text,
  OUT supplier character varying,
  OUT parent_code character varying,
  OUT quantity double precision,
  OUT reg_quantity double precision,
  OUT compl_quantity double precision,
  OUT short_name character varying,
  OUT alt_quantity double precision,
  OUT alt_short_name character varying,
  OUT show_alt integer
) RETURNS SETOF record
LANGUAGE plpgsql
AS $function$
DECLARE
  a_critery INT := 1;
  a_prop_id INT DEFAULT 0; -- Идентификатор свойства "Учет в ведомости покупных"
BEGIN
  -- Таблицы для временных выборок
  CREATE TEMPORARY TABLE a_parts (c_child_id INT, c_parent_id INT, c_quantity FLOAT, c_reg_quantity FLOAT, critery INT) ON COMMIT DROP;

  -- Вставка верхнего узла
  INSERT INTO a_parts(c_child_id, c_parent_id, c_quantity, c_reg_quantity, critery) VALUES (_object_id, NULL, _quantity, 0, a_critery);

  -- Перебор нижних уровней
  LOOP
    INSERT INTO a_parts(c_child_id, c_parent_id, c_quantity, c_reg_quantity, critery)
    SELECT p.child_id, p.parent_id,
    p.quantity*a.c_quantity/fn_if(po.unit_id = 1, 1::FLOAT, COALESCE(fp.ratio, 1)), -- Если не штуки, то учитываем потери
    p.reg_quantity*a.c_quantity/fn_if(po.unit_id = 1, 1::FLOAT, COALESCE(fp.ratio, 1)), -- Если не штуки, то учитываем потери
    a_critery + 1
    FROM a_parts a
    INNER JOIN pdm_partobject po ON (po.entity_ptr_id = a.c_child_id) AND (po.source_id < 3) -- Состав только не покупных и кооперации
    INNER JOIN vw_parts p ON (p.parent_id = a.c_child_id) AND NOT (p.not_buyed) -- Исключаем непокупные с пометкой
    LEFT JOIN vw_first_points fp ON (fp.object_id = p.parent_id) -- Первые точки маршрутов
    WHERE (a.critery = a_critery);
    -- выход по завершению перебора
    EXIT WHEN NOT FOUND;
    a_critery := a_critery + 1;
  END LOOP;

  -- Очистка критерия
  UPDATE a_parts SET critery = 0;

  -- Получение идентификатора свойства "Учет в ведомости покупных"
  SELECT p.id INTO a_prop_id FROM core_property p WHERE (p.property_name = 'Учет в ведомости покупных') AND (p.dlt_sess = 0) LIMIT 1;

  -- Подсчет суммарного количества
  INSERT INTO a_parts(c_child_id, c_quantity, critery)
  SELECT p.c_child_id, SUM(p.c_quantity + COALESCE(p.c_reg_quantity, 0)), 1
  FROM a_parts p
  GROUP BY p.c_child_id;

  -- Вывод обработанной информации
  RETURN QUERY SELECT CONCAT_WS('.', CAST(p.c_parent_id AS CHARACTER VARYING), CAST(p.c_child_id AS CHARACTER VARYING)),
  g.code, fn_if(po.part_type_id IN ('assembly', 'detail'), CONCAT_WS(' ', o.code, po.title), o.code::TEXT),
  po.nom_code, d.code, o.description, COALESCE(sup.code, 'Не определен'), COALESCE(pro.code, 'Всего:') AS pc,
  p.c_quantity, p.c_reg_quantity, CAST(NULL AS FLOAT), u.short_name,
  fn_if(po.unit_id = uw.numerator_id, (p.c_quantity+COALESCE(p.c_reg_quantity, 0))/po.weight, (p.c_quantity+COALESCE(p.c_reg_quantity, 0))*po.weight),
  fn_if(po.unit_id = uw.numerator_id, ud.short_name, un.short_name), fn_if(ps.unit_id = uw.denominator_id, 1, 0)
  FROM (SELECT a.c_child_id, a.c_parent_id, SUM(a.c_quantity) AS c_quantity, SUM(a.c_reg_quantity) AS c_reg_quantity, a.critery
    FROM a_parts a GROUP BY a.c_child_id, a.c_parent_id, a.critery) p
  INNER JOIN core_entity o ON (o.id = p.c_child_id)
  INNER JOIN pdm_partobject po ON (po.entity_ptr_id = p.c_child_id) AND (po.source_id = 3)
  LEFT JOIN core_entity d ON (d.id = o.parent_id)
  LEFT JOIN core_entity g ON (g.id = o.group_id)
  LEFT JOIN core_classification gc ON (gc.entity_ptr_id = o.group_id)
  LEFT JOIN core_entity pro ON (pro.id = p.c_parent_id)
  LEFT JOIN core_measureunit u ON (u.id = po.unit_id)
  LEFT JOIN core_measureunit uw ON (uw.id = po.weight_unit_id)
  LEFT JOIN core_measureunit un ON (un.id = uw.numerator_id)
  LEFT JOIN core_measureunit ud ON (ud.id = uw.denominator_id)
  LEFT JOIN supply_price pr ON (pr.supplied_entity_id = p.c_child_id) AND (pr.is_active) -- AND (pr.dlt_sess = 0)
  LEFT JOIN core_entity sup ON (sup.id = pr.supplier_id)
  LEFT JOIN core_link es ON (es.parent_id = p.c_child_id) AND (es.link_class = 'typesizesort') AND (es.dlt_sess = 0)
  LEFT JOIN core_link em ON (em.parent_id = p.c_child_id) AND (em.link_class = 'typesizemater') AND (em.dlt_sess = 0)
  LEFT JOIN core_entity s ON (s.id = es.child_id)
  LEFT JOIN pdm_partobject ps ON (ps.entity_ptr_id = es.child_id)
  LEFT JOIN core_propertyvalue prv1 ON (prv1.entity_id = p.c_child_id) AND (prv1.property_id = a_prop_id) AND (prv1.dlt_sess = 0)
  LEFT JOIN core_propertyvalue prv2 ON (prv2.entity_id = em.child_id) AND (prv2.property_id = a_prop_id) AND (prv2.dlt_sess = 0)
  WHERE (po.part_type_id NOT IN ('material', 'exemplar')) OR ((po.part_type_id NOT IN ('material', 'exemplar')) AND ((UPPER(prv1.value) = 'ДА') OR (UPPER(prv2.value) = 'ДА'))) -- Фильтра материалов для ведомости покупных
  ORDER BY gc.order_num, g.code, o.code, d.code, p.critery, pc;
END $function$
;
