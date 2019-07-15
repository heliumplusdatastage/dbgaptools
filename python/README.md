# dbgap_dd_to_json

This command-line utility assists in converting DbGaP output data dictionaries (DD) from XML to JSON format. 

## Installation

Install the most up-to-date version of the tool using docker:
Repo: **heliumdatastage/dbgap_dd_to_json:latest**

    docker pull heliumdatastage/dbgap_dd_to_json:latest

## Usage
Docker endpoint automatically calls dbgap_dd_to_json.py script so no need to type further commands. 
For basic usage and help messages:
        
    docker run -v "/path/to/dbGaP_DDs/:/data" heliumdatastage/dbgap_dd_to_json:latest --help
    
Usage overview:

    usage: data_dict_to_json [-h] --dd-xml INPUT_DD --output OUTPUT_FILE [-v]

    optional arguments:
    -h, --help            show this help message and exit
    --dd-xml INPUT_DD     Path to DbGaP data dictionary XML file
    --output OUTPUT_FILE  Path to JSON output
    -v                    Increase verbosity of the program.Multiple -v's
                          increase the verbosity level: 0 = Errors 1 = Errors +
                          Warnings 2 = Errors + Warnings + Info 3 = Errors +
                          Warnings + Info + Debug

