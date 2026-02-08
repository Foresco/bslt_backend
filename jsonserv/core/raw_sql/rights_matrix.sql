SELECT u.username, u.first_name, u.last_name, --* 
g.name AS group_name,
p.name AS right_name, p.codename
FROM 
auth_user_groups ug
INNER JOIN auth_user u ON (u.id = ug.user_id)
INNER JOIN auth_group g ON (g.id = ug.group_id)
INNER JOIN auth_group_permissions gp ON (gp.group_id = ug.group_id)
INNER JOIN auth_permission p ON (p.id = gp.permission_id)
ORDER BY u.username, g.name, p.name;