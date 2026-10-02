# Shared helpers for the report rerun. Preprocessing rules are in config/rerun_plan.json.
library(data.table)
AREAS <- c("Melbourne", "Yarra", "Yarra Ranges", "Port Phillip", "Stonnington", "Merri-bek")
FORMULA <- busy ~ area + dwelling + bedrooms + price_vs_similar_10 + one_night + amenities_10

prepare_features <- function(raw) {
  x <- copy(raw)
  x[, busy := as.integer(review_target_met)]
  x[, area := factor(neighbourhood_cleansed, levels = AREAS)]
  x[, dwelling := factor(ifelse(grepl("House", configuration), "House/townhouse", "Apartment/unit"),
                          levels = c("Apartment/unit", "House/townhouse"))]
  x[, bedrooms := factor(substr(configuration, 1L, 1L), levels = c("1", "2", "3"))]
  x[, segment := paste(neighbourhood_cleansed, configuration)]
  # The binary definition is an outcome-informed historical research choice.
  # It is frozen for this sensitivity run; the imputation value is NOT frozen.
  x[, one_night_raw := fifelse(is.na(minimum_nights), NA_character_,
                              fifelse(minimum_nights <= 1, "Yes", "No"))]
  x[, was_minimum_missing := as.integer(is.na(minimum_nights))]
  x[, amenities_10 := n_amenities / 10]
  stopifnot(!anyNA(x$area), !anyNA(x$dwelling), !anyNA(x$bedrooms),
            !anyNA(x$price_num), !anyNA(x$amenities_10),
            all(x$price_num > 0), all(x$busy %in% c(0L, 1L)))
  x
}

fit_preprocessor <- function(training_features) {
  # Only feature columns are passed here. The outcome is not available.
  stopifnot(!("busy" %in% names(training_features)),
            !("review_target_met" %in% names(training_features)))
  observed <- training_features$one_night_raw[!is.na(training_features$one_night_raw)]
  stopifnot(length(observed) > 0L)
  counts <- table(factor(observed, levels = c("No", "Yes")))
  fill <- names(counts)[which.max(counts)]  # first maximum: fixed tie order No, Yes
  list(fill = fill, observed_no = unname(counts["No"]), observed_yes = unname(counts["Yes"]),
       price_medians = training_features[, .(training_segment_median_price = median(price_num)), by = segment],
       global_price_median = median(training_features$price_num))
}

apply_preprocessor <- function(target, fitted) {
  out <- copy(target)
  med <- fitted$price_medians
  out[, training_segment_median_price := med$training_segment_median_price[match(segment, med$segment)]]
  out[, unseen_segment := as.integer(is.na(training_segment_median_price))]
  out[is.na(training_segment_median_price), training_segment_median_price := fitted$global_price_median]
  out[, price_vs_similar_10 := (price_num / training_segment_median_price - 1) * 10]
  out[, one_night := factor(fifelse(is.na(one_night_raw), fitted$fill, one_night_raw), levels = c("No", "Yes"))]
  stopifnot(!anyNA(out$one_night), all(is.finite(out$price_vs_similar_10)))
  out
}

training_preprocessor <- function(train) {
  fit_preprocessor(train[, .(one_night_raw, price_num, segment)])
}

segment_predict <- function(train, test, smoothing = 10) {
  prevalence <- mean(train$busy)
  rates <- train[, .(score = (sum(busy) + smoothing * prevalence) / (.N + smoothing)), by = segment]
  p <- rates$score[match(test$segment, rates$segment)]
  p[is.na(p)] <- prevalence
  p
}

quota_weights <- function(p, fraction = .25) {
  stopifnot(length(p) > 0L, all(is.finite(p)), all(p >= 0 & p <= 1))
  quota <- ceiling(length(p) * fraction)
  boundary <- sort(p, decreasing = TRUE)[quota]
  above <- p > boundary
  tied <- p == boundary
  w <- as.numeric(above)
  w[tied] <- (quota - sum(above)) / sum(tied)
  stopifnot(abs(sum(w) - quota) < 1e-9, all(w >= 0 & w <= 1))
  w
}

auc <- function(y, p) {
  stopifnot(length(y) == length(p), all(is.finite(p)))
  n1 <- sum(y == 1L); n0 <- sum(y == 0L)
  stopifnot(n1 > 0L, n0 > 0L)
  (sum(rank(p, ties.method = "average")[y == 1L]) - n1 * (n1 + 1) / 2) / (n1 * n0)
}

paired_metrics <- function(y, logistic, baseline, fraction = .25) {
  stopifnot(length(y) == length(logistic), length(y) == length(baseline))
  wl <- quota_weights(logistic, fraction); wb <- quota_weights(baseline, fraction)
  pl <- sum(wl * y) / sum(wl); pb <- sum(wb * y) / sum(wb)
  al <- auc(y, logistic); ab <- auc(y, baseline)
  bl <- mean((y - logistic)^2); bb <- mean((y - baseline)^2)
  data.table(quota = ceiling(length(y) * fraction),
             logistic_precision = pl, segment_precision = pb, precision_difference_pp = 100 * (pl - pb),
             logistic_auc = al, segment_auc = ab, auc_difference = al - ab,
             logistic_brier = bl, segment_brier = bb, brier_difference = bl - bb,
             logistic_expected_positive = sum(wl * y), segment_expected_positive = sum(wb * y))
}
