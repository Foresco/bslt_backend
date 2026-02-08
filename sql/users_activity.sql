SELECT * 
FROM core_usersession us
INNER JOIN auth_user u ON (u.id = user_id)
ORDER BY session_datetime DESC