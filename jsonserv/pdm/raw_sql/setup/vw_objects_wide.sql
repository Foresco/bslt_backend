CREATE OR REPLACE VIEW vw_objects_wide
AS 
SELECT 
  o.id,
  CASE
  WHEN et.doc_key THEN (o.code::text || COALESCE(' '::text || d.code::text, ''::text))::character varying
  ELSE o.code
  END AS key_code,
  o.code AS object_code,
  d.code AS object_doc,
  po.title AS object_name,
  fn_format_string(o.id) AS draft_format,
  po.part_type_id AS type_id,
  o.group_id,
  pt.type_name,
  po.part_type_id AS form_name,
  o.rating,
  po.preference_id AS pref_id,
  po.unit_id,
  po.source_id,
  u.short_name,
  po.weight,
  po.weight_unit_id AS w_unit_id,
  o.dlt_sess AS del_tract_id
FROM core_entity o
JOIN core_entitytype et ON et.type_key::text = o.type_key_id::text
JOIN pdm_partobject po ON po.entity_ptr_id = o.id
JOIN pdm_parttype pt ON pt.part_type::text = po.part_type_id::text
LEFT JOIN core_measureunit u ON u.id = po.unit_id
LEFT JOIN core_entity d ON d.id = o.parent_id;