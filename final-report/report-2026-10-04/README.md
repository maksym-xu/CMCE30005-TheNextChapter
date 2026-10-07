# Final report reviewed 7 October 2026

[Report PDF](Final_Report.pdf) · [Report Word](Final_Report.docx) · [Matching report text](Final_Report.md)

The root [README](../../README.md) includes the complete report. The report uses analysis revision e4c68cae863e35bd1e7df0af4738c41b589f0bad. The 7 October refinement makes the prose more direct, clarifies how 25,728 listings become 3,873 analysis homes, names the covered dwelling types, and connects screening capacity to the initial ten-property investigation pool. Source analyses, figures and the final presentation remain unchanged. The package stays at this stable path so existing links continue to work.

## Publication checks

Microsoft Word counted 2,124 words for sections 1-7, including their tables and captions, and 2,755 words for the full document including title, references, acknowledgement and appendices. The PDF has 8 pages, all rendered and inspected. Word and Markdown match in ordered text, apart from the Word title block and heading formatting. The PDF contains the reported numbers and clickable links to this report branch and the frozen analysis revision.

[Package checks](package_checks.json) record file hashes and the check scope. The earlier analysis review recalculated public arithmetic for 2,700 metric rows and 54 paired summaries. The 7 October edit checked the headline screening figures and capacity results against those published tables; private records, raw reviews and model fits were unchanged.

## Figures and their sources

| Figure | Files | Published numerical source |
|---|---|---|
| Figure 1 priority groups | [PNG](figures/figure_1_priority_groups.png), [SVG](figures/figure_1_priority_groups.svg) | [Group rates and host-resampled ranges](../../final-presentation/analysis/reference/segment_ladder.csv) |
| Figure 2 screening comparison | [PNG](figures/figure_2_paired_screening.png), [SVG](figures/figure_2_paired_screening.svg) | [Screening summary](../screening-followup-2026-10-03/outputs/screening_summary.csv), scope priority_fixed_quota, fraction 0.25 |
| Figure 3 two annual windows | [PNG](figures/figure_3_historical_persistence.png), [SVG](figures/figure_3_historical_persistence.svg) | [Temporal validation metrics](../../final-presentation/analysis/reference/temporal-validation/validation_metrics.json) |
| Appendix B all 14 groups | [PNG](figures/appendix_all_14_groups.png), [SVG](figures/appendix_all_14_groups.svg) | [Complete group table](../../final-presentation/analysis/reference/segment_ladder.csv) |

[build_figures.py](build_figures.py) regenerates all four charts from these published aggregates. It requires numpy and matplotlib:

```sh
python final-report/report-2026-10-04/build_figures.py
```

No private listing or host identifiers are included in this report package. The source packages document the conditions needed to rerun the models: [paired analysis](../paired-analysis-2026-10-02/README.md) and [screening follow-up](../screening-followup-2026-10-03/README.md).

## Contributions and review status

The report integrates the analysis published by Maksym Xu and the report review and drafting coordinated by Eric Huang. The listed authors remain the four project group members. This release does not assign unverified contribution percentages. The group should review the final wording and AI acknowledgement before its LMS submission.

The AI acknowledgement is integrated into the report. There is no separate declaration attachment. Existing interim files and presentation files remain unchanged.
