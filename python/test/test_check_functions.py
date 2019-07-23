import pytest
import os
import logging
import pandas as pd
import numpy as np

import constants as const
import check_functions as cf

LOGGER = logging.getLogger(__name__)

@pytest.fixture
def data_dir():
    this_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(this_dir, 'data_files/')

@pytest.fixture
def test_dd():
    dd = pd.DataFrame()
    for col in const.REQUIRED_JSON_COLS:
        dd[col] = np.nan
    dd[const.VARIABLE_ACC_FIELD] = pd.Series(["one", "two", "three"])
    return dd

def test_good_data_pass(data_dir):
    csv_file = os.path.join(data_dir, 'phs000001.v1.pht000001.v1.ardpheno.data_dict_2008_10_31.csv')
    dd = pd.read_csv(csv_file)
    cf.check_dd(dd, const.REQUIRED_JSON_COLS)

def test_good_data_pass_with_optional_fields(data_dir):
    csv_file = os.path.join(data_dir, 'phs000001.v1.pht000001.v1.ardpheno.data_dict_2008_10_31.csv')
    dd = pd.read_csv(csv_file)
    cf.check_dd(dd, const.REQUIRED_JSON_COLS, optional_cols=["TYPE"])

def test_handles_missing_required_col(test_dd):
    with pytest.raises(cf.DbGapDataDictError) as err:
        cf.check_dd(test_dd, const.REQUIRED_JSON_COLS+["DERP"])
    assert str(err.value) == "Required column 'DERP' missing from data dictionary!"

def test_warns_missing_optional_col(test_dd, caplog):
    cf.check_dd(test_dd, const.REQUIRED_JSON_COLS, optional_cols=["DERP"])
    assert "Optional columns missing from data dictionary: DERP" in caplog.text

def test_warns_nonstandard_col(test_dd, caplog):
    test_dd["DERP"] = np.nan
    cf.check_dd(test_dd, const.REQUIRED_JSON_COLS, const.OPTIONAL_JSON_COLS)
    assert "Ignoring columns in data dictionary: DERP" in caplog.text

def test_warns_no_encoded_values(test_dd, caplog):
    test_dd = test_dd[[x for x in test_dd.columns if x != const.VALUES_FIELD]]
    cf.check_dd(test_dd, [const.VARIABLE_ACC_FIELD])
    assert "No encoded value fields detected in data dictionary!" in caplog.text

def test_handles_no_equals_in_encoded(test_dd):
    test_dd[const.VALUES_FIELD] = np.nan
    test_dd.loc[test_dd[const.VARIABLE_ACC_FIELD] == "one", const.VALUES_FIELD] = "DERP"
    with pytest.raises(cf.DbGapDataDictError) as err:
        cf.check_dd(test_dd, [const.VARIABLE_ACC_FIELD])
    assert str(err.value) == "Variable one contains encoded value field that doesn't follow formatting (CODE=VAL): DERP"

def test_handles_empty_encoded_value(test_dd):
    test_dd[const.VALUES_FIELD] = np.nan
    test_dd.loc[test_dd[const.VARIABLE_ACC_FIELD] == "one", const.VALUES_FIELD] = "DERP="
    with pytest.raises(cf.DbGapDataDictError) as err:
        cf.check_dd(test_dd, [const.VARIABLE_ACC_FIELD])
    assert str(err.value) == "Variable one contains correctly formatted encoded field but value is empty: DERP="

def test_warns_multi_encoded_value(test_dd, caplog):
    test_dd[const.VALUES_FIELD] = np.nan
    test_dd.loc[test_dd[const.VARIABLE_ACC_FIELD] == "one", const.VALUES_FIELD] = "DERP=12Nerp=10"
    cf.check_dd(test_dd, [const.VARIABLE_ACC_FIELD])
    assert "Variable one possibly contains multiple encoded variables in single field: DERP=12Nerp=10" in caplog.text
