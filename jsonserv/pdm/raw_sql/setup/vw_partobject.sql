CREATE OR REPLACE VIEW vw_partobject
AS SELECT ce.id,
    CASE
        WHEN pt.doc_key OR pt.code_join THEN (ce.code::text || COALESCE(' '::text || d.code::text, ''::text))::character varying
        ELSE ce.code
    END AS code,
    ce.description,
    ce.parent_id,
    ce.group_id,
    ce.head_key,
    ce.rating,
    po.part_type_id,
    po.title,
    po.nom_code,
    po.source_id,
    po.prod_order_id,
    ce.dlt_sess,
    mu.short_name AS ei
FROM pdm_partobject po
INNER JOIN core_entity ce ON (po.entity_ptr_id = ce.id)
INNER JOIN pdm_parttype pt ON pt.part_type = po.part_type_id
LEFT JOIN core_measureunit mu ON (mu.id = po.unit_id)
LEFT JOIN core_entity d ON (d.id = ce.parent_id);

GRANT SELECT ON TABLE vw_partobject to basauser;
