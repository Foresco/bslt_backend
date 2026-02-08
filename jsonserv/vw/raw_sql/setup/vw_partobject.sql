CREATE OR REPLACE VIEW vw_partobject
AS SELECT ce.id,
    ce.code,
    ce.description,
    ce.parent_id,
    ce.group_id,
    ce.head_key,
    ce.rating,
    po.part_type_id,
    po.title,
    po.nom_code,
    po.prod_order_id,
    ce.dlt_sess,
    mu.short_name AS ei
FROM pdm_partobject po
JOIN core_entity ce ON po.entity_ptr_id = ce.id
LEFT JOIN core_measureunit mu ON mu.id = po.unit_id;