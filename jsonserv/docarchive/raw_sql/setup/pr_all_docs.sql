CREATE OR REPLACE FUNCTION pr_all_docs(
  IN _object_id INTEGER, 
  IN _doc_types TEXT, 
  IN _notices SMALLINT,
  IN _levels INTEGER,
  IN _archive_id INTEGER, 
  OUT object_id INTEGER, 
  OUT doc_id INTEGER, 
  OUT folder_name CHARACTER VARYING, 
  OUT doc_code CHARACTER VARYING, 
  OUT doc_type CHARACTER VARYING, 
  OUT o_quant DOUBLE PRECISION,
  OUT arcdoc_id INTEGER, 
  OUT version_num INTEGER
) RETURNS SETOF RECORD
LANGUAGE plpgsql
AS $$
BEGIN
  -- Таблица c объектами
  CREATE TEMPORARY TABLE a_doc_heads (
    c_doc_object_id INT, -- Идентификатор объекта для связи с файлами
    c_object_id INT DEFAULT NULL, -- Идентификатор объекта (извещения) от архивных документов
    c_o_quant FLOAT,
    c_arcdoc_id INT DEFAULT NULL -- Идентификатор архивного документа (отдельно, чтобы не запутаться)
    ) ON COMMIT DROP;
  -- Таблица с типами
  CREATE TEMPORARY TABLE a_doc_types (c_doc_type_id INT) ON COMMIT DROP;
  -- Заполнение списком типов
  IF (_doc_types = '') THEN
    -- Включаем все возможные варианты
    INSERT INTO a_doc_types(c_doc_type_id)
    SELECT id FROM docarchive_documenttype;
  ELSE
    INSERT INTO a_doc_types(c_doc_type_id)
    SELECT CAST(SPLIT_PART(_doc_types, ', ', GENERATE_SERIES) AS INT)
    FROM GENERATE_SERIES(1, (CHAR_LENGTH(_doc_types) - CHAR_LENGTH(REPLACE(_doc_types, ', ', '')))/2 + 1);
  END IF;
  -- Получение списка объектов
  INSERT INTO a_doc_heads (c_doc_object_id, c_o_quant)
  SELECT o.child_id, o.quantity
  FROM fn_all_objects_level(_object_id, 1, _levels) o;
  -- Вставка ссылок на базовые исполнения
  INSERT INTO a_doc_heads (c_doc_object_id)
  SELECT DISTINCT r.parent_id
  FROM a_doc_heads a
  INNER JOIN pdm_rendition r ON (r.rendition_id = a.c_doc_object_id) AND (r.dlt_sess = 0)
  LEFT JOIN a_doc_heads ta ON (ta.c_doc_object_id = r.parent_id)
  WHERE (ta.c_doc_object_id IS NULL);

  IF (_notices = 1) THEN -- Если надо выгружать и извещения
    INSERT INTO a_doc_heads (c_doc_object_id)
    SELECT DISTINCT nl.notice_id
    FROM a_doc_heads a
    INNER JOIN vw_notice_links nl ON (nl.object_id = a.c_doc_object_id) AND (nl.dlt_sess = 0);
  END IF;

  -- Вставка ссылок на архивные документы
  INSERT INTO a_doc_heads (c_doc_object_id, c_object_id, c_arcdoc_id)
  SELECT DISTINCT al.parent_id, MIN(a.c_doc_object_id), -- Берем первый из объектов (чтобы не задваивать)
  al.parent_id
  FROM a_doc_heads a
  INNER JOIN core_link al ON (al.child_id = a.c_doc_object_id) AND (al.link_class = 'arcdocumentobject') AND (al.dlt_sess = 0)
  GROUP BY al.parent_id;

  RETURN QUERY SELECT COALESCE(a.c_object_id, a.c_doc_object_id), d.id, d.folder_name, d.doc_code, 
  d.doc_type, a.c_o_quant, a.c_arcdoc_id, d.version_num
  FROM (SELECT c_doc_object_id, c_object_id, c_arcdoc_id, SUM(c_o_quant) AS c_o_quant 
  FROM a_doc_heads GROUP BY c_doc_object_id, c_object_id, c_arcdoc_id) a
  INNER JOIN vw_files_for_upload d ON (d.object_id = a.c_doc_object_id) AND (d.archive_id = _archive_id) AND (d.del_tract_id = 0)
  INNER JOIN a_doc_types dt ON (dt.c_doc_type_id = d.doc_type_id); -- Только указанные типы
END $$
;