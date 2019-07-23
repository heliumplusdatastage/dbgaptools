# from lxml import etree
# import numpy as np
import os
import pandas as pd
import xml.etree.ElementTree as ET
import re
import logging

import constants as const

# Count the number of headlines. Return the integer value.
def count_hdr_lines(filename, colname=None):
    nskip = 0
    # done = False
    with open(filename, "r") as lines:
        for tmp in lines:
            chkname = False
            if colname is not None:
                # Check for the column on the line. If exists, make chkname True
                for col in colname:
                    chkname = not re.search(col, tmp)
            r_tmp = tmp.rstrip("\n").split("\t")
            # Check for lines which starts with #.
            if r_tmp[:1][0][0] == "#" or r_tmp[1:2] == [""] or chkname:
                nskip = nskip + 1
            else:
                break
    return nskip

def read_ds_file(filename, dd=False, na_vals=["NA", "N/A", "na", "n/a"],
                 remove_empty_row=True, remove_empty_col=False):
    if not os.path.isfile(filename):
        return None

    # exit if file extension indicates other than .txt (e.g., csv, xlsx)
    ext = os.path.splitext(filename)[1]
    if ext != ".txt":
        print("Expected tab-delimited input file (.txt), not " + ext)
        return None

    # add name of file to error message in case of failure
    try:
        # may be comment characters in the data fields. first decide how many lines to skip
        if not dd:
            nskip = count_hdr_lines(filename)
        elif dd:
            nskip = count_hdr_lines(filename, colname="VARNAME")

        if nskip > 0:
            print("Additional rows are present before column headers and should be removed prior to dbGaP submission")

        data = pd.read_csv(filename, delimiter='\t', comment='#', keep_default_na=False, na_values=na_vals,
                           skiprows=nskip)

        # remove rows with all blanks/NAs
        if remove_empty_row:
            data = data.dropna(how='all')
        # remove columns with all blanks/NAs (FALSE by default - removes too many DD cols)
        if remove_empty_col:
            data = data.dropna(axis=1, how='all')
    except Exception as e:
        print("in reading file" + filename + ":")
        print(e)

    return data

# Read data dictionary files(.txt, .xlsx, .xls and .xml) and converts into a pandas dataframe.
def read_dd_file(filename, remove_empty_row=True, remove_empty_column=False):

    allowed_text_exts = [".txt"]
    allowed_xls_exts = [".xlsx", ".xls"]
    allowed_xml_exts = [".xml"]

    allowed_exts = allowed_text_exts + allowed_xls_exts + allowed_xml_exts
    file_name, file_extension = os.path.splitext(filename)

    if file_extension not in allowed_exts:
        print("Expected tab-delimited or Excel input file, not %s" % file_extension)
        exit
    try:
        if file_extension in allowed_xml_exts:
            ordered_dd = read_dd_xml(filename)
        elif file_extension in allowed_text_exts:
            ordered_dd = read_dd_txt(filename)
        elif file_extension in allowed_xls_exts:
            ordered_dd = read_dd_xls(filename)
        else:
            raise Exception

    except Exception as e:
        print("in reading file", filename)
        print(e)

    pd.set_option('expand_frame_repr', False)
    pd.set_option('display.max_columns', 999)

    if remove_empty_row:
        dd = ordered_dd.dropna(how="all")

    if remove_empty_column:
        dd = ordered_dd.dropna(axis="columns", how="all")
    return dd

def read_dd_txt(filename):
    dd = read_ds_file(filename, dd=True)

    # rename extra columns after VALUES as "X__*"
    columns = list(dd.columns)
    try:
        index = columns.index("VALUES")
        for i in range(index + 1, len(columns)):
            columnname = "X__" + str(i - index)
            columns[i] = columnname
        dd.columns = columns
    except Exception as _:
        pass

    return dd

def read_dd_xls(filename):
    xl = pd.ExcelFile(filename)

    # check if there are multiple sheets
    if len(xl.sheet_names) > 1:
        print("Data dictionary Excel contaiins mulitple sheets; assuming first is the DD")
    dd = xl.parse()

    # Identify if first row was not column headers
    colnames = [x.upper() for x in dd.columns]
    if "VARNAME" not in colnames:
        # Find header row if preceded by comments
        print("Additional rows are present before column headers and should be removed prior to dbGaP submission")

        # Check to see if 'VARNAME' is contained in any rows
        def is_header_row(row):
            return "VARNAME" in [str(x).upper() for x in list(row)]
        header_tests = dd.apply(is_header_row, axis=1)

        # Re-parse and skip all rows before header line
        header_row = list(header_tests).index(True)
        dd = xl.parse(header=header_row+1)

    return dd

def read_dd_xml(filename):
    # Set parent_dd_file to the filename of the XML data dictionary on disk
    xml_dd = ET.parse(filename)

    # Select variable nodes
    variable_nodes = xml_dd.findall('variable')

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

    # unique_keys = xml_dd.findall('unique_key')
    # print(unique_keys)

    df_list = []
    for variable_node in variable_nodes:
        df = {}

        # Search for required nodes on each variable node and add them to the df dictionary.
        for key, value in required_nodes.items():
            xpath = './/%s' % value
            try:
                text = variable_node.find(xpath).text
            except Exception as _:
                text = variable_node.find(xpath)
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
        for index, value in enumerate(child_value_nodes):
            try:
                value_string = str(value.attrib['code']) + '=' + value.text
                if index == 0:
                    name_string = const.VALUES_FIELD
                else:
                    name_string = 'X__' + str(index)
                df[name_string] = value_string
            except Exception as _:
                pass

        # Append the df dictionary of each variable node to the df list.
        df_list.append(df)

    # Create a dataframe from the df list.
    dd = pd.DataFrame(df_list)

    required_column_order = [const.VARNAME_FIELD, const.VARDESC_FIELD, const.TYPE_FIELD, const.UNITS_FIELD,
                             const.MIN_FIELD, const.MAX_FIELD, const.UNIQUE_KEY_FIELD, const.VALUES_FIELD]

    # Arrange the dataframe columns in a specific order.
    ordered_dd = pd.DataFrame()
    for value in required_column_order:
        if value in dd.columns:
            ordered_dd[value] = dd[value]
            dd.pop(value)

    # Concatenates the left over columns on dd dataframe to the ordered_dd dataframe. Return the ordered dataframe.
    ordered_dd = pd.concat([ordered_dd, dd], axis=1, sort=False)
    return ordered_dd


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
    study_id = get_node_attrib(dataset_node, 'study_id', node_type="Data Table")
    participant_set_id = get_node_attrib(dataset_node, 'participant_set', node_type="Data Table")

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

        # Add participant set and dataset desc fields
        df[const.DATASET_PART_SET_FIELD] = participant_set_id
        df[const.DATASET_DESC_FIELD] = dataset_desc

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


class DbGapMissingDataError(BaseException):
    pass

class DbGapInvalidDataError(BaseException):
    pass

def get_node_attrib(node, attrib, node_type):
    if attrib not in node.attrib:
        raise DbGapMissingDataError("{0} missing the required '{1}' attribute!".format(node_type, attrib))
    return node.attrib[attrib]
