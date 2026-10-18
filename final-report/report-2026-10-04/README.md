# Final report package (revised 19 October 2026)

[Report PDF](Final_Report.pdf) · [Report Word](Final_Report.docx) · [Report text](Final_Report.md)

Prepared by Eric Huang and Maksym Xu. `Final_Report.md` is the source text; the Word file is built from it, the PDF is exported from the Word file, and the root `README.md` carries the same report.

## Files

| Path | Purpose |
|---|---|
| `Final_Report.md`, `.docx`, `.pdf` | The report in three formats |
| `figures/figure_1_review_distribution` … `figure_5_weekly_reach` (`.png`, `.svg`) | The five report figures |
| `build_figures.py` | Builds the five figures from committed aggregate tables (matplotlib) |
| `scripts/revision_evidence.R` | Evidence added on 16–17 October: data exploration, estimated nights and revenue (all homes and homes below target, with each group's rank on both measures), model assumption checks, top-three stability and the all-input odds ratios |
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
| Table 4, Recommendation 3, Section 5.2 rankings, worked example | `outputs/revision/group_estimated_revenue.csv` (`rank_median_revenue`, `median_est_revenue_below_target_aud`, `median_weekly_aud`, `median_weekly_below_target_aud`) and `outputs/priority_group_descriptives.csv`; the worked example's rents and costs are illustrative, not data |
| Figure 3, Table 6 | `../screening-followup-2026-10-03/outputs/screening_summary.csv` (scope `priority_fixed_quota`) |
| Table 5 | `../../final-presentation/analysis/outputs/test_confusion.csv` (pooled five-fold scores) |
| Section 5.3 scenario chances | `../../final-presentation/analysis/reference/final_logit_scenarios.csv` |
| Figure 5 | `outputs/revision/weekly_revenue_reach.csv` (share of each priority group's homes whose estimated weekly revenue reached each weekly cost, AUD 0–2,000 in steps of 10) |
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

## Changes on 19 October

- Integrated this revision on top of `ad63ad8`, preserving its weekly-cost coverage curve and all published model results. The curve's axis explicitly labels revenue as estimated.
- Methods keeps the plain-language assumptions; the diagnostic numbers and host-weighted comparison are in Appendix A. Section 5.3 distinguishes the 50 priority-group tests from the pooled five-fold test.
- The next steps specify rent and cost quotes, client paid nights and net cash flow, and a later-snapshot test of the unchanged model and selection rule.
- README opens with the project summary, report links and full report; repository instructions and historical contributions remain after it. Current-report contributions name Eric Huang and Maksym Xu.
- Follow-up the same day: Section 2 states what changed since the interim report (an explainable logistic regression in place of the random forest, plus tests within the leading groups); Recommendation 3 again names the owners' corporation check on stays under 28 days; the sentence on price and minimum stay now follows the result it explains.
- Before the follow-up: Microsoft Word count 2,954; ten pages; exported from Word for Windows as PDF/A with all fonts embedded. The package check, six existing unit tests and three new navigation/figure tests passed. All 603 weekly-cost coverage points were independently recalculated from the original CSVs; the largest rounding difference was below 1e-15. No model was refitted in this revision.
- After the follow-up: Microsoft Word count 2,984; ten pages; saved as PDF from Word for Mac with all fonts embedded.

## Changes on 18 October (team review)

- The worked example now ends in rent negotiation and a cash-flow plan for the home itself; a group median is not a forecast for one home, and the one-year buffer is a planning assumption. Table 7 (rent negotiation in weeks 2–3, the cash-flow plan in week 4), Recommendation 3 and the Section 5.2 rule now use the same logic.
- Section 2 states that 30 reviews equal about 180 nights only with three-night stays (Inside Airbnb uses the minimum stay when it is longer).
- Ten candidates are a starting pool: listed homes are ranked within their group and inspected as time and budget allow, and hits can differ widely from the test averages.
- Corrected two descriptions: the 8.7-point gap counts each host once within each set of groups, and Table A1's odds ratios come from the average coefficient over the 50 fits. The 42% and 18% chances are labelled as coming from the model fitted to all homes.
- Table 4 is lighter: units moved to the title, nightly price moved to the text, shorter headers. One source note under Figure 1 covers all figures and tables.
- After a further marking round: Section 6 gains Figure 5 (share of each priority group's homes whose estimated weekly revenue reached a given weekly cost) to support Recommendation 3; Section 5.3 explains why Table 5's hit rate (43.7%, all homes in one list) is below 49.6% (within priority groups); the assumption and two-year passages use plainer words; future work lists three concrete steps. Microsoft Word count 2,987; ten pages.

## Changes on 17 October

- Table 4 now gives each priority group's rank on estimated revenue (of 14) and the median revenue of its homes below target; the one-night column it replaced is still in `outputs/priority_group_descriptives.csv`.
- Section 5.2 explains how to choose when the activity and revenue rankings differ: activity sets where to search, revenue tests each lease, and between leases that pass the larger margin of typical revenue over costs wins. Recommendation 1 now points to this rule instead of ranking Yarra Ranges houses strictly behind City leases.
- Section 6 adds a worked example for two unlisted rentals (rents and costs are illustrative, not data). Recommendation 3 gives below-target weekly revenue as the amount a cash buffer must cover, and Table 7's week-4 rule uses it instead of the all-group 60 nights.
- Recommendation 2 now says the model orders candidates already on Airbnb; Section 4 describes the reduced model as a test of what price and minimum stay add.
- About 150 words were cut elsewhere to stay under 3,000 words (Microsoft Word count 2,982 on 17 October, 2,987 after the 18 October changes). Figures 2 and 4 are slightly shorter and the appendix starts on a new page, so the report stays at nine pages.
- The whole analysis was re-run from the three course CSV files (SHA-256 checked); see the root README.
- `check_report_package.py` also checks the new Table 4 values and Microsoft Word's recorded word count.

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
