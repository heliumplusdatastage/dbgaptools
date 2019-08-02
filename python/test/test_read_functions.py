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
    assert str(err.value) == "Duplicate variables with id '00164675'"

def test_warns_duplicate_variable_code(data_dir, caplog):
    test_file = os.path.join(data_dir, 'dd_dup_var_code.xml')
    rf.read_dbgap_dd_xml(test_file)
    assert "Variable 00000137 contains duplicate coded field 'N'" in caplog.text

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
    assert dd.shape == (174, 24)

def test_parse_id_function():
    ds_id = "pht000013235.v1"
    sd_id = "phs000013235.v5"
    var_id = "phv0023423.v2"

    ds_id, ds_ver = rf.parse_id_and_version(ds_id)
    assert ds_id == "000013235" and ds_ver == "1"

    sd_id, sd_ver = rf.parse_id_and_version(sd_id)
    assert sd_id == "000013235" and sd_ver == "5"

    var_id, var_ver = rf.parse_id_and_version(var_id)
    assert var_id == "0023423" and var_ver == "2"

def test_bad_ids():
    bad_ids = ["pht000013235.1", "phd000013235.v5", "phv0023423..v2", "asdfasdf", "phv.v5", "phtt0980983v2", "pht0.0.v2"]
    for bad_id in bad_ids:
        with pytest.raises(rf.DbGapInvalidDataError) as err:
            rf.check_id_format(bad_id)
        assert str(err.value) == "Invalid Dataset/Study/Variable id: '{0}' IDs must be of form 'ph[s/t/v][0-9]+.v[0-9]".format(bad_id)

def test_good_ids():
    good_ids = ["pht000013235.v1", "phs000013235.v5", "phv0023423.v2", "pht0980983.v2"]
    for good_id in good_ids:
        rf.check_id_format(good_id)

def test_parse_study_name_from_filename():
    assert rf.parse_study_name_from_filename("phs000001.v1.pht000001.v1.ardpheno.data_dict_2008_10_31.xml") == "ardpheno"
    assert rf.parse_study_name_from_filename("phs000001.v1.pht000001.v1.ardpheno.data_dict_2008_10_31.xml") == "ardpheno"
    assert rf.parse_study_name_from_filename("phs000001.v1.ardpheno.data_dict_2008_10_31.xml") is None
    assert rf.parse_study_name_from_filename("phs001747.v1.pht008642.v1.CAREGIVER_WHAT_UP_data_.data_dict.xm") == "CAREGIVER_WHAT_UP_data_"
    assert rf.parse_study_name_from_filename("phs001747.v1.CAREGIVER_WHAT_UP_data_.data_dict.xm") is None
    assert rf.parse_study_name_from_filename("//phs001747.v1.pht008642.v1.CAREGIVER_WHAT_UP_data_.data_dict.xm") is None
    assert rf.parse_study_name_from_filename("phs001783.v1.pht008819.v1.THILS_wil_actuall_be_23_a_pretty_logn_234234_one_JEEZ-yes.data_dict.xml") == "THILS_wil_actuall_be_23_a_pretty_logn_234234_one_JEEZ-yes"

def test_parse_dbgap_handles_bad_ids(data_dir):
    bad_id_files = ['dd_malformed_dataset_id.xml', 'dd_malformed_dataset_id.xml', 'dd_malformed_dataset_id.xml']
    bad_ids = ["ph000001.v1", "phs000001.1", "ph00000173.1"]
    for i in range(len(bad_id_files)):
        bad_id_file = os.path.join(data_dir, bad_id_files[i])
        with pytest.raises(rf.DbGapInvalidDataError) as err:
            rf.read_dbgap_dd_xml(bad_id_file)
            assert str(err.value) == "Invalid Dataset/Study/Variable id: '{0}' IDs must be of form 'ph[s/t/v][0-9]+.v[0-9]".format(bad_ids[i])
