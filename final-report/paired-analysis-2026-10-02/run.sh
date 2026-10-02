#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Check authorised input fingerprints before creating or replacing any outputs.
"${REPORT_PYTHON_BIN:-python3}" - <<'PY'
import hashlib
import json
from pathlib import Path

root = Path.cwd()
provenance = json.loads((root / "reference/provenance.json").read_text())
for name, key in (("analysis_input.csv", "input_sha256"),
                  ("legacy_oof_predictions_PRIVATE.csv", "legacy_oof_sha256")):
    path = root / "private-inputs" / name
    if not path.is_file():
        raise SystemExit("Authorised private input is required: private-inputs/" + name)
    if hashlib.sha256(path.read_bytes()).hexdigest() != provenance[key]:
        raise SystemExit("Private input fingerprint differs from the recorded source: " + name)
print("Authorised input fingerprints match.")
PY
mkdir -p logs outputs working
Rscript scripts/test_model_helpers.R > logs/helper_tests.log 2>&1
Rscript scripts/run_paired_analysis.R > logs/run.log 2>&1
"${REPORT_PYTHON_BIN:-python3}" scripts/verify_rerun.py
printf '%s\n' 'Analysis and independent verification completed. Results: outputs/paired_summary.csv'
# Optional report graphics require matplotlib and numpy:
# "${REPORT_PYTHON_BIN:-python3}" scripts/plot_paired_results.py
