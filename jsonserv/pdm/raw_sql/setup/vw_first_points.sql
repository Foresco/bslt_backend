CREATE OR REPLACE VIEW vw_first_points
AS
SELECT
  r.subject_id AS object_id,
  rp.place_id AS id,
  ple.parent_id,
  pl.ratio
FROM pdm_route r
JOIN pdm_routepoint rp ON rp.route_id = r.id AND rp.id = r.first_point_id
JOIN core_entity ple ON ple.id = rp.place_id
JOIN core_place pl ON pl.entity_ptr_id = rp.place_id
WHERE r.is_active AND r.dlt_sess = 0;