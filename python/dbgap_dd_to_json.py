import os
import sys
import logging
import argparse
import json

# User libraries
from read_functions import read_dbgap_dd_xml
from write_functions import dbgap_dd_to_json
import constants as const


def configure_logging(verbosity):
    # Setting the format of the logs
    FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"

    # Configuring the logging system to the lowest level
    logging.basicConfig(level=logging.DEBUG, format=FORMAT, stream=sys.stderr)

    # Defining the ANSI Escape characters
    BOLD = '\033[1m'
    DEBUG = '\033[92m'
    INFO = '\033[94m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    END = '\033[0m'

    # Coloring the log levels
    if sys.stderr.isatty():
        logging.addLevelName(logging.ERROR, "%s%s%s%s%s" % (BOLD, ERROR, "DATA_DICT_TO_JSON_ERROR", END, END))
        logging.addLevelName(logging.WARNING, "%s%s%s%s%s" % (BOLD, WARNING, "DATA_DICT_TO_JSON_WARNING", END, END))
        logging.addLevelName(logging.INFO, "%s%s%s%s%s" % (BOLD, INFO, "DATA_DICT_TO_JSON_INFO", END, END))
        logging.addLevelName(logging.DEBUG, "%s%s%s%s%s" % (BOLD, DEBUG, "DATA_DICT_TO_JSON_DEBUG", END, END))
    else:
        logging.addLevelName(logging.ERROR, "DATA_DICT_TO_JSON_ERROR")
        logging.addLevelName(logging.WARNING, "DATA_DICT_TO_JSON_WARNING")
        logging.addLevelName(logging.INFO, "DATA_DICT_TO_JSON_INFO")
        logging.addLevelName(logging.DEBUG, "DATA_DICT_TO_JSON_DEBUG")

    # Setting the level of the logs
    verbosity = 3 if verbosity > 0 else verbosity
    level = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG][verbosity]
    logging.getLogger().setLevel(level)

def configure_argparser(argparser_obj):

    def file_type(arg_string):
        """
        This function check both the existance of input file and the file size
        :param arg_string: file name as string
        :return: file name as string
        """
        if not os.path.exists(arg_string):
            err_msg = "%s does not exist! " \
                      "Please provide a valid file!" % arg_string
            raise argparse.ArgumentTypeError(err_msg)

        return arg_string

    # Path to projections spreadsheet
    argparser_obj.add_argument("--dd-xml",
                               action="store",
                               type=file_type,
                               dest="input_dd",
                               required=True,
                               help="Path to DbGaP data dictionary XML file")

    # Path to output file
    argparser_obj.add_argument("--output",
                               action="store",
                               type=str,
                               dest="output_file",
                               required=True,
                               help="Path to JSON output")

    # Verbosity level
    argparser_obj.add_argument("-v",
                               action='count',
                               dest='verbosity_level',
                               required=False,
                               default=1,
                               help="Increase verbosity of the program."
                                    "Multiple -v's increase the verbosity level:\n"
                                    "0 = Errors\n"
                                    "1 = Errors + Warnings\n"
                                    "2 = Errors + Warnings + Info\n"
                                    "3 = Errors + Warnings + Info + Debug")

def main():

    # Configure argparser
    argparser = argparse.ArgumentParser(prog="data_dict_to_json")
    configure_argparser(argparser)

    # Parse the arguments
    args = argparser.parse_args()

    # Configure logging
    configure_logging(args.verbosity_level)

    # Get names of input/output files
    input_dd = args.input_dd
    output_file = args.output_file

    # Parse data dictionary into Pandas dataframe
    data_df = read_dbgap_dd_xml(input_dd)

    # Convert to reformatted JSON with required columns
    dd_out = dbgap_dd_to_json(data_df,
                              required_cols=const.REQUIRED_JSON_COLS,
                              optional_cols=const.OPTIONAL_JSON_COLS,
                              missing_val_char=const.MISSING_DATA_VALUE)

    # Write to output file
    with open(output_file, "w") as fh:
        json.dump(dd_out, fh, indent=4)

if __name__ == "__main__":
    main()