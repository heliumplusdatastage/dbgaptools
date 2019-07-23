import pytest
import os
import logging
import pandas as pd
import numpy as np
import json

import constants as const
import write_functions as wf
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

@pytest.fixture
def test_variable_dict():
    return {const.VALUES_FIELD: "0=Derp",
            "X__1": "1=Nerp",
            "X__2": "2=Flerp"}

@pytest.fixture
def bad_variable_dict():
    return {const.VALUES_FIELD: "0=Derp",
            "X_1": "1=Nerp",
            "X__2": "2=Flerp"}

def test_dbgap_to_json_no_values_field(test_dd):
    with pytest.raises(cf.DbGapDataDictError) as err:
        wf.dbgap_dd_to_json(test_dd, [])
    assert str(err.value) == "Required field {0} missing from DataDictionary!".format(const.VALUES_FIELD)

def test_dbgap_to_json_output(data_dir):
    csv_file = os.path.join(data_dir, 'phs000001.v1.pht000001.v1.ardpheno.data_dict_2008_10_31.csv')
    json_file = os.path.join(data_dir, 'phs000001.v1.pht000001.v1.ardpheno.data_dict_2008_10_31.json')
    dd_in = pd.read_csv(csv_file, dtype=object)
    dd_in = wf.dbgap_dd_to_json(dd_in, const.REQUIRED_JSON_COLS + const.OPTIONAL_JSON_COLS)
    with open(json_file, "r") as fh:
        dd_out = json.load(fh)
    assert len(dd_in) == len(dd_out)
    for i in range(len(dd_in)):
        assert dd_in[i] == dd_out[i]

def test_unpack_encoded_values(test_variable_dict, bad_variable_dict):
    assert wf.unpack_encoded_vals({const.VALUES_FIELD: None}) is None
    assert json.dumps(wf.unpack_encoded_vals(test_variable_dict)) == json.dumps({"0": "Derp", "1": "Nerp", "2": "Flerp"})
    assert json.dumps(wf.unpack_encoded_vals(bad_variable_dict)) == json.dumps({"0": "Derp"})
    bad_variable_dict["X__1"] = bad_variable_dict["X_1"]
    assert json.dumps(wf.unpack_encoded_vals(bad_variable_dict)) == json.dumps({"0": "Derp", "1": "Nerp", "2": "Flerp"})
    bad_variable_dict.pop(const.VALUES_FIELD)
    with pytest.raises(KeyError):
        wf.unpack_encoded_vals(bad_variable_dict)
