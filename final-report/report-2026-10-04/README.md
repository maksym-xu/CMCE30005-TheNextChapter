# Final report package (revised 23 October 2026)

[Report PDF](Final_Report.pdf) · [Report Word](Final_Report.docx) · [Report text](Final_Report.md)

Prepared by Eric Huang and Maksym Xu. `Final_Report.md` is the source text; the Word file is built from it, the PDF is exported from the Word file, and the root `README.md` carries the same report.

## Files

| Path | Purpose |
|---|---|
| `Final_Report.md`, `.docx`, `.pdf` | The report in three formats |
| `figures/figure_1_review_distribution` … `figure_6_weekly_reach` (`.png`, `.svg`) | The six report figures |
| `build_figures.py` | Builds the six figures from committed aggregate tables (matplotlib) |
| `scripts/revision_evidence.R` | Evidence added on 16–17 October: data exploration, estimated nights and revenue (all homes and homes below target, with each group's rank on both measures), model assumption checks, top-three stability and the all-input odds ratios |
| `scripts/review_sentiment.py` | Scores the tone of each analysis home's reviews in its collection year with VADER (`vaderSentiment==3.3.2`); checks that the window reproduces every home's review count |
| `scripts/feedback_checks.R` | Evidence added on 23 October after the final-presentation feedback: guest ratings of busy homes and the rest, and the two-setting rule (one-night stays, price at or below the group median) in the priority groups |
| `outputs/revision/` | Aggregate outputs of `revision_evidence.R` and `feedback_checks.R` (no listing or host identifiers) |
| `scripts/build_report_docx.py`, `reference/report_template.docx` | Builds the Word file from the Markdown with the report's template |
| `scripts/sync_readme.py` | Copies the report into the root `README.md` |
| `scripts/check_report_package.py` | Checks the four versions against each other, the word limit, PDF font embedding, the unchanged AI acknowledgement and key numbers against the outputs |
| `scripts/summarize_report_additions.py`, `scripts/test_report_additions.py`, `outputs/*.csv`, `outputs/report_additions.json` | Priority-group listing settings and saved coefficient summaries (14 October); the test now also runs the package check |
| `package_checks.json` | Result of the latest package check |

## Rebuild

From the repository root, with the private analysis input copied to `final-report/report-2026-10-04/private-inputs/analysis_input.csv` and the processed data in `data/processed/`:

```sh
Rscript final-report/report-2026-10-04/scripts/revision_evidence.R
Rscript final-report/report-2026-10-04/scripts/feedback_checks.R   # also needs data/raw/listings_airbnb.csv
python final-report/report-2026-10-04/scripts/review_sentiment.py   # needs vaderSentiment and data/raw/reviews_airbnb.csv
python final-report/report-2026-10-04/build_figures.py
python final-report/report-2026-10-04/scripts/build_report_docx.py
# export Final_Report.pdf from Final_Report.docx in Microsoft Word (embeds fonts)
python final-report/report-2026-10-04/scripts/sync_readme.py
python final-report/report-2026-10-04/scripts/check_report_package.py
```

## Sources of the figures and tables

| Report item | Source |
|---|---|
| Figure 1, Table 3 | `outputs/revision/review_histogram_bins.csv`, `review_distribution.csv`, `target_profile.csv`; rating row from `rating_check.csv`; negative-tone row and the Section 5.1 tone results from `review_sentiment.csv` |
| Figure 2 | `../../final-presentation/analysis/reference/segment_ladder.csv` (group rates and 1,000-draw host-resampled ranges) |
| Table 4, Recommendation 3, Section 5.2 rankings, worked example | `outputs/revision/group_estimated_revenue.csv` (`rank_median_revenue`, `median_est_revenue_below_target_aud`, `median_weekly_aud`, `median_weekly_below_target_aud`) and `outputs/priority_group_descriptives.csv`; the worked example's rents and costs are illustrative, not data |
| Figure 3, Section 5.3 scenario chances | `../../final-presentation/analysis/reference/final_logit_scenarios.csv` (model fitted to all study homes; host-clustered 95% ranges) |
| Table 5, Section 5.3 two-setting rule | `outputs/revision/two_setting_rule.csv` |
| Figure 4 | `../screening-followup-2026-10-03/outputs/screening_summary.csv` (scope `priority_fixed_quota`); list lengths of 10%, 25% and 50% are in the same file, and the reduced model by group in `priority_group_summary.csv` |
| Table A2 | `../../final-presentation/analysis/outputs/test_confusion.csv` (pooled five-fold scores) |
| Table A3 | `outputs/revision/top3_resample_shares.csv`; `../../reports/tables/rq_support_rule_top3.csv`; `../../final-presentation/analysis/reference/temporal-validation/validation_metrics.json` (host-weighted gap); `../screening-followup-2026-10-03/outputs/screening_summary.csv` and `priority_group_summary.csv` |
| Figure 6 | `outputs/revision/weekly_revenue_reach.csv` (share of each priority group's homes whose estimated weekly revenue reached each weekly cost, AUD 0–2,000 in steps of 10) |
| Figure 5, Section 5.4 | `../../final-presentation/analysis/reference/temporal-validation/validation_metrics.json` |
| Section 4 assumptions | `outputs/revision/model_gvif.csv`, `model_se_ratio.csv`, `revision_summary.json` |
| Section 5.2 stability | `outputs/revision/top3_resample_shares.csv`; the same top three without the price or history rule and under other group-size rules: `../../reports/tables/rq_support_rule_top3.csv` |
| Table A1 | `outputs/revision/all_term_odds_ratios.csv` (from `../screening-followup-2026-10-03/reference/prior_full_coefficients.csv`) |

## Evaluation designs

The report's headline (Figure 4) picks 25% of test homes separately in each priority group. Other designs give different numbers because they test different homes or allocate places differently; they should not be compared as if they were the same test.

| Design (25% of homes picked) | Model | Group rates | Gain (points) | Model better |
|---|---:|---:|---:|---:|
| Five host-grouped folds, all 3,873 homes scored once, one pooled list | 43.65% | 28.07% | +15.58 | — |
| 50 host splits, all 14 groups, about 1,184 test homes per split | 43.42% | 31.96% | +11.46 | 48 of 50 |
| 50 host splits, three priority groups pooled into one list | 48.91% | 32.37% | +16.54 | 47 of 50 |
| 50 host splits, separate quota in each priority group (report headline) | 49.62% | 32.43% | +17.19 | 46 of 50 |

In the pooled five-fold design, group-rate scores from five different training sets share one list, which tends to favour the model. Across the 50 splits on all groups, mean AUC is 0.708 against 0.603 (better in 50 of 50) and mean Brier score 0.1715 against 0.1841 (better in 44). Within the separate group quotas, gains average +16.4 points in City two-bedroom apartments, +17.6 in City three-bedroom apartments and +25.0 in Yarra Ranges houses; Yarra Ranges contributes only 5–9 picked homes per split.

## Changes on 23 October, third pass (toward the instructor's 2,000-word guide)

- Team review (Eric Huang): the two-setting rule is presented as a quick first check found in this sample, not as matching the model's tested hit rate; Section 2 says review counts record past guest activity and that converting them into nights needs assumptions about review rates and stay length; the model assumption is stated in terms of odds; Table 3 labels the rating as lifetime.
- Section 3 now says the 30-review target came from the set-aside hosts' homes within the 14 groups (the busiest quarter of those 906 homes), not from all 1,342 set-aside homes.
- Negative reviews are described as a share of each group's reviews ("proportionally fewer"), not a count.
- Microsoft Word count 2,972 words (whole document) across eleven pages; Sections 1–7 are about 2,420 words. PDF saved from Word for Mac with all fonts embedded.

- The body (Sections 1–7) is about 2,420 words, down from about 2,500; technical checks sit in Appendix A, now with Table A3 (further checks) referenced from Sections 2, 5.2 and 5.3.
- One term throughout: homes are **busy** (30+ reviews in the year) or **not busy**.
- Section 3 justifies each scope rule; Section 4 says which question each check answers.
- Review text is scored for tone with VADER (Hutto & Gilbert, 2014) in `scripts/review_sentiment.py`: about 90% of the 78,288 reviews read as positive in both groups, and 1.6% of busy homes' reviews read as negative against 2.9% for the rest. This replaces the "rated below 4.5 stars" row, which was noisy for homes with few reviews.
- The introduction gives the three main answers as a short list; key findings add a separate finding on guest satisfaction.

## Changes on 23 October (presentation feedback and Week 12)

The final-presentation feedback said the group did not explain what review activity measures or consider review sentiment, spent most of its time on model accuracy rather than the factors behind activity, and could have reached the top-three groups with a simple summary. The Week 12 lecture asked for recommendations based on the group's own evidence, insight before equations, and every table, figure and appendix item referenced in the text.

- Section 2 explains what review activity measures (completed bookings, a guide to demand and occupancy) and what it does not (profit, satisfaction), and says Objective 1 needs only a group summary while Objective 2 needs a model.
- Table 3 and Section 5.1 add guest ratings: busy homes averaged 4.84 stars against 4.69, and only 1.1% averaged below 4.5 against 15.2% of the rest; the gap holds in each priority group (`scripts/feedback_checks.R`).
- Section 5.3 leads with the factors (new Figure 3 of model-estimated chances) and adds a two-setting rule (Table 5): in the priority groups, homes with one-night stays priced at or below the group median were busy 50.4% of the time, against 9.3% with neither, about the model's 49.6%. Recommendation 2 is now this checklist rather than the model ranking.
- The confusion matrix moved to Appendix A (Table A2); the list-length table and per-group reduced-model results moved to the repository. Section 5.4 is the two-year check, now naming the three groups and Yarra Ranges' later-year 21.4%.
- Appendix A reports the curvature test in full (ordinary p = 0.03; p = 0.17 with host-clustered errors) and explains that the odds-ratio ranges are not confidence intervals.
- The legal checks (landlord consent, owners' corporation rules, short-stay levy) moved from Recommendation 3 into the inspection plan, because they come from public guidance rather than our analysis.
- Figures renumbered: 3 factors (new), 4 screening, 5 two years, 6 weekly reach. No model was refitted; the two new tables come from the analysis input and the raw listings file.
- Plainer key findings, a note that the two-setting rule was checked only on the homes that suggested it, star ratings named as the sentiment check, and corrected wording of the curvature test.
- Microsoft Word count 2,980 words (whole document) across ten pages after the second pass. PDF saved from Word for Mac with all fonts embedded.

## Changes on 20 October

- Clarified the two screening results, the all-home revenue medians and the ten-candidate inspection workflow, retaining the report's structure and business explanations.
- Restored five figure embeds and seven direct source links. Kept the model, aggregate outputs and figures unchanged.
- Microsoft Word count: 2,957 words across ten pages. Exported this revision through Microsoft Word on Windows as PDF/A; all font resources are embedded.
- The package check reconciles 38 values with the saved outputs. Six additions tests and five reader-revision tests pass. This revision does not retrain models.
- The report's repository links point directly to `main`. Release descriptions use neutral project wording.

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
