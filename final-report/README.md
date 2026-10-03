# Final report and evidence

## Current final report reviewed 4 October 2026

The [current report package](report-2026-10-04/README.md) contains the [PDF](report-2026-10-04/Final_Report.pdf), [Word](report-2026-10-04/Final_Report.docx), matching [report text](report-2026-10-04/Final_Report.md), print-sized charts and publication checks. The root [README](../README.md) includes the complete report.

The report uses logistic regression and the within-group screening comparison: 49.6% for the complete model, 38.6% without price and minimum-stay inputs, and 32.4% for group rates. Each method selects a separate 25% quota within each of three fixed priority groups. Figures from other evaluation designs remain separate in Appendix A.

## Analysis packages

The [3 October screening follow-up](screening-followup-2026-10-03/README.md) tests whether the model adds value within the three previously selected property groups, how much it depends on recorded price and minimum-stay information, and how results change at 10%, 25% and 50% screening quotas. It reuses the same 50 host splits and the saved full-model and baseline scores, fitting only a reduced property model on each training set.

At a separate 25% quota inside each priority group, the full model averaged 49.62% historical review-target attainment, compared with 32.43% for the group-rate baseline and 38.61% for the reduced model. The full-versus-baseline gain averaged 17.19 percentage points, with 46 better and four worse splits. The fifth-to-ninety-fifth percentile range was -0.66 to 31.76 points: a measure of split sensitivity, not a confidence interval. The reduced model did not improve screening in every group; Melbourne three-bedroom apartments averaged 2.05 points below the baseline.

The [English findings brief](screening-followup-2026-10-03/deliverables/TheNextChapter_Screening_Findings.docx), [report methods](screening-followup-2026-10-03/METHODS_FOR_REPORT.md), figures, aggregate tables and independent score and arithmetic verification accompany the follow-up. Use market groups to guide initial investigation and the full score as supplementary evidence for comparable established listings when the required information is available. Permissions, actual quotations and conservative cash flow remain necessary before signing.

The [2 October paired model comparison](paired-analysis-2026-10-02/README.md) evaluates logistic regression and the simple segment-rate baseline on the same 50 host splits, using the same test listings and shortlist quota in each split. It includes training-only missing-value handling, precision, AUC, Brier and paired differences. Across all eligible test listings, the mean shortlist target rates were 43.42% and 31.96%, a gain of 11.46 points, with logistic screening better in 48 of 50 splits.

The [English speaking script](../final-presentation/english-script-2026-10-02/README.md) distinguishes that repeated comparison from the original pooled five-fold result shown in the presentation: 423 of 969 selections reached the target, or 43.65%, compared with 28.07% for the baseline. The new 49.62% figure uses a different evaluation population and fixed group quotas; it must not replace 43.65% as though the same model test had improved.

All repeated-split comparisons are exploratory retrospective checks. Test sets overlap, and group and feature choices followed earlier outcome exploration. Removing price as an input does not extend validation beyond the original established listings with usable prices. Reviews do not measure future bookings or profit. Independent verification reconstructs scores and metrics; it does not independently refit coefficients or rebuild raw dated reviews. Private inputs and row-level predictions remain excluded from publication.
