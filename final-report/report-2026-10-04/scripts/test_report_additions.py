#!/usr/bin/env python3
"""Test observed-data summaries, saved-coefficient selection and report consistency."""

import argparse
import json
import math
import re
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from summarize_report_additions import coefficient_summary, describe, summarize


def normalized(text):
    return re.sub(r"\s+", " ", text).strip().replace("\u2212", "-").replace("\u2011", "-")


def word_paragraphs(path):
    with zipfile.ZipFile(path) as archive:
        document = ElementTree.fromstring(archive.read("word/document.xml"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    return ["".join(p.itertext()) for p in document.findall(".//w:body/w:p", ns)]


class SummaryTests(unittest.TestCase):
    def test_missing_stay_is_excluded_not_no(self):
        rows = [{"price_num": str(p), "n_amenities": str(a), "minimum_nights": m}
                for p, a, m in ((10, 40, "1"), (20, 50, "2"), (30, 60, "NA"))]
        result = describe(rows, "Example", "Example")
        self.assertEqual(result["one_night_percent"], 50)
        self.assertEqual(result["missing_stay_count"], 1)
        self.assertEqual(result["median_nightly_price_aud"], 20)
        self.assertEqual(result["median_amenity_count"], 50)

    @staticmethod
    def coefficients():
        return [{"design": "repeated_host_split", "split": str(split), "term": term,
                 "coefficient": str(value)} for split in range(1, 51)
                for term, value in (("one_nightYes", 1.2), ("amenities_10", .2),
                                    ("price_vs_similar_10", -.1))]

    def test_only_repeated_fits_enter_means(self):
        rows = self.coefficients() + [{"design": "host_fold", "split": "0",
                                      "term": "one_nightYes", "coefficient": "999"}]
        result = coefficient_summary(rows)
        self.assertAlmostEqual(result[0]["mean_coefficient"], 1.2)
        self.assertEqual(result[0]["training_fits"], 50)
        self.assertAlmostEqual(result[0]["odds_ratio_exp_mean_coefficient"], math.exp(1.2))

    def test_duplicate_coefficient_rejected(self):
        rows = self.coefficients()
        with self.assertRaises(ValueError):
            coefficient_summary(rows + [rows[0]])

    def test_missing_repeated_split_rejected(self):
        with self.assertRaises(ValueError):
            coefficient_summary([r for r in self.coefficients() if r["split"] != "50"])

    def test_sub_one_night_value_rejected(self):
        with self.assertRaises(ValueError):
            describe([{"price_num": "20", "n_amenities": "4", "minimum_nights": "0"}],
                     "Example", "Example")

    def test_nonfinite_coefficient_rejected(self):
        rows = self.coefficients()
        rows[0]["coefficient"] = "inf"
        with self.assertRaises(ValueError):
            coefficient_summary(rows)


def check_report(report_root, analysis_input, coefficients, phase):
    """Recompute the saved aggregates, then run the current package checks.

    The sentence-level checks of the 14 October revision were replaced on 16 October
    2026, when the report was rewritten; check_report_package.py now checks the
    Markdown, Word, PDF and README versions against each other and the outputs.
    """
    package = report_root / "final-report/report-2026-10-04"
    result = summarize(analysis_input, coefficients)
    expected_n = [3873, 1235, 306, 90]
    if [row["n_listings"] for row in result["descriptives"]] != expected_n:
        raise AssertionError("Unexpected eligible/priority sample counts")
    if result["descriptives"][0]["missing_stay_count"] != 3:
        raise AssertionError("Unexpected missing-stay count")
    saved = json.loads((package / "outputs/report_additions.json").read_text())
    if result != saved:
        raise AssertionError("Saved aggregate output differs from recomputation")
    if phase == "modified":
        import subprocess, sys
        subprocess.run([sys.executable, str(Path(__file__).with_name("check_report_package.py"))],
                       cwd=report_root, check=True)
    print(f"PASS: {phase} report; 3873 rows; 50 repeated fits; 3 missing stay rules excluded")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-root", type=Path)
    parser.add_argument("--analysis-input", type=Path)
    parser.add_argument("--coefficients", type=Path)
    parser.add_argument("--phase", choices=("baseline", "modified"))
    parser.add_argument("--unit-tests", action="store_true")
    args = parser.parse_args()
    if args.unit_tests:
        tests = unittest.defaultTestLoader.loadTestsFromTestCase(SummaryTests)
        result = unittest.TextTestRunner(verbosity=1).run(tests)
        raise SystemExit(0 if result.wasSuccessful() else 1)
    if not all((args.report_root, args.analysis_input, args.coefficients, args.phase)):
        parser.error("Provide the report root, both inputs and phase, or use --unit-tests")
    check_report(args.report_root, args.analysis_input, args.coefficients, args.phase)


if __name__ == "__main__":
    main()
