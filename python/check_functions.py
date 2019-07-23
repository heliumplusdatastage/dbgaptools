import logging
import pandas as pd

import constants as const


class DbGapDataDictError(BaseException):
    pass


def check_dd(dd, required_cols, optional_cols=[]):

    logging.info("Checking dbgap data dictionary structure...")

    # Check to make sure all required columns present
    missing_cols = []
    for required_col in required_cols:
        if required_col not in dd.columns:
            # Log missing column name to stderr
            logging.error("Required column '{0}' missing from data dictionary!".format(required_col))
            missing_cols.append(required_col)

    # Raise error if any columns are missing
    if missing_cols:
        raise DbGapDataDictError("Required column '{0}' missing from data dictionary!".format(", ".join(missing_cols)))

    # Warn if any optional columns are missing
    missing_cols = []
    for optional_col in optional_cols:
        if optional_col not in dd.columns and optional_col != const.ENCODED_VALUE_FIELD:
            missing_cols.append(optional_col)
    if missing_cols:
        logging.warning("Optional columns missing from data dictionary: {0}".format(", ".join(missing_cols)))

    # Warn if contains any non-standard colnames
    non_standard_cols = []
    for colname in dd.columns:
        if colname not in required_cols and colname not in optional_cols and not colname.startswith("X_") and not colname == const.VALUES_FIELD:
            non_standard_cols.append(colname)
    if non_standard_cols:
        logging.warning("Ignoring columns in data dictionary: {0}".format(", ".join(non_standard_cols)))

    # Check that any value fields look good
    value_cols = [x for x in dd.columns if x.startswith("X_") or x == const.VALUES_FIELD]
    if not value_cols:
        logging.warning("No encoded value fields detected in data dictionary!")

    # Check all encoded value fields in data dictionary for formatting
    for value_col in value_cols:
        dd.apply(check_encoded_val, value_col=value_col, axis=1)


def check_encoded_val(row, value_col):
    var_id = row[const.VARIABLE_ACC_FIELD]
    enc_val = row[value_col]
    if not pd.isnull(enc_val):
        # Enforce "=" in encoded value
        if not "=" in enc_val:
            raise DbGapDataDictError("Variable {0} contains encoded value field that doesn't follow formatting (CODE=VAL): {1}".format(var_id, enc_val))
        enc_val_list = enc_val.split("=")
        # Warn if more or less than expected number of fields present after splitting
        if len(enc_val_list) > 2:
            logging.warning("Variable {0} possibly contains multiple encoded variables in single field: {1}".format(var_id, enc_val))
        elif len(enc_val_list) == 2 and not enc_val_list[1]:
            raise DbGapDataDictError("Variable {0} contains correctly formatted encoded field but value is empty: {1}".format(var_id, enc_val))
