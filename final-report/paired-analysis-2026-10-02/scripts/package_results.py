#!/usr/bin/env python3
"""Check or package the explicit publication allowlist, never private records.

Default: validate the listed files and write MANIFEST.sha256.json.
--check: validate files and an existing manifest without changing anything.
--archive: also create a ZIP containing exactly the allowlist and manifest.
These are scope/integrity checks, not reconstruction of analysis from raw data.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST = (
    ".gitignore",
    "README.md",
    "METHODS_FOR_REPORT.md",
    "run.sh",
    "config/review_analysis.json",
    "config/rerun_plan.json",
    "scripts/model_helpers.R",
    "scripts/run_paired_analysis.R",
    "scripts/test_model_helpers.R",
    "scripts/verify_rerun.py",
    "scripts/plot_paired_results.py",
    "scripts/package_results.py",
    "reference/provenance.json",
    "reference/R_session_info.txt",
    "reference/published_final_logit_repeated_splits.csv",
    "reference/published_final_logit_repeated_splits_summary.csv",
    "outputs/change_from_published.json",
    "outputs/change_from_published_repeats.csv",
    "outputs/five_fold_pooled_comparison.csv",
    "outputs/full_descriptive_coefficients.csv",
    "outputs/helper_tests.json",
    "outputs/metric_distribution.csv",
    "outputs/minimum_stay_missingness.csv",
    "outputs/paired_summary.csv",
    "outputs/preprocessing_audit.csv",
    "outputs/results.json",
    "outputs/split_coefficients.csv",
    "outputs/split_metrics.csv",
    "outputs/verification.json",
    "figures/paired_model_gain.png",
    "figures/paired_model_gain.svg",
)
FORBIDDEN_CSV_FIELDS = {
    "id", "listing_id", "host_id", "name", "listing_url", "host_url",
    "latitude", "longitude", "p_logistic", "p_segment_mean", "one_night",
    "training_segment_median_price", "w_logistic", "w_segment_mean",
}


def checked_hashes():
    if len(ALLOWLIST) != len(set(ALLOWLIST)):
        raise SystemExit("Publication allowlist contains duplicate paths.")
    hashes = {}
    for relative in sorted(ALLOWLIST):
        path = ROOT / relative
        if not path.is_file() or path.is_symlink() or ROOT not in path.resolve().parents:
            raise SystemExit("Missing or unsafe allowlisted file: " + relative)
        if any(part in {"private-inputs", "working", "logs", "__pycache__"} for part in path.relative_to(ROOT).parts):
            raise SystemExit("Private directory is not allowed in publication.")
        if "PRIVATE" in path.name or path.suffix == ".pyc":
            raise SystemExit("Private or compiled file is not allowed in publication.")
        if path.suffix == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                fields = set(reader.fieldnames or [])
                if not fields or fields & FORBIDDEN_CSV_FIELDS:
                    raise SystemExit("CSV publication schema failed: " + relative)
                if not any(reader):
                    raise SystemExit("Empty aggregate CSV: " + relative)
        elif path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Check files and existing manifest without writing.")
    mode.add_argument("--archive", action="store_true", help="Write manifest and publication ZIP.")
    args = parser.parse_args()
    hashes = checked_hashes()
    manifest = ROOT / "MANIFEST.sha256.json"
    if args.check:
        if manifest.is_file():
            if json.loads(manifest.read_text(encoding="utf-8")) != hashes:
                raise SystemExit("Manifest differs from current allowlisted files; investigate before refreshing it.")
            print(f"Publication scope, CSV schema and manifest passed: {len(hashes)} files.")
        else:
            print(f"Publication scope and CSV schema passed: {len(hashes)} files; no manifest supplied.")
        return
    manifest.write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote manifest for {len(hashes)} explicitly allowed files.")
    if args.archive:
        archive = ROOT / "TheNextChapter_Final_Report_Analysis_2026-10-02.zip"
        packaged = sorted(hashes) + [manifest.name]
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as handle:
            for relative in packaged:
                handle.write(ROOT / relative, Path(ROOT.name) / relative)
        with zipfile.ZipFile(archive) as handle:
            expected = {str(Path(ROOT.name) / relative) for relative in packaged}
            if set(handle.namelist()) != expected or handle.testzip() is not None:
                raise SystemExit("Publication archive verification failed.")
        print(f"Created and checked {archive.name}: {len(packaged)} files.")


if __name__ == "__main__":
    main()
