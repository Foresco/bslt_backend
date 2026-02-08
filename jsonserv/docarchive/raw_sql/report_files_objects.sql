SELECT
o.code AS object_code,
po.title AS object_name,
a.o_quant,
po.weight,
(mo.code::TEXT || COALESCE(' '::TEXT || md.code::TEXT, ''::TEXT))::CHARACTER VARYING AS mater_code,
g.code AS group_name,
a.version_num,
n.code AS notice_num,
pn.notice_date,
ct.list_value AS change_type,
nl.change_num,
a.doc_code,
onl.comment AS remark,
a.doc_type
FROM pr_all_docs(%(object_id)s, %(doc_types)s, %(notices)s::SMALLINT, %(archive)s) a
INNER JOIN core_entity o ON (o.id = a.object_id)
INNER JOIN pdm_partobject po ON (po.entity_ptr_id = o.id)
LEFT JOIN core_entity g ON (g.id = o.group_id)
LEFT JOIN core_link m ON (m.parent_id = o.id) AND (m.link_class = 'designmater') AND (m.dlt_sess = 0)
LEFT JOIN core_entity mo ON (mo.id = m.child_id)
LEFT JOIN core_entity md ON (md.id = mo.parent_id)
LEFT JOIN vw_notice_links nl ON (nl.object_id = a.doc_id) AND (nl.dlt_sess = 0)
LEFT JOIN pdm_changetype ct ON (ct.id = nl.change_type_id)
LEFT JOIN core_entity n ON (n.id = nl.notice_id)
LEFT JOIN pdm_notice pn ON (pn.entity_ptr_id = nl.notice_id)
LEFT JOIN vw_notice_links onl ON (onl.object_id = a.object_id) AND (onl.notice_id = nl.notice_id) AND (onl.dlt_sess = 0)
ORDER BY o.code, a.doc_code;