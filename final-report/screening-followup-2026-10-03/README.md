# Screening follow-up: candidate groups, model inputs and shortlist size

Completed 3 October 2026. This analysis answers three questions: does the model help after restricting the search to three priority groups; how much does it rely on price and minimum-stay information; and do its gains persist at different screening quotas?

We reused the exact 50 host splits and full-model/baseline predictions from the preceding paired analysis. We fitted only one additional model per split. The sample remains 3,873 eligible listings from 1,726 hosts, with a target of at least 30 dated reviews in the preceding 365 days. All listings belonging to one host remain together within each training/test allocation.

The priority groups are Melbourne two-bedroom apartments, Melbourne three-bedroom apartments, and Yarra Ranges three-bedroom houses or townhouses. These groups and the full-model specification followed earlier outcome exploration. This is a retrospective sensitivity analysis, not an untouched test of the complete group-selection process or a forecast of profit.

## 1. Does ranking help within the priority groups?

At the main 25% quota, the following are equal-weight means over 50 splits:

| Evaluation and allocation rule | Group-rate baseline | Reduced property model | Full model |
|---|---:|---:|---:|
| All eligible test listings | 31.96% | 34.26% | 43.42% |
| Three priority groups combined into one pool | 32.37% | 36.52% | 48.91% |
| Separate fixed quota inside each priority group | 32.43% | 38.61% | 49.62% |

With fixed quotas inside each priority group, the full model improved precision by **17.19 percentage points** on average and performed better in **46 of 50 splits**, with four worse and no ties. The paired difference's 5th to 95th percentiles were **-0.66 to +31.76 points**; its full observed range was -2.78 to +38.40 points. These are split-sensitivity ranges, **not confidence intervals**. The improvement cannot come from moving selection places between groups under this allocation rule.

The pooled-priority comparison allows such reallocation. Its average gain was 16.54 points, with 47 better and three worse splits. Separate rounding gives the pooled and fixed-group rules different total quotas; they should not be described as equal-workload comparisons with each other. Models have equal quotas within each particular comparison.

The baseline is the training target rate for the same area, dwelling type and bedroom group, smoothed towards overall training prevalence with fixed weight 10. Within a single group and split, it assigns every listing the same score. Its expected result at a fixed group quota therefore equals uniform selection within that group.

## 2. How much do price and minimum-stay information contribute?

The full logistic model uses area, dwelling type, bedrooms, price relative to comparable listings, one-night acceptance and amenity count. The reduced model is refitted as:

```text
busy ~ area + dwelling + bedrooms + amenities_10
```

Both models use all eligible training hosts. The priority restriction is applied to the test candidate pool after scoring; no model is trained only on the three groups. Removing price and one-night acceptance measures their **joint predictive contribution**, not either input's separate contribution or a causal effect of changing a setting.

At fixed 25% quotas inside the priority groups, the full model exceeded the reduced model by 11.00 points on average, with 42 better and eight worse splits. The reduced model exceeded the baseline by 6.19 points, also with 42 better and eight worse splits. Its benefit was not uniform: for Melbourne three-bedroom apartments, reduced-model precision averaged 33.87%, below the baseline's 35.92%; it beat the baseline in only 18 of 50 splits.

Within any one property group, area, dwelling type and bedrooms are constant. The reduced model can therefore rank listings inside that group **only through amenity count**. Its use assumes amenities are already known at screening time. All models retain the original established listings with usable recorded prices: removing price as an input does not validate the reduced model for excluded unpriced listings or new rental candidates.

## 3. Do gains persist at other shortlist sizes?

For the full model with separate quotas inside each priority group:

| Nominal share selected | Precision | Target-reaching listings captured: recall | Mean gain over baseline | Better / tied / worse splits |
|---|---:|---:|---:|---:|
| 10% | 54.47% | 17.15% | +22.04 points | 46 / 0 / 4 |
| 25% | 49.62% | 38.29% | +17.19 points | 46 / 0 / 4 |
| 50% | 43.10% | 66.68% | +10.67 points | 49 / 0 / 1 |

A smaller shortlist has higher precision but captures fewer target-reaching listings. The 10% result is also more variable; Yarra Ranges contributes only two to four selections per test split at that quota. These checks do not establish an optimal business quota.

All quotas are rounded up. Boundary ties share the remaining quota uniformly without using outcomes, so selected target counts are expectations and can be fractional. The saved scores are reused for all three quotas. AUC and Brier score are reported separately for the all-eligible and priority-pool populations; they do not change when only the screening quota changes. They are not separately reported for individual priority groups.

## Relationship to earlier results

The original five-fold pooled result remains **423/969 = 43.65% versus 28.07%**, a 15.58-point difference. It uses one held-out prediction per analysis listing and one pooled quota. The repeated-split all-eligible result is **43.42% versus 31.96%**, an 11.46-point average difference. The new fixed-priority-group result is **49.62% versus 32.43%**, a 17.19-point difference. These have different populations or allocation rules and must be labelled separately.

This follow-up preserves every stored full-model and baseline test score. It does not refit those models, change the outcome, tune a quota, or select a new algorithm. The 50 tests overlap and are not 50 independent studies. Current property settings may differ from conditions during the historical review window. Reviews do not measure bookings, occupancy, revenue, profit or the effect of a management intervention. See [METHODS_FOR_REPORT.md](METHODS_FOR_REPORT.md) for report-ready methods.

## Files

| Location | Contents |
|---|---|
| [config/followup_plan.json](config/followup_plan.json) | Frozen questions, models, candidate scopes, quotas and limitations |
| [reference/input_fingerprints.json](reference/input_fingerprints.json) | SHA-256 fingerprints and source filenames for the required frozen inputs |
| `reference/prior_*` | Previous model helpers, coefficient and metric aggregates, and the prior verification record |
| [outputs/screening_summary.csv](outputs/screening_summary.csv) and [paired_screening_summary.csv](outputs/paired_screening_summary.csv) | Main screening results and within-split paired differences |
| `outputs/split_screening_metrics.csv`, `paired_screening_differences.csv` | Every scope, quota, model and contrast for all 50 splits |
| `outputs/priority_group_*`, `paired_priority_group_*` | Each priority group's results and model comparisons |
| `outputs/discrimination_*`, `paired_discrimination_*` | AUC, Brier and paired differences, independent of quota |
| `outputs/property_only_coefficients.csv`, `property_only_fit_diagnostics.csv` | Fifty reduced fits, coefficient estimates, convergence and sample checks |
| [outputs/run_checks.json](outputs/run_checks.json), [outputs/verification.json](outputs/verification.json) | Provenance, score-preservation checks and independent verification |
| `figures/` | PNG and SVG comparisons generated from aggregate tables |
| [deliverables/TheNextChapter_Screening_Findings.docx](deliverables/TheNextChapter_Screening_Findings.docx) | English findings brief |

Each summary gives equal weight to each split. Paired differences are computed within a split before summarising. Screening precision/recall differences are percentage points; AUC, Brier and expected-count differences retain their original units. Finite-value counts are explicit. Better/tied/worse counts use tolerance 1e-12. Do not pool overlapping test rows or take the difference between separately computed marginal percentiles.

## Reproduce

The complete rerun requires these **three authorised private files**, restored byte-for-byte under the following names:

| Required file | Source in the preceding paired-analysis package |
|---|---|
| `private-inputs/analysis_input.csv` | `private-inputs/analysis_input.csv` |
| `private-inputs/prior_test_predictions_PRIVATE.csv` | `working/test_predictions_PRIVATE.csv` |
| `private-inputs/prior_split_membership_PRIVATE.csv` | `working/split_membership_PRIVATE.csv` |

Use the complete frozen source exports, including their original design rows. Their fingerprints are in `reference/input_fingerprints.json`; a different snapshot, reordered export or truncated file must not be silently substituted. The compact input, stored predictions and memberships cannot be reconstructed from the public aggregate tables alone. Raw review-window construction and eligibility processing belong to the earlier source pipeline, not this package.

Requirements for `run.sh`:

- R with `data.table`, `jsonlite` and `ggplot2`. The model and metric helpers use base R; no additional model-fitting package is required.
- An available `shasum` or `sha256sum` command for frozen-input fingerprint checks.
- Python 3; the independent verifier uses only the standard library.
- R graphics support for PNG and SVG output. Figures use Arial; font availability or substitution can affect their appearance.

From the package root:

```sh
bash run.sh
```

This fits the 50 reduced models, writes aggregates and private working predictions, runs independent verification, then regenerates figures. `REPORT_PYTHON_BIN` can select the Python executable. The optional brief builder is not part of `run.sh`; it requires `python-docx` and `lxml`, plus the completed aggregate outputs and figures:

```sh
python3 scripts/build_report_brief.py
```

Figures can be regenerated from the public aggregates without private inputs using `Rscript scripts/plot_followup.R`. The saved verification report can be inspected publicly, but reproducing its data-level checks requires the private files and regenerated working predictions. Do not run the data-level verifier against an aggregate-only copy expecting it to reproduce the recorded pass.

## Verification and privacy

All 50 reduced fits converged without warnings. The independent standard-library implementation checked 59,220 held-out predictions, exact frozen host allocations, unchanged full/baseline scores, training-only baseline reconstruction, reduced-model scores reconstructed from original features and exported coefficients, equal quotas, tie weights, and all 12 metric/difference/summary tables. The maximum reconstruction discrepancies were approximately 5.27 x 10^-16 for the baseline and 2.39 x 10^-15 for the reduced model. The original all-eligible 25% comparison was reproduced.

This is independent score and arithmetic verification, **not coefficient refitting by a second engine**. It does not rebuild raw dated reviews or independently replay the original random sampling. It does not remove earlier outcome-informed selection, validate future performance or turn percentile ranges into confidence intervals.

Only code, configuration, aggregate results, figures and the findings brief belong in a public release. `private-inputs/`, `working/`, `logs/`, caches and row-level identifiers remain local and are excluded by `.gitignore`. In particular, `working/test_predictions_PRIVATE.csv` contains listing/host identifiers and must not be published. Saved hashes identify the checked files without disclosing their row-level contents.
