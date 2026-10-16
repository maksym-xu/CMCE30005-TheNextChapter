# Final report package (revised 16 October 2026)

[Report PDF](Final_Report.pdf) · [Report Word](Final_Report.docx) · [Report text](Final_Report.md)

Prepared by Eric Huang and Maksym Xu. `Final_Report.md` is the source text; the Word file is built from it, the PDF is exported from the Word file, and the root `README.md` carries the same report.

## Files

| Path | Purpose |
|---|---|
| `Final_Report.md`, `.docx`, `.pdf` | The report in three formats |
| `figures/figure_1_review_distribution` … `figure_4_two_years` (`.png`, `.svg`) | The four report figures |
| `build_figures.py` | Builds the four figures from committed aggregate tables (matplotlib) |
| `scripts/revision_evidence.R` | Evidence added on 16 October: data exploration, estimated nights and revenue, model assumption checks, top-three stability and the all-input odds ratios |
| `outputs/revision/` | Aggregate outputs of `revision_evidence.R` (no listing or host identifiers) |
| `scripts/build_report_docx.py`, `reference/report_template.docx` | Builds the Word file from the Markdown with the report's template |
| `scripts/sync_readme.py` | Copies the report into the root `README.md` |
| `scripts/check_report_package.py` | Checks the four versions against each other, the word limit, PDF font embedding, the unchanged AI acknowledgement and key numbers against the outputs |
| `scripts/summarize_report_additions.py`, `scripts/test_report_additions.py`, `outputs/*.csv`, `outputs/report_additions.json` | Priority-group listing settings and saved coefficient summaries (14 October); the test now also runs the package check |
| `package_checks.json` | Result of the latest package check |

## Rebuild

From the repository root, with the private analysis input copied to `final-report/report-2026-10-04/private-inputs/analysis_input.csv` and the processed data in `data/processed/`:

```sh
Rscript final-report/report-2026-10-04/scripts/revision_evidence.R
python final-report/report-2026-10-04/build_figures.py
python final-report/report-2026-10-04/scripts/build_report_docx.py
# export Final_Report.pdf from Final_Report.docx in Microsoft Word (embeds fonts)
python final-report/report-2026-10-04/scripts/sync_readme.py
python final-report/report-2026-10-04/scripts/check_report_package.py
```

## Sources of the figures and tables

| Report item | Source |
|---|---|
| Figure 1, Table 3 | `outputs/revision/review_histogram_bins.csv`, `review_distribution.csv`, `target_profile.csv` |
| Figure 2 | `../../final-presentation/analysis/reference/segment_ladder.csv` (group rates and 1,000-draw host-resampled ranges) |
| Table 4, Recommendation 3 | `outputs/revision/group_estimated_revenue.csv` and `outputs/priority_group_descriptives.csv` |
| Figure 3, Table 6 | `../screening-followup-2026-10-03/outputs/screening_summary.csv` (scope `priority_fixed_quota`) |
| Table 5 | `../../final-presentation/analysis/outputs/test_confusion.csv` (pooled five-fold scores) |
| Section 5.3 scenario chances | `../../final-presentation/analysis/reference/final_logit_scenarios.csv` |
| Figure 4, Section 5.5 | `../../final-presentation/analysis/reference/temporal-validation/validation_metrics.json` |
| Section 4 assumptions | `outputs/revision/model_gvif.csv`, `model_se_ratio.csv`, `revision_summary.json` |
| Section 5.2 stability | `outputs/revision/top3_resample_shares.csv` |
| Table A1 | `outputs/revision/all_term_odds_ratios.csv` (from `../screening-followup-2026-10-03/reference/prior_full_coefficients.csv`) |

## Evaluation designs

The report's headline (Figure 3) picks 25% of test homes separately in each priority group. Other designs give different numbers because they test different homes or allocate places differently; they should not be compared as if they were the same test.

| Design (25% of homes picked) | Model | Group rates | Gain (points) | Model better |
|---|---:|---:|---:|---:|
| Five host-grouped folds, all 3,873 homes scored once, one pooled list | 43.65% | 28.07% | +15.58 | — |
| 50 host splits, all 14 groups, about 1,184 test homes per split | 43.42% | 31.96% | +11.46 | 48 of 50 |
| 50 host splits, three priority groups pooled into one list | 48.91% | 32.37% | +16.54 | 47 of 50 |
| 50 host splits, separate quota in each priority group (report headline) | 49.62% | 32.43% | +17.19 | 46 of 50 |

In the pooled five-fold design, group-rate scores from five different training sets share one list, which tends to favour the model. Across the 50 splits on all groups, mean AUC is 0.708 against 0.603 (better in 50 of 50) and mean Brier score 0.1715 against 0.1841 (better in 44). Within the separate group quotas, gains average +16.4 points in City two-bedroom apartments, +17.6 in City three-bedroom apartments and +25.0 in Yarra Ranges houses; Yarra Ranges contributes only 5–9 picked homes per split.

## Changes in the 16 October revision

- Added a data-exploration subsection (Figure 1, Table 3) and a variable table (Table 2).
- Translated the 30-review target into estimated nights and revenue (Section 2, Table 4) using Inside Airbnb's published assumptions.
- Added a confusion matrix (Table 5), model assumption checks (Section 4), scenario chances, a key-findings list linked to figures, and all eleven odds ratios (Table A1).
- Replaced Figure 1 and Appendix B with one chart of all 14 groups (Figure 2); renamed and relabelled the screening and two-year figures.
- Corrected wording: the price-exclusion comparison now uses the residential scope; the two-year check is described as surviving homes with a host-weighted gap; group stability is reported from 1,000 host redraws.
- Defined "busy" (30+ reviews in a year) and used it throughout; explained odds, AUC, precision and recall in plain words.
- Corrected two claims a review flagged: City two-bedroom apartments rank fifth of 14 on estimated revenue (not first), and busy homes charge slightly less than similar homes.
- Described the five-fold design behind Table 5 and stated the model's plain accuracy (71.5%).
- Added external sources for the regulatory checks; dated the R reference; cited this branch.
- The AI acknowledgement is unchanged.

The 14 October version of this folder is in commit `3e6e043`.
