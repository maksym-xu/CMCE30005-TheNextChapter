# Final report 14 October 2026

[Report PDF](Final_Report.pdf) · [Report Word](Final_Report.docx) · [Matching report text](Final_Report.md)

The current report is prepared by Eric Huang and Maksym Xu. It combines the revised business narrative, APA 7 data-source reference and a short AI acknowledgement with the listing benchmarks and saved coefficient summaries published in revision 4e2dd23. The model analysis remains pinned to e4c68cae863e35bd1e7df0af4738c41b589f0bad. Models, headline screening results, figures, historical submissions and presentation files are unchanged.

## Additional descriptive and model evidence

[Listing settings](outputs/priority_group_descriptives.csv) cover all 3,873 analysis homes and each priority group. Prices and amenities are medians of the observed records. One-night percentages exclude missing minimum-stay records: three are missing in the full sample and none in the priority groups. The observed minimum stay is at least one night, so `minimum_nights == 1` agrees with the model's `minimum_nights <= 1` category. Advertised nightly rates are not residential rents or rates actually paid by guests.

[Operating coefficients](outputs/operating_coefficient_summary.csv) use only the 50 `repeated_host_split` fits in the saved [full-model coefficients](../screening-followup-2026-10-03/reference/prior_full_coefficients.csv). The five `host_fold` fits are excluded. The actual price term is `price_vs_similar_10`, defined as `(price / training-group median - 1) * 10`; amenities are divided by ten. The reported odds ratio is `exp(mean coefficient)`, not the arithmetic mean of odds ratios. Direction agreement across overlapping training samples is descriptive, not a causal or significance test.

[Aggregate output and source hashes](outputs/report_additions.json) contain no listing or host identifiers. The private input is not included in the repository. Its hash matches the existing [input fingerprint](../screening-followup-2026-10-03/reference/input_fingerprints.json).

```sh
python final-report/report-2026-10-04/scripts/summarize_report_additions.py \
  --analysis-input /path/to/private/analysis_input.csv
python final-report/report-2026-10-04/scripts/test_report_additions.py --unit-tests
```

The summary and unit tests use only Python's standard library. Full document consistency checks also require pypdf. Supply both original inputs and the repository root:

```sh
python final-report/report-2026-10-04/scripts/test_report_additions.py \
  --phase modified --report-root . \
  --analysis-input /path/to/private/analysis_input.csv \
  --coefficients final-report/screening-followup-2026-10-03/reference/prior_full_coefficients.csv
```

## Figures and their sources

| Figure | Published numerical source |
|---|---|
| Figure 1 priority groups | [Group rates and host-resampled ranges](../../final-presentation/analysis/reference/segment_ladder.csv) |
| Figure 2 screening comparison | [Screening summary](../screening-followup-2026-10-03/outputs/screening_summary.csv), priority_fixed_quota, fraction 0.25 |
| Figure 3 two annual windows | [Temporal metrics](../../final-presentation/analysis/reference/temporal-validation/validation_metrics.json) |
| Appendix B all 14 groups | [Complete group table](../../final-presentation/analysis/reference/segment_ladder.csv) |

`build_figures.py` still regenerates the four figures from the existing published aggregates. The images were not changed by this update.

## Current and historical contributions

This report integrates Maksym Xu's analysis and Eric Huang's report drafting and review. Historical interim and presentation files retain their original team details. The existing acknowledgement remains in the report.

[Package checks](package_checks.json) separate this update's aggregation and document checks from earlier model and published-arithmetic checks. The private records and model fits are unchanged.

## Current document verification

Microsoft Word counted 2,334 words for Sections 1–7, including tables and captions, and 2,974 words for the full document including title, references, acknowledgement and appendices. The PDF has eight pages, all rendered and inspected using Microsoft Word and PDFium. Word and Markdown match in ordered text. All four original figures and tables are retained; the four-week action table stays on one page.

References contain the Inside Airbnb dataset in APA 7 format. AI use is acknowledged briefly outside the reference list. The previous R and AI-tool bibliography entries have been removed. The saved coefficients from the 50 repeated host splits were independently aggregated again; no model was refitted and the private listing medians were not recomputed in this publication step.
