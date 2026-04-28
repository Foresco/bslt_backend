CREATE OR REPLACE FUNCTION fn_origin_id_get(
  _head_key CHARACTER VARYING(400)
) RETURNS integer
LANGUAGE sql
AS $$
  SELECT ce.id
  FROM core_entity ce
  INNER JOIN pdm_partobject pp ON (pp.entity_ptr_id = ce.id) AND (pp.prod_order_id IS NULL)
  WHERE (ce.head_key = $1)
  AND (ce.dlt_sess = 0) ORDER BY ce.id LIMIT 1;
$$;