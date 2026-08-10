python manage.py loaddata place_types.json entity_types.json
python manage.py loaddata essences.json property_types.json
python manage.py loaddata core_form_fields.json
python manage.py import_json 1 0 core/fixtures/menu_items.json
python manage.py import_json 1 0 core/fixtures/measure_units.json
python manage.py import_json 1 0 core/fixtures/panels.json
python manage.py import_json 1 0 core/fixtures/type_panels.json

python manage.py loaddata pdm_entity_types.json rendition_tails.json part_types.json
python manage.py loaddata sources.json preferences.json sections.json
python manage.py loaddata change_types.json notice_reasons.json notice_types.json
python manage.py loaddata roles.json norm_units.json route_states.json
python manage.py loaddata tp_row_types.json formats.json pdm_form_fields.json
python manage.py loaddata pdm_type_settings.json

python manage.py import_json 1 0 pdm/fixtures/menu_items.json
python manage.py import_json 1 0 pdm/fixtures/panels.json
python manage.py import_json 1 0 pdm/fixtures/type_panels.json
python manage.py import_json 1 0 pdm/fixtures/part_states.json


python manage.py loaddata docarchive_entity_types.json archives_and_folders.json docarchive_type_settings.json
python manage.py loaddata docarchive_form_fields.json docarchive_entity_types.json python manage.py document_types.json

python manage.py import_json 1 0 docarchive/fixtures/type_panels.json
python manage.py import_json 1 0 docarchive/fixtures/panels.json
python manage.py import_json 1 0 docarchive/fixtures/menu_items.json

python manage.py loaddata community_entity_types.json letter_types.json
python manage.py loaddata letter_directions.json task_types.json
python manage.py loaddata community_form_fields.json community_type_settings.json

python manage.py import_json 1 0 community/fixtures/menu_items.json
python manage.py import_json 1 0 community/fixtures/panels.json
python manage.py import_json 1 0 community/fixtures/type_panels.json

python manage.py loaddata external_partners.json
python manage.py import_json 1 0 exchange/fixtures/panels.json

python manage.py loaddata manufacture_entity_types.json manufacture_form_fields.json
python manage.py loaddata prodorder_states.json work_shifts.json
python manage.py loaddata supply_states.json link_worker_states.json order_link_tp_row_states.json
python manage.py loaddata spec_account_states.json payment_states.json
python manage.py loaddata manufacture_type_settings.json manufacture_panels.json

python manage.py import_json 1 0 manufacture/fixtures/menu_items.json
python manage.py import_json 1 0 manufacture/fixtures/panels.json
python manage.py import_json 1 0 manufacture/fixtures/type_panels.json
python manage.py import_json 1 0 manufacture/fixtures/order_link_tp_row_states.json

python manage.py loaddata mdm_type_settings.json

python manage.py import_json 1 0 mdm/fixtures/menu_items.json
python manage.py import_json 1 0 mdm/fixtures/panels.json
python manage.py import_json 1 0 mdm/fixtures/type_panels.json

python manage.py loaddata person_category.json staff_form_fields.json
python manage.py loaddata staff_type_settings.json

python manage.py import_json 1 0 staff/fixtures/panels.json
python manage.py import_json 1 0 staff/fixtures/type_panels.json

python manage.py loaddata supply_entity_types.json supply_form_fields.json
python manage.py loaddata supply_type_settings.json

python manage.py import_json 1 0 supply/fixtures/menu_items.json
python manage.py import_json 1 0 supply/fixtures/panels.json
python manage.py import_json 1 0 supply/fixtures/type_panels.json

python manage.py loaddata toolover_entity_types.json toolover_sources.json toolover_preferences.json toolover_states.json
python manage.py loaddata toolover_fields.json


pause
