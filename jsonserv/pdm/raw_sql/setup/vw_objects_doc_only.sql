CREATE OR REPLACE VIEW vw_objects_doc_only
AS 
SELECT o.id,
  CASE
  WHEN et.doc_key AND pod.part_type_id::text = 'document'::text THEN (o.code::text || COALESCE(' '::text || d.code::text, ''::text))::character varying
  ELSE o.code
  END AS object_code,
  po.title AS object_name,
  fn_format_string(o.id) AS draft_format,
  po.part_type_id AS type_id,
  pt.type_name,
  o.rating,
  po.unit_id,
  o.dlt_sess AS del_tract_id
FROM core_entity o
JOIN core_entitytype et ON et.type_key::text = o.type_key_id::text
JOIN pdm_partobject po ON po.entity_ptr_id = o.id
JOIN pdm_parttype pt ON pt.part_type::text = po.part_type_id::text
LEFT JOIN core_entity d ON d.id = o.parent_id
JOIN pdm_partobject pod ON pod.entity_ptr_id = o.parent_id;