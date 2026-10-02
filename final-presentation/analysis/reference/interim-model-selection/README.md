# Why the presentation model changed

The interim report provisionally selected the **enhanced property-only random
forest** for probability ranking. Its AUC was 0.639589 and Brier score 0.181316;
the nested procedure selected that forest in all five outer folds by the lowest
inner Brier score. Those findings remain valid. The copied original files and
verbatim report excerpt preserve that evidence.

The final simple logistic model has AUC 0.705134, but it also uses current price
and minimum-stay information and different feature coding. Comparing 0.705 with
the interim forest's 0.640 does **not** isolate the effect of the algorithm.
The same enhanced property-only inputs actually favored the forest over the
earlier logistic model (AUC 0.639589 vs 0.607116; Brier 0.181316 vs 0.186853).

The original operating-controls comparison used identical features for its own
logistic and forest models. Their AUCs were 0.714080 and 0.712596 respectively;
the forest had lower Brier error (0.170011 vs 0.171956) and higher top-quarter
precision (46.23% vs 43.55%). Neither is an exact match to the final simplified
input design. Richer operating-controls gradient boosting reached AUC 0.749290;
the final logistic is not claimed to be the best-performing candidate overall.

## New matched-input check

The separate `scripts/matched_rf_comparison.R` uses the final model's same
3,873 listings, host folds, outcome and eleven encoded predictor columns. Price
medians are computed from training rows only. Both scores receive an expected
screening quota of 969, with fractional allocation at boundary ties.

One forest configuration was fixed before inspecting results: R `randomForest`,
250 trees, `mtry = 3`, `nodesize = 10`, bootstrap sampling, no class weighting,
seed `30005 + fold`. No tuning was performed.

| Model | AUC | Brier error (lower is better) | Top-quarter share reaching 30 reviews |
|---|---:|---:|---:|
| Final logistic | 0.7051 | 0.17180 | 43.65% |
| Matched-input forest | 0.6838 | 0.18723 | 45.15% |

This fixed forest has higher screening precision by 1.49 percentage points, but
the paired host-bootstrap 95% interval is −2.35 to +7.31 points. The interval is
descriptive and holds predictions fixed. It omits refitting and earlier model
selection. The logistic model has higher pooled AUC and lower Brier error in this
comparison; AUC's paired difference interval includes zero narrowly. The forest
does not establish a clear overall advantage.

Keeping logistic as the main presentation model is therefore defensible as a
choice for explanation with reasonable validated performance. It does **not**
show that logistic regression universally beats forests. Retain the interim
forest and this matched check as supporting benchmarks, and explicitly disclose
the change from the interim selection.

Suggested presentation wording:

> We kept the interim forest as a benchmark and simplified the model after the
> feedback. In an additional comparison using the same inputs and host tests,
> the forest showed no clear overall advantage, so we present the logistic model
> we can explain directly.

The new forest uses R `randomForest`, while the interim implementation was
Python scikit-learn. It is a new supplementary baseline, **not** a reproduction
of the old forest: probability construction and the meaning of `nodesize` differ
from scikit-learn's `min_samples_leaf`. It evaluates one configuration and seed
rule, not a complete search over either model family. All models remain
retrospective, exploratory classifiers of review activity.
