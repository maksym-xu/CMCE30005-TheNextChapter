# Final presentation analysis evidence

This directory contains source code and aggregate results for the final presentation. The [slide evidence map](../EVIDENCE_MAP.md) identifies the relevant files for each slide and Q&A answer. The primary presentation result covers all 3,873 eligible listings; the supplementary three-group comparison has a different scope and comparator.

## Public checks

From this directory, using Python 3 with no additional packages:

```sh
python3 scripts/check_publication.py
```

This checks public counts, percentages, quotas, coefficient directions and temporal weighted averages across the distributed tables. It **does not** refit a model, inspect private records, prove host separation, rebuild review windows or regenerate intervals. Its report is `checks/publication_check.json`.

The retained `checks/validation_report.json` records the earlier 35 checks against authorised local data and predictions. `checks/shortlisted_group_validation_independent_check.json` records a separate R implementation of the frozen-prediction subgroup arithmetic. These saved reports are not evidence of a new complete data-pipeline rerun at publication time.

## Reproduction with authorised school data

Raw school files, the compact listing-level input and listing-level predictions are intentionally excluded. Obtain the authorised school data independently. Follow the repository root README to rebuild `data/processed/listings_clean.rds` and `data/processed/rq_analysis_main_manifest.csv` using the recorded scope rules and source hashes. Do not substitute a newer public snapshot and expect the same figures.

From this directory, with R packages `data.table`, `jsonlite`, `sandwich`, and `randomForest`, plus Python 3:

```sh
mkdir -p private-inputs working logs
Rscript scripts/prepare_private_input.R ../..
bash run.sh
Rscript scripts/matched_rf_comparison.R
Rscript scripts/association_stability.R
python3 scripts/shortlisted_group_validation.py
Rscript scripts/verify_shortlisted_group_validation.R
python3 scripts/check_publication.py
```

`prepare_private_input.R` accepts the repository root (or an authorised frozen audit root) as its argument. The main R script fits logistic regression, reconstructs the training-host segment-rate comparator and creates local out-of-fold predictions. The Python validator independently checks their arithmetic. The matched forest uses the same inputs and host folds but is not the interim Python forest. Association checks reuse the existing training folds. The subgroup calculation reuses fixed predictions without refitting or tuning.

The earlier temporal results under `reference/temporal-validation/` are retained evidence. To rebuild them from dated raw reviews, run the repository's original `scripts/validation/temporal_holdout.py` pipeline; the compact presentation runner does not recreate that pipeline. Both windows come from the same supplied snapshot and the same surviving homes. Threshold 34 belongs to that check; threshold 30 belongs to the main model analysis.

## Interpretation

- Main historical comparison: logistic 423/969 = 43.7%, versus a quota-matched training-fold group-rate expectation of 28.1%. The difference is 15.6 percentage points across the full eligible sample.
- Supplementary fixed-group check: 202/409 = 49.4%, versus 33.4% expected under uniform selection within the same three groups and quotas. It is an exploratory post-selection check, not a new business trial.
- The stored group-rate scores vary across folds. Their 19.9% result inside the three groups is a diagnostic of an unfavourable fold-ranking effect, not a neutral business comparator. The group-by-fold quota sensitivity limits this reallocation and remains positive.
- Neither review target measures occupancy or profit. Current settings may differ from historical settings. Random forest remains a benchmark; logistic is the main presentation model for clearer explanation, not a proven universal winner.
- Overlapping descriptive intervals motivate treating the groups as promising options. Overlap alone is not a test of pairwise differences.

The public source-provenance file retains hashes and repository-relative names. Publication changes documentation and packaging; it does not add new data or retrain the models.
