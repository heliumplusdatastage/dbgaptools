# from lxml import etree
# import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET


def count_hdr_lines(filename, colname):
    with open(filename, 'r') as con:
        header_count = 0
        for line in con:
            raw_line = line.rstrip("\n")
            r_line = raw_line.strip().split("\t")
            header_count = header_count + 1
            for col in colname:
                if col in r_line:
                    break
                else:
                    continue
        print(header_count)


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
            text = variable_node.find(xpath).text
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


#result = read_dd_xml('C:\\Users\mural\PycharmProjects\dbGaPDataDictionaryParser\sample.xml')
#pd.set_option('expand_frame_repr', False)
#pd.set_option('display.max_columns', 999)
#print(result)

result1 = count_hdr_lines('C:\\Users\mural\PycharmProjects\dbGaPDataDictionaryParser\sam_text.txt',["IS_TUMOR"])