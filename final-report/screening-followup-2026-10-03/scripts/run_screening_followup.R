# Run from this package root. Reuse frozen host splits and full/baseline scores.
# Fit only the reduced logistic model, removing price and minimum-stay predictors.
library(data.table)
library(jsonlite)
source("scripts/screening_helpers.R")

plan <- fromJSON("config/followup_plan.json")
fingerprints <- fromJSON("reference/input_fingerprints.json", simplifyVector = FALSE)
for (path in names(fingerprints)) check_file_fingerprint(path, fingerprints[[path]]$sha256)
source("reference/prior_model_helpers.R")
for (directory in c("outputs", "working", "logs")) dir.create(directory, recursive = TRUE, showWarnings = FALSE)

raw <- fread("private-inputs/analysis_input.csv", colClasses = c(id = "character", host_id = "character"))
stopifnot(nrow(raw) == plan$input_rows, uniqueN(raw$host_id) == plan$input_hosts,
          all(raw$host_role == "analysis"), !anyDuplicated(raw$id),
          all(raw$review_target_met == as.integer(raw$reviews_365d >= 30)),
          all(raw$common_review_threshold == 30), all(raw[, uniqueN(fold), by = host_id]$V1 == 1L))
d <- prepare_features(raw)
stopifnot(all(is.finite(d$amenities_10)), all(d$segment %in% unique(d$segment)))
prior <- fread("private-inputs/prior_test_predictions_PRIVATE.csv", colClasses = c(id = "character", host_id = "character"))
members <- fread("private-inputs/prior_split_membership_PRIVATE.csv", colClasses = c(host_id = "character"))
full_coefficients <- fread("reference/prior_full_coefficients.csv")
prior_metrics <- fread("reference/prior_split_metrics.csv")
prior <- prior[design == "repeated_host_split"]
members <- members[design == "repeated_host_split"]
full_coefficients <- full_coefficients[design == "repeated_host_split"]
prior_metrics <- prior_metrics[design == "repeated_host_split"]
split_numbers <- seq_len(plan$splits)
stopifnot(identical(sort(unique(prior$split)), split_numbers),
          identical(sort(unique(members$split)), split_numbers),
          identical(sort(unique(full_coefficients$split)), split_numbers),
          identical(sort(unique(prior_metrics$split)), split_numbers),
          all(plan$priority_groups %in% d$segment),
          identical(as.numeric(plan$fractions), c(.1, .25, .5)))

PROPERTY_FORMULA <- busy ~ area + dwelling + bedrooms + amenities_10
score_columns <- c(baseline = "p_baseline", property_only = "p_property_only", full = "p_full")
screening <- list(); group_screening <- list(); discrimination <- list()
predictions <- list(); reduced_coefficients <- list(); diagnostics <- list()
all_hosts <- unique(d$host_id)

for (split_number in split_numbers) {
  membership <- members[split == split_number]
  stopifnot(nrow(membership) == length(all_hosts), !anyDuplicated(membership$host_id),
            setequal(membership$host_id, all_hosts), all(membership$role %in% c("train", "test")))
  train_ids <- membership[role == "train"]$host_id
  test_ids <- membership[role == "test"]$host_id
  stopifnot(length(train_ids) > 0L, length(test_ids) > 0L, !length(intersect(train_ids, test_ids)))
  train <- d[host_id %chin% train_ids]
  old <- prior[split == split_number]
  stopifnot(!anyDuplicated(old$id), setequal(old$id, d[host_id %chin% test_ids]$id))
  test <- d[match(old$id, d$id)]
  stopifnot(identical(test$id, old$id), identical(test$host_id, old$host_id),
            identical(test$segment, old$segment), all(test$busy == old$busy),
            setequal(test$host_id, test_ids), nrow(train) + nrow(test) == nrow(d))

  # Independently check frozen baseline and full scores without fitting either.
  expected_baseline <- segment_predict(train, test, smoothing = 10)
  baseline_difference <- max(abs(expected_baseline - old$p_segment_mean))
  fitted_preprocessor <- training_preprocessor(train)
  full_test_features <- apply_preprocessor(test, fitted_preprocessor)
  full_matrix <- model.matrix(FORMULA, data = full_test_features)
  old_coefficients <- full_coefficients[split == split_number]
  stopifnot(!anyDuplicated(old_coefficients$term), setequal(colnames(full_matrix), old_coefficients$term))
  ordered_coefficients <- old_coefficients$coefficient[match(colnames(full_matrix), old_coefficients$term)]
  reconstructed_full <- plogis(drop(full_matrix %*% ordered_coefficients))
  full_difference <- max(abs(reconstructed_full - old$p_logistic))
  stopifnot(baseline_difference < 1e-10, full_difference < 1e-10)

  warnings_seen <- character()
  fit <- withCallingHandlers(glm(PROPERTY_FORMULA, family = binomial(), data = train, na.action = na.fail),
     warning = function(w) { warnings_seen <<- c(warnings_seen, conditionMessage(w)); invokeRestart("muffleWarning") })
  stopifnot(fit$converged, nobs(fit) == nrow(train), !anyNA(coef(fit)), all(is.finite(coef(fit))))
  p_reduced <- as.numeric(predict(fit, newdata = test, type = "response"))
  stopifnot(all(is.finite(p_reduced)), all(p_reduced >= 0 & p_reduced <= 1))
  scored <- data.table(split = split_number, id = test$id, host_id = test$host_id,
     segment = test$segment, busy = test$busy, p_baseline = old$p_segment_mean,
     p_property_only = p_reduced, p_full = old$p_logistic)
  stopifnot(all(scored[, uniqueN(p_baseline), by = segment]$V1 == 1L))
  predictions[[split_number]] <- scored
  reduced_coefficients[[split_number]] <- data.table(split = split_number,
       term = names(coef(fit)), coefficient = unname(coef(fit)))
  diagnostics[[split_number]] <- data.table(split = split_number,
       train_listings = nrow(train), train_hosts = uniqueN(train$host_id),
       test_listings = nrow(test), test_hosts = uniqueN(test$host_id),
       converged = fit$converged, iterations = fit$iter, nobs = nobs(fit),
       coefficient_count = length(coef(fit)), has_na_coefficients = anyNA(coef(fit)),
       warning_count = length(warnings_seen), baseline_reconstruction_max_difference = baseline_difference,
       full_score_reconstruction_max_difference = full_difference)
  priority <- scored[segment %chin% plan$priority_groups]
  stopifnot(setequal(unique(priority$segment), plan$priority_groups))

  for (fraction in plan$fractions) {
    for (model_name in names(score_columns)) {
      score_column <- score_columns[[model_name]]
      for (scope_name in c("all_eligible", "priority_pool", "priority_fixed_quota")) {
        rows <- if (scope_name == "all_eligible") scored else priority
        value <- screen_one(rows, score_column, fraction, scope_name == "priority_fixed_quota")
        screening[[length(screening) + 1L]] <- cbind(data.table(split = split_number,
             scope = scope_name, fraction = fraction, model = model_name), value)
      }
      for (group in plan$priority_groups) {
        rows <- priority[segment == group]
        value <- screen_one(rows, score_column, fraction)
        if (model_name == "baseline")
          stopifnot(abs(value$expected_target_selected - value$quota * mean(rows$busy)) < 1e-9)
        group_screening[[length(group_screening) + 1L]] <- cbind(data.table(split = split_number,
             segment = group, fraction = fraction, model = model_name), value)
      }
    }
  }
  for (scope_name in c("all_eligible", "priority_pool")) {
    rows <- if (scope_name == "all_eligible") scored else priority
    for (model_name in names(score_columns))
      discrimination[[length(discrimination) + 1L]] <- cbind(data.table(split = split_number,
          scope = scope_name, model = model_name), discrimination_one(rows, score_columns[[model_name]]))
  }
}

screening <- rbindlist(screening)
group_screening <- rbindlist(group_screening)
discrimination <- rbindlist(discrimination)
diagnostics <- rbindlist(diagnostics)
stopifnot(nrow(screening) == 50L * 3L * 3L * 3L, nrow(group_screening) == 50L * 3L * 3L * 3L,
          nrow(discrimination) == 50L * 2L * 3L,
          all(screening[, uniqueN(quota), by = .(split, scope, fraction)]$V1 == 1L))

# Confirm the old full-population 25% comparison is retained exactly in meaning.
prior_comparison_checks <- list()
for (model_name in c("baseline", "full")) {
  new <- screening[scope == "all_eligible" & fraction == .25 & model == model_name]
  old <- prior_metrics[match(new$split, split)]
  old_prefix <- if (model_name == "full") "logistic" else "segment"
  stopifnot(all(new$n_listings == old$test_listings), all(new$quota == old$quota))
  precision_difference <- max(abs(new$precision - old[[paste0(old_prefix, "_precision")]]))
  positive_difference <- max(abs(new$expected_target_selected - old[[paste0(old_prefix, "_expected_positive")]]))
  disc <- discrimination[scope == "all_eligible" & model == model_name]
  old_disc <- prior_metrics[match(disc$split, split)]
  auc_difference <- max(abs(disc$auc - old_disc[[paste0(old_prefix, "_auc")]]))
  brier_difference <- max(abs(disc$brier - old_disc[[paste0(old_prefix, "_brier")]]))
  stopifnot(precision_difference < 1e-10, positive_difference < 1e-8,
            auc_difference < 1e-10, brier_difference < 1e-10)
  prior_comparison_checks[[model_name]] <- list(max_precision_difference = precision_difference,
       max_expected_positive_difference = positive_difference,
       max_auc_difference = auc_difference, max_brier_difference = brier_difference)
}

screen_specs <- list(precision_difference_pp = c("precision", 100),
                    recall_difference_pp = c("recall", 100),
                    expected_target_selected_difference = c("expected_target_selected", 1))
count_keys <- c("n_listings", "n_hosts", "target_count", "quota")
paired_screening <- make_paired_differences(screening, c("split", "scope", "fraction", count_keys), screen_specs)
paired_groups <- make_paired_differences(group_screening, c("split", "segment", "fraction", count_keys), screen_specs)
disc_specs <- list(auc_difference = c("auc", 1), brier_difference = c("brier", 1))
paired_discrimination <- make_paired_differences(discrimination,
      c("split", "scope", "n_listings", "n_hosts", "target_count"), disc_specs)
screen_fields <- c("precision", "recall", "expected_target_selected", "quota")
exports <- list(
  split_screening_metrics = screening,
  paired_screening_differences = paired_screening,
  screening_summary = summarise_models(screening, c("scope", "fraction", "model"), screen_fields),
  paired_screening_summary = summarise_pairs(paired_screening, c("scope", "fraction", "pair"), names(screen_specs)),
  priority_group_metrics = group_screening,
  priority_group_summary = summarise_models(group_screening, c("segment", "fraction", "model"), screen_fields),
  paired_priority_group_differences = paired_groups,
  paired_priority_group_summary = summarise_pairs(paired_groups, c("segment", "fraction", "pair"), names(screen_specs)),
  discrimination_metrics = discrimination,
  discrimination_summary = summarise_models(discrimination, c("scope", "model"), c("auc", "brier")),
  paired_discrimination_differences = paired_discrimination,
  paired_discrimination_summary = summarise_pairs(paired_discrimination, c("scope", "pair"), names(disc_specs)),
  property_only_coefficients = rbindlist(reduced_coefficients),
  property_only_fit_diagnostics = diagnostics
)
for (name in names(exports)) fwrite(exports[[name]], file.path("outputs", paste0(name, ".csv")), na = "")
fwrite(rbindlist(predictions), "working/test_predictions_PRIVATE.csv", na = "")
write_json(list(plan = plan, fingerprint_checks_passed = length(fingerprints), input_fingerprints = fingerprints,
    rows = nrow(d), hosts = uniqueN(d$host_id), target_count = sum(d$busy),
    splits = length(split_numbers), property_only_fits = nrow(diagnostics),
    all_property_only_fits_converged = all(diagnostics$converged),
    total_fit_warnings = sum(diagnostics$warning_count),
    maximum_baseline_reconstruction_difference = max(diagnostics$baseline_reconstruction_max_difference),
    maximum_full_reconstruction_difference = max(diagnostics$full_score_reconstruction_max_difference),
    prior_all_eligible_25_percent_checks = prior_comparison_checks,
    baseline_constant_within_every_segment_and_split = TRUE,
    within_segment_reduced_model_note = "Area, dwelling and bedrooms are constant within a segment; the reduced model can rank listings within a segment only through amenity count.",
    summary_method = "Equal weight for each split; finite values only for undefined metrics; empirical type-7 P05/P95, not confidence intervals; better/tie tolerance 1e-12.",
    no_new_full_or_baseline_fit = TRUE,
    output_csv_rows = lapply(exports, nrow)),
    "outputs/run_checks.json", pretty = TRUE, auto_unbox = TRUE, digits = 16, na = "null")
capture.output(sessionInfo(), file = "logs/R_session_info.txt")
cat("Completed 50 reduced-model fits and matched screening checks. No original models were refitted.\n")
print(exports$paired_screening_summary[fraction == .25 & metric == "precision_difference_pp",
      .(scope, pair, mean_difference, p05_difference, p95_difference, better_splits, tied_splits, worse_splits)])
