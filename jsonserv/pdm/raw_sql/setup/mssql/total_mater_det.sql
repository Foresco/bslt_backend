SELECT
g.code AS group_code, -- Группа
IIF(a.is_replace = 0, dse.code, 'З: ' + dse.code) + dbo.fn_replace_codes(dse.code) AS code, -- ДСЕ
m.code AS mater_code, -- Материал
IIF(tpr.replaced_id IS NULL, mp.nom_code, 'З: ' + mp.nom_code) AS nom_code,
dbo.fn_repl_nom_code(tpr.id, COALESCE(tpr.replaced_id, tpr.id), 1) AS repl_1, -- Замена 1
dbo.fn_repl_nom_code(tpr.id, COALESCE(tpr.replaced_id, tpr.id), 2) AS repl_2, -- Замена 2
d.code AS doc_code, -- Документ
pl.code AS place_code, -- Цех
CASE WHEN r.is_active = 1 THEN '' ELSE 'Зам.' END AS r_replace,
a.parent_quantity,
a.quantity_ratio*a.quantity AS norm, -- Норма
mu.short_name AS ei -- ЕИ
FROM (
  SELECT l.id, l.child_id, l.parent_id, la.quantity AS parent_quantity, la.quantity_ratio, l.quantity, la.is_replace
  FROM (
    SELECT a.child_id, SUM(a.quantity) AS quantity, SUM(a.quantity_ratio) AS quantity_ratio, IIF(a.replaced_id IS NULL, 0, 1) AS is_replace
    FROM fn_svod_vem_mat_sed(%(object_id)s, %(quantity)s, NULL) a
    GROUP BY a.child_id, IIF(a.replaced_id IS NULL, 0, 1)
  ) la
  INNER JOIN core_link l ON (l.parent_id = la.child_id) AND (l.link_class = 'tpresource') AND (l.dlt_sess = 0)
) a
INNER JOIN core_entity m ON (m.id = a.child_id)
INNER JOIN core_entity dse ON (dse.id = a.parent_id)
INNER JOIN pdm_partobject mp ON (mp.entity_ptr_id = m.id) AND (mp.source_id = 3)
INNER JOIN pdm_parttype pt ON (pt.part_type = mp.part_type_id)
INNER JOIN pdm_tpresource rs ON (rs.link_ptr_id = a.id)
INNER JOIN pdm_tprow tpr ON (tpr.id = rs.tp_row_id) AND (tpr.dlt_sess = 0)
INNER JOIN pdm_routepoint rp ON (rp.id = tpr.route_point_id) AND (rp.dlt_sess = 0)
INNER JOIN pdm_route r ON (r.id = rp.route_id)
INNER JOIN core_entity pl ON (pl.id = rp.place_id)
LEFT JOIN core_entity g ON (g.id = m.group_id)
LEFT JOIN core_classification cc ON (cc.entity_ptr_id = m.group_id)
LEFT JOIN core_entity d ON (d.id = m.parent_id)
LEFT JOIN core_measureunit mu ON (mu.id = mp.unit_id)
LEFT JOIN pdm_tprow tprr ON (tprr.id = tpr.replaced_id)
LEFT JOIN pdm_tpresource rsr ON (rsr.tp_row_id = tprr.id)
LEFT JOIN core_link lr ON (lr.id = rsr.link_ptr_id)
LEFT JOIN core_entity mr ON (mr.id = lr.child_id)
ORDER BY cc.order_num, group_code, pt.order_num, dse.code, COALESCE(mr.code, m.code), tpr.replaced_id;