import pytest
import os
import logging
import xml.etree.ElementTree as ET
import pandas as pd

import read_functions as rf
import constants as const

LOGGER = logging.getLogger(__name__)

@pytest.fixture
def data_dir():
    this_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(this_dir, 'data_files/')

def test_handles_dd_file_not_exists():
    missing_file = "not_a_file.txt"
    # Remove file if it already exists to  make sure it's a missing file
    if os.path.exists(missing_file):
        os.remove(missing_file)
    with pytest.raises(FileNotFoundError):
        rf.read_dbgap_dd_xml(missing_file)

def test_handles_dd_file_invalid_xml(data_dir):
    test_file = os.path.join(data_dir, '2a_dbGaP_SubjectPhenotypesDS.txt')
    with pytest.raises(ET.ParseError):
        rf.read_dbgap_dd_xml(test_file)

def test_handles_missing_dataset_id(data_dir):
    test_file = os.path.join(data_dir, 'dd_missing_dataset_id.xml')
    with pytest.raises(rf.DbGapMissingDataError) as err:
        rf.read_dbgap_dd_xml(test_file)
    assert str(err.value) == "Data Table missing the required 'id' attribute!"

def test_handles_missing_study_id(data_dir):
    test_file = os.path.join(data_dir, 'dd_missing_study_id.xml')
    with pytest.raises(rf.DbGapMissingDataError) as err:
        rf.read_dbgap_dd_xml(test_file)
    assert str(err.value) == "Data Table missing the required 'study_id' attribute!"

def test_handles_missing_participant_set_id(data_dir):
    test_file = os.path.join(data_dir, 'dd_missing_participant_set_id.xml')
    with pytest.raises(rf.DbGapMissingDataError) as err:
        rf.read_dbgap_dd_xml(test_file)
    assert str(err.value) == "Data Table missing the required 'participant_set' attribute!"

def test_handles_missing_variable_id(data_dir):
    test_file = os.path.join(data_dir, 'dd_missing_variable_id_field.xml')
    with pytest.raises(rf.DbGapMissingDataError):
        rf.read_dbgap_dd_xml(test_file)

def test_handles_no_datatable(data_dir):
    test_file = os.path.join(data_dir, 'dd_missing_data_table.xml')
    with pytest.raises(ET.ParseError):
        rf.read_dbgap_dd_xml(test_file)

def test_handles_no_variables(data_dir):
    test_file = os.path.join(data_dir, 'dd_missing_variables.xml')
    with pytest.raises(rf.DbGapMissingDataError) as err:
        rf.read_dbgap_dd_xml(test_file)
    assert str(err.value) == "Data table contains no variables!"

def test_handles_missing_req_var_field(data_dir):
    test_file = os.path.join(data_dir, 'dd_missing_req_variable_field.xml')
    with pytest.raises(rf.DbGapMissingDataError) as err:
        rf.read_dbgap_dd_xml(test_file)
    assert str(err.value) == "Missing required variable field 'name'"

def test_handles_duplicate_variable_id(data_dir):
    test_file = os.path.join(data_dir, 'dd_dup_var_id.xml')
    with pytest.raises(rf.DbGapInvalidDataError) as err:
        rf.read_dbgap_dd_xml(test_file)
    assert str(err.value) == "Duplicate variables with id 'phv00164675.v1'"

def test_warns_duplicate_variable_code(data_dir, caplog):
    test_file = os.path.join(data_dir, 'dd_dup_var_code.xml')
    rf.read_dbgap_dd_xml(test_file)
    assert "Variable phv00000137.v1 contains duplicate coded field 'N'" in caplog.text

def test_returns_dataframe(data_dir):
    test_file = os.path.join(data_dir, 'phs000001.v1.pht000001.v1.ardpheno.data_dict_2008_10_31.xml')
    dd = rf.read_dbgap_dd_xml(test_file)
    assert isinstance(dd, pd.DataFrame)

def test_required_columns_present(data_dir):
    test_file = os.path.join(data_dir, 'phs000001.v1.pht000001.v1.ardpheno.data_dict_2008_10_31.xml')
    dd = rf.read_dbgap_dd_xml(test_file)
    for col in const.REQUIRED_JSON_COLS:
        assert col in dd.columns

def test_value_columns_present(data_dir):
    test_file = os.path.join(data_dir, 'phs000001.v1.pht000001.v1.ardpheno.data_dict_2008_10_31.xml')
    dd = rf.read_dbgap_dd_xml(test_file)
    assert const.VALUES_FIELD in dd.columns

def test_extra_value_columns_present(data_dir):
    test_file = os.path.join(data_dir, 'phs000001.v1.pht000001.v1.ardpheno.data_dict_2008_10_31.xml')
    dd = rf.read_dbgap_dd_xml(test_file)
    val_cols_required = sorted(["X__%s" % i for i in range(1, 11)])
    val_cols_present = sorted([x for x in dd.columns if x.startswith("X_")])
    assert "*".join(val_cols_present) == "*".join(val_cols_required)

def test_good_output_shape_data(data_dir):
    test_file = os.path.join(data_dir, 'phs000001.v1.pht000001.v1.ardpheno.data_dict_2008_10_31.xml')
    dd = rf.read_dbgap_dd_xml(test_file)
    assert dd.shape == (174, 20)




