#!/usr/bin/env python3
"""Validate the standalone R run and publish aggregate, presentation-safe JSON.

All probabilities in the JSON are fractions in [0,1]. Display percentages are
explicitly labelled. This script needs only Python's standard library.
"""
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []

def rows(path):
    with (ROOT / path).open(newline="") as handle:
        return list(csv.DictReader(handle))

def require(condition, message):
    if not condition:
        raise AssertionError(message)
    checks.append(message)

def close(a, b, tolerance=1e-11):
    return math.isclose(float(a), float(b), abs_tol=tolerance, rel_tol=tolerance)

def auc(y, scores):
    order = sorted(range(len(y)), key=lambda i: scores[i])
    rank_sum = 0.0
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and scores[order[j]] == scores[order[i]]:
            j += 1
        mean_rank = (i + 1 + j) / 2
        rank_sum += mean_rank * sum(y[order[k]] for k in range(i, j))
        i = j
    positive = sum(y)
    negative = len(y) - positive
    return (rank_sum - positive * (positive + 1) / 2) / (positive * negative)

def equal_quota_precision(y, scores):
    quota = math.ceil(len(y) / 4)
    boundary = sorted(scores, reverse=True)[quota - 1]
    above = [i for i, p in enumerate(scores) if p > boundary]
    tied = [i for i, p in enumerate(scores) if p == boundary]
    tie_weight = (quota - len(above)) / len(tied)
    return (sum(y[i] for i in above) + tie_weight * sum(y[i] for i in tied)) / quota

data = rows("private-inputs/analysis_input.csv")
require(len(data) == 3873 and len({r["host_id"] for r in data}) == 1726,
        "Compact input reproduces 3,873 listings and 1,726 hosts")
require(len({r["id"] for r in data}) == len(data), "Listing identifiers are unique")
require(all(int(r["review_target_met"]) == int(int(r["reviews_365d"]) >= 30) for r in data),
        "Every outcome equals the 30-review event in the frozen 365-day counts")
require(sum(int(r["review_target_met"]) for r in data) == 981,
        "981 listings reach the target")
host_folds = defaultdict(set)
for r in data:
    host_folds[r["host_id"]].add(r["fold"])
require(all(len(x) == 1 for x in host_folds.values()),
        "Every host has exactly one validation fold")
require(all(int(hashlib.sha256(("30005|benchmark|" + r["host_id"]).encode()).hexdigest()[:7], 16) % 5 != 0
            for r in data), "Reference-host hash partition is absent from model input")

oof = rows("working/oof_predictions_PRIVATE.csv")
require({r["id"] for r in oof} == {r["id"] for r in data}, "OOF IDs match the input exactly")
input_by_id = {r["id"]: r for r in data}
require(all(r["host_id"] == input_by_id[r["id"]]["host_id"]
            and r["fold"] == input_by_id[r["id"]]["fold"]
            and r["busy"] == input_by_id[r["id"]]["review_target_met"] for r in oof),
        "OOF hosts, folds and outcomes match the frozen input")

# Independently reconstruct the segment baseline from training-host outcomes.
for fold in sorted({r["fold"] for r in data}):
    train = [r for r in data if r["fold"] != fold]
    prevalence = sum(int(r["review_target_met"]) for r in train) / len(train)
    segment_values = defaultdict(list)
    for r in train:
        segment_values[(r["neighbourhood_cleansed"], r["configuration"])].append(int(r["review_target_met"]))
    baseline = {key: (sum(y) + 10 * prevalence) / (len(y) + 10)
                for key, y in segment_values.items()}
    test = [r for r in oof if r["fold"] == fold]
    require(all(close(r["p_segment_mean"], baseline[(input_by_id[r["id"]]["neighbourhood_cleansed"],
                                                    input_by_id[r["id"]]["configuration"])]) for r in test),
            f"Fold {fold}: Python independently reproduces the training-only segment baseline")

comparison = {r["model"]: r for r in rows("outputs/model_comparison.csv")}
y = [int(r["busy"]) for r in oof]
for model, column in [("simple_logistic", "p"), ("segment_mean", "p_segment_mean"),
                      ("location_type_bedrooms_logistic", "p_location_only")]:
    scores = [float(r[column]) for r in oof]
    require(close(auc(y, scores), comparison[model]["roc_auc"]),
            f"Python independently reproduces AUC for {model}")
    require(close(equal_quota_precision(y, scores), comparison[model]["precision_top_quarter"]),
            f"Python independently reproduces equal-quota precision for {model}")
    require(close(comparison[model]["expected_top_quarter_n"], 969),
            f"{model} uses exactly 969 selections in expectation")

for file, key, numeric_columns in [
    ("final_logit_coefficients.csv", "term", ["coefficient", "odds_ratio", "or_ci95_lo", "or_ci95_hi", "p_value"]),
    ("final_logit_scenarios.csv", "scenario", ["predicted_chance_busy", "ci95_lo", "ci95_hi", "typical_amenities"]),
]:
    expected = {r[key]: r for r in rows("reference/" + file)}
    actual = {r[key]: r for r in rows("outputs/" + file)}
    require(expected.keys() == actual.keys(), f"{file}: same rows as frozen original")
    require(all(close(actual[k][c], expected[k][c]) for k in expected for c in numeric_columns),
            f"{file}: unchanged model numerics match the frozen original")

old_metrics = {r["metric"]: r for r in rows("reference/final_logit_test_metrics.csv")}
require(close(comparison["simple_logistic"]["roc_auc"], old_metrics["auc_full_model"]["value"]),
        "The full model's AUC matches the original audit")
require(close(comparison["simple_logistic"]["precision_top_quarter"], old_metrics["hit_rate_in_flagged_top_quarter"]["value"]),
        "The full model's screening precision matches the original audit")
require(close(comparison["segment_mean"]["roc_auc"], .5810323533019487)
        and close(comparison["segment_mean"]["precision_top_quarter"], .28068961330662295),
        "Segment-average results match the independently audited original baseline")
require(close(comparison["location_type_bedrooms_logistic"]["precision_top_quarter"], .291123849227028),
        "Location/type/bedrooms comparator uses corrected 29.11%, not inclusive-ties 29.35%")

conf = rows("outputs/test_confusion.csv")[0]
require([int(conf[k]) for k in ["true_positives", "false_positives", "false_negatives", "true_negatives"]]
        == [423, 546, 558, 2346], "All four confusion-matrix counts match the original audit")
segments = rows("outputs/descriptive_segments.csv")
old_segments = {(r["lga"], r["configuration"]): r for r in rows("reference/final_segment_summary.csv")}
require(len(segments) == 14, "Fourteen descriptive segments remain")
require(all(all(close(r[c], old_segments[(r["lga"], r["configuration"])][c])
                    for c in ["listings", "hosts", "busy_listings", "busy_share", "busy_share_ci90_lo", "busy_share_ci90_hi"])
            for r in segments), "Observed segment rates and inherited bootstrap ranges match the frozen project")

temporal = json.loads((ROOT / "reference/temporal-validation/validation_metrics.json").read_text())
require(temporal["threshold"]["value"] == 34 and temporal["sample"]["analysis_listings"] == 2657
        and temporal["sample"]["segments_retained"] == 10, "Temporal validation retains its separate 34-review design")
changes = rows("reference/temporal-validation/segment_cross_period.csv")
require(any(float(r["change_pp"]) > 0 for r in changes) and any(float(r["change_pp"]) == 0 for r in changes),
        "Temporal claim is aggregate decline; some segments rose or stayed unchanged")

def model_record(key, label):
    r = comparison[key]
    return {"label": label, "auc": float(r["roc_auc"]), "brier_score": float(r["brier_score"]),
            "top_quarter_precision": float(r["precision_top_quarter"]),
            "top_quarter_precision_percent_1dp": round(float(r["precision_top_quarter"]) * 100, 1),
            "expected_screened_listings": 969,
            "expected_true_positives": float(r["expected_true_positives_top_quarter"]),
            "recall": float(r["recall_top_quarter"]), "quota_method": r["quota_method"]}

full = model_record("simple_logistic", "Simple logistic model")
full["confusion"] = {k: int(conf[k]) for k in ["true_positives", "false_positives", "false_negatives", "true_negatives"]}
full["accuracy"] = float(conf["accuracy"])
full["all_negative_accuracy"] = float(conf["all_negative_accuracy"])
folds = rows("outputs/fold_metrics.csv")
full["folds_beating_segment_mean_auc"] = sum(float(r["auc_simple_logistic"]) > float(r["auc_segment_mean"]) for r in folds)
full["fold_auc"] = [float(r["auc_simple_logistic"]) for r in folds]
scenario_rows = rows("outputs/final_logit_scenarios.csv")[:2]
top_segments = [{"lga": r["lga"], "configuration": r["configuration"], "listings": int(r["listings"]),
                 "hosts": int(r["hosts"]), "positive_listings": int(r["busy_listings"]),
                 "observed_share": float(r["busy_share"]),
                 "observed_share_percent_1dp": round(float(r["busy_share"]) * 100, 1),
                 "ci90_lower": float(r["busy_share_ci90_lo"]), "ci90_upper": float(r["busy_share_ci90_hi"])}
                for r in segments[:3]]
provenance = json.loads((ROOT / "reference/source_provenance.json").read_text())
payload = {
    "schema_version": "1.0",
    "units": "Probabilities, shares, accuracy and AUC are fractions; fields ending percent_1dp are percentages.",
    "source": {"source_commit": provenance["source_commit"], "commit_status_note": "Historical base project commit; see ../EVIDENCE_MAP.md for publication provenance.",
               "school_snapshot": "Inside Airbnb Melbourne; supplied through subject LMS; collected 17 June–1 July 2026",
               "input_sha256": hashlib.sha256((ROOT / "private-inputs/analysis_input.csv").read_bytes()).hexdigest()},
    "sample": {"analysis_listings": 3873, "analysis_hosts": 1726, "busy_listings": 981,
               "busy_share": 981/3873, "busy_share_percent_1dp": round(981/3873*100, 1),
               "segments": 14, "council_areas": 6, "reference_listings": 906,
               "source_listings": 25728, "zero_reviews": 334,
               "melbourne_lga_share": sum(int(r["listings"]) for r in segments if r["lga"] == "Melbourne")/3873},
    "outcome": {"label": "30+ guest reviews in the preceding 365 days", "threshold": 30,
                "type": "binary historical outcome", "reference_group_p75": 29.75,
                "note": "The separate reference group defines the cutoff. The analysis sample's 25.3% is observed, not forced by design."},
    "segments": {"ranking_basis": "Observed outcome proportions, not logistic model scores",
                 "top_three": top_segments, "uncertainty": "90% intervals from the frozen project's host bootstrap; copied and checked, not regenerated by this standalone logistic script.",
                 "interpretation": "The intervals overlap. These are search candidates, not a certain exact ordering."},
    "model": {
        "family": "binomial logistic regression, unpenalised R glm",
        "scope": "Retrospective classification of held-out hosts; no prospective time validation for this model",
        "inputs": ["Council area", "Apartment or house/townhouse", "Bedrooms (1–3)", "Current price relative to training-fold segment median", "Accepts 1-night stays, yes/no", "Listed amenity count"],
        "validation": "Five folds grouped by host; price medians fitted within training folds; same exploratory sample, not an untouched final external test",
        "full": full,
        "baseline_segment_mean": model_record("segment_mean", "Training-fold segment average (fixed smoothing weight 10)"),
        "baseline_location_type_bedrooms": model_record("location_type_bedrooms_logistic", "Additive logistic model: council area, property type and bedrooms"),
        "repeated_host_splits": {"count": 50, "train_share": .7, "test_share": .3,
              "results": [{"metric": r["metric"], "mean": float(r["mean"]), "p05": float(r["p05"]), "p95": float(r["p95"])}
                          for r in rows("outputs/final_logit_repeated_splits_summary.csv")],
              "note": "The 5th–95th percentile range is split sensitivity, not a confidence interval or independent external testing."},
        "scenarios_backup": {"role": "Backup illustration only; comparisons are associations, not intervention effects",
              "example": "Melbourne 2BR apartment; segment-median price; 43 amenities; one-night stay setting varied",
              "items": [{"scenario": r["scenario"], "probability": float(r["predicted_chance_busy"]),
                         "ci95_lower": float(r["ci95_lo"]), "ci95_upper": float(r["ci95_hi"])} for r in scenario_rows]}
    },
    "temporal_validation": {
        "validated_object": "Persistence of the earlier top-three segment shortlist, NOT the simple logistic model",
        "sample_listings": 2657, "sample_hosts": 1208, "segments": 10,
        "threshold": 34, "threshold_source": "Earlier-window reference-host P75; held fixed for both windows",
        "windows": temporal["windows"],
        "earlier_top_three_recent_share": temporal["top3_vs_rest_recent_window"]["listing_weighted"]["top3_recent_rate"],
        "others_recent_share": temporal["top3_vs_rest_recent_window"]["listing_weighted"]["rest_recent_rate"],
        "difference_percentage_points": temporal["top3_vs_rest_recent_window"]["listing_weighted"]["difference_pp"],
        "difference_ci95_percentage_points": [temporal["bootstrap"]["interval_A_fixed_candidates"]["lower_95_pp"], temporal["bootstrap"]["interval_A_fixed_candidates"]["upper_95_pp"]],
        "overall_earlier_share": temporal["overall_attainment"]["earlier"],
        "overall_recent_share": temporal["overall_attainment"]["recent"],
        "trend_wording": "Overall attainment fell; not every segment fell.",
        "exact_top_three_set_bootstrap_recurrence": temporal["bootstrap"]["share_replicates_reproducing_point_estimate_top3_set"],
        "limits": "Same surviving listings across two windows. Longer-history sample. No forecast of a new operator's profit. Copied validated project evidence; raw temporal pipeline is not rerun in this compact package."
    },
    "caveats": ["Reviews are not bookings, occupancy or profit.", "Current settings can differ from settings during the previous year.",
                "Longer stays can generate fewer reviewed stays; test operating changes against actual margin.",
                "Estimated revenue is constructed from reviews and price. It is not used to set rent or cost ceilings.",
                "Listing-level school data and OOF predictions are private working inputs; do not publish them."]
}
(ROOT / "outputs/presentation_metrics.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
report = {"status": "passed", "validated_at_utc": datetime.now(timezone.utc).isoformat(), "checks": checks,
          "check_count": len(checks), "corrected_baseline_precision": {
              "segment_mean": payload["model"]["baseline_segment_mean"]["top_quarter_precision"],
              "location_type_bedrooms": payload["model"]["baseline_location_type_bedrooms"]["top_quarter_precision"]}}
(ROOT / "logs/validation_report.json").write_text(json.dumps(report, indent=2) + "\n")
for check in checks:
    print("PASS:", check)
print(f"Completed {len(checks)} checks. Published outputs/presentation_metrics.json.")
