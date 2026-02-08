CREATE VIEW vw_objects
AS SELECT
  o.id,
  CASE
     WHEN et.doc_key = 1 and d.code IS NOT NULL THEN o.code + ' ' + d.code
     ELSE o.code
  END AS object_code,
  po.title AS object_name,
  dbo.fn_format_string(o.id) AS draft_format,
  po.part_type_id,
  pt.type_name,
  o.rating,
  po.unit_id,
  o.dlt_sess AS del_tract_id
FROM core_entity o
JOIN core_entitytype et ON et.type_key = o.type_key_id
JOIN pdm_partobject po ON po.entity_ptr_id = o.id
JOIN pdm_parttype pt ON pt.part_type = po.part_type_id
LEFT JOIN core_entity d ON d.id = o.parent_id;