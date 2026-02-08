python manage.py loaddata place_types.json entity_types.json panels.json
python manage.py loaddata essences.json property_types.json
python manage.py loaddata form_fields.json
python manage.py import_json 1 0 core/fixtures/menu_items.json
python manage.py import_json 1 0 core/fixtures/measure_units.json
python manage.py import_json 1 0 core/fixtures/type_panels.json

python manage.py loaddata pdm_entity_types.json pdm_panels.json rendition_tails.json part_types.json
python manage.py loaddata sources.json preferences.json states.json states.json
python manage.py loaddata change_types.json notice_reasons.json notice_types.json
python manage.py loaddata roles.json norm_units.json route_states.json
python manage.py loaddata tp_row_types.json

python manage.py import_json 1 0 pdm/fixtures/menu_items.json

python manage.py loaddata docarchive_entity_types.json archives_and_folders.json
python manage.py loaddata document_types.json

