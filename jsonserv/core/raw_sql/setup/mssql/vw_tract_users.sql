CREATE OR ALTER VIEW vw_tract_users
AS
SELECT s.id,
s.user_id,
CASE
    WHEN COALESCE(u.first_name, '') > '' THEN u.username
    ELSE u.username
END AS user_name,
s.session_datetime AS tract_datetime,
s.comment AS remark,
s.notice_id AS note_id
FROM core_usersession s
INNER JOIN auth_user u ON u.id = s.user_id;