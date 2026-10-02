# Aggregate screening and paired-summary helpers. No outcomes enter quota weights.

check_file_fingerprint <- function(path, expected_sha256) {
  stopifnot(file.exists(path))
  binary <- Sys.which("shasum")
  if (nzchar(binary)) {
    result <- system2(binary, c("-a", "256", shQuote(path)), stdout = TRUE, stderr = TRUE)
  } else {
    binary <- Sys.which("sha256sum")
    if (!nzchar(binary)) stop("A SHA-256 command (shasum or sha256sum) is required.")
    result <- system2(binary, shQuote(path), stdout = TRUE, stderr = TRUE)
  }
  stopifnot(is.null(attr(result, "status")), length(result) == 1L)
  observed <- strsplit(result, "[[:space:]]+")[[1L]][1L]
  if (!identical(tolower(observed), tolower(expected_sha256)))
    stop("A frozen input fingerprint does not match.")
  invisible(TRUE)
}

screen_one <- function(rows, score_column, fraction, fixed_group_quota = FALSE) {
  stopifnot(nrow(rows) > 0L, fraction > 0, fraction <= 1)
  scores <- rows[[score_column]]
  stopifnot(all(is.finite(scores)), all(scores >= 0 & scores <= 1))
  if (fixed_group_quota) {
    weights <- numeric(nrow(rows))
    quota <- 0L
    for (group in unique(rows$segment)) {
      at <- which(rows$segment == group)
      weights[at] <- quota_weights(scores[at], fraction)
      quota <- quota + ceiling(length(at) * fraction)
    }
  } else {
    weights <- quota_weights(scores, fraction)
    quota <- ceiling(nrow(rows) * fraction)
  }
  stopifnot(abs(sum(weights) - quota) < 1e-9, all(weights >= 0 & weights <= 1))
  target_count <- sum(rows$busy)
  expected_selected <- sum(weights * rows$busy)
  data.table(n_listings = nrow(rows), n_hosts = uniqueN(rows$host_id), target_count = target_count,
             quota = as.integer(quota), expected_target_selected = expected_selected,
             precision = expected_selected / quota,
             recall = if (target_count > 0L) expected_selected / target_count else NA_real_)
}

discrimination_one <- function(rows, score_column) {
  target_count <- sum(rows$busy)
  scores <- rows[[score_column]]
  data.table(n_listings = nrow(rows), n_hosts = uniqueN(rows$host_id), target_count = target_count,
             auc = if (target_count > 0L && target_count < nrow(rows)) auc(rows$busy, scores) else NA_real_,
             brier = mean((rows$busy - scores)^2))
}

make_paired_differences <- function(metrics, keys, specifications) {
  pairs <- list(full_vs_baseline = c("full", "baseline"),
                property_only_vs_baseline = c("property_only", "baseline"),
                full_vs_property_only = c("full", "property_only"))
  fields <- vapply(specifications, function(x) x[[1L]], character(1))
  rbindlist(lapply(names(pairs), function(pair_name) {
    models <- pairs[[pair_name]]
    left <- metrics[model == models[1L], c(keys, fields), with = FALSE]
    right <- metrics[model == models[2L], c(keys, fields), with = FALSE]
    stopifnot(nrow(left) == nrow(right), !anyDuplicated(left[, ..keys]), !anyDuplicated(right[, ..keys]))
    setnames(left, fields, paste0(fields, "_left"))
    setnames(right, fields, paste0(fields, "_right"))
    joined <- merge(left, right, by = keys, all = FALSE, sort = FALSE)
    stopifnot(nrow(joined) == nrow(left))
    result <- joined[, ..keys]
    result[, `:=`(pair = pair_name, left_model = models[1L], right_model = models[2L])]
    for (name in names(specifications)) {
      field <- specifications[[name]][[1L]]
      multiplier <- as.numeric(specifications[[name]][[2L]])
      result[, (name) := multiplier * (joined[[paste0(field, "_left")]] - joined[[paste0(field, "_right")]])]
    }
    result
  }))
}

summarise_models <- function(metrics, keys, fields) {
  long <- melt(metrics, id.vars = keys, measure.vars = fields, variable.name = "metric", value.name = "value")
  long[, metric := as.character(metric)]
  result <- long[, {
    finite <- value[is.finite(value)]
    stats <- if (length(finite)) c(mean(finite), median(finite),
       unname(quantile(finite, .05, type = 7)), unname(quantile(finite, .95, type = 7)), min(finite), max(finite))
       else rep(NA_real_, 6L)
    .(splits = .N, n_finite = length(finite), mean = stats[1L], median = stats[2L],
      p05 = stats[3L], p95 = stats[4L], min = stats[5L], max = stats[6L])
  }, by = c(keys, "metric")]
  setorderv(result, c(keys, "metric"))
  result
}

summarise_pairs <- function(metrics, keys, fields) {
  long <- melt(metrics, id.vars = keys, measure.vars = fields, variable.name = "metric", value.name = "value")
  long[, metric := as.character(metric)]
  result <- long[, {
    finite <- value[is.finite(value)]
    direction <- if (metric[1L] == "brier_difference") "lower" else "higher"
    signed <- if (direction == "lower") -finite else finite
    stats <- if (length(finite)) c(mean(finite), median(finite),
       unname(quantile(finite, .05, type = 7)), unname(quantile(finite, .95, type = 7)), min(finite), max(finite))
       else rep(NA_real_, 6L)
    .(splits = .N, n_finite = length(finite), mean_difference = stats[1L], median_difference = stats[2L],
      p05_difference = stats[3L], p95_difference = stats[4L], min_difference = stats[5L], max_difference = stats[6L],
      better_splits = sum(signed > 1e-12), tied_splits = sum(abs(signed) <= 1e-12), worse_splits = sum(signed < -1e-12),
      better_direction = direction)
  }, by = c(keys, "metric")]
  setorderv(result, c(keys, "metric"))
  result
}
