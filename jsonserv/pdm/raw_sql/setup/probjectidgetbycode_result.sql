CREATE TYPE probjectidgetbycode_result AS (
  object_id int4,
  type_id varchar(20),
  object_code varchar(200),
  object_doc varchar(200),
  object_name varchar(250),
  unit_id int4,
  short_name varchar(10),
  form_name varchar(25),
  result_id int4
);