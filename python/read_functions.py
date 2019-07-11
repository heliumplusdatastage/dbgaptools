# from lxml import etree
# import numpy as np
import os
import pandas as pd
import xml.etree.ElementTree as ET
import re


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
            print(chkname)
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
        'VARNAME': 'name',
        'VARDESC': 'description'
    }

    # Process some optional nodes; others are ignored
    optional_nodes = {
        'TYPE': 'type',
        'UNITS': 'unit',
        'MIN': 'logical_min',
        'MAX': 'logical_max'
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

        # if len(unique_keys) > 0:
        #     for value in unique_keys:
        #         if df['VARNAME'] == value.text:
        #             df['UNIQUEKEY'] = 'X'

        # Find all the value nodes in each variable node. If it has multiple value nodes. Value with index 0 - VALUES
        # Value with index 1 - X__1
        child_value_nodes = variable_node.findall('.//value')
        for index, value in enumerate(child_value_nodes):
            try:
                value_string = str(value.attrib['code']) + '=' + value.text
                if index == 0:
                    name_string = 'VALUES'
                else:
                    name_string = 'X__' + str(index)
                df[name_string] = value_string
            except Exception as _:
                pass

        # Append the df dictionary of each variable node to the df list.
        df_list.append(df)

    # Create a dataframe from the df list.
    dd = pd.DataFrame(df_list)

    required_column_order = ['VARNAME', 'VARDESC', 'TYPE', 'UNITS', 'MIN', 'MAX', 'UNIQUEKEY', 'VALUES']

    # Arrange the dataframe columns in a specific order.
    ordered_dd = pd.DataFrame()
    for value in required_column_order:
        if value in dd.columns:
            ordered_dd[value] = dd[value]
            dd.pop(value)

    # Concatenates the left over columns on dd dataframe to the ordered_dd dataframe. Return the ordered dataframe.
    ordered_dd = pd.concat([ordered_dd, dd], axis=1, sort=False)
    return ordered_dd
