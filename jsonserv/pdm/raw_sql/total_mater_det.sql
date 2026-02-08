SELECT
g.code AS group_code, -- Группа
dse.code, -- ДСЕ
m.code AS mater_code, -- Материал
mp.nom_code, -- Код материала
fn_repl_nom_code(tpr.id, 1) AS repl_1, -- Замена 1
fn_repl_nom_code(tpr.id, 2) AS repl_2, -- Замена 2
d.code AS doc_code, -- Документ
pl.code AS place_code, -- Цех
a.parent_quantity*a.quantity*rs.k_zap*1000 AS norm, -- Норма
mu.short_name AS ei -- ЕИ
FROM (
  SELECT l.id, l.child_id, l.parent_id, la.quantity AS parent_quantity, l.quantity
  FROM fn_linked_all(%(object_id)s, %(quantity)s, NULL) la
  INNER JOIN core_link l ON (l.parent_id = la.child_id) AND (l.link_class = 'tpresource')
) a
INNER JOIN core_entity m ON (m.id = a.child_id)
INNER JOIN core_entity dse ON (dse.id = a.parent_id)
INNER JOIN pdm_partobject mp ON (mp.entity_ptr_id = m.id) AND (mp.source_id = 3)
INNER JOIN pdm_tpresource rs ON (rs.link_ptr_id = a.id)
INNER JOIN pdm_tprow tpr ON (tpr.id = rs.tp_row_id) AND (tpr.replaced_id IS NULL)
INNER JOIN pdm_routepoint rp ON (rp.id = tpr.route_point_id)
INNER JOIN core_entity pl ON (pl.id = rp.place_id)
LEFT JOIN core_entity g ON (g.id = m.group_id)
LEFT JOIN core_classification cc ON (cc.entity_ptr_id = m.group_id)
LEFT JOIN core_entity d ON (d.id = m.parent_id)
LEFT JOIN core_measureunit mu ON (mu.id = mp.unit_id)
ORDER BY cc.order_num, group_code, mater_code, dse.code;