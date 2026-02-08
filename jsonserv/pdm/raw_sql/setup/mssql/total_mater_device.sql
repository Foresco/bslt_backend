SELECT
t.code AS top_code, -- Изделие
g.code AS group_code, -- Группа
m.code AS mater_code, -- Материал
IIF(b.replaced_id = 0, mp.nom_code, 'З: ' + mp.nom_code) AS nom_code,
b.repl_1, -- Замена 1
b.repl_2, -- Замена 2
d.code AS doc_code, -- Документ
b.norm,
mu.short_name AS ei -- ЕИ
FROM
(
  SELECT
  a.child_id, a.top_id, 
  dbo.fn_repl_nom_code(tpr.id, COALESCE(tpr.replaced_id, tpr.id), 1) AS repl_1, -- Замена 1
  dbo.fn_repl_nom_code(tpr.id, COALESCE(tpr.replaced_id, tpr.id), 2) AS repl_2, -- Замена 2
  COALESCE(lr.child_id, 0) AS replaced_id,
  SUM(a.quantity_ratio*a.quantity) AS norm -- Норма
  FROM (
    SELECT l.id, la.top_id, l.child_id, l.parent_id, la.quantity AS parent_quantity, la.quantity_ratio, l.quantity
    FROM (
      SELECT a.top_id, a.child_id, SUM(a.quantity) AS quantity, SUM(a.quantity_ratio) AS quantity_ratio
      FROM fn_linked_all_device(%(object_id)s, %(quantity)s, NULL) a
      GROUP BY a.top_id, a.child_id
    ) la
    INNER JOIN core_link l ON (l.parent_id = la.child_id) AND (l.link_class = 'tpresource') AND (l.dlt_sess = 0)
  ) a
  INNER JOIN pdm_tpresource rs ON (rs.link_ptr_id = a.id)
  INNER JOIN pdm_tprow tpr ON (tpr.id = rs.tp_row_id)
  INNER JOIN pdm_routepoint rp ON (rp.id = tpr.route_point_id)
  LEFT JOIN pdm_tpresource rsr ON (rsr.tp_row_id = tpr.replaced_id)
  LEFT JOIN core_link lr ON (lr.id = rsr.link_ptr_id)
  GROUP BY a.child_id, a.top_id, 
  dbo.fn_repl_nom_code(tpr.id, COALESCE(tpr.replaced_id, tpr.id), 1),
  dbo.fn_repl_nom_code(tpr.id, COALESCE(tpr.replaced_id, tpr.id), 2),
  COALESCE(lr.child_id, 0)
) b
INNER JOIN core_entity m ON (m.id = b.child_id)
INNER JOIN core_entity t ON (t.id = b.top_id)
INNER JOIN pdm_partobject mp ON (mp.entity_ptr_id = m.id) AND (mp.source_id = 3)
LEFT JOIN core_entity ms ON (ms.id = IIF(b.replaced_id = 0, b.child_id, b.replaced_id))
LEFT JOIN core_entity g ON (g.id = m.group_id)
LEFT JOIN core_classification cc ON (cc.entity_ptr_id = m.group_id)
LEFT JOIN core_entity d ON (d.id = m.parent_id)
LEFT JOIN core_measureunit mu ON (mu.id = mp.unit_id)
ORDER BY cc.order_num, group_code, t.code, ms.code, IIF(b.replaced_id = 0, 0, 1), mater_code;