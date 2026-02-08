CREATE FUNCTION check_role_unique() RETURNS TRIGGER AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM pdm_designrole WHERE role_id = NEW.role_id ) THEN
            RAISE EXCEPTION 'Invalid product type: %', NEW.product_type;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;