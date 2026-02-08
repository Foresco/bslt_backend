SELECT a.child_id
FROM fn_linked_all(%(parent_id)s, %(quantity)s, %(link_classes)s) a;