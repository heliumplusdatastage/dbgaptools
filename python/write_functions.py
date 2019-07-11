import os
from datetime import datetime
import pandas as pd
import logging
import csv

import constants as const

def write_dbgap(x, file="", study_name=None, phs=None,
                DD=False, dstype="", generate_fn=False):

    # Check for required info if generating fn
    if generate_fn:
        if study_name is None and phs is None:
            raise IOError("To generate a file name, one of studyname or phs must be provided")

        dstypes = ["pheno","ped","sattr","ssm","subj"]
        if not dstype in dstypes:
            raise IOError("Please specify dstype, one of: {0}".format(", ".join(dstypes)))

        # Make verbose version of dstype
        ftype_map = {
                    "pheno": "Phenotype",
                    "ped"  : "Pedigree",
                    "sattr": "SampleAttributes",
                    "ssm"  : "SampleSubjectMapping",
                    "subj" : "Subject"
                     }

        ftype = ftype_map[dstype]

        # Generate file name
        if study_name is None:
            pt1 = phs
        elif phs is None:
            pt1 = study_name
        else:
            pt1 = "{0}_{1}".format(study_name, phs)

        ftype_str = "{0}DD".format(ftype) if DD else "{0}DS".format(ftype)

        # Make filename
        timestamp = datetime.today().strftime('%Y%m%d')
        file = "{0}_{1}_{2}.txt".format(pt1, ftype_str, timestamp)

    # Raise error if not filename provided
    if not generate_fn and not file:
        raise IOError("Please specify filename or set generate_fn=True")

    filename, file_extension = os.path.splitext(file)
    if file_extension.lower() != ".txt":
        logging.warning("Warning: Output file name recommended to have .txt extension")

    # If there is a column name like "X__*" in a DD, assume it's an encoded values
    # colname and should be set to blank
    if DD:
        colnames = []
        for colname in x.columns:
            if colname.startswith("X__"):
                colnames.append("")
            else:
                colnames.append(colname)
        x.columns = colnames

    # write file
    x.to_csv(file, sep="\t", index=False, quoting=csv.QUOTE_NONE)

def dbgap_dd_to_json(dd, required_cols, optional_cols=[], missing_val_char=None):

    # Check to make sure all required columns present
    errors = False
    for required_col in required_cols:
        if required_col not in dd.columns:
            # Log missing column name to stderr
            logging.error("Required column '{0}' missing from data "
                          "dictionary input to dbgap_dd_to_json!".format(required_col))
            errors = True

    # Raise error if any required columns are missing from data dictionary input
    if errors:
        raise IOError("One or more required columns is missing from the data dictionary input! "
                      "See log above for details.")


    # Convert pandas dataframe to list of dictionaries (one for each variable)
    dd_dict = dd.to_dict(orient="records")

    # Reformat each variable record and return final dictionary
    return [__reformat_variable(variable, required_cols+optional_cols, missing_val_char) for variable in dd_dict]

def __reformat_variable(variable_dict, required_cols, missing_val_char):
    # Convencience function to converts variable into dictionary with encoded values unpacked and only required fields present

    # Unpack encoded values into separate dictionary
    variable_dict[const.ENCODED_VALUE_FIELD] = __unpack_encoded_vals(variable_dict)

    # Set any missing values to missing value character
    for key, val in variable_dict.items():
        variable_dict[key] = missing_val_char if pd.isnull(val) or pd.isna(val) or val in ["", None] else val

    # Filter out non-required columns
    return { key: val for key,val in variable_dict.items() if key in required_cols }

def __unpack_encoded_vals(variable_dict):
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
