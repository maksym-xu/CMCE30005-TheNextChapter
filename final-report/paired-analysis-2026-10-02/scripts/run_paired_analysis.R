# Run from this package root with Rscript scripts/run_paired_analysis.R.
# Historical, outcome-informed six-input specification: no new model selection.
library(data.table)
library(jsonlite)
library(sandwich)
source("scripts/model_helpers.R")
for (name in c("outputs", "working", "logs")) dir.create(name, showWarnings = FALSE, recursive = TRUE)
plan <- fromJSON("config/rerun_plan.json")
raw <- fread("private-inputs/analysis_input.csv", colClasses = c(id = "character", host_id = "character"))
stopifnot(nrow(raw) == 3873L, uniqueN(raw$host_id) == 1726L, !anyDuplicated(raw$id),
          all(raw$host_role == "analysis"), sum(is.na(raw$minimum_nights)) == 3L,
          all(raw$review_target_met == as.integer(raw$reviews_365d >= plan$outcome_threshold)),
          all(raw[, uniqueN(fold), by = host_id]$V1 == 1L))
d <- prepare_features(raw)
hosts <- sort(unique(d$host_id))
membership <- list(); predictions <- list(); metrics <- list(); preprocessing <- list(); coefficients <- list()

evaluate <- function(design_name, split_number, test_hosts, split_seed = NA_integer_) {
  train <- d[!host_id %in% test_hosts]; test <- d[host_id %in% test_hosts]
  stopifnot(!length(intersect(train$host_id, test$host_id)), nrow(train) + nrow(test) == nrow(d),
            length(unique(train$busy)) == 2L, length(unique(test$busy)) == 2L)
  prep <- training_preprocessor(train)
  tr <- apply_preprocessor(train, prep); te <- apply_preprocessor(test, prep)
  fit <- glm(FORMULA, family = binomial(), data = tr, na.action = na.fail)
  stopifnot(fit$converged, nobs(fit) == nrow(train), !anyNA(coef(fit)))
  te[, p_logistic := as.numeric(predict(fit, newdata = te, type = "response"))]
  te[, p_segment_mean := segment_predict(train, te, plan$baseline_smoothing_weight)]
  stopifnot(all(is.finite(te$p_logistic)), all(is.finite(te$p_segment_mean)))
  te[, `:=`(w_logistic = quota_weights(p_logistic, plan$screening_fraction),
            w_segment_mean = quota_weights(p_segment_mean, plan$screening_fraction))]
  index <- length(metrics) + 1L
  membership[[index]] <<- data.table(design = design_name, split = split_number, host_id = hosts,
                                    role = ifelse(hosts %in% test_hosts, "test", "train"))
  audit <- data.table(design = design_name, split = split_number, fill_one_night = prep$fill,
     observed_train_no = prep$observed_no, observed_train_yes = prep$observed_yes,
     train_missing_minimum = sum(tr$was_minimum_missing), test_missing_minimum = sum(te$was_minimum_missing),
     unseen_test_segments = uniqueN(te[unseen_segment == 1L]$segment))
  preprocessing[[index]] <<- audit
  values <- paired_metrics(te$busy, te$p_logistic, te$p_segment_mean, plan$screening_fraction)
  metrics[[index]] <<- cbind(data.table(design = design_name, split = split_number, seed = split_seed,
      train_hosts = uniqueN(tr$host_id), test_hosts = uniqueN(te$host_id),
      train_listings = nrow(tr), test_listings = nrow(te)), values)
  predictions[[index]] <<- cbind(data.table(design = design_name, split = split_number),
      te[, .(id, host_id, segment, busy, p_logistic, p_segment_mean, one_night,
             was_minimum_missing, training_segment_median_price, w_logistic, w_segment_mean)])
  cf <- data.table(design = design_name, split = split_number, term = names(coef(fit)), coefficient = unname(coef(fit)))
  coefficients[[index]] <<- cf
  invisible(NULL)
}

# Recompute the original five-fold result under the corrected preprocessing rule.
for (k in sort(unique(d$fold))) evaluate("host_fold", k, unique(d[fold == k]$host_id))

# Exactly the original 50 host samples. Both methods refit on each same training set.
for (i in seq_len(plan$repeats)) {
  set.seed(as.integer(plan$seed + i))
  test_hosts <- sample(hosts, round(plan$test_host_share * length(hosts)))
  evaluate("repeated_host_split", i, test_hosts, as.integer(plan$seed + i))
}

met <- rbindlist(metrics); pred <- rbindlist(predictions); audit <- rbindlist(preprocessing)
fwrite(met, "outputs/split_metrics.csv")
fwrite(audit, "outputs/preprocessing_audit.csv")
fwrite(rbindlist(coefficients), "outputs/split_coefficients.csv")
# These identifiers and per-listing predictions are private reproduction material.
fwrite(rbindlist(membership), "working/split_membership_PRIVATE.csv")
fwrite(pred, "working/test_predictions_PRIVATE.csv")

repeated <- met[design == "repeated_host_split"]
summary <- rbindlist(lapply(list(
  c("precision_difference_pp", "logistic_precision", "segment_precision", "higher"),
  c("auc_difference", "logistic_auc", "segment_auc", "higher"),
  c("brier_difference", "logistic_brier", "segment_brier", "lower")
), function(spec) {
  delta <- repeated[[spec[1]]]; better <- if (spec[4] == "higher") delta > 1e-12 else delta < -1e-12
  tied <- abs(delta) <= 1e-12
  data.table(metric = spec[1], logistic_mean = mean(repeated[[spec[2]]]), segment_mean = mean(repeated[[spec[3]]]),
    mean_difference = mean(delta), median_difference = median(delta),
    p05_difference = unname(quantile(delta, .05, type = 7)), p95_difference = unname(quantile(delta, .95, type = 7)),
    min_difference = min(delta), max_difference = max(delta), better_splits = sum(better),
    tied_splits = sum(tied), worse_splits = sum(!better & !tied), better_direction = spec[4], splits = nrow(repeated))
}))
fwrite(summary, "outputs/paired_summary.csv")
metric_distribution <- rbindlist(lapply(c("logistic_precision", "segment_precision", "logistic_auc", "segment_auc", "logistic_brier", "segment_brier"), function(nm) {
  x <- repeated[[nm]]
  data.table(metric = nm, mean = mean(x), median = median(x), p05 = unname(quantile(x, .05)),
             p95 = unname(quantile(x, .95)), min = min(x), max = max(x), splits = length(x))
}))
fwrite(metric_distribution, "outputs/metric_distribution.csv")

# Pooled OOF is the original five-fold design only. Never pool the 50 overlapping tests.
oof <- pred[design == "host_fold"]
stopifnot(nrow(oof) == nrow(d), !anyDuplicated(oof$id))
fwrite(paired_metrics(oof$busy, oof$p_logistic, oof$p_segment_mean), "outputs/five_fold_pooled_comparison.csv")
old <- fread("reference/published_final_logit_repeated_splits.csv")
changes <- merge(repeated, old, by = "split")
stopifnot(nrow(changes) == 50L, all(changes$test_listings.x == changes$test_listings.y))
fwrite(changes[, .(split, test_listings = test_listings.x, old_auc = auc, corrected_auc = logistic_auc,
  auc_change = logistic_auc - auc, old_precision = hit_rate_top_quarter, corrected_precision = logistic_precision,
  precision_change_pp = 100 * (logistic_precision - hit_rate_top_quarter))], "outputs/change_from_published_repeats.csv")
legacy_oof <- fread("private-inputs/legacy_oof_predictions_PRIVATE.csv", colClasses = c(id = "character", host_id = "character"))
joined <- merge(oof, legacy_oof[, .(id, legacy_logistic = p, legacy_baseline = p_segment_mean)], by = "id")
stopifnot(nrow(joined) == nrow(d))
impact <- list(max_oof_probability_change = max(abs(joined$p_logistic - joined$legacy_logistic)),
  max_oof_baseline_change = max(abs(joined$p_segment_mean - joined$legacy_baseline)),
  max_repeated_auc_change = max(abs(changes$logistic_auc - changes$auc)),
  max_repeated_precision_change_pp = max(abs(100 * (changes$logistic_precision - changes$hit_rate_top_quarter))),
  note = "Comparison with stored published outputs; floating-point differences below 1e-12 are numerical tolerance. No equality to previous results is forced.")
write_json(impact, "outputs/change_from_published.json", pretty = TRUE, auto_unbox = TRUE, digits = 16)

# Full-data descriptive fit uses all analysis rows as its training data, and is not a test.
full_prep <- training_preprocessor(d); full <- apply_preprocessor(d, full_prep)
fit <- glm(FORMULA, family = binomial(), data = full, na.action = na.fail)
stopifnot(fit$converged, nobs(fit) == nrow(full), !anyNA(coef(fit)))
vc <- vcovCL(fit, cluster = ~host_id); estimate <- coef(fit); se <- sqrt(diag(vc))
fwrite(data.table(term = names(estimate), coefficient = unname(estimate), host_clustered_se = unname(se),
  odds_ratio = exp(unname(estimate)), odds_ratio_ci95_lo = exp(unname(estimate - 1.96 * se)),
  odds_ratio_ci95_hi = exp(unname(estimate + 1.96 * se)),
  interpretation = "Descriptive, conditional on outcome-informed frozen specification; not selection-adjusted or causal"),
  "outputs/full_descriptive_coefficients.csv")
stay <- d[, .(listings = .N, positives = sum(busy)), by = .(minimum_stay_category = fifelse(is.na(minimum_nights), "Missing",
  fifelse(minimum_nights <= 1, "1 night", fifelse(minimum_nights <= 6, "2-6 nights", "7+ nights"))))]
fwrite(stay, "outputs/minimum_stay_missingness.csv")
write_json(list(plan = plan, input_rows = nrow(d), input_hosts = length(hosts), positives = sum(d$busy),
  missing_minimum_nights = sum(is.na(d$minimum_nights)), full_fit_imputation = full_prep$fill,
  repeated_splits = nrow(repeated), original_host_folds = uniqueN(met[design == "host_fold"]$split),
  paired_summary = summary, change_from_published = impact,
  limitations = c("P05/P95 are split sensitivity, not confidence limits.",
    "The 50 host samples overlap; count of better splits is descriptive, not an independent-test probability.",
    "Outcome-informed binary coding and earlier model exploration remain outside this resampling procedure.",
    "No prospective performance, occupancy, profit or intervention effect is established.",
    "The archived forest comparison and old nested-selection workflow are not rerun or newly validated here.")),
  "outputs/results.json", pretty = TRUE, auto_unbox = TRUE, digits = 16)
capture.output(sessionInfo(), file = "logs/R_session_info.txt")
print(summary)
print(impact)
cat("Completed 50 paired repeated host splits and five original host folds.\n")
