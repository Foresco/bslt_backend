SELECT
  o.id,
  o.code,
  b.prcnt
FROM
(SELECT lp.parent_id, CAST(COUNT(*) AS DOUBLE PRECISION)/MIN(a.cnt) AS prcnt
FROM (
  SELECT l.child_id, COUNT(*) OVER () AS cnt
  FROM core_link l
  WHERE (l.parent_id = %(object_id)s) AND (l.link_class = 'partlink') AND (l.dlt_sess = 0)
) a	
INNER JOIN core_link lp ON (lp.child_id = a.child_id) AND (lp.parent_id != %(object_id)s) AND (lp.link_class = 'partlink') AND (lp.dlt_sess = 0)
GROUP BY lp.parent_id) b
INNER JOIN vw_partobject o ON (o.id = b.parent_id) AND (o.prod_order_id IS NULL) -- Из заказов пока не выбираем
ORDER BY b.prcnt DESC, o.code;