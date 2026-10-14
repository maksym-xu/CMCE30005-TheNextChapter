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
    package = report_root / "final-report/report-2026-10-04"
    result = summarize(analysis_input, coefficients)
    expected_n = [3873, 1235, 306, 90]
    if [row["n_listings"] for row in result["descriptives"]] != expected_n:
        raise AssertionError("Unexpected eligible/priority sample counts")
    if result["descriptives"][0]["missing_stay_count"] != 3:
        raise AssertionError("Unexpected missing-stay count")
    md = (package / "Final_Report.md").read_text(encoding="utf-8")
    readme = (report_root / "README.md").read_text(encoding="utf-8")
    paragraphs = word_paragraphs(package / "Final_Report.docx")
    docx = normalized(" ".join(paragraphs))
    for addition in result["report_text"].values():
        if phase == "baseline":
            if addition in md or normalized(addition) in docx:
                raise AssertionError("Baseline unexpectedly contains the new additions")
        else:
            if md.count(addition) != 1 or readme.count(addition) != 1:
                raise AssertionError("Markdown/root README additions are not synchronized")
            if docx.count(normalized(addition)) != 1:
                raise AssertionError("Word addition is absent or duplicated")
    for unchanged in ("49.6%", "32.4%", "46", "50", "34-review"):
        if unchanged not in md:
            raise AssertionError(f"Existing headline missing: {unchanged}")
    if phase == "modified":
        if paragraphs[2] != "Eric Huang and Maksym Xu":
            raise AssertionError("The current report must list the two current members")
        if "Loc Le" in docx or "Qihang Sun" in docx:
            raise AssertionError("Former members remain in the current report")
        saved = json.loads((package / "outputs/report_additions.json").read_text())
        if result != saved:
            raise AssertionError("Saved aggregate output differs from recomputation")
        from pypdf import PdfReader
        pdf = normalized(" ".join(page.extract_text() or "" for page in
                                  PdfReader(package / "Final_Report.pdf").pages))
        for token in ("Eric Huang and Maksym Xu", "AUD285", "AUD450", "AUD425.75",
                      "22.2%", "59.8%", "+1.183", "+0.237", "-0.127", "3.27",
                      "1.27", "0.88", "conditional historical associations"):
            if token not in pdf:
                raise AssertionError(f"PDF lacks new value/phrase: {token}")
        if "Loc Le" in pdf or "Qihang Sun" in pdf:
            raise AssertionError("Former members remain in the current PDF")
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
