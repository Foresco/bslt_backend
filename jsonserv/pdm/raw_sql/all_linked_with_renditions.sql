SELECT a.child_id
FROM fn_linked_all_w_renditions(%(parent_id)s, %(quantity)s, %(link_classes)s) a;