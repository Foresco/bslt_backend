SELECT
g.code AS group_code, -- Группа
m.code AS mater_code, -- Материал
mp.nom_code, -- Код материала
b.repl_1, -- Замена 1
b.repl_2, -- Замена 2
d.code AS doc_code, -- Документ
b.norm,
mu.short_name AS ei -- ЕИ
FROM
(
  SELECT
  a.child_id,
  fn_repl_nom_code(tpr.id, 1) AS repl_1, -- Замена 1
  fn_repl_nom_code(tpr.id, 2) AS repl_2, -- Замена 2
  SUM(a.parent_quantity*a.quantity) AS norm -- Норма
  FROM (
    SELECT l.id, l.child_id, l.parent_id, la.quantity AS parent_quantity, l.quantity
    FROM (
      SELECT a.child_id, SUM(a.quantity) AS quantity FROM fn_linked_all(%(object_id)s, %(quantity)s, NULL) a
      GROUP BY a.child_id
    ) la
    INNER JOIN core_link l ON (l.parent_id = la.child_id) AND (l.link_class = 'tpresource') AND (l.dlt_sess = 0)
  ) a
  INNER JOIN pdm_tpresource rs ON (rs.link_ptr_id = a.id)
  INNER JOIN pdm_tprow tpr ON (tpr.id = rs.tp_row_id) AND (tpr.replaced_id IS NULL)
  INNER JOIN pdm_routepoint rp ON (rp.id = tpr.route_point_id)
  GROUP BY a.child_id, repl_1, repl_2
) b
INNER JOIN core_entity m ON (m.id = b.child_id)
INNER JOIN pdm_partobject mp ON (mp.entity_ptr_id = m.id) AND (mp.source_id = 3)
LEFT JOIN core_entity g ON (g.id = m.group_id)
LEFT JOIN core_classification cc ON (cc.entity_ptr_id = m.group_id)
LEFT JOIN core_entity d ON (d.id = m.parent_id)
LEFT JOIN core_measureunit mu ON (mu.id = mp.unit_id)
ORDER BY cc.order_num, group_code, mater_code;