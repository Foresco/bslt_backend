-- SELECT * FROM prLostRenditions(55061);

-- На сервере не обновлено! Добавлена привязка файлов
CREATE OR REPLACE FUNCTION prLostRenditions (
  _tract_id INT
)
RETURNS INT
AS $$
DECLARE
  a_id INT;
  a_base_id INT;
  a_tail_id INT;
  a_rep_tail CHARACTER VARYING(4);
  a_search_tail CHARACTER VARYING(5);
  a_object_code CHARACTER VARYING (200);
  a_count INT := 0;
BEGIN
  FOR a_tail_id, a_rep_tail, a_search_tail IN
  SELECT id, '-' || list_value, '%-' || list_value FROM pdm_renditiontail LOOP
    FOR a_id, a_object_code IN
    SELECT o.id, REPLACE(o.code, a_rep_tail, '')
    FROM vw_partobject o
    LEFT JOIN pdm_rendition r ON (r.rendition_id = o.id)
    WHERE (o.part_type_id IN ('complex', 'assembly', 'detail'))
    AND (o.code LIKE a_search_tail)
    AND (o.dlt_sess = 0) 
    AND (o.prod_order_id IS NULL) -- Не из заказа
    AND (r.id IS NULL)
    LOOP
      -- Поиск базового исполнения
      SELECT o.id INTO a_base_id FROM vw_partobject o WHERE (o.code = a_object_code) AND (o.dlt_sess = 0) AND (o.prod_order_id IS NULL) LIMIT 1;
      IF FOUND THEN
        INSERT INTO pdm_rendition (parent_id, rendition_id, tail_id, crtd_sess_id, edt_sess, dlt_sess)
        VALUES (a_base_id, a_id, a_tail_id, _tract_id, 0, 0);
        -- Привязка файлов
        INSERT INTO docarchive_entitydocumentversion(entity_id, document_version_id, old_version, crtd_sess_id, edt_sess, dlt_sess)
        SELECT a_id, document_version_id, old_version, _tract_id, 0, 0
        FROM docarchive_entitydocumentversion edv WHERE (edv.entity_id = a_base_id) AND (edv.dlt_sess = 0) AND NOT (edv.old_version)
        AND NOT EXISTS (SELECT 1 FROM docarchive_entitydocumentversion edvt WHERE (edvt.entity_id = a_id) AND (edvt.document_version_id = edv.document_version_id));
        a_count := a_count + 1;
      END IF;
    END LOOP;
  END LOOP;
  RETURN a_count;
END $$ LANGUAGE plpgsql;