CREATE VIEW vw_designroles AS
SELECT dr.subject_id, r.list_value AS role_name, d.designer 
FROM pdm_designrole dr
INNER JOIN pdm_role r ON (r.id = dr.role_id)
INNER JOIN pdm_designer d ON (d.id = dr.designer_id)
WHERE (dr.dlt_sess = 0);
