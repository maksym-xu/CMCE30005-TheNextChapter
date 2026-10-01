#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p outputs working logs
command -v Rscript >/dev/null 2>&1 || { echo 'Rscript is required.' >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo 'Python 3 is required.' >&2; exit 1; }
Rscript -e 'required <- c("data.table","jsonlite","sandwich"); missing <- required[!vapply(required, requireNamespace, logical(1), quietly=TRUE)]; if(length(missing)) stop("Install the required R packages: ", paste(missing, collapse=", "))' > logs/dependency_check.log 2>&1
Rscript scripts/14_simple_logistic.R > logs/model_rerun.log 2>&1
python3 scripts/validate_and_export.py > logs/validation.log 2>&1
echo 'Analysis and independent validation passed.'
echo 'Presentation data: outputs/presentation_metrics.json'
echo 'Checks: logs/validation_report.json'
