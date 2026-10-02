#!/usr/bin/env python3
"""Independently verify the screening follow-up exports using the standard library.

This checks frozen input hashes, original host memberships, retained scores,
training-only segment baselines, reduced-model scoring from exported coefficients,
selection arithmetic, and every exported metric and paired summary. It does not
refit logistic regression or repeat the earlier raw-review construction. All public
output is aggregate; failures never print listing or host identifiers.
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
SPLITS = set(range(1, 51))
FRACTIONS = (0.10, 0.25, 0.50)
MODELS = ("baseline", "property_only", "full")
SCOPES = ("all_eligible", "priority_pool", "priority_fixed_quota")
PRIORITY = (
    "Melbourne 2BR Apartment/unit",
    "Melbourne 3BR Apartment/unit",
    "Yarra Ranges 3BR House/townhouse",
)
AREAS = {"Melbourne", "Yarra", "Yarra Ranges", "Port Phillip", "Stonnington", "Merri-bek"}
TERMS = {
    "(Intercept)", "areaYarra", "areaYarra Ranges", "areaPort Phillip",
    "areaStonnington", "areaMerri-bek", "dwellingHouse/townhouse",
    "bedrooms2", "bedrooms3", "amenities_10",
}
PAIRS = {
    "full_vs_baseline": ("full", "baseline"),
    "property_only_vs_baseline": ("property_only", "baseline"),
    "full_vs_property_only": ("full", "property_only"),
}
SCREEN_METRICS = ("precision", "recall", "expected_target_selected", "quota")
SCREEN_DELTAS = (
    "precision_difference_pp", "recall_difference_pp", "expected_target_selected_difference",
)
SUMMARY_FIELDS = ("splits", "n_finite", "mean", "median", "p05", "p95", "min", "max")
PAIRED_SUMMARY_FIELDS = (
    "splits", "n_finite", "mean_difference", "median_difference", "p05_difference",
    "p95_difference", "min_difference", "max_difference", "better_splits",
    "tied_splits", "worse_splits", "better_direction",
)
SCREEN_FIELDS = (
    "n_listings", "n_hosts", "target_count", "quota", "expected_target_selected", "precision", "recall",
)
POPULATION_FIELDS = ("n_listings", "n_hosts", "target_count")
MISSING = {"", "NA", "NaN", "nan", "null", "NULL"}
INPUT = "private-inputs/analysis_input.csv"
MEMBERSHIP = "private-inputs/prior_split_membership_PRIVATE.csv"
OLD_PREDICTIONS = "private-inputs/prior_test_predictions_PRIVATE.csv"
PREDICTIONS = "working/test_predictions_PRIVATE.csv"
OLD_METRICS = "reference/prior_split_metrics.csv"
COEFFICIENTS = "outputs/property_only_coefficients.csv"
DIAGNOSTICS = "outputs/property_only_fit_diagnostics.csv"
RUN_CHECKS = "outputs/run_checks.json"
PRIOR_VERIFICATION = "reference/prior_verification.json"
PLAN = "config/followup_plan.json"
FINGERPRINTS = "reference/input_fingerprints.json"
TABLES = {
    "screening": "outputs/split_screening_metrics.csv",
    "group": "outputs/priority_group_metrics.csv",
    "screening_pairs": "outputs/paired_screening_differences.csv",
    "group_pairs": "outputs/paired_priority_group_differences.csv",
    "screening_summary": "outputs/screening_summary.csv",
    "group_summary": "outputs/priority_group_summary.csv",
    "screening_pair_summary": "outputs/paired_screening_summary.csv",
    "group_pair_summary": "outputs/paired_priority_group_summary.csv",
    "discrimination": "outputs/discrimination_metrics.csv",
    "discrimination_pairs": "outputs/paired_discrimination_differences.csv",
    "discrimination_summary": "outputs/discrimination_summary.csv",
    "discrimination_pair_summary": "outputs/paired_discrimination_summary.csv",
}


class VerificationError(Exception):
    """A failure message that does not contain a private row or identifier."""


class Checks:
    def __init__(self):
        self.counts = Counter()

    def require(self, condition, category, message):
        self.counts[category] += 1
        if not condition:
            raise VerificationError(f"{category}: {message}")

    def close(self, actual, expected, category, message):
        if actual is None or expected is None:
            self.require(actual is None and expected is None, category, message)
        else:
            self.require(math.isclose(actual, expected, rel_tol=REL_TOL, abs_tol=ABS_TOL), category, message)


def number(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise VerificationError("schema: invalid numeric value") from None
    if not math.isfinite(result):
        raise VerificationError("schema: non-finite numeric value")
    return result


def optional_number(value):
    return None if str(value).strip() in MISSING else number(value)


def integer(value):
    result = number(value)
    if not result.is_integer():
        raise VerificationError("schema: expected integer value")
    return int(result)


def boolean(value):
    clean = str(value).strip().lower()
    if clean in {"true", "t", "1"}:
        return 1
    if clean in {"false", "f", "0"}:
        return 0
    raise VerificationError("schema: invalid binary value")


def read_csv(root, relative, required, checks):
    with (root / relative).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        checks.require(set(required).issubset(reader.fieldnames or []), "schema", relative + ": missing columns")
        rows = list(reader)
    checks.require(bool(rows), "schema", relative + ": empty export")
    checks.require(all(None not in row and all(v is not None for v in row.values()) for row in rows),
                   "schema", relative + ": malformed row")
    return rows


def typed_key(row, fields):
    result = []
    for field in fields:
        value = row[field]
        if field == "split":
            value = integer(value)
        elif field == "fraction":
            value = round(number(value), 10)
        result.append(value)
    return tuple(result)


def index_table(rows, fields, checks, category):
    result = {}
    for row in rows:
        key = typed_key(row, fields)
        checks.require(key not in result, category, "duplicate key")
        result[key] = row
    return result


def check_table(root, relative, keys, fields, expected, checks):
    rows = read_csv(root, relative, (*keys, *fields), checks)
    actual = index_table(rows, keys, checks, relative)
    checks.require(set(actual) == set(expected), relative, "row coverage differs from independently rebuilt table")
    for key, wanted in expected.items():
        for field in fields:
            value = wanted[field]
            if isinstance(value, str):
                checks.require(actual[key][field] == value, relative, "incorrect " + field)
            else:
                checks.close(optional_number(actual[key][field]), value, relative, "incorrect " + field)


def quantile(values, probability):
    ordered = sorted(values)
    if not ordered:
        return None
    position = (len(ordered) - 1) * probability
    lo, hi = math.floor(position), math.ceil(position)
    return ordered[lo] + (position - lo) * (ordered[hi] - ordered[lo])


def auc(labels, scores):
    positives = sum(labels)
    negatives = len(labels) - positives
    if not positives or not negatives:
        return None
    ordered = sorted(zip(scores, labels))
    rank_sum = 0.0
    left = 0
    while left < len(ordered):
        right = left + 1
        while right < len(ordered) and ordered[right][0] == ordered[left][0]:
            right += 1
        average_rank = (left + 1 + right) / 2
        rank_sum += average_rank * sum(y for _, y in ordered[left:right])
        left = right
    return (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)


def quota_weights(scores, fraction):
    if not scores:
        return 0, []
    quota = math.ceil(len(scores) * fraction)
    boundary = sorted(scores, reverse=True)[quota - 1]
    above = sum(score > boundary for score in scores)
    tied = sum(score == boundary for score in scores)
    tied_weight = (quota - above) / tied
    weights = [1.0 if score > boundary else tied_weight if score == boundary else 0.0 for score in scores]
    return quota, weights


def population(rows):
    return {"n_listings": len(rows), "n_hosts": len({r["host"] for r in rows}),
            "target_count": sum(r["y"] for r in rows)}


def screening(rows, model, fraction, fixed_groups, checks):
    if fixed_groups:
        quota = 0
        selected = 0.0
        for group in PRIORITY:
            group_rows = [row for row in rows if row["segment"] == group]
            k, weights = quota_weights([r[model] for r in group_rows], fraction)
            checks.close(math.fsum(weights), k, "quota", "fixed-group weights do not exhaust quota")
            checks.require(all(0 <= w <= 1 for w in weights), "quota", "invalid fixed-group weight")
            quota += k
            selected += math.fsum(w * r["y"] for w, r in zip(weights, group_rows))
    else:
        quota, weights = quota_weights([r[model] for r in rows], fraction)
        checks.close(math.fsum(weights), quota, "quota", "weights do not exhaust quota")
        checks.require(all(0 <= w <= 1 for w in weights), "quota", "invalid selection weight")
        selected = math.fsum(w * r["y"] for w, r in zip(weights, rows))
    counts = population(rows)
    return {**counts, "quota": quota, "expected_target_selected": selected,
            "precision": selected / quota if quota else None,
            "recall": selected / counts["target_count"] if counts["target_count"] else None}


def discrimination(rows, model):
    labels = [r["y"] for r in rows]
    scores = [r[model] for r in rows]
    return {**population(rows), "auc": auc(labels, scores),
            "brier": math.fsum((y - p) ** 2 for y, p in zip(labels, scores)) / len(rows) if rows else None}


def property_score(raw, coefficients):
    features = {"(Intercept)": 1.0, "amenities_10": raw["amenities"] / 10}
    if raw["area"] != "Melbourne":
        features["area" + raw["area"]] = 1.0
    if raw["dwelling"] == "House/townhouse":
        features["dwellingHouse/townhouse"] = 1.0
    if raw["bedrooms"] != "1":
        features["bedrooms" + raw["bedrooms"]] = 1.0
    z = math.fsum(coefficients[term] * value for term, value in features.items())
    if z >= 0:
        return 1 / (1 + math.exp(-z))
    exp_z = math.exp(z)
    return exp_z / (1 + exp_z)


def difference(left, right, multiplier=1):
    return None if left is None or right is None else multiplier * (left - right)


def paired_rows(metric_rows, screening_table=True):
    result = {}
    bases = {key[:-1] for key in metric_rows}
    for base in bases:
        for pair, (left, right) in PAIRS.items():
            l, r = metric_rows[base + (left,)], metric_rows[base + (right,)]
            row = {field: l[field] for field in POPULATION_FIELDS}
            row.update(left_model=left, right_model=right)
            if screening_table:
                row.update(quota=l["quota"],
                           precision_difference_pp=difference(l["precision"], r["precision"], 100),
                           recall_difference_pp=difference(l["recall"], r["recall"], 100),
                           expected_target_selected_difference=difference(l["expected_target_selected"], r["expected_target_selected"]))
            else:
                row.update(auc_difference=difference(l["auc"], r["auc"]),
                           brier_difference=difference(l["brier"], r["brier"]))
            result[base + (pair,)] = row
    return result


def summary_rows(metric_rows, fields, paired=False):
    groups = defaultdict(list)
    for key, row in metric_rows.items():
        for field in fields:
            groups[key[1:] + (field,)].append(row[field])
    result = {}
    for key, values in groups.items():
        finite = [value for value in values if value is not None]
        stats = {"splits": len(values), "n_finite": len(finite),
                 "mean": statistics.fmean(finite) if finite else None,
                 "median": statistics.median(finite) if finite else None,
                 "p05": quantile(finite, .05), "p95": quantile(finite, .95),
                 "min": min(finite) if finite else None, "max": max(finite) if finite else None}
        if paired:
            stats = {name + "_difference" if name not in {"splits", "n_finite"} else name: value
                     for name, value in stats.items()}
            lower = key[-1] == "brier_difference"
            favourable = [-value if lower else value for value in finite]
            stats.update(better_splits=sum(value > TIE_TOL for value in favourable),
                         tied_splits=sum(abs(value) <= TIE_TOL for value in favourable),
                         worse_splits=sum(value < -TIE_TOL for value in favourable),
                         better_direction="lower" if lower else "higher")
        result[key] = stats
    return result


def verify(root, checks):
    plan = json.loads((root / PLAN).read_text(encoding="utf-8"))
    checks.require(plan["input_rows"] == 3873 and plan["input_hosts"] == 1726 and plan["splits"] == 50,
                   "plan", "population or split plan changed")
    checks.require(tuple(plan["fractions"]) == FRACTIONS and plan["primary_fraction"] == .25,
                   "plan", "quota fractions changed")
    checks.require(set(plan["priority_groups"]) == set(PRIORITY) and set(plan["scopes"]) == set(SCOPES),
                   "plan", "scope definitions changed")
    checks.require(set(plan["models"]) == set(MODELS) and
                   "busy ~ area + dwelling + bedrooms + amenities_10" in plan["models"]["property_only"],
                   "plan", "reduced specification does not retain exactly the planned inputs")
    prior_verification = json.loads((root / PRIOR_VERIFICATION).read_text(encoding="utf-8"))
    checks.require(prior_verification["status"] == "passed", "prior_verification", "prior independent check did not pass")
    prior_paths = {
        INPUT: "private-inputs/analysis_input.csv",
        MEMBERSHIP: "working/split_membership_PRIVATE.csv",
        OLD_PREDICTIONS: "working/test_predictions_PRIVATE.csv",
        OLD_METRICS: "outputs/split_metrics.csv",
        "reference/prior_full_coefficients.csv": "outputs/split_coefficients.csv",
    }
    for current, previous in prior_paths.items():
        checks.require(sha256(root / current) == prior_verification["file_sha256"][previous],
                       "prior_verification", "current source differs from the independently checked prior export")
    checks.require(prior_verification["results"]["host_fold_splits"] == 5 and
                   prior_verification["results"]["repeated_host_splits"] == 50 and
                   prior_verification["results"]["test_prediction_rows"] == 63093,
                   "prior_verification", "prior verification scope changed")

    inputs = read_csv(root, INPUT, ("id", "host_id", "host_role", "neighbourhood_cleansed", "configuration",
                     "reviews_365d", "review_target_met", "common_review_threshold", "n_amenities"), checks)
    records = {}
    for row in inputs:
        identifier = row["id"]
        checks.require(bool(identifier) and identifier not in records, "input", "missing or duplicate listing identifier")
        checks.require(bool(row["host_id"]) and row["host_role"] == "analysis", "input", "invalid host or population role")
        area = row["neighbourhood_cleansed"]
        config = row["configuration"]
        valid_configs = {f"{n}BR {kind}" for n in (1, 2, 3) for kind in ("Apartment/unit", "House/townhouse")}
        checks.require(area in AREAS and config in valid_configs, "input", "unexpected property category")
        y = boolean(row["review_target_met"])
        checks.require(integer(row["common_review_threshold"]) == 30 and y == (integer(row["reviews_365d"]) >= 30),
                       "input", "outcome differs from fixed review threshold")
        amenities = number(row["n_amenities"])
        checks.require(amenities >= 0, "input", "negative amenity count")
        records[identifier] = {"host": row["host_id"], "segment": area + " " + config,
                               "y": y, "area": area, "bedrooms": config[0],
                               "dwelling": config.split(" ", 1)[1], "amenities": amenities}
    all_hosts = {r["host"] for r in records.values()}
    checks.require(len(records) == 3873 and len(all_hosts) == 1726 and sum(r["y"] for r in records.values()) == 981,
                   "input", "input population count differs from frozen sample")

    partitions = defaultdict(list)
    for row in read_csv(root, MEMBERSHIP, ("design", "split", "host_id", "role"), checks):
        checks.require(row["design"] in {"host_fold", "repeated_host_split"}, "membership", "unknown prior design")
        if row["design"] == "repeated_host_split":
            partitions[integer(row["split"])].append(row)
    checks.require(set(partitions) == SPLITS, "membership", "expected all fifty original memberships")
    prior_predictions = defaultdict(dict)
    for row in read_csv(root, OLD_PREDICTIONS, ("design", "split", "id", "host_id", "segment", "busy", "p_logistic", "p_segment_mean"), checks):
        if row["design"] == "repeated_host_split":
            split = integer(row["split"])
            checks.require(row["id"] not in prior_predictions[split], "prior_scores", "duplicate prior test row")
            prior_predictions[split][row["id"]] = row
    checks.require(set(prior_predictions) == SPLITS, "prior_scores", "expected prior predictions for fifty splits")
    prior_metrics = {}
    for row in read_csv(root, OLD_METRICS, ("design", "split", "seed", "quota", "logistic_precision", "segment_precision",
                       "logistic_auc", "segment_auc", "logistic_brier", "segment_brier",
                       "logistic_expected_positive", "segment_expected_positive", "precision_difference_pp",
                       "auc_difference", "brier_difference"), checks):
        if row["design"] == "repeated_host_split":
            split = integer(row["split"])
            checks.require(split not in prior_metrics, "prior_metrics", "duplicate original repeated split")
            prior_metrics[split] = row
            checks.require(integer(row["seed"]) == 30005 + split, "prior_metrics", "unexpected declared original seed")
    checks.require(set(prior_metrics) == SPLITS, "prior_metrics", "expected metrics for fifty original splits")

    predictions = defaultdict(list)
    for row in read_csv(root, PREDICTIONS, ("split", "id", "host_id", "segment", "busy", "p_baseline", "p_property_only", "p_full"), checks):
        predictions[integer(row["split"])].append(row)
    checks.require(set(predictions) == SPLITS, "scores", "expected fifty follow-up test sets")
    coefficients = defaultdict(dict)
    for row in read_csv(root, COEFFICIENTS, ("split", "term", "coefficient"), checks):
        split = integer(row["split"])
        checks.require(row["term"] not in coefficients[split], "coefficients", "duplicate reduced-model coefficient")
        coefficients[split][row["term"]] = number(row["coefficient"])
    checks.require(set(coefficients) == SPLITS, "coefficients", "expected reduced coefficients for fifty splits")
    diagnostics = index_table(read_csv(root, DIAGNOSTICS, (
        "split", "train_listings", "train_hosts", "test_listings", "test_hosts", "converged", "iterations",
        "nobs", "coefficient_count", "has_na_coefficients", "warning_count",
        "baseline_reconstruction_max_difference", "full_score_reconstruction_max_difference"), checks),
        ("split",), checks, "fit_diagnostics")
    checks.require(set(diagnostics) == {(split,) for split in SPLITS}, "fit_diagnostics", "expected fifty diagnostics rows")

    screened, group_screened, discriminated = {}, {}, {}
    max_errors = Counter()
    test_rows_checked = 0
    test_host_counts, test_listing_counts = [], []
    zero_target_group_splits = 0
    for split in sorted(SPLITS):
        membership = partitions[split]
        member_hosts = [row["host_id"] for row in membership]
        checks.require(len(member_hosts) == len(set(member_hosts)) and set(member_hosts) == all_hosts,
                       "membership", "frozen partition does not contain each host exactly once")
        checks.require(all(row["role"] in {"train", "test"} for row in membership), "membership", "invalid role")
        train_hosts = {r["host_id"] for r in membership if r["role"] == "train"}
        test_hosts = {r["host_id"] for r in membership if r["role"] == "test"}
        checks.require(not train_hosts & test_hosts and train_hosts | test_hosts == all_hosts,
                       "membership", "training and test hosts overlap or fail to cover input")
        checks.require(len(test_hosts) == round(.3 * len(all_hosts)), "membership", "incorrect original test-host count")
        train = [r for r in records.values() if r["host"] in train_hosts]
        test_ids = {i for i, r in records.items() if r["host"] in test_hosts}
        test_host_counts.append(len(test_hosts))
        test_listing_counts.append(len(test_ids))
        rows = predictions[split]
        ids = [row["id"] for row in rows]
        checks.require(len(ids) == len(set(ids)) and set(ids) == test_ids == set(prior_predictions[split]),
                       "test_rows", "follow-up and prior tests differ from frozen memberships")
        checks.require(set(coefficients[split]) == TERMS, "coefficients", "property-only coefficient terms changed")
        diagnostic = diagnostics[(split,)]
        diagnostic_counts = {
            "train_listings": len(train), "train_hosts": len(train_hosts),
            "test_listings": len(test_ids), "test_hosts": len(test_hosts),
            "nobs": len(train), "coefficient_count": len(TERMS), "warning_count": 0,
        }
        for field, value in diagnostic_counts.items():
            checks.require(integer(diagnostic[field]) == value, "fit_diagnostics", "incorrect reported " + field)
        checks.require(boolean(diagnostic["converged"]) == 1 and boolean(diagnostic["has_na_coefficients"]) == 0 and
                       integer(diagnostic["iterations"]) > 0, "fit_diagnostics", "reported fit did not converge cleanly")
        training_groups = defaultdict(list)
        for row in train:
            training_groups[row["segment"]].append(row)
        prevalence = sum(r["y"] for r in train) / len(train)
        baseline = {group: (sum(r["y"] for r in rs) + 10 * prevalence) / (len(rs) + 10)
                    for group, rs in training_groups.items()}
        current = []
        for row in rows:
            source = records[row["id"]]
            prior = prior_predictions[split][row["id"]]
            checks.require(row["host_id"] == prior["host_id"] == source["host"] and
                           row["segment"] == prior["segment"] == source["segment"] and
                           integer(row["busy"]) == integer(prior["busy"]) == source["y"],
                           "test_rows", "test features, host or outcome differ from original input")
            scored = {**source, **{model: number(row["p_" + model]) for model in MODELS}}
            checks.require(all(0 <= scored[m] <= 1 for m in MODELS), "scores", "score outside probability bounds")
            comparisons = (
                ("retained_full", scored["full"], number(prior["p_logistic"])),
                ("retained_baseline", scored["baseline"], number(prior["p_segment_mean"])),
                ("reconstructed_baseline", scored["baseline"], baseline.get(source["segment"], prevalence)),
                ("reconstructed_property_only", scored["property_only"], property_score(source, coefficients[split])),
            )
            for label, actual, expected in comparisons:
                max_errors[label] = max(max_errors[label], abs(actual - expected))
                checks.close(actual, expected, "scores", label + " score mismatch")
            current.append(scored)
        test_rows_checked += len(current)
        priority_rows = [row for row in current if row["segment"] in PRIORITY]
        for segment in {row["segment"] for row in current}:
            checks.require(len({row["baseline"] for row in current if row["segment"] == segment}) == 1,
                           "within_group_baseline", "stored baseline is not constant within segment and split")
        populations = {"all_eligible": current, "priority_pool": priority_rows, "priority_fixed_quota": priority_rows}
        for scope, scope_rows in populations.items():
            for fraction in FRACTIONS:
                quotas = set()
                for model in MODELS:
                    result = screening(scope_rows, model, fraction, scope == "priority_fixed_quota", checks)
                    screened[(split, scope, fraction, model)] = result
                    quotas.add(result["quota"])
                checks.require(len(quotas) == 1, "quota", "models do not share the same scope quota")
            if scope != "priority_fixed_quota":
                for model in MODELS:
                    discriminated[(split, scope, model)] = discrimination(scope_rows, model)
        for group in PRIORITY:
            group_rows = [r for r in priority_rows if r["segment"] == group]
            zero_target_group_splits += int(sum(r["y"] for r in group_rows) == 0)
            for fraction in FRACTIONS:
                for model in MODELS:
                    result = screening(group_rows, model, fraction, False, checks)
                    group_screened[(split, group, fraction, model)] = result
                    if model == "baseline" and group_rows:
                        checks.close(result["precision"], sum(r["y"] for r in group_rows) / len(group_rows),
                                     "within_group_baseline", "constant group baseline differs from uniform selection expectation")
        for fraction in FRACTIONS:
            for model in MODELS:
                combined = screened[(split, "priority_fixed_quota", fraction, model)]
                parts = [group_screened[(split, group, fraction, model)] for group in PRIORITY]
                checks.close(combined["quota"], sum(p["quota"] for p in parts), "group_aggregation", "fixed quotas do not sum")
                checks.close(combined["expected_target_selected"], math.fsum(p["expected_target_selected"] for p in parts),
                             "group_aggregation", "fixed-group expected target counts do not sum")
        old = prior_metrics[split]
        for model, prefix in (("full", "logistic"), ("baseline", "segment")):
            selected = screened[(split, "all_eligible", .25, model)]
            ranked = discriminated[(split, "all_eligible", model)]
            checks.close(selected["quota"], number(old["quota"]), "prior_replication", "original all-eligible 25% quota changed")
            for field in ("precision", "expected_target_selected", "auc", "brier"):
                old_field = "expected_positive" if field == "expected_target_selected" else field
                result = selected[field] if field in selected else ranked[field]
                checks.close(result, number(old[prefix + "_" + old_field]), "prior_replication", "original all-eligible 25% metric changed")

    screen_pairs = paired_rows(screened)
    group_pairs = paired_rows(group_screened)
    discrimination_pairs = paired_rows(discriminated, False)
    for split in sorted(SPLITS):
        old = prior_metrics[split]
        checks.close(screen_pairs[(split, "all_eligible", .25, "full_vs_baseline")]["precision_difference_pp"],
                     number(old["precision_difference_pp"]), "prior_replication", "original precision difference changed")
        for field in ("auc_difference", "brier_difference"):
            checks.close(discrimination_pairs[(split, "all_eligible", "full_vs_baseline")][field],
                         number(old[field]), "prior_replication", "original discrimination difference changed")

    for name, group_field, values in (("screening", "scope", screened), ("group", "segment", group_screened)):
        check_table(root, TABLES[name], ("split", group_field, "fraction", "model"), SCREEN_FIELDS, values, checks)
        check_table(root, TABLES[name + "_summary"], (group_field, "fraction", "model", "metric"),
                    SUMMARY_FIELDS, summary_rows(values, SCREEN_METRICS), checks)
    pair_fields = (*POPULATION_FIELDS, "quota", "left_model", "right_model", *SCREEN_DELTAS)
    for name, group_field, values in (("screening", "scope", screen_pairs), ("group", "segment", group_pairs)):
        check_table(root, TABLES[name + "_pairs"], ("split", group_field, "fraction", "pair"), pair_fields, values, checks)
        check_table(root, TABLES[name + "_pair_summary"], (group_field, "fraction", "pair", "metric"),
                    PAIRED_SUMMARY_FIELDS, summary_rows(values, SCREEN_DELTAS, True), checks)
    check_table(root, TABLES["discrimination"], ("split", "scope", "model"),
                (*POPULATION_FIELDS, "auc", "brier"), discriminated, checks)
    check_table(root, TABLES["discrimination_summary"], ("scope", "model", "metric"), SUMMARY_FIELDS,
                summary_rows(discriminated, ("auc", "brier")), checks)
    check_table(root, TABLES["discrimination_pairs"], ("split", "scope", "pair"),
                (*POPULATION_FIELDS, "left_model", "right_model", "auc_difference", "brier_difference"),
                discrimination_pairs, checks)
    check_table(root, TABLES["discrimination_pair_summary"], ("scope", "pair", "metric"), PAIRED_SUMMARY_FIELDS,
                summary_rows(discrimination_pairs, ("auc_difference", "brier_difference"), True), checks)
    run_checks = json.loads((root / RUN_CHECKS).read_text(encoding="utf-8"))
    checks.require(run_checks["plan"] == plan, "run_metadata", "R metadata does not match frozen plan")
    checks.require(run_checks["input_fingerprints"] == json.loads((root / FINGERPRINTS).read_text(encoding="utf-8")),
                   "run_metadata", "R metadata provenance differs from frozen manifest")
    checks.require(run_checks["fingerprint_checks_passed"] == 6 and run_checks["rows"] == len(records) and
                   run_checks["hosts"] == len(all_hosts) and run_checks["target_count"] == 981 and
                   run_checks["splits"] == 50 and run_checks["property_only_fits"] == 50 and
                   run_checks["all_property_only_fits_converged"] is True and run_checks["total_fit_warnings"] == 0,
                   "run_metadata", "reported population or fit counts differ")
    checks.require(run_checks["baseline_constant_within_every_segment_and_split"] is True and
                   run_checks["no_new_full_or_baseline_fit"] is True,
                   "run_metadata", "retained-score declarations differ from the agreed design")
    for name, expected_count in run_checks["output_csv_rows"].items():
        relative = "outputs/" + name + ".csv"
        with (root / relative).open(encoding="utf-8-sig", newline="") as handle:
            count = sum(1 for _ in csv.DictReader(handle))
        checks.require(count == expected_count, "run_metadata", "reported CSV row count differs")
    checks.close(run_checks["maximum_baseline_reconstruction_difference"],
                 max(number(row["baseline_reconstruction_max_difference"]) for row in diagnostics.values()),
                 "run_metadata", "baseline diagnostic maximum differs")
    checks.close(run_checks["maximum_full_reconstruction_difference"],
                 max(number(row["full_score_reconstruction_max_difference"]) for row in diagnostics.values()),
                 "run_metadata", "full-model diagnostic maximum differs")
    return {
        "input_listings": len(records), "input_hosts": len(all_hosts), "positive_listings": sum(r["y"] for r in records.values()),
        "original_repeated_host_splits": len(SPLITS), "test_rows_checked": test_rows_checked,
        "test_hosts_per_split": sorted(set(test_host_counts)),
        "test_listing_range": [min(test_listing_counts), max(test_listing_counts)],
        "property_only_coefficient_rows": sum(len(c) for c in coefficients.values()),
        "maximum_score_discrepancies": dict(max_errors),
        "zero_target_single_group_splits": zero_target_group_splits,
        "screening_metric_rows": len(screened), "priority_group_metric_rows": len(group_screened),
        "paired_screening_rows": len(screen_pairs), "paired_priority_group_rows": len(group_pairs),
        "discrimination_metric_rows": len(discriminated), "paired_discrimination_rows": len(discrimination_pairs),
        "aggregate_and_paired_tables_checked": list(TABLES.values()),
        "original_all_eligible_25_percent_comparison_reproduced": True,
        "prior_independent_full_model_scoring_check": {
            "status": prior_verification["status"],
            "prior_test_rows": prior_verification["results"]["test_prediction_rows"],
            "prior_maximum_score_discrepancy": prior_verification["results"]["maximum_logistic_scoring_difference"],
            "source_hashes_match": True,
            "note": "The prior check reconstructed full-model scoring for 55 splits; this follow-up reuses and checks exactly its 50 repeated-split score exports.",
        },
        "fit_diagnostics_boundary": "Reported convergence, warnings and training sample counts match the exports; coefficient estimation was not independently repeated.",
    }


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def self_test():
    assert auc([0, 1], [.5, .5]) == .5
    assert auc([0, 1], [.1, .9]) == 1
    assert auc([0, 1], [.9, .1]) == 0
    assert auc([0, 0], [.1, .9]) is None
    k, w = quota_weights([.9, .8, .8, .8, .1], .25)
    assert k == 2 and w == [1, 1 / 3, 1 / 3, 1 / 3, 0]
    assert quota_weights([], .25) == (0, [])
    assert math.isclose(quantile([0, 10, 20, 30], .05), 1.5)
    assert quantile([], .05) is None
    source = {"area": "Melbourne", "dwelling": "Apartment/unit", "bedrooms": "1", "amenities": 20}
    coefficients = {term: 0.0 for term in TERMS}
    coefficients["amenities_10"] = .5
    assert math.isclose(property_score(source, coefficients), 1 / (1 + math.exp(-1)))
    example = {(1, "all_eligible", .25, "full"): {"precision": 1.0},
               (2, "all_eligible", .25, "full"): {"precision": None}}
    summary = summary_rows(example, ("precision",))[("all_eligible", .25, "full", "precision")]
    assert summary["splits"] == 2 and summary["n_finite"] == 1 and summary["mean"] == 1.0
    print("Arithmetic self-tests passed; no private inputs read.")


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
        "schema_version": "1.0", "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "validator": "scripts/verify_screening_followup.py", "status": "incomplete",
        "scope": [
            "Frozen source-file hashes match the supplied provenance manifest.",
            "All fifty original host memberships are reused with complete and disjoint host partitions.",
            "Each follow-up test set exactly matches the frozen held-out listings and the prior prediction export.",
            "Full-model and baseline scores are unchanged from the prior paired analysis.",
            "The prior independent full-model scoring report is linked to the current frozen inputs and score exports by matching hashes.",
            "Segment baseline scores are reconstructed from training outcomes with fixed smoothing weight ten.",
            "Property-only scores are independently reconstructed from raw property features and exported reduced-model coefficients, retaining amenities and excluding price and one-night acceptance.",
            "Identical quotas across models; score-only boundary ties; all-eligible, pooled-priority and per-group fixed-quota screening.",
            "Independent precision, recall, expected target counts, all three paired model contrasts, and every exported aggregate and paired summary.",
            "AUC and Brier are checked for the all-eligible and priority-pool populations independently of screening quota.",
            "The original all-eligible 25-percent full-versus-baseline metrics are reproduced on each split.",
        ],
        "limits": [
            "Reduced-model coefficients are used to reconstruct scores, not independently re-estimated; model fitting is not verified by a second fitting engine.",
            "The original raw dated-review construction and sample eligibility pipeline are not rebuilt in this pass.",
            "Original random sampling is not replayed; exact saved memberships and frozen source-file hashes are checked.",
            "Priority-group and full-model choices followed earlier outcome exploration. This check does not make those choices independent or untouched.",
            "Fifty overlapping tests describe split sensitivity, not independent studies; P05/P95 are not confidence intervals.",
            "Removing price and one-night acceptance assesses their joint predictive contribution, not separate or causal policy effects.",
            "The reduced model retains amenities, which must be known when screening a candidate.",
            "AUC/Brier are not computed separately for each single priority group or conditioned on a shortlist quota.",
            "Historical review attainment is not future occupancy, revenue, profit or a verified lease decision.",
        ],
        "numeric_tolerance": {"absolute": ABS_TOL, "relative": REL_TOL, "better_tie_epsilon": TIE_TOL},
        "file_sha256": {},
    }
    expected_files = [PLAN, FINGERPRINTS, INPUT, MEMBERSHIP, OLD_PREDICTIONS, OLD_METRICS, COEFFICIENTS, PREDICTIONS,
                      DIAGNOSTICS, RUN_CHECKS, PRIOR_VERIFICATION,
                      *TABLES.values()]
    missing = [name for name in expected_files if not (root / name).is_file()]
    try:
        checks.require(not missing, "files", "required input or export files are not ready")
        fingerprints = json.loads((root / FINGERPRINTS).read_text(encoding="utf-8"))
        for relative, metadata in fingerprints.items():
            path = root / relative
            checks.require(path.is_file() and sha256(path) == metadata["sha256"], "source_hash", "frozen source hash mismatch")
        monitored = {root / name for name in expected_files} | {root / name for name in fingerprints}
        monitored |= set((root / "outputs").glob("*.csv"))
        monitored |= {Path(__file__).resolve()}
        hashes_before = {str(p.relative_to(root)): sha256(p) for p in sorted(monitored)}
        report["file_sha256"] = hashes_before
        report["results"] = verify(root, checks)
        hashes_after = {str(p.relative_to(root)): sha256(p) for p in sorted(monitored)}
        checks.require(hashes_before == hashes_after, "file_stability", "an input, export or checker changed during verification")
        report["status"] = "passed"
    except VerificationError as exc:
        report["status"] = "failed"
        report["failure"] = str(exc)
    except (OSError, KeyError, TypeError, ValueError, IndexError, ZeroDivisionError) as exc:
        report["status"] = "failed"
        report["failure"] = "Unexpected schema or file-processing failure (" + type(exc).__name__ + ")."
    if missing:
        report["missing_required_files"] = missing
    report["checks_by_category"] = dict(sorted(checks.counts.items()))
    destination = root / "outputs/verification.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2) + "\n", encoding="utf-8")
    print("Screening verification " + report["status"] + "; report: outputs/verification.json")
    if "failure" in report:
        print(report["failure"], file=sys.stderr)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
