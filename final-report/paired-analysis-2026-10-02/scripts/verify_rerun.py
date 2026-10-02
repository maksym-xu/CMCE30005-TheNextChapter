#!/usr/bin/env python3
"""Independently check the revised, paired host-split exports with the stdlib.

Run from anywhere: python3 /path/to/analysis/scripts/verify_rerun.py
The default analysis directory is this script's parent directory's parent.
Use --self-test to exercise the arithmetic helpers without reading private data.

This is an audit of exported partitions, preprocessing, baseline predictions,
logistic scoring from exported coefficients, and evaluation arithmetic. It does
not refit logistic regression. Fifty overlapping splits describe sensitivity to
partitions; they are not fifty independent test sets or external validation.
The JSON report contains aggregate counts and hashes, never listing/host IDs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ABS_TOL = 2e-10
REL_TOL = 2e-10
TIE_TOL = 1e-12
REPEATS = 50
TEST_SHARE = 0.30
SMOOTHING = 10.0
DESIGNS = {"host_fold", "repeated_host_split"}
AREAS = {"Melbourne", "Yarra", "Yarra Ranges", "Port Phillip", "Stonnington", "Merri-bek"}
COEFFICIENT_TERMS = {"(Intercept)", "areaYarra", "areaYarra Ranges", "areaPort Phillip",
                     "areaStonnington", "areaMerri-bek", "dwellingHouse/townhouse",
                     "bedrooms2", "bedrooms3", "price_vs_similar_10", "one_nightYes", "amenities_10"}
MISSING = {"", "NA", "NaN", "nan", "null", "NULL"}
FILES = {
    "config": "config/review_analysis.json",
    "plan": "config/rerun_plan.json",
    "input": "private-inputs/analysis_input.csv",
    "membership": "working/split_membership_PRIVATE.csv",
    "predictions": "working/test_predictions_PRIVATE.csv",
    "metrics": "outputs/split_metrics.csv",
    "preprocessing": "outputs/preprocessing_audit.csv",
    "summary": "outputs/paired_summary.csv",
    "coefficients": "outputs/split_coefficients.csv",
}
REQUIRED = {
    "input": {"id", "host_id", "host_role", "neighbourhood_cleansed", "configuration",
              "reviews_365d", "review_target_met", "fold", "common_review_threshold",
              "price_num", "minimum_nights", "n_amenities"},
    "membership": {"design", "split", "host_id", "role"},
    "predictions": {"design", "split", "id", "host_id", "segment", "busy", "p_logistic",
                    "p_segment_mean", "one_night", "was_minimum_missing",
                    "training_segment_median_price", "w_logistic", "w_segment_mean"},
    "metrics": {"design", "split", "seed", "train_hosts", "test_hosts", "train_listings",
                "test_listings", "quota", "logistic_precision", "segment_precision",
                "precision_difference_pp", "logistic_auc", "segment_auc", "auc_difference",
                "logistic_brier", "segment_brier", "brier_difference",
                "logistic_expected_positive", "segment_expected_positive"},
    "preprocessing": {"design", "split", "fill_one_night", "observed_train_no",
                      "observed_train_yes", "train_missing_minimum", "test_missing_minimum",
                      "unseen_test_segments"},
    "summary": {"metric", "logistic_mean", "segment_mean", "mean_difference", "median_difference",
                "p05_difference", "p95_difference", "min_difference", "max_difference",
                "better_splits", "tied_splits", "worse_splits", "better_direction", "splits"},
    "coefficients": {"design", "split", "term", "coefficient"},
}


class VerificationError(Exception):
    """A deliberately sanitized, non-row-level check failure."""


class Checks:
    def __init__(self):
        self.counts = Counter()

    def require(self, condition, category, message):
        self.counts[category] += 1
        if not condition:
            raise VerificationError(f"{category}: {message}")

    def close(self, actual, expected, category, message):
        self.require(math.isclose(actual, expected, rel_tol=REL_TOL, abs_tol=ABS_TOL),
                     category, message)


def number(value, field):
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise VerificationError(f"numeric_schema: invalid numeric field {field}") from None
    if not math.isfinite(result):
        raise VerificationError(f"numeric_schema: non-finite numeric field {field}")
    return result


def integer(value, field):
    result = number(value, field)
    if not result.is_integer():
        raise VerificationError(f"numeric_schema: non-integer field {field}")
    return int(result)


def boolean(value, field):
    if str(value).strip().lower() in {"true", "t", "1"}:
        return True
    if str(value).strip().lower() in {"false", "f", "0"}:
        return False
    raise VerificationError(f"boolean_schema: invalid boolean field {field}")


def optional_number(value, field):
    return None if str(value).strip() in MISSING else number(value, field)


def split_key(row):
    if row["design"] not in DESIGNS:
        raise VerificationError("split_schema: unexpected design")
    return row["design"], integer(row["split"], "split")


def read_csv(path, name, checks):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        checks.require(REQUIRED[name].issubset(reader.fieldnames or []), "schema",
                       f"required columns missing in {FILES[name]}")
        rows = list(reader)
    checks.require(bool(rows), "schema", f"empty file {FILES[name]}")
    checks.require(all(None not in row and all(v is not None for v in row.values()) for row in rows),
                   "schema", f"malformed CSV row in {FILES[name]}")
    return rows


def unique_by_split(rows, name, checks):
    result = {}
    for row in rows:
        key = split_key(row)
        checks.require(key not in result, "schema", f"duplicate split in {FILES[name]}")
        result[key] = row
    return result


def quantile_type7(values, probability):
    ordered = sorted(values)
    if not ordered:
        raise VerificationError("arithmetic: cannot compute an empty quantile")
    position = (len(ordered) - 1) * probability
    lo = math.floor(position)
    hi = math.ceil(position)
    return ordered[lo] + (position - lo) * (ordered[hi] - ordered[lo])


def auc_rank(labels, scores):
    """Mann-Whitney AUC; average ranks give half credit to tied scores."""
    positives = sum(labels)
    negatives = len(labels) - positives
    if not positives or not negatives:
        raise VerificationError("arithmetic: AUC requires both outcome classes")
    ordered = sorted(zip(scores, labels))
    rank_sum = 0.0
    left = 0
    while left < len(ordered):
        right = left + 1
        while right < len(ordered) and ordered[right][0] == ordered[left][0]:
            right += 1
        average_rank = (left + 1 + right) / 2.0
        rank_sum += average_rank * sum(y for _, y in ordered[left:right])
        left = right
    return (rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def quota_weights(scores):
    quota = (len(scores) + 3) // 4
    if quota == 0:
        raise VerificationError("arithmetic: empty screening population")
    boundary = sorted(scores, reverse=True)[quota - 1]
    above = sum(p > boundary for p in scores)
    tied = sum(p == boundary for p in scores)
    fraction = (quota - above) / tied
    return quota, [1.0 if p > boundary else fraction if p == boundary else 0.0 for p in scores]


def performance(labels, scores):
    quota, weights = quota_weights(scores)
    expected_positive = math.fsum(w * y for w, y in zip(weights, labels))
    return {
        "quota": quota,
        "precision": expected_positive / quota,
        "auc": auc_rank(labels, scores),
        "brier": math.fsum((p - y) ** 2 for p, y in zip(scores, labels)) / len(labels),
        "expected_positive": expected_positive,
    }, weights


def logistic_probability(source, imputed_one_night, training_median, coefficients):
    """Recreate treatment contrasts and the six-input score, without fitting."""
    features = {
        "(Intercept)": 1.0,
        "price_vs_similar_10": (source["price"] / training_median - 1) * 10,
        "one_nightYes": float(imputed_one_night == "Yes"),
        "amenities_10": source["amenities"] / 10,
    }
    if source["area"] != "Melbourne":
        features["area" + source["area"]] = 1.0
    if source["dwelling"] == "House/townhouse":
        features["dwellingHouse/townhouse"] = 1.0
    if source["bedrooms"] != "1":
        features["bedrooms" + source["bedrooms"]] = 1.0
    linear = math.fsum(coefficients[term] * value for term, value in features.items())
    if linear >= 0:
        return 1.0 / (1.0 + math.exp(-linear))
    exp_linear = math.exp(linear)
    return exp_linear / (1.0 + exp_linear)


def validate(root, checks):
    config = json.loads((root / FILES["config"]).read_text(encoding="utf-8"))
    plan = json.loads((root / FILES["plan"]).read_text(encoding="utf-8"))
    seed = integer(config["seed"], "config.seed")
    for field, value in (("seed", seed), ("repeats", REPEATS), ("test_host_share", TEST_SHARE),
                         ("screening_fraction", .25), ("baseline_smoothing_weight", SMOOTHING)):
        checks.close(number(plan[field], "plan." + field), value, "plan", "unexpected frozen plan value " + field)
    data = {name: read_csv(root / rel, name, checks) for name, rel in FILES.items() if name in REQUIRED}
    records = {}
    host_folds = {}
    for raw in data["input"]:
        checks.require(bool(raw["id"]) and bool(raw["host_id"]), "input", "empty private identifier")
        checks.require(raw["id"] not in records, "input", "duplicate listing identifier")
        checks.require(raw["host_role"] == "analysis", "input", "non-analysis host in analysis input")
        y = integer(raw["review_target_met"], "review_target_met")
        cutoff = number(raw["common_review_threshold"], "common_review_threshold")
        checks.close(cutoff, number(plan["outcome_threshold"], "plan.outcome_threshold"), "input",
                     "listing outcome threshold differs from frozen plan")
        checks.require(y in (0, 1) and y == int(number(raw["reviews_365d"], "reviews_365d") >= cutoff),
                       "input", "outcome and frozen review threshold disagree")
        fold = integer(raw["fold"], "fold")
        if raw["host_id"] in host_folds:
            checks.require(host_folds[raw["host_id"]] == fold, "input", "one host spans original folds")
        host_folds[raw["host_id"]] = fold
        minimum = optional_number(raw["minimum_nights"], "minimum_nights")
        price = number(raw["price_num"], "price_num")
        checks.require(price > 0, "input", "non-positive eligible listing price")
        amenities = number(raw["n_amenities"], "n_amenities")
        checks.require(raw["neighbourhood_cleansed"] in AREAS and raw["configuration"][:1] in {"1", "2", "3"},
                       "input", "unsupported area or bedroom factor level")
        records[raw["id"]] = {"host": raw["host_id"], "fold": fold, "y": y,
            "segment": raw["neighbourhood_cleansed"] + " " + raw["configuration"],
            "price": price, "minimum": minimum,
            "area": raw["neighbourhood_cleansed"], "bedrooms": raw["configuration"][:1],
            "dwelling": "House/townhouse" if "House" in raw["configuration"] else "Apartment/unit",
            "amenities": amenities,
            "one_night": None if minimum is None else "Yes" if minimum <= 1 else "No"}
    all_hosts = set(host_folds)
    fold_values = set(host_folds.values())
    checks.require(len(fold_values) == 5, "input", "expected five original host folds")
    expected_keys = {("host_fold", k) for k in fold_values} | {
        ("repeated_host_split", i) for i in range(1, REPEATS + 1)}
    partitions = defaultdict(list)
    predictions = defaultdict(list)
    for row in data["membership"]:
        partitions[split_key(row)].append(row)
    for row in data["predictions"]:
        predictions[split_key(row)].append(row)
    metrics = unique_by_split(data["metrics"], "metrics", checks)
    preprocessing = unique_by_split(data["preprocessing"], "preprocessing", checks)
    coefficients = defaultdict(dict)
    for row in data["coefficients"]:
        key = split_key(row)
        checks.require(row["term"] not in coefficients[key], "coefficients", "duplicate coefficient term within split")
        coefficients[key][row["term"]] = number(row["coefficient"], "coefficient")
    for name, mapping in (("membership", partitions), ("predictions", predictions),
                          ("metrics", metrics), ("preprocessing", preprocessing), ("coefficients", coefficients)):
        checks.require(set(mapping) == expected_keys, "split_coverage",
                       f"{FILES[name]} must contain the same five folds and fifty repeated splits")
    recomputed = {}
    unseen_counts = []
    train_fill_counts = Counter()
    maximum_probability_difference = 0.0
    for key in sorted(expected_keys):
        design, split = key
        context = f"{design} split {split}"
        checks.require(set(coefficients[key]) == COEFFICIENT_TERMS, "coefficients",
                       context + ": coefficient terms differ from frozen six-input model")
        members = partitions[key]
        seen_hosts = [r["host_id"] for r in members]
        checks.require(len(seen_hosts) == len(set(seen_hosts)) and set(seen_hosts) == all_hosts,
                       "partition", context + ": every input host must occur once")
        checks.require(all(r["role"] in {"train", "test"} for r in members),
                       "partition", context + ": invalid membership role")
        train_hosts = {r["host_id"] for r in members if r["role"] == "train"}
        test_hosts = {r["host_id"] for r in members if r["role"] == "test"}
        checks.require(bool(train_hosts) and bool(test_hosts) and not train_hosts & test_hosts,
                       "partition", context + ": overlapping or empty train/test hosts")
        if design == "host_fold":
            checks.require(test_hosts == {h for h, f in host_folds.items() if f == split},
                           "partition", context + ": test membership differs from original host fold")
        else:
            checks.require(len(test_hosts) == round(TEST_SHARE * len(all_hosts)),
                           "partition", context + ": incorrect 30 percent test-host count")
            checks.require(integer(metrics[key]["seed"], "seed") == seed + split,
                           "partition", context + ": incorrect declared repeated-split seed")
        train = [r for r in records.values() if r["host"] in train_hosts]
        test = {i: r for i, r in records.items() if r["host"] in test_hosts}
        rows = predictions[key]
        exported_ids = [r["id"] for r in rows]
        checks.require(len(exported_ids) == len(set(exported_ids)) and set(exported_ids) == set(test),
                       "test_rows", context + ": exported tests differ from complete held-out-host listings")
        observed = Counter(r["one_night"] for r in train if r["one_night"] is not None)
        checks.require(sum(observed.values()) > 0, "preprocessing", context + ": no observed training minimum stay")
        fill = "Yes" if observed["Yes"] > observed["No"] else "No"
        train_fill_counts[fill] += 1
        audit = preprocessing[key]
        checks.require(audit["fill_one_night"] == fill, "preprocessing", context + ": wrong training binary mode")
        expected_audit = {
            "observed_train_no": observed["No"], "observed_train_yes": observed["Yes"],
            "train_missing_minimum": sum(r["minimum"] is None for r in train),
            "test_missing_minimum": sum(r["minimum"] is None for r in test.values()),
        }
        train_segments = defaultdict(list)
        for row in train:
            train_segments[row["segment"]].append(row)
        unseen = {r["segment"] for r in test.values()} - set(train_segments)
        unseen_counts.append(len(unseen))
        expected_audit["unseen_test_segments"] = len(unseen)
        for field, expected in expected_audit.items():
            checks.require(integer(audit[field], field) == expected, "preprocessing",
                           context + ": incorrect audit count " + field)
        train_prevalence = sum(r["y"] for r in train) / len(train)
        global_price = statistics.median(r["price"] for r in train)
        medians = {s: statistics.median(r["price"] for r in rs) for s, rs in train_segments.items()}
        baseline = {s: (sum(r["y"] for r in rs) + SMOOTHING * train_prevalence) / (len(rs) + SMOOTHING)
                    for s, rs in train_segments.items()}
        labels, logit_scores, baseline_scores = [], [], []
        for row in rows:
            source = test[row["id"]]
            checks.require(row["host_id"] == source["host"] and row["segment"] == source["segment"],
                           "test_rows", context + ": test host/segment does not match input")
            checks.require(integer(row["busy"], "busy") == source["y"], "test_rows",
                           context + ": exported test outcome differs from frozen input")
            checks.require(boolean(row["was_minimum_missing"], "was_minimum_missing") == (source["minimum"] is None),
                           "preprocessing", context + ": wrong original missingness flag")
            checks.require(row["one_night"] == (source["one_night"] or fill), "preprocessing",
                           context + ": test binary setting not filled from observed training mode")
            checks.close(number(row["training_segment_median_price"], "training_segment_median_price"),
                         medians.get(source["segment"], global_price), "preprocessing",
                         context + ": segment price median differs from training-only median")
            p_l = number(row["p_logistic"], "p_logistic")
            p_s = number(row["p_segment_mean"], "p_segment_mean")
            checks.require(0 <= p_l <= 1 and 0 <= p_s <= 1, "scores", context + ": probability outside [0,1]")
            checks.close(p_s, baseline.get(source["segment"], train_prevalence), "baseline",
                         context + ": baseline differs from train-only smoothed segment outcome rate")
            reconstructed_p = logistic_probability(source, source["one_night"] or fill,
                                                   medians.get(source["segment"], global_price), coefficients[key])
            maximum_probability_difference = max(maximum_probability_difference, abs(p_l - reconstructed_p))
            checks.close(p_l, reconstructed_p, "logistic_scoring",
                         context + ": probability differs from independent feature/contrast reconstruction and exported coefficients")
            labels.append(source["y"])
            logit_scores.append(p_l)
            baseline_scores.append(p_s)
        left, left_weights = performance(labels, logit_scores)
        right, right_weights = performance(labels, baseline_scores)
        for field, computed in (("w_logistic", left_weights), ("w_segment_mean", right_weights)):
            for row, weight in zip(rows, computed):
                checks.close(number(row[field], field), weight, "quota", context + ": wrong equal-quota tie weight")
            checks.close(math.fsum(computed), left["quota"], "quota", context + ": quota not exhausted exactly in expectation")
        expected_metrics = {
            "train_hosts": len(train_hosts), "test_hosts": len(test_hosts),
            "train_listings": len(train), "test_listings": len(test), "quota": left["quota"],
            "precision_difference_pp": 100 * (left["precision"] - right["precision"]),
            "auc_difference": left["auc"] - right["auc"],
            "brier_difference": left["brier"] - right["brier"],
        }
        for prefix, result in (("logistic", left), ("segment", right)):
            expected_metrics.update({f"{prefix}_{field}": result[field]
                                     for field in ("precision", "auc", "brier", "expected_positive")})
        for field, expected in expected_metrics.items():
            checks.close(number(metrics[key][field], field), expected, "split_metrics",
                         context + ": incorrect exported metric " + field)
        recomputed[key] = expected_metrics

    # Summarize within-split paired differences; never pool repeat predictions or
    # subtract marginal quantiles from two separately summarized model series.
    summary_rows = {r["metric"]: r for r in data["summary"]}
    specs = {"precision_difference_pp": ("precision", "higher"),
             "auc_difference": ("auc", "higher"), "brier_difference": ("brier", "lower")}
    checks.require(len(summary_rows) == len(data["summary"]) and set(summary_rows) == set(specs),
                   "paired_summary", "expected exactly the three paired-difference metrics")
    repeats = [recomputed[("repeated_host_split", i)] for i in range(1, REPEATS + 1)]
    checked_summaries = []
    for metric, (component, direction) in specs.items():
        row = summary_rows[metric]
        differences = [r[metric] for r in repeats]
        signed = [x if direction == "higher" else -x for x in differences]
        expected = {
            "logistic_mean": statistics.fmean(r[f"logistic_{component}"] for r in repeats),
            "segment_mean": statistics.fmean(r[f"segment_{component}"] for r in repeats),
            "mean_difference": statistics.fmean(differences),
            "median_difference": statistics.median(differences),
            "p05_difference": quantile_type7(differences, .05),
            "p95_difference": quantile_type7(differences, .95),
            "min_difference": min(differences), "max_difference": max(differences),
            "better_splits": sum(x > TIE_TOL for x in signed),
            "tied_splits": sum(abs(x) <= TIE_TOL for x in signed),
            "worse_splits": sum(x < -TIE_TOL for x in signed), "splits": REPEATS,
        }
        checks.require(row["better_direction"] == direction, "paired_summary",
                       "incorrect better direction for " + metric)
        for field, value in expected.items():
            checks.close(number(row[field], field), value, "paired_summary",
                         "incorrect paired summary field " + metric + "." + field)
        checked_summaries.append({"metric": metric, **expected, "better_direction": direction})
    return {
        "input_listings": len(records), "input_hosts": len(all_hosts),
        "input_positive_listings": sum(r["y"] for r in records.values()),
        "input_missing_minimum_nights": sum(r["minimum"] is None for r in records.values()),
        "host_fold_splits": len(fold_values), "repeated_host_splits": REPEATS,
        "test_prediction_rows": len(data["predictions"]),
        "training_imputation_modes_by_split": dict(sorted(train_fill_counts.items())),
        "maximum_unseen_test_segments_per_split": max(unseen_counts),
        "maximum_logistic_scoring_difference": maximum_probability_difference,
        "independently_recomputed_paired_summary": checked_summaries,
    }


def self_test():
    assert auc_rank([0, 1], [0.0, 1.0]) == 1.0
    assert auc_rank([0, 1], [1.0, 0.0]) == 0.0
    assert auc_rank([0, 1], [0.5, 0.5]) == 0.5
    assert auc_rank([0, 1, 0, 1], [0, 0, 1, 1]) == 0.5
    quota, weights = quota_weights([.9, .8, .8, .8, .1])
    assert quota == 2 and weights == [1, 1 / 3, 1 / 3, 1 / 3, 0]
    p, w = performance([1, 0, 1, 0, 0], [.9, .8, .8, .8, .1])
    assert math.isclose(p["precision"], 2 / 3)
    assert math.isclose(sum(w), 2)
    assert math.isclose(quantile_type7([0, 10, 20, 30], .05), 1.5)
    assert math.isclose(quantile_type7([0, 10, 20, 30], .95), 28.5)
    assert statistics.median([1, 2, 3, 4]) == 2.5
    assert boolean("TRUE", "test") and not boolean("0", "test")
    source = {"price": 100, "amenities": 0, "area": "Melbourne", "bedrooms": "1", "dwelling": "Apartment/unit"}
    zero_coefficients = {term: 0.0 for term in COEFFICIENT_TERMS}
    assert logistic_probability(source, "No", 100, zero_coefficients) == .5
    print("Arithmetic self-tests passed (no private data read; no models fit).")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    root = args.analysis_root.resolve()
    checks = Checks()
    report = {
        "schema_version": "1.0",
        "validator": "scripts/verify_rerun.py (Python standard library; independent metric implementation)",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "incomplete",
        "scope": [
            "Complete, disjoint host partitions and exact test-row membership against frozen private input",
            "Original host-fold membership; repeated test-host counts and declared seeds",
            "Training-only observed binary mode (No on a tie), exported test imputation and missingness",
            "Training-only segment price medians; training-global median fallback for unseen segments",
            "Training-only segment outcome baseline with smoothing weight 10 and prevalence fallback",
            "Independent six-input feature/contrast reconstruction and logistic scoring from every split's exported coefficients",
            "Same ceil(test listings / 4) expected quota; uniform fractional weights at each score boundary",
            "Independent AUC with half credit for ties, Brier score, precision, positives and paired differences",
            "Fifty within-split paired summaries with R type-7 quantiles and explicit better directions",
        ],
        "limits": [
            "Recreates logistic scoring from exported coefficients, but does not refit or independently verify their estimation.",
            "Does not replay R's random-number generator; verifies frozen memberships, counts and declared seeds.",
            "Exported train-mode counts and test transformations are checked; training model-matrix internals are not exported.",
            "The fifty repeated splits overlap and are correlated internal sensitivity checks, not independent tests.",
            "The 5th and 95th percentiles describe split variation, not confidence intervals or external validation.",
            "One-night binarisation was selected after earlier outcome exploration and then frozen; these checks do not undo that selection.",
            "Earlier nested model selection does not validate this revised exploratory specification.",
            "Current settings paired with prior-year outcomes establish retrospective discrimination, not future forecasts or causal effects.",
        ],
        "numeric_tolerance": {"absolute": ABS_TOL, "relative": REL_TOL, "better_tie_epsilon": TIE_TOL},
        "units": {"precision_model_means": "proportion", "precision_differences": "percentage points",
                  "auc_and_brier_model_means_and_differences": "raw score units"},
        "file_sha256": {},
    }
    missing = [rel for rel in FILES.values() if not (root / rel).is_file()]
    if missing:
        report["missing_required_files"] = missing
    else:
        report["file_sha256"] = {rel: hashlib.sha256((root / rel).read_bytes()).hexdigest()
                                  for rel in FILES.values()}
        try:
            report["results"] = validate(root, checks)
            report["status"] = "passed"
        except VerificationError as exc:
            report["status"] = "failed"
            report["failure"] = str(exc)
        except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            # Do not expose arbitrary exception text, which may include private
            # row content or absolute local paths. This is an explicit failure.
            report["status"] = "failed"
            report["failure"] = "Unexpected schema or file-processing error (" + type(exc).__name__ + ")."
    report["checks_by_category"] = dict(sorted(checks.counts.items()))
    destination = root / "outputs/verification.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print("Verification " + report["status"] + "; report: outputs/verification.json")
    if "failure" in report:
        print(report["failure"], file=sys.stderr)
    if missing:
        print("Required exports are not ready: " + ", ".join(missing), file=sys.stderr)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
