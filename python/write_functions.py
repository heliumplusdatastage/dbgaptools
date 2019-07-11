import os
from datetime import datetime
import json

import python.read_functions as rd

def write_dbgap(x, file="", study_name=None, phs=None,
                DD=False, dstype="", generate_fn=False):

    # Check for required info if generating fn
    if generate_fn:
        if study_name is None and phs is None:
            raise IOError("To generate a file name, one of studyname or phs must be provided")

        dstypes = ["pheno","ped","sattr","ssm","subj"]
        if not dstype in dstypes:
            raise IOError("Please specify dstype, one of: {0}".format(", ".join(dstypes)))

        # Make verbose version of dstype
        ftype_map = {
                    "pheno": "Phenotype",
                    "ped"  : "Pedigree",
                    "sattr": "SampleAttributes",
                    "ssm"  : "SampleSubjectMapping",
                    "subj" : "Subject"
                     }

        ftype = ftype_map[dstype]

        # Generate file name
        if study_name is None:
            pt1 = phs
        elif phs is None:
            pt1 = study_name
        else:
            pt1 = "{0}_{1}".format(study_name, phs)

        ftype_str = "{0}DD".format(ftype) if DD else "{0}DS".format(ftype)

        # Make filename
        timestamp = datetime.today().strftime('%Y%m%d')
        file = "{0}_{1}_{2}.json".format(pt1, ftype_str, timestamp)

    # Raise error if not filename provided
    if not generate_fn and not file:
        raise IOError("Please specify filename or set generate_fn=True")

    filename, file_extension = os.path.splitext(file)
    if file_extension.lower() != ".json":
        print("Warning: Output file name recommended to have .json extension")


    # If there is a column name like "X__*" in a DD, assume it's an encoded values
    # colname and should be set to blank
    if DD:
        colnames = []
        for colname in x.columns:
            if colname.startswith("X__"):
                colnames.append("")
            else:
                colnames.append(colname)
        x.columns = colnames

    # write file
    x_dict = x.to_dict(orient="records")
    #with open(file, "w") as fh:
    print(json.dumps(x_dict, indent=4))
    #utils::write.table(x, file, sep="\t",  na="",  col.names=TRUE, row.names=FALSE, quote=FALSE)



result_1 = rd.read_dd_file('/Users/awaldrop/PycharmProjects/dbgaptools/python/samplexls_hasheader.xlsx')
#result_1 = rd.read_dd_file('/Users/awaldrop/PycharmProjects/dbgaptools/python/sample_xml.data_dict.xml')
write_dbgap(result_1, study_name="Derp", DD=False, generate_fn=True, dstype="sattr")