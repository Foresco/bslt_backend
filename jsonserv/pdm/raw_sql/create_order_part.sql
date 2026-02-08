SELECT fn_create_order_part AS object_id
FROM fn_create_order_part (%(origin_id)s, %(prod_order_id)s, %(crtd_sess_id)s);