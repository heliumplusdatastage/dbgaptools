import pandas as pd

import constants as const
import check_functions as cf


def dbgap_dd_to_json(dd, output_cols, missing_val_char=None):

    # Check to make sure values field exists
    if not const.VALUES_FIELD in dd.columns:
        raise cf.DbGapDataDictError("Required field {0} missing from DataDictionary!".format(const.VALUES_FIELD))

    # Convert pandas dataframe to list of dictionaries (one for each variable)
    dd_dict = dd.to_dict(orient="records")

    # Reformat each variable record and return final dictionary
    return [get_variable_dict(variable, output_cols, missing_val_char) for variable in dd_dict]


def get_variable_dict(variable_dict, output_cols, missing_val_char):
    # Convencience function to converts variable into dictionary with encoded values unpacked and only required fields present

    # Unpack encoded values into separate dictionary
    variable_dict[const.ENCODED_VALUE_FIELD] = unpack_encoded_vals(variable_dict)

    # Set any missing values to missing value character
    for key, val in variable_dict.items():
        variable_dict[key] = missing_val_char if pd.isnull(val) or pd.isna(val) or val in ["", None] else val

    # Filter out non-required columns
    return {key: val for key,val in variable_dict.items() if key in output_cols}


def unpack_encoded_vals(variable_dict):
    # Convenience function to unpacks encoded values for a variable into a single dictionary
    enc_val_dict = {}

    # Add first value from VALUES field
    if not pd.isna(variable_dict[const.VALUES_FIELD]):
        # Only add encoding if valid (i.e. of form 'NAME=VALUE')
        if "=" in variable_dict[const.VALUES_FIELD]:
            enc_val_dict[variable_dict[const.VALUES_FIELD].split("=")[0]] = variable_dict[const.VALUES_FIELD].split("=")[1]

    # Check additional values (e.g X__1, X__2) in numerical order to get any remaining encodings
    i = 1
    var_key = "X__%s" % i
    while var_key in variable_dict:
        # Only add encoding if valid (i.e. of form 'NAME=VALUE')
        if not pd.isna(variable_dict[var_key]) and "=" in variable_dict[var_key]:
            enc_val_dict[variable_dict[var_key].split("=")[0]] = variable_dict[var_key].split("=")[1]

        # Increment count to move on to next numeric value column
        var_key = "X__%s" % i
        i += 1

    # Return encoded values as dictionary
    return enc_val_dict if enc_val_dict else None
