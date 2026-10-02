#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs working outputs figures
Rscript scripts/run_screening_followup.R > logs/run.log 2>&1
"${REPORT_PYTHON_BIN:-python3}" scripts/verify_screening_followup.py
Rscript scripts/plot_followup.R
printf '%s\n' 'Screening comparisons and independent verification completed.'
