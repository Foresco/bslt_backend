GRANT EXECUTE ON FUNCTION fn_format_string(
  _part_object_id INTEGER
) to basalta2;

GRANT EXECUTE ON FUNCTION fn_last_notice_get(
  IN _object_id INT
) to basalta2;

GRANT EXECUTE ON FUNCTION fn_files_str(
  _entity_id INT
) to basalta2;

GRANT EXECUTE ON FUNCTION fn_has_parts(
  _object_id integer
) to basalta2;

GRANT EXECUTE ON FUNCTION fn_has_arcdocs(
  _object_id integer
) to basalta2;

GRANT SELECT ON TABLE vw_partobject_files to basalta2;

GRANT SELECT ON TABLE vw_root_tree to basalta2;

GRANT SELECT ON TABLE vw_staff_tree to basalta2;