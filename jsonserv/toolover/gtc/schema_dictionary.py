# Схемы разбора параметров *.p21
schema_dictionary = {
    'ALIAS_IDENTIFICATION': (
        'alias_id',
        'alias_scope',
        'alias_version_id',
        'description',
        'is_applied_to'
    ),
    'CLASSIFICATION_ASSOCIATION': (
        'associated_classification',
        'classified_element',
        'definition',
        'role'
    ),
    'COATING': (
        'coating_name',
        'coating_process'
    ),
    'CUTTING_CONDITION': (
        'condition_name',
    ),
    'DATE_TIME': (
        'date',
        'time'
    ),
    'DIGITAL_DOCUMENT': (
        'associated_document_version',
        'common_location',
        'content',
        'creation',
        'unknown',
        'id',
        'representation_format',
        'description',
        'file'
    ),
    'DIGITAL_FILE': (
        'content',
        'creation',
        'unknown',
        'external_id_and_location',
        'file_format',
        'file_id',
        'version_id',
        'unknown1'
    ),
    'DOCUMENT': (
        'description',
        'document_id',
        'name'
    ),
    'DOCUMENT_ASSIGNMENT': (
        'assigned_document',
        'is_assigned_to',
        'role'
    ),
    'DOCUMENT_FORMAT_PROPERTY': (
        'character_code',
        'data_format',
        'unknown'
    ),
    'DOCUMENT_LOCATION_PROPERTY': (
        'location_name',
    ),
    'DOCUMENT_VERSION': (
        'assigned_document',
        'description',
        'id'
    ),
    'EFFECTIVITY': (
        'organization',
        'description',
        'effectivity_context',
        'id',
        'version_id',
        'period',
        'start_definition',
        'unknown'
    ),
    'EFFECTIVITY_ASSIGNMENT': (
        'assigned_effictivity',
        'effective_element',
        'effectivity_indication',
        'role'
    ),
    'EXTERNAL_FILE_ID_AND_LOCATION': (
        'external_id',
        'location'
    ),
    'EXTERNAL_LIBRARY_REFERENCE': (
        'description',
        'external_id',
        'library_type'
    ),
    'GENERAL_CLASSIFICATION': (
        'classification_source',
        'description',
        'id',
        'unknown',
        'version_id'
    ),
    'GRADE': (
        'coating',
        'cutting_condition',
        'identifier',
        'standard_designation',
        'substrate',
        'workpiece_material'
    ),
    'ITEM': (
        'description',
        'id',
        'name'
    ),
    'ITEM_CHARACTERISTIC_ASSOCIATION': (
        'associated_characteristic',
        'associated_item',
        'relation_type'
    ),
    'ITEM_DEFINITION': (
        'associated_item_version',
        'inknown',
        'id',
        'name'
    ),
    'ITEM_VERSION': (
        'associated_item',
        'description',
        'id'
    ),
    'LANGUAGE': (
        'country_code',
        'language_code'
    ),
    'MATERIAL_DESIGNATION': (
        'material_name',
    ),
    'MULTI_LANGUAGE_STRING': (
        'extra_language_strings',  # Мое предположение
        'primary_language_string'
    ),
    'NUMERICAL_VALUE': (
        'value_name',
        'significant_digits',
        'unit_component',
        'value_component'
    ),
    'ORGANIZATION': (
        'delivery_address',
        'id',
        'organization_name',
        'organization_type',
        'postal_address',
        'visitor_address'
    ),
    'PERSON_ORGANIZATION_ASSIGNMENT': (
        'associated_organization',
        'description',
        'is_applied_to',
        'role'
    ),
    'PLIB_CLASS_REFERENCE': (
        'code',
        'supplier_bsu',
        'version'
    ),
    'PLIB_PROPERTY_REFERENCE': (
        'code',
        'name_scope',
        'version'
    ),
    'PROPERTY': (
        'unit',
        'description',
        'id',
        'property_source',
        'property_type',
        'version_id'
    ),
    'PROPERTY_VALUE_ASSOCIATION': (
        'unknown1',
        'described_element',
        'describing_property_value',
        'unknown2',
        'unknown3'
    ),
    'PROPERTY_VALUE_REPRESENTATION': (
        'definition',
        'unknown1',
        'unknown2',
        'value',
        'unknown4'
    ),
    'PROPERTY_VALUE_REPRESENTATION_RELATIONSHIP': (
        'description',
        'related',
        'relating',
        'relation_type'
    ),
    'SPECIFIC_ITEM_CLASSIFICATION': (
        'associated_items',
        'classification_name',
        'description'
    ),
    'STRING_VALUE': (
        'value_name',
        'value_specification'
    ),
    'STRING_WITH_LANGUAGE': (
        'contents',
        'language'
    ),
    'SUBSTRATE': (
        'name',
    ),
    'UNIT': (
        'unit name',
    )
}

# Первая звездочка - есть в шаблоне парсинга
# Вторая звездочка - есть обработчик в p21bulder

# ALIAS_IDENTIFICATION *
# CLASSIFICATION_ASSOCIATION *
# COATING *
# CUTTING_CONDITION *
# DATE_TIME *
# DIGITAL_DOCUMENT *
# DIGITAL_FILE *
# DOCUMENT *
# DOCUMENT_ASSIGNMENT *
# DOCUMENT_FORMAT_PROPERTY *
# DOCUMENT_LOCATION_PROPERTY *
# DOCUMENT_VERSION *
# EFFECTIVITY *
# EFFECTIVITY_ASSIGNMENT *
# EXTERNAL_FILE_ID_AND_LOCATION *
# EXTERNAL_LIBRARY_REFERENCE *
# GENERAL_CLASSIFICATION *
# GRADE *
# ITEM * *
# ITEM_CHARACTERISTIC_ASSOCIATION *
# ITEM_DEFINITION * *
# ITEM_VERSION * *
# LANGUAGE * *
# MATERIAL_DESIGNATION *
# MULTI_LANGUAGE_STRING *
# NUMERICAL_VALUE *
# ORGANIZATION *
# PERSON_ORGANIZATION_ASSIGNMENT * *
# PLIB_CLASS_REFERENCE *
# PLIB_PROPERTY_REFERENCE *
# PROPERTY *
# PROPERTY_VALUE_ASSOCIATION * *
# PROPERTY_VALUE_REPRESENTATION *
# PROPERTY_VALUE_REPRESENTATION_RELATIONSHIP *
# SPECIFIC_ITEM_CLASSIFICATION * *
# STRING_VALUE *
# STRING_WITH_LANGUAGE *
# SUBSTRATE *
# UNIT *