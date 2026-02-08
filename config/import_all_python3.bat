python3 manage.py loaddata place_types.json entity_types.json panels.json
python3 manage.py loaddata essences.json property_types.json
python3 manage.py loaddata form_fields.json
python3 manage.py import_json 1 0 core/fixtures/menu_items.json
python3 manage.py import_json 1 0 core/fixtures/measure_units.json
python3 manage.py import_json 1 0 core/fixtures/type_panels.json

python3 manage.py loaddata pdm_entity_types.json rendition_tails.json part_types.json
python3 manage.py loaddata sources.json preferences.json states.json states.json
python3 manage.py loaddata change_types.json notice_reasons.json notice_types.json
python3 manage.py loaddata roles.json norm_units.json route_states.json
python3 manage.py loaddata tp_row_types.json

python3 manage.py import_json 1 0 pdm/fixtures/menu_items.json
python3 manage.py import_json 1 0 pdm/fixtures/panels.json
python3 manage.py import_json 1 0 pdm/fixtures/type_panels.json

python3 manage.py loaddata docarchive_entity_types.json archives_and_folders.json
python3 manage.py loaddata document_types.json

python3 manage.py loaddata manufacture_entity_types.json manufacture_form_fields.json
python3 manage.py loaddata prodorder_states.json work_shifts.json
python3 manage.py loaddata supply_states.json link_worker_states.json order_link_tp_row_states.json

python3 manage.py import_json 1 0 manufacture/fixtures/menu_items.json
python3 manage.py import_json 1 0 manufacture/fixtures/panels.json
python3 manage.py import_json 1 0 manufacture/fixtures/type_panels.json
