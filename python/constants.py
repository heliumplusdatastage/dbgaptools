
########## XML DD INPUT CONSTANTS
# Standardized vocab for data columns
VARIABLE_ACC_FIELD      = "VARIABLE_ACC"
DATASET_ACC_FIELD       = "DATASET_ACC"
STUDY_ACC_FIELD         = "STUDY_ACC"
DATASET_PART_SET_FIELD  = 'DATASET_PARTICIPANT_SET'
DATASET_DESC_FIELD      = 'DATASET_DESC'
ENCODED_VALUE_FIELD     = 'ENCODED_VALUES'
VARNAME_FIELD           = 'VARNAME'
VARDESC_FIELD           = 'VARDESC'
TYPE_FIELD              = 'TYPE'
UNITS_FIELD             = 'UNITS'
MIN_FIELD               = 'MIN'
MAX_FIELD               = 'MAX'
UNIQUE_KEY_FIELD        = 'UNIQUEKEY'
VALUES_FIELD            = 'VALUES'


READ_DBGAP_COLUMN_ORDER = [VARIABLE_ACC_FIELD, DATASET_ACC_FIELD,
                           DATASET_PART_SET_FIELD, STUDY_ACC_FIELD,
                           DATASET_DESC_FIELD, VARNAME_FIELD,
                           VARDESC_FIELD, TYPE_FIELD,
                           UNITS_FIELD, MIN_FIELD,
                           MAX_FIELD, UNIQUE_KEY_FIELD,
                           VALUES_FIELD]

########## JSON OUTPUT CONSTANTS
# Value that will fill missing data slots
MISSING_DATA_VALUE = None

# Required data columns in json output
REQUIRED_JSON_COLS = [VARIABLE_ACC_FIELD, DATASET_ACC_FIELD,
                      STUDY_ACC_FIELD, VARNAME_FIELD]

# Required data columns in json output
OPTIONAL_JSON_COLS = [DATASET_PART_SET_FIELD, DATASET_DESC_FIELD,
                      VARDESC_FIELD, UNITS_FIELD, ENCODED_VALUE_FIELD]