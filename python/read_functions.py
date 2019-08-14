import pandas as pd
import xml.etree.ElementTree as ET
import logging
import re
import os

import constants as const

class DbGapMissingDataError(BaseException):
    pass

class DbGapInvalidDataError(BaseException):
    pass


def get_node_attrib(node, attrib, node_type):
    if attrib not in node.attrib:
        raise DbGapMissingDataError("{0} missing the required '{1}' attribute!".format(node_type, attrib))
    return node.attrib[attrib]


def parse_id_and_version(id_string):
    check_id_format(id_string)
    version = id_string.split(".")[1].replace("v", "")
    id_string = id_string.split(".")[0].replace("phs", "").replace("pht", "").replace("phv","")
    return id_string, version


def check_id_format(id_string):
    variable_pattern = re.compile(r'ph[s|v|t][0-9]+\.v[0-9]')
    if re.match(variable_pattern, id_string) is None:
        logging.error(
            "Invalid Dataset/Study/Variable id: '{0}' IDs must be of form 'ph[s/t/v][0-9]+.v[0-9]".format(id_string))
        raise DbGapInvalidDataError(
            "Invalid Dataset/Study/Variable id: '{0}' IDs must be of form 'ph[s/t/v][0-9]+.v[0-9]".format(id_string))


def parse_study_name_from_filename(filename):
    # Parse the study name from the xml filename if it exists. Return None if filename isn't right format to get id from
    dbgap_file_pattern = re.compile(r'phs[0-9]+\.v[0-9]\.pht[0-9]+\.v[0-9]\.(.+)\.data_dict.*')
    match = re.match(dbgap_file_pattern, filename)
    if match is not None:
        return match.group(1)
    return None


def read_dbgap_dd_xml(filename):
    # Set parent_dd_file to the filename of the XML data dictionary on disk
    logging.info("Parsing DbGaP data dictionary from XML file: {0}".format(filename))

    # Try to read in XML file and raise error if not valid
    try:
        xml_dd = ET.parse(filename)
    except ET.ParseError:
        logging.error("Input file is not valid XML!")
        raise

    # Get dataset, study, participant set ids
    dataset_node = xml_dd.findall('.')[0]

    dataset_id = get_node_attrib(dataset_node, 'id', node_type="Data Table")
    dataset_id, dataset_vers = parse_id_and_version(dataset_id)

    study_id = get_node_attrib(dataset_node, 'study_id', node_type="Data Table")
    study_id, study_vers = parse_id_and_version(study_id)
    participant_set_id = get_node_attrib(dataset_node, 'participant_set', node_type="Data Table")

    # Get study name from filename
    dataset_name = parse_study_name_from_filename(os.path.basename(filename))

    # Get dataset description
    dataset_desc = dataset_node.find("./description").text if dataset_node.find("./description") is not None else None

    # Select variable nodes
    variable_nodes = xml_dd.findall('variable')
    if not variable_nodes:
        logging.error("XML file contains no variables! Make sure XML is correclty formatted.")
        raise DbGapMissingDataError("Data table contains no variables!")

    # Create a one-line data frame for each variable node
    required_nodes = {
        const.VARNAME_FIELD: 'name',
        const.VARDESC_FIELD: 'description'
    }

    # Process some optional nodes; others are ignored
    optional_nodes = {
        const.TYPE_FIELD: 'type',
        const.UNITS_FIELD: 'unit',
        const.MIN_FIELD: 'logical_min',
        const.MAX_FIELD: 'logical_max'
    }

    df_list = []
    variable_ids = []
    for variable_node in variable_nodes:
        df = {}

        # Get variable accession number
        variable_id = get_node_attrib(variable_node, 'id', node_type="Variable")
        variable_id, variable_vers = parse_id_and_version(variable_id)

        # Check to make sure no variable id duplicates
        if variable_id in variable_ids:
            logging.error("Duplicate variables with id '{0}'".format(variable_id))
            raise DbGapInvalidDataError("Duplicate variables with id '{0}'".format(variable_id))

        # Add to list of seen variable ids
        variable_ids.append(variable_id)

        # Search for required nodes on each variable node and add them to the df dictionary.
        for key, value in required_nodes.items():
            xpath = './/%s' % value
            try:
                text = variable_node.find(xpath).text
            except Exception as _:
                text = variable_node.find(xpath)

            # Raise error if required field is missing
            if text is None:
                logging.error("Missing required variable field '{0}'".format(value))
                raise DbGapMissingDataError("Missing required variable field '{0}'".format(value))

            # Add variable and value to dictionary
            df[key] = text

        # Search for optional nodes on each variable node and add them to the df dictionary.
        for key, value in optional_nodes.items():
            xpath = './/%s' % value
            node = variable_node.find(xpath)
            if node is not None:
                df[key] = node.text

        # Find all the value nodes in each variable node. If it has multiple value nodes. Value with index 0 - VALUES
        # Value with index 1 - X__1
        child_value_nodes = variable_node.findall('.//value')
        seen_codes = []
        for index, value in enumerate(child_value_nodes):
            code = get_node_attrib(value, 'code', node_type="Value")
            # Warn if variable contains duplicate code
            if code in seen_codes:
                logging.warning("Variable {0} contains duplicate coded field '{1}'".format(variable_id, code))

            # Add code to list of codes already seen
            seen_codes.append(code)

            # Create new column for each code
            value_string = str(code) + '=' + value.text
            if index == 0:
                name_string = const.VALUES_FIELD
            else:
                name_string = 'X__' + str(index)
            df[name_string] = value_string

        # Add dataset, study, variable accession numbers
        df[const.DATASET_ACC_FIELD] = dataset_id
        df[const.STUDY_ACC_FIELD] = study_id
        df[const.VARIABLE_ACC_FIELD] = variable_id

        # Add dataset, study, variable version numbers
        df[const.DATASET_VERSION_FIELD] = dataset_vers
        df[const.STUDY_VERSION_FIELD] = study_vers
        df[const.VARIABLE_VERSION_FIELD] = variable_vers

        # Add participant set and dataset desc fields
        df[const.STUDY_PART_SET_FIELD] = participant_set_id
        df[const.DATASET_DESC_FIELD] = dataset_desc
        df[const.DATASET_NAME_FIELD] = dataset_name

        # Append the df dictionary of each variable node to the df list.
        df_list.append(df)

    # Create a dataframe from the df list.
    dd = pd.DataFrame(df_list)

    # Arrange the dataframe columns in a specific order.
    ordered_dd = pd.DataFrame()
    for value in const.READ_DBGAP_COLUMN_ORDER:
        if value in dd.columns:
            ordered_dd[value] = dd[value]
            dd.pop(value)

    # Concatenates the left over columns on dd dataframe to the ordered_dd dataframe. Return the ordered dataframe.
    ordered_dd = pd.concat([ordered_dd, dd], axis=1, sort=False)
    return ordered_dd
