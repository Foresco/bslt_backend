SELECT
f.parent_id,
p.code AS parent_code,
f.top_id,
t.code AS top_code,
f.quantity,
f.quantity_ratio
FROM
dbo.fn_linked_all_reverse(%(object_id)s, %(quantity)s, %(link_classes)s) f
INNER JOIN core_entity p ON (p.id = f.parent_id)
INNER JOIN core_entity t ON (t.id = f.top_id)
ORDER BY parent_code, top_code;