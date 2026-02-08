CREATE VIEW vw_designmater AS
SELECT
  cl.id,
  cl.parent_id,
  cl.child_id
FROM
pdm_designmater dm
INNER JOIN core_link cl ON (cl.id = dm.link_ptr_id) AND (cl.dlt_sess = 0);

GRANT SELECT ON TABLE vw_designmater to basauser;