% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/check_functions.R
\name{check_ped}
\alias{check_ped}
\title{Check pedigree file}
\usage{
check_ped(dsfile, ddfile = NULL, na_vals = c("NA", "N/A", "na", "n/a"),
  subj_exp = NULL, subjectID_col = "SUBJECT_ID", check_incons = TRUE,
  male = 1, female = 2)
}
\arguments{
\item{dsfile}{Path to the data file on disk}

\item{ddfile}{Path to the data dictionary file on disk}

\item{na_vals}{Vector of strings that should be read in as NA/missing in data file (see details of \code{read_ds_file})}

\item{subj_exp}{Vector of expected subject IDs}

\item{subjectID_col}{Column name for subject-level ID}

\item{check_incons}{Logical whether to report pedigree inconsistencies, using \code{GWASTools pedigreeCheck}}

\item{male}{Encoded value for male in SEX column}

\item{female}{Encoded value for female in SEX column}
}
\value{
ped_report, a list of the following issues (when present):
\item{lowercase}{Logical flag indicating non-upper case variable names}
\item{missing_vars}{Missing and required variables}
\item{dd_errors}{Differences in fields between data file and data dictionary}
\item{extra_subjects}{Subjects in data file missing from \code{ssm_exp}}
\item{missing_subjects}{Subjects in \code{ssm_exp} missing from data file}
\item{extra_sexvals}{Additional values in SEX column beyond what's specified by \code{male} and \code{female} function arguments}
\item{mztwin_errors}{List of potential errors with MZ twins}
}
\description{
Check contents of a pedigree file for dbGaP posting
}
\details{
If an MZ twin column is detected, returns issues including column name other than 'MZ_TWIN_ID' and a data frame of all twin pairs with logical flags to indicate > 1 family ID per pair (\code{chk_family=TRUE}); non-unique subject ID (\code{chk_subjectID=TRUE}); > 1 sex, which could indicate dizygotic twins are included (\code{chk_sex=TRUE}).

If a data dictionary is provided (\code{ddfile != NULL}), additionally checks 
correspondence between column names in data file and entries in data dictionary.
Data dictionary files can be Excel (.xls, .xlsx) or tab-delimited .txt.
}
