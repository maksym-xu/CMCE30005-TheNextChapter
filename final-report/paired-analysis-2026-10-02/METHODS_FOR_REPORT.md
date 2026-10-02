# Methods and interpretation for the final report

This document describes the completed paired rerun of 2 October 2026. The source release, processed-input fingerprints and aggregate evidence are documented in [README.md](README.md) and [provenance.json](reference/provenance.json). The rerun preserves the existing outcome and specification; it corrects imputation and adds a paired baseline comparison to every repeated host split.

## Population and outcome

We analysed the same 3,873 eligible listings from 1,726 hosts used in the final presentation. The binary outcome was whether a listing received at least 30 guest reviews during the 365 days ending on its recorded scrape date: `(last_scraped - 365 days, last_scraped]`. The threshold came from a separate reference group of hosts and was held fixed. Reference hosts were excluded from model fitting and evaluation.

The rerun starts from an authorised compact input containing the derived review count. It checks that the binary outcome equals that count compared with the fixed cutoff. It does not independently rebuild review counts from raw dated reviews or prove that the raw-data extraction is correct. [review_analysis.json](config/review_analysis.json) records the upstream eligibility and review-window rules.

## Model and variables

We used unpenalised logistic regression with six characteristic groups: council area, dwelling type, bedroom count, nightly price relative to comparable listings, whether one-night stays were accepted, and the number of listed amenities. A segment comprises listings with the same area, dwelling type and bedroom count. The fitted model combines weighted characteristics into a score between zero and one; we use higher scores to rank listings more likely to have met the historical review threshold.

The formula is:

```text
busy ~ area + dwelling + bedrooms + price_vs_similar_10 + one_night + amenities_10
```

Area, dwelling and bedrooms are factors. Their reference levels are Melbourne, Apartment/unit and one bedroom. The one-night reference is No. Relative price is `(nightly price / training segment median - 1) * 10`, so one unit means ten percentage points above the comparable median. Amenity count is divided by ten. The fitted coefficients are in [split_coefficients.csv](outputs/split_coefficients.csv).

The binary one-night definition was chosen after prior outcome inspection showed no target-reaching listing in the former seven-or-more-night category. This is an outcome-informed exploratory specification. Freezing it for the present run does not undo that history. We did not reselect variables or models inside the training partitions, and do not describe the run as nested selection or an untouched-test evaluation. The earlier nested comparison evaluated a different selection procedure and cannot supply independent validation of this revised model.

## Training-only preprocessing

For each split, all records belonging to a host stay together. Observed minimum-night values are converted to Yes when at most one night, and No otherwise. The three missing values remain missing until the split is formed. The most frequent observed binary value among training listings fills missing values in both training and test sets; an exact tie resolves to No. The procedure stops if the training set contains no observed minimum stay. The preprocessing function receives feature columns only, not outcomes.

Price is normalised using the median price of the same segment in the training set. A test segment absent from training uses the overall training price median. The fitted logistic model uses the transformed training data only. All 55 realised training partitions learned No, and none needed an unseen-segment fallback. These observed results are documented in [preprocessing_audit.csv](outputs/preprocessing_audit.csv); they were not imposed as a rule. Synthetic checks also cover a Yes mode, a tied mode, all missing values, test-data changes and unseen segments.

## Paired comparator and evaluation

We retained the original 50 host samples with seeds 30006 through 30055. Each iteration randomly sampled `round(0.3 * 1726) = 518` test hosts without replacement; the other 1,208 hosts formed the training set. Each host's listings stayed together, so listing counts varied between splits. R sorted character host identifiers and used `set.seed(30005 + split)` before sampling.

For the comparator, each test listing received its segment's training target rate, smoothed towards overall training prevalence with fixed weight 10:

```text
(training segment positive count + 10 * overall training positive share)
/ (training segment listing count + 10)
```

An unseen segment would use the overall training positive share. The weight was not tuned. This comparator is a smoothed segment mean, distinct from a model with additive area/type/bedroom coefficients.

Both methods rank exactly the same test listings and receive exactly `ceil(test listings / 4)` selections in expectation. All scores above the selection boundary receive weight one. Listings tied at the boundary share the remaining quota uniformly. Outcomes never break ties. Fractional weights express the expected result of uniform selection within a tie, not the physical selection of a fraction of a property.

Precision is the weighted number of target-reaching listings divided by the quota. AUC gives the probability that a randomly chosen positive ranks above a randomly chosen negative, with half credit to equal scores. Brier score is the average squared difference between predicted score and binary outcome. Higher precision and AUC are better; lower Brier score is better.

Differences are calculated within each split as logistic minus baseline, then summarised with equal weight per split. Precision differences use percentage points; AUC and Brier differences retain raw score units. Summary columns include mean, median, R type-7 empirical 5th and 95th percentiles, full range and better/tied/worse counts, using a numerical tie tolerance of 1e-12. [paired_summary.csv](outputs/paired_summary.csv) is the primary evidence. Its average differences are +11.46 percentage points for precision, +0.1049 for AUC and -0.01256 for Brier; logistic is better in 48, 50 and 44 of the 50 splits respectively.

## Separate five-fold and descriptive results

We also repeated the original five host-grouped folds with corrected imputation. Their pooled out-of-fold shortlist precision is 43.65% for logistic and 28.07% for the segment baseline, a difference of 15.58 percentage points. This pools one held-out prediction per analysis listing and applies one common quota of 969. The 50-repeat result instead applies a quota separately within each 70/30 host split and averages those split-level metrics. Its 11.46-point mean difference answers a different evaluation question. Neither number replaces the other, and the overlapping 50-repeat predictions must not be pooled as independent observations.

The full-sample descriptive model uses all analysis records as its training data, with full-sample price medians, the observed binary mode and host-clustered standard errors. Those coefficients are not used to generate held-out predictions. Their intervals are conditional on the chosen specification and do not adjust for prior exploration. This rerun does not repeat subgroup screening tests, random-forest comparisons or the earlier nested workflow.

## Verification and reproducibility limits

[model_helpers.R](scripts/model_helpers.R) defines preprocessing, scoring metrics and tie handling; [run_paired_analysis.R](scripts/run_paired_analysis.R) fits the models and writes the exports. [test_model_helpers.R](scripts/test_model_helpers.R) checks fourteen preprocessing and quota properties. The standard-library [verify_rerun.py](scripts/verify_rerun.py) independently checks complete, disjoint host memberships against private input, test rows and outcomes, training modes and medians, smoothed baseline probabilities, score reconstruction from exported logistic coefficients, expected quota weights and metric/summary arithmetic.

The saved verification covered 63,093 test-row predictions across 55 partitions. Its maximum reconstructed logistic-score discrepancy was 3.50 x 10^-15. This checks exported coefficients and features against predictions but does not independently refit the coefficients. It also does not reconstruct raw reviews or replay R sampling in Python. Membership completeness, original-fold agreement, sample sizes and declared seeds were checked. [verification.json](outputs/verification.json) records the checked-file hashes and scope; [helper_tests.json](outputs/helper_tests.json) records the helper checks.

Authorised private processed inputs are necessary to reproduce these checks and fits. The publication includes aggregate results, code and hashes, not listing identifiers, host memberships, raw logs or per-listing predictions. Public-file integrity checks can verify the package scope and hashes, but cannot substitute for private-data reproduction.

## Business interpretation and research limitations

The repeated splits share hosts and listings. Their percentile ranges show sensitivity to the training/test allocation, not sampling confidence intervals or 50 independent studies. The outcome-informed feature choice remains outside this resampling procedure. Computational host separation avoids sharing a host between training and test within a split, but does not create a new unexamined dataset.

The model relates characteristics recorded in the supplied snapshot to an earlier review window. Its scores therefore support retrospective screening, not a validated forecast of future demand or business success. Reviews are an activity proxy, not direct bookings, occupancy or profit. Conditional associations do not show that changing minimum stays, prices or amenities would cause an improvement. Historical ranking evidence can support investigation, but property permissions, actual lease terms and cash-flow assessment remain necessary before a business commitment.
