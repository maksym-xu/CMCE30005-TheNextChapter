#!/usr/bin/env python3
"""Summarise observed listing settings and saved training coefficients without refitting."""

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path


PRIORITY_GROUPS = (
    ("Melbourne", "2BR Apartment/unit"),
    ("Melbourne", "3BR Apartment/unit"),
    ("Yarra Ranges", "3BR House/townhouse"),
)
TERMS = ("one_nightYes", "amenities_10", "price_vs_similar_10")
MISSING = {"", "NA", "NaN", "nan", "null", "NULL"}


def read_rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def numeric(value):
    if value is None or value.strip() in MISSING:
        return None
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Non-finite numeric value")
    return result


def describe(rows, area, configuration):
    prices = [numeric(row["price_num"]) for row in rows]
    amenities = [numeric(row["n_amenities"]) for row in rows]
    stays = [numeric(row["minimum_nights"]) for row in rows]
    if not rows or None in prices or None in amenities:
        raise ValueError("Empty group or missing price/amenity observations")
    observed = [stay for stay in stays if stay is not None]
    if not observed or any(stay < 1 for stay in observed):
        raise ValueError("Observed minimum stays must be at least one night")
    # The observed input satisfies <=1 ==1, matching the saved model definition.
    accepting = sum(stay == 1 for stay in observed)
    return {
        "area": area,
        "configuration": configuration,
        "n_listings": len(rows),
        "median_nightly_price_aud": statistics.median(prices),
        "one_night_count": accepting,
        "observed_stay_count": len(observed),
        "missing_stay_count": len(rows) - len(observed),
        "one_night_percent": 100 * accepting / len(observed),
        "median_amenity_count": statistics.median(amenities),
    }


def coefficient_summary(rows):
    keys = [(row["design"], row["split"], row["term"]) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate design/split/term coefficient")
    repeated = [row for row in rows if row["design"] == "repeated_host_split"]
    if {int(row["split"]) for row in repeated} != set(range(1, 51)):
        raise ValueError("Expected repeated splits 1 through 50")
    summaries = []
    for term in TERMS:
        selected = [row for row in repeated if row["term"] == term]
        if len(selected) != 50 or {int(row["split"]) for row in selected} != set(range(1, 51)):
            raise ValueError(f"Expected one coefficient per repeated split for {term}")
        coefficients = [numeric(row["coefficient"]) for row in selected]
        if None in coefficients:
            raise ValueError(f"Missing coefficient for {term}")
        mean = statistics.fmean(coefficients)
        direction = "positive" if mean > 0 else "negative" if mean < 0 else "zero"
        same_sign = sum((value > 0 and mean > 0) or (value < 0 and mean < 0)
                        or (value == 0 and mean == 0) for value in coefficients)
        summaries.append({
            "term": term,
            "training_fits": 50,
            "mean_coefficient": mean,
            "odds_ratio_exp_mean_coefficient": math.exp(mean),
            "mean_direction": direction,
            "same_sign_fits": same_sign,
            "same_sign_percent": 100 * same_sign / 50,
            "minimum_coefficient": min(coefficients),
            "maximum_coefficient": max(coefficients),
        })
    return summaries


def report_text(descriptives, coefficients):
    groups = descriptives[1:]
    prices = [f"{row['median_nightly_price_aud']:g}" for row in groups]
    rates = [row["one_night_percent"] for row in groups]
    amenity_counts = [row["median_amenity_count"] for row in groups]
    descriptive = (
        f"In the supplied snapshot, median quoted nightly prices are AUD{prices[0]}, "
        f"AUD{prices[1]} and AUD{prices[2]} for Melbourne two-bedroom apartments, "
        "Melbourne three-bedroom apartments and Yarra Ranges three-bedroom houses/townhouses, "
        f"respectively. One-night acceptance ranges from {min(rates):.1f}% to {max(rates):.1f}%, "
        f"and median amenity counts from {min(amenity_counts):g} to {max(amenity_counts):g}. "
        "These are advertised rates, not rents or prices actually paid."
    )
    by_term = {row["term"]: row for row in coefficients}
    night, amenities, price = [by_term[term] for term in TERMS]
    if any(row["same_sign_fits"] != 50 for row in coefficients):
        raise ValueError("Update the report's direction-stability sentence before publishing")
    specification = (
        "Across the 50 repeated training fits, mean log-odds weights are "
        f"{night['mean_coefficient']:+.3f} for one-night acceptance "
        f"(odds ratio {night['odds_ratio_exp_mean_coefficient']:.2f}), "
        f"{amenities['mean_coefficient']:+.3f} per ten additional amenities "
        f"({amenities['odds_ratio_exp_mean_coefficient']:.2f}), and "
        f"{price['mean_coefficient']:+.3f} per price increase equal to 10% of the training-group median "
        f"({price['odds_ratio_exp_mean_coefficient']:.2f}). "
        "All three directions persist in 50/50 fits. These odds ratios describe conditional "
        "historical associations, not probability changes or causal effects."
    )
    return {"section_5_1_append": descriptive, "appendix_a_append": specification}


def summarize(analysis_path, coefficients_path):
    rows = read_rows(analysis_path)
    if len(rows) != 3873 or len({row["id"] for row in rows}) != 3873:
        raise ValueError("Expected 3,873 distinct analysis listings")
    if {row["host_role"] for row in rows} != {"analysis"}:
        raise ValueError("Input must exclude reference hosts")
    if {numeric(row["common_review_threshold"]) for row in rows} != {30}:
        raise ValueError("Input must use the established 30-review outcome")
    descriptives = [describe(rows, "All eligible homes", "All 14 groups")]
    for area, configuration in PRIORITY_GROUPS:
        selected = [row for row in rows if row["neighbourhood_cleansed"] == area
                    and row["configuration"] == configuration]
        descriptives.append(describe(selected, area, configuration))
    coefficients = coefficient_summary(read_rows(coefficients_path))
    return {
        "schema_version": 1,
        "analysis_input_sha256": hashlib.sha256(Path(analysis_path).read_bytes()).hexdigest(),
        "coefficient_input_sha256": hashlib.sha256(Path(coefficients_path).read_bytes()).hexdigest(),
        "model_refitted": False,
        "descriptive_policy": "Observed values only; missing stay rules excluded from percentage denominators",
        "coefficient_policy": "50 repeated_host_split fits only; excludes five host folds; OR is exp(mean beta)",
        "coefficient_training_scope": "Pooled eligible-home training samples, not group-specific model fits",
        "descriptives": descriptives,
        "coefficients": coefficients,
        "report_text": report_text(descriptives, coefficients),
    }


def write_outputs(result, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    for key, filename in (("descriptives", "priority_group_descriptives.csv"),
                          ("coefficients", "operating_coefficient_summary.csv")):
        with (output_dir / filename).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(result[key][0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(result[key])
    (output_dir / "report_additions.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    package = Path(__file__).resolve().parents[1]
    parser.add_argument("--analysis-input", type=Path, required=True)
    parser.add_argument("--coefficients", type=Path,
                        default=package.parent / "screening-followup-2026-10-03/reference/prior_full_coefficients.csv")
    parser.add_argument("--output-dir", type=Path, default=package / "outputs")
    args = parser.parse_args()
    result = summarize(args.analysis_input, args.coefficients)
    write_outputs(result, args.output_dir)
    print("PASS: 3873 observed listings; 3 priority groups; 50 repeated fits; no model refit")


if __name__ == "__main__":
    main()
