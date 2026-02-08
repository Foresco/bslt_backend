-- Удаление позиции

-- Отгрузки
UPDATE manufacture_shipment SET dlt_sess = 6638
WHERE prod_order_link_id IN (
SELECT id FROM core_link WHERE child_id = 2145 AND link_class = 'prodorderlink' AND dlt_sess = 0
) AND dlt_sess = 0;

-- Отчеты
UPDATE manufacture_workerreportconsist SET dlt_sess = 6638
WHERE task_link_id IN (
SELECT id FROM manufacture_prodorderlinkworker WHERE prod_order_link_id IN (
SELECT id FROM core_link WHERE child_id = 2145 AND link_class = 'prodorderlink' AND dlt_sess = 0
)
) AND dlt_sess = 0;

-- Задания
UPDATE manufacture_prodorderlinkworker SET dlt_sess = 6638
WHERE prod_order_link_id IN (
SELECT id FROM core_link WHERE child_id = 2145 AND link_class = 'prodorderlink' AND dlt_sess = 0
) AND dlt_sess = 0;

-- Операции
UPDATE pdm_tprow  SET dlt_sess = 6638
WHERE route_id IN (
SELECT id FROM pdm_route WHERE subject_id = 2145
) AND dlt_sess = 0;

-- Элементы маршрута
UPDATE pdm_routepoint SET dlt_sess = 6638
WHERE route_id IN (
SELECT id FROM pdm_route WHERE subject_id = 2145
) AND dlt_sess = 0;

-- Маршруты
UPDATE pdm_route SET dlt_sess = 6638
WHERE subject_id = 2145
AND dlt_sess = 0;

-- Вхождения
UPDATE core_link SET dlt_sess = 6638
WHERE child_id = 2145 AND link_class = 'prodorderlink' AND dlt_sess = 0;