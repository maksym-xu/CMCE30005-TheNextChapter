#!/usr/bin/env python3
"""Post-exploration subgroup checks of frozen OOF scores. No fitting or tuning.

Run from anywhere with Python 3. Uses only the standard library. Probabilities
are fractions; *_pp fields are percentage points. Row-level data stays local.
"""
import csv
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUPS = ["Melbourne 2BR Apartment/unit", "Melbourne 3BR Apartment/unit",
          "Yarra Ranges 3BR House/townhouse"]
REPLICATES = 1000
SEED = 30005

def read_csv(path):
    with (ROOT / path).open(newline="") as handle:
        return list(csv.DictReader(handle))

def write_csv(name, rows):
    with (ROOT / "outputs" / name).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def quantile(values, probability):
    ordered = sorted(values)
    index = (len(ordered) - 1) * probability
    lower = math.floor(index)
    upper = math.ceil(index)
    return ordered[lower] + (index - lower) * (ordered[upper] - ordered[lower])

source = ROOT / "working/oof_predictions_PRIVATE.csv"
rows = read_csv("working/oof_predictions_PRIVATE.csv")
assert len(rows) == 3873 and len({r["id"] for r in rows}) == 3873
for r in rows:
    r["busy"] = int(r["busy"])
    r["p"] = float(r["p"])
    r["p_segment_mean"] = float(r["p_segment_mean"])
subset = [r for r in rows if r["segment"] in GROUPS]
assert len(subset) == 1631 and sum(r["busy"] for r in subset) == 544
assert len({r["host_id"] for r in subset}) == 625

def selection(data, score):
    n = len(data)
    quota = math.ceil(n / 4)
    boundary = sorted((r[score] for r in data), reverse=True)[quota - 1]
    above = [r for r in data if r[score] > boundary]
    tied = [r for r in data if r[score] == boundary]
    tie_weight = (quota - len(above)) / len(tied)
    expected_positive = sum(r["busy"] for r in above) + tie_weight * sum(r["busy"] for r in tied)
    return {"quota": quota, "expected_positive": expected_positive,
            "precision": expected_positive / quota, "boundary": boundary,
            "boundary_tied_listings": len(tied), "boundary_weight": tie_weight,
            "fractional_allocation": 0 < tie_weight < 1}

def evaluate(data):
    pooled_model = selection(data, "p")
    pooled_segment = selection(data, "p_segment_mean")
    by_group = []
    for group in GROUPS:
        part = [r for r in data if r["segment"] == group]
        assert part, "A resampled subgroup is absent"
        model = selection(part, "p")
        baseline = selection(part, "p_segment_mean")
        assert model["quota"] == baseline["quota"]
        positives = sum(r["busy"] for r in part)
        random_expected = model["quota"] * positives / len(part)
        by_group.append({"segment": group, "listings": len(part),
            "hosts": len({r["host_id"] for r in part}), "positive_listings": positives,
            "observed_share": positives / len(part), "quota": model["quota"],
            "model_expected_positive": model["expected_positive"], "model_precision": model["precision"],
            "segment_mean_expected_positive": baseline["expected_positive"],
            "segment_mean_precision": baseline["precision"],
            "random_expected_positive": random_expected,
            "random_expected_precision": positives / len(part),
            "gain_model_minus_segment_mean_pp": 100 * (model["precision"] - baseline["precision"]),
            "gain_model_minus_random_pp": 100 * (model["precision"] - positives / len(part)),
            "model_boundary_tied_listings": model["boundary_tied_listings"],
            "model_boundary_weight": model["boundary_weight"],
            "segment_mean_boundary_tied_listings": baseline["boundary_tied_listings"],
            "segment_mean_boundary_weight": baseline["boundary_weight"]})
    quota = sum(r["quota"] for r in by_group)
    model_tp = sum(r["model_expected_positive"] for r in by_group)
    baseline_tp = sum(r["segment_mean_expected_positive"] for r in by_group)
    random_tp = sum(r["random_expected_positive"] for r in by_group)
    overall = [
        {"design": "pooled_three_groups", "listings": len(data), "hosts": len({r["host_id"] for r in data}),
         "quota": pooled_model["quota"], "model_expected_positive": pooled_model["expected_positive"],
         "model_precision": pooled_model["precision"],
         "segment_mean_expected_positive": pooled_segment["expected_positive"],
         "segment_mean_precision": pooled_segment["precision"],
         "random_expected_positive": pooled_model["quota"] * sum(r["busy"] for r in data) / len(data),
         "random_expected_precision": sum(r["busy"] for r in data) / len(data),
         "gain_model_minus_segment_mean_pp": 100 * (pooled_model["precision"] - pooled_segment["precision"]),
         "gain_model_minus_random_pp": 100 * (pooled_model["precision"] - sum(r["busy"] for r in data) / len(data))},
        {"design": "fixed_quota_within_each_group", "listings": len(data), "hosts": len({r["host_id"] for r in data}),
         "quota": quota, "model_expected_positive": model_tp, "model_precision": model_tp / quota,
         "segment_mean_expected_positive": baseline_tp, "segment_mean_precision": baseline_tp / quota,
         "random_expected_positive": random_tp, "random_expected_precision": random_tp / quota,
         "gain_model_minus_segment_mean_pp": 100 * (model_tp - baseline_tp) / quota,
         "gain_model_minus_random_pp": 100 * (model_tp - random_tp) / quota},
    ]
    return overall, by_group

overall, by_group = evaluate(subset)
assert overall[0]["quota"] == 408 and overall[0]["model_expected_positive"] == 201
assert overall[1]["quota"] == 409 and overall[1]["model_expected_positive"] == 202
assert [r["quota"] for r in by_group] == [309, 77, 23]

# Diagnose why the stored OOF segment baseline is below random within groups.
# It is constant within a segment AND fold, but changes across folds. This creates
# fold-level ranking, not property-specific discrimination inside a segment.
diagnostic = []
cell_results = []
for group in GROUPS:
    for fold in sorted({r["fold"] for r in subset}):
        part = [r for r in subset if r["segment"] == group and r["fold"] == fold]
        values = {r["p_segment_mean"] for r in part}
        assert len(values) == 1
        diagnostic.append({"segment": group, "held_out_fold": fold, "listings": len(part),
            "positive_listings": sum(r["busy"] for r in part),
            "observed_held_out_share": sum(r["busy"] for r in part) / len(part),
            "training_segment_mean_score": next(iter(values))})
        model = selection(part, "p")
        baseline = selection(part, "p_segment_mean")
        assert baseline["boundary_tied_listings"] == len(part)
        assert model["quota"] == baseline["quota"]
        cell_results.append({"segment": group, "held_out_fold": fold, "listings": len(part),
            "quota": model["quota"], "model_expected_positive": model["expected_positive"],
            "baseline_expected_positive": baseline["expected_positive"],
            "model_precision": model["precision"], "baseline_precision": baseline["precision"]})

cell_groups = []
for group in GROUPS:
    cells = [r for r in cell_results if r["segment"] == group]
    quota = sum(r["quota"] for r in cells)
    model_tp = sum(r["model_expected_positive"] for r in cells)
    baseline_tp = sum(r["baseline_expected_positive"] for r in cells)
    cell_groups.append({"segment": group, "listings": sum(r["listings"] for r in cells),
        "quota": quota, "model_expected_positive": model_tp,
        "baseline_expected_positive": baseline_tp, "model_precision": model_tp / quota,
        "baseline_precision": baseline_tp / quota,
        "gain_model_minus_baseline_pp": 100 * (model_tp - baseline_tp) / quota})
cell_quota = sum(r["quota"] for r in cell_results)
cell_model_tp = sum(r["model_expected_positive"] for r in cell_results)
cell_baseline_tp = sum(r["baseline_expected_positive"] for r in cell_results)
cell_overall = {"quota": cell_quota, "model_expected_positive": cell_model_tp,
    "baseline_expected_positive": cell_baseline_tp, "model_precision": cell_model_tp / cell_quota,
    "baseline_precision": cell_baseline_tp / cell_quota,
    "gain_model_minus_baseline_pp": 100 * (cell_model_tp - cell_baseline_tp) / cell_quota}
assert cell_quota == 416 and cell_model_tp == 222

# A small, fixed paired host bootstrap: scores are held fixed; ranking boundaries
# and ceil(n/4) quotas are recomputed for each resampled population. Hosts present
# in multiple groups are drawn once and bring all their subgroup listings along.
host_rows = defaultdict(list)
for r in subset:
    host_rows[r["host_id"]].append(r)
hosts = sorted(host_rows)
rng = random.Random(SEED)
bootstrap = defaultdict(list)
for _ in range(REPLICATES):
    draw = [r for h in rng.choices(hosts, k=len(hosts)) for r in host_rows[h]]
    sampled_overall, sampled_groups = evaluate(draw)
    for r in sampled_overall:
        for metric in ["model_precision", "segment_mean_precision", "random_expected_precision",
                       "gain_model_minus_segment_mean_pp", "gain_model_minus_random_pp"]:
            bootstrap[(r["design"], metric)].append(r[metric])
    for r in sampled_groups:
        for metric in ["model_precision", "gain_model_minus_random_pp"]:
            bootstrap[(r["segment"], metric)].append(r[metric])
intervals = [{"scope": scope, "metric": metric, "ci95_lower": quantile(values, .025),
              "ci95_upper": quantile(values, .975), "host_replicates": REPLICATES}
             for (scope, metric), values in bootstrap.items()]

association_path = ROOT / "outputs/association_stability.json"
assert association_path.is_file()
association = json.loads(association_path.read_text())
assert all(x["training_folds_with_same_direction"] == 5 for x in association["findings"].values())

payload = {
    "schema_version": "1.0", "units": "Shares are fractions in [0,1]; gains with _pp are percentage points.",
    "source": {"path": "working/oof_predictions_PRIVATE.csv", "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
               "main_analysis_unchanged": True, "retraining": False, "tuning": False},
    "scope": {"segments": GROUPS, "listings": 1631, "distinct_hosts": 625,
              "positive_listings": 544, "observed_share": 544/1631, "outcome": "30+ reviews in the preceding 365 days"},
    "quota_rule": "ceil(n/4); scores above the cutoff are selected; the remaining quota is shared equally across boundary ties, without using outcomes",
    "comparisons": overall, "by_group": by_group,
    "quota_difference_note": "Pooled top quarter has 408 places. Fixing a separate quarter in each group has 309+77+23=409 places because of ceiling rounding. Both methods have exactly the same quota within each design.",
    "interpretation": {
        "pooled_three_groups": "Scores can gain by allocating different numbers across the three groups, as well as by ranking inside them; not pure within-group evidence.",
        "fixed_quota_within_each_group": "Both rules select the same number in each group; the pooled improvement cannot come from reallocating places between groups.",
        "frozen_baseline_caution": "The stored segment-average score varies across held-out folds but is constant within each group/fold. High training rates often correspond here to lower held-out rates. Its 19.9% within-group result reflects an unfavorable fold-ranking artifact and is not a sensible estimate of random screening within a group. Do not present the full 29.5-point gap as a dependable operational gain.",
        "implication_for_primary_comparison": "The full-sample 43.7% versus 28.1% remains the verified frozen OOF result for all 3,873 eligible listings. It is not a pure within-shortlist gain. Pooled OOF scores combine different fitted folds; fold-specific score levels and between-group allocation may affect the comparison. This limitation is not evidence that held-out labels or hosts leaked into training.",
        "neutral_reference": "Random selection within each group at the same fixed quotas has an exact descriptive expected hit count of quota * observed group rate. It uses observed labels only to evaluate that no-ranking reference; it is not an independently fitted predictive model.",
        "recommended_claim": "With the same screening quota in each recommended group, the frozen model identified 202 high-review listings among 409 selections (49.4%), versus about 136 expected under random selection within those groups (33.4%). This is an exploratory retrospective comparison."},
    "group_by_fold_sensitivity": {
        "reason": "Targeted check prompted by fold-level score variation. It prevents reallocating places across either groups or held-out folds.",
        "rule": "For each of the 15 group-by-held-out-fold cells, select ceil(cell_n/4) with the same tie-sharing rule, then combine results. The segment-average score is constant within every cell, so its expected selection equals uniform random sampling inside that cell.",
        "overall": cell_overall, "by_group": cell_groups,
        "extra_places_vs_fixed_group_design": cell_quota - overall[1]["quota"],
        "extra_places_vs_pooled_design": cell_quota - overall[0]["quota"],
        "uncertainty": "No additional bootstrap run for this sensitivity; point estimates only.",
        "limits": "Exploratory sensitivity using existing OOF scores; changing the allocation rule and rounding gives 416 places instead of 409 or 408. It is not a new external test, a tuned replacement rule or a causal business effect."},
    "host_bootstrap": {"replicates": REPLICATES, "seed": SEED, "unit": "Distinct hosts, with replacement; all their listings in these three groups are carried together",
        "fixed": "OOF predictions and the chosen three groups", "recomputed": "Score cutoff, boundary tie weights, per-group quota and observed reference share in each replicate",
        "intervals": intervals,
        "limits": "Conditional descriptive intervals. They omit model refitting, past model selection and the data-driven choice of these three groups. They are not external validation or prospective uncertainty."},
    "association_stability": {"present": True, "path": "outputs/association_stability.json",
         "sha256": hashlib.sha256(association_path.read_bytes()).hexdigest(), "both_selected_directions_hold_in_five_training_folds": True},
    "limitations": ["These three groups were chosen after examining the data. This is a post-exploration subgroup analysis, not a prespecified untouched test.",
        "The same historical snapshot and exploratory host folds underlie the original and subgroup results.",
        "Reviews are not occupancy, booking revenue or profit; the outcome may favor short-stay models.",
        "Current price and stay rules may differ from those used during the preceding review year.",
        "No future-period individual model validation, causal effect or guaranteed within-group business return is established."]
}
write_csv("shortlisted_group_validation.csv", overall)
write_csv("shortlisted_group_validation_by_group.csv", by_group)
write_csv("shortlisted_group_validation_fold_diagnostic.csv", diagnostic)
write_csv("shortlisted_group_validation_group_fold_cells.csv", cell_results)
write_csv("shortlisted_group_validation_group_fold_summary.csv", cell_groups)
write_csv("shortlisted_group_validation_intervals.csv", intervals)
(ROOT / "outputs/shortlisted_group_validation.json").write_text(json.dumps(payload, indent=2) + "\n")
print(json.dumps({"scope": payload["scope"], "comparisons": overall, "by_group": by_group}, indent=2))
print("Completed 1,000 fixed-prediction host resamples. No model was refitted; main outputs unchanged.")
