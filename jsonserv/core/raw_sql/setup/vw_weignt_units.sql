CREATE OR REPLACE VIEW vw_weignt_units
AS 
SELECT 
  u.id,
  u.numerator_id,
  nu.short_name AS numerator,
  du.short_name AS denominator
FROM core_measureunit u
JOIN core_measureunit nu ON nu.id = u.numerator_id
JOIN core_measureunit du ON du.id = u.denominator_id;