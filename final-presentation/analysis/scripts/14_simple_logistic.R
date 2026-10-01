# CMCE30005: one simple, explainable model for the final presentation and report.
# Run from this analysis package root. Inputs are frozen processed school data.
# This is retrospective classification, not a prospective forecast or causal model.
#
# Outcome (Y): busy = 1 when a listing received 30 or more guest reviews in the
#   365 days before collection (review_target_met in the analysis manifest), else 0.
# Predictors (X): council area, apartment or house, bedrooms, nightly price compared
#   with similar listings (same area, dwelling type and bedrooms), whether the
#   listing accepts 1-night stays, and amenity count.
# Model: logistic regression (base R glm). Host-clustered standard errors because
#   one host can run many similar listings.
# Testing: the manifest's five host-grouped folds (each listing is predicted by a
#   model that never saw its host), plus 50 random 70/30 host splits.
# All associations are descriptive; they do not show that changing a setting
# causes a listing to become busy.

library(data.table)
library(jsonlite)
library(sandwich)

dir.create("outputs", showWarnings = FALSE, recursive = TRUE)
dir.create("working", showWarnings = FALSE, recursive = TRUE)
cfg <- fromJSON("config/review_analysis.json")
SEED <- as.integer(cfg$seed)
REPEATS <- 50L
TEST_SHARE <- 0.3
AREAS <- c("Melbourne", "Yarra", "Yarra Ranges", "Port Phillip", "Stonnington", "Merri-bek")

# Probability that a random busy listing scores above a random quiet one.
auc <- function(y, p) {
  r <- rank(p)
  n1 <- sum(y == 1L)
  n0 <- sum(y == 0L)
  (sum(r[y == 1L]) - n1 * (n1 + 1) / 2) / (n1 * n0)
}

# ---- Data -------------------------------------------------------------------
d <- fread("private-inputs/analysis_input.csv",
           colClasses = c(id = "character", host_id = "character"))
stopifnot(all(d$host_role == "analysis"), !anyDuplicated(d$id),
          !anyNA(d$price_num), !anyNA(d$n_amenities),
          all(d[, uniqueN(fold), by = host_id]$V1 == 1L))

d[, busy := as.integer(review_target_met)]
stopifnot(all(d$busy == as.integer(d$reviews_365d >= d$common_review_threshold)))
d[, area := factor(neighbourhood_cleansed, levels = AREAS)]
stopifnot(!anyNA(d$area))
d[, dwelling := factor(ifelse(grepl("House", configuration), "House/townhouse", "Apartment/unit"),
                       levels = c("Apartment/unit", "House/townhouse"))]
d[, bedrooms := factor(substr(configuration, 1L, 1L), levels = c("1", "2", "3"))]
d[, segment := paste(neighbourhood_cleansed, configuration)]
# Three listings have no minimum stay; they take the most common setting.
d[, min_stay := fifelse(is.na(minimum_nights), "2-6 nights",
                 fifelse(minimum_nights <= 1, "1 night",
                 fifelse(minimum_nights <= 6, "2-6 nights", "7+ nights")))]
d[, min_stay := factor(min_stay, levels = c("1 night", "2-6 nights", "7+ nights"))]
# No listing with a 7+ night minimum is busy, so a three-level setting would be
# perfectly separated; the model uses one yes/no setting instead.
d[, one_night := factor(fifelse(min_stay == "1 night", "Yes", "No"), levels = c("No", "Yes"))]
d[, amenities_10 := n_amenities / 10]

# Price compared with similar listings: percent above (+) or below (-) the median
# price of the same segment, measured in steps of 10 points. Medians come only
# from the listings used to fit the model.
add_price_position <- function(target, reference) {
  med <- reference[, .(segment_median_price = median(price_num)), by = segment]
  out <- merge(target, med, by = "segment", all.x = TRUE, sort = FALSE)
  out[, price_vs_similar_10 := (price_num / segment_median_price - 1) * 10]
  out
}

FORMULA <- busy ~ area + dwelling + bedrooms + price_vs_similar_10 + one_night + amenities_10
LOCATION_ONLY <- busy ~ area + dwelling + bedrooms

# ---- Final model on all analysis listings -------------------------------------
full <- add_price_position(d, d)
fit <- glm(FORMULA, family = binomial(), data = full)
vc <- vcovCL(fit, cluster = ~host_id)
se <- sqrt(diag(vc))
est <- coef(fit)
labels <- c(
  "(Intercept)" = "Baseline odds (Melbourne 1BR apartment, typical price, minimum stay 2+ nights, 0 amenities)",
  "areaYarra" = "Area: Yarra (vs Melbourne)",
  "areaYarra Ranges" = "Area: Yarra Ranges (vs Melbourne)",
  "areaPort Phillip" = "Area: Port Phillip (vs Melbourne)",
  "areaStonnington" = "Area: Stonnington (vs Melbourne)",
  "areaMerri-bek" = "Area: Merri-bek (vs Melbourne)",
  "dwellingHouse/townhouse" = "House or townhouse (vs apartment)",
  "bedrooms2" = "2 bedrooms (vs 1)",
  "bedrooms3" = "3 bedrooms (vs 1)",
  "price_vs_similar_10" = "Each 10% priced above similar listings",
  "one_nightYes" = "Accepts 1-night stays (vs minimum of 2+ nights)",
  "amenities_10" = "Each 10 extra listed amenities"
)
coef_table <- data.table(
  term = names(est),
  plain_label = unname(labels[names(est)]),
  coefficient = unname(est),
  odds_ratio = exp(unname(est)),
  or_ci95_lo = exp(unname(est - 1.96 * se)),
  or_ci95_hi = exp(unname(est + 1.96 * se)),
  p_value = unname(2 * pnorm(-abs(est / se))),
  se_method = "Host-clustered (sandwich::vcovCL)"
)
stopifnot(!anyNA(coef_table$plain_label))
fwrite(coef_table, "outputs/final_logit_coefficients.csv")

# ---- What changes the chance: one setting at a time ----------------------------
typical <- data.table(
  area = factor("Melbourne", levels = AREAS),
  dwelling = factor("Apartment/unit", levels = levels(d$dwelling)),
  bedrooms = factor("2", levels = c("1", "2", "3")),
  price_vs_similar_10 = 0,
  one_night = factor("Yes", levels = levels(d$one_night)),
  amenities_10 = median(d$n_amenities) / 10
)
scenario <- function(label, ...) {
  row <- copy(typical)
  changes <- list(...)
  for (nm in names(changes)) {
    value <- changes[[nm]]
    if (is.factor(row[[nm]])) value <- factor(value, levels = levels(row[[nm]]))
    set(row, j = nm, value = value)
  }
  row[, scenario := label]
  row
}
scen <- rbindlist(list(
  scenario("Example listing: Melbourne 2BR apartment, priced like similar listings, accepts 1-night stays, median amenities"),
  scenario("Requires a minimum of 2+ nights", one_night = "No"),
  scenario("Priced 20% above similar listings", price_vs_similar_10 = 2),
  scenario("Priced 20% below similar listings", price_vs_similar_10 = -2),
  scenario("10 more amenities", amenities_10 = typical$amenities_10 + 1),
  scenario("10 fewer amenities", amenities_10 = typical$amenities_10 - 1),
  scenario("3 bedrooms instead of 2", bedrooms = "3"),
  scenario("1 bedroom instead of 2", bedrooms = "1"),
  scenario("Same apartment in Yarra", area = "Yarra"),
  scenario("Same apartment in Port Phillip", area = "Port Phillip"),
  scenario("Same apartment in Stonnington", area = "Stonnington")
))
X <- model.matrix(delete.response(terms(fit)), scen, xlev = fit$xlevels)
link <- drop(X %*% est)
link_se <- sqrt(rowSums((X %*% vc) * X))
scen_out <- data.table(
  scenario = scen$scenario,
  predicted_chance_busy = plogis(link),
  ci95_lo = plogis(link - 1.96 * link_se),
  ci95_hi = plogis(link + 1.96 * link_se),
  typical_amenities = median(d$n_amenities),
  note = "Model-based chance for one hypothetical listing; host-clustered 95% interval"
)
fwrite(scen_out, "outputs/final_logit_scenarios.csv")

# ---- Test on hosts the model never saw -----------------------------------------
fit_predict <- function(formula, train, test) {
  tr <- add_price_position(train, train)
  te <- add_price_position(test, train)
  m <- glm(formula, family = binomial(), data = tr)
  te[, p := predict(m, newdata = te, type = "response")]
  te[, .(id, host_id, segment, busy, p)]
}
oof <- rbindlist(lapply(sort(unique(d$fold)), function(k) {
  full_p <- fit_predict(FORMULA, d[fold != k], d[fold == k])
  loc_p <- fit_predict(LOCATION_ONLY, d[fold != k], d[fold == k])
  full_p[, `:=`(fold = k, p_location_only = loc_p$p[match(full_p$id, loc_p$id)])]
}))
stopifnot(nrow(oof) == nrow(d), !anyNA(oof$p), !anyNA(oof$p_location_only))

# Separate comparator: smoothed SEGMENT MEAN, not the additive location model.
# Each training-fold segment gets (positives + 10 * training prevalence)/(n + 10).
# Fixed smoothing weight matches the original project baseline; it is not tuned.
oof[, p_segment_mean := NA_real_]
for (k in sort(unique(d$fold))) {
  tr <- d[fold != k]
  te <- d[fold == k]
  stopifnot(!length(intersect(tr$host_id, te$host_id)))
  rates <- tr[, .(p = (sum(busy) + 10 * mean(tr$busy)) / (.N + 10)), by = segment]
  te[, p_base := rates$p[match(segment, rates$segment)]]
  te[is.na(p_base), p_base := mean(tr$busy)]
  oof[fold == k, p_segment_mean := te$p_base[match(id, te$id)]]
}
stopifnot(!anyNA(oof$p_segment_mean))

# Fair screening quota: exactly ceil(n/4) selections in expectation for EVERY
# score. Share the remaining quota uniformly across listings tied at the boundary.
# Weights use only scores, never outcomes. The simple model has no boundary tie.
quota_weights <- function(p, fraction = .25) {
  k <- ceiling(length(p) * fraction)
  boundary <- sort(p, decreasing = TRUE)[k]
  above <- p > boundary
  tied <- p == boundary
  weight <- as.numeric(above)
  weight[tied] <- (k - sum(above)) / sum(tied)
  stopifnot(abs(sum(weight) - k) < 1e-10, all(weight >= 0 & weight <= 1))
  weight
}
metrics_for <- function(label, p) {
  w <- quota_weights(p)
  data.table(model = label, listings = nrow(oof), hosts = uniqueN(oof$host_id),
    roc_auc = auc(oof$busy, p), brier_score = mean((oof$busy - p)^2),
    observed_target_share = mean(oof$busy),
    expected_top_quarter_n = sum(w),
    expected_true_positives_top_quarter = sum(w * oof$busy),
    precision_top_quarter = sum(w * oof$busy) / sum(w),
    recall_top_quarter = sum(w * oof$busy) / sum(oof$busy),
    quota_method = "Exactly ceil(n/4) in expectation; fractional weight at tied boundary")
}
comparison <- rbindlist(list(
  metrics_for("simple_logistic", oof$p),
  metrics_for("segment_mean", oof$p_segment_mean),
  metrics_for("location_type_bedrooms_logistic", oof$p_location_only)
))
fwrite(comparison, "outputs/model_comparison.csv")

w <- quota_weights(oof$p)
stopifnot(all(w %in% c(0, 1)))
oof[, flagged := as.integer(w)]
tp <- oof[flagged == 1L & busy == 1L, .N]
fp <- oof[flagged == 1L & busy == 0L, .N]
fn <- oof[flagged == 0L & busy == 1L, .N]
tn <- oof[flagged == 0L & busy == 0L, .N]
confusion <- data.table(true_positives = tp, false_positives = fp,
  false_negatives = fn, true_negatives = tn,
  accuracy = (tp + tn) / nrow(oof), all_negative_accuracy = mean(oof$busy == 0L))
fwrite(confusion, "outputs/test_confusion.csv")
fold_metrics <- oof[, .(listings = .N, hosts = uniqueN(host_id),
  observed_target_share = mean(busy), auc_simple_logistic = auc(busy, p),
  auc_segment_mean = auc(busy, p_segment_mean),
  auc_location_type_bedrooms_logistic = auc(busy, p_location_only)), by = fold]
fwrite(fold_metrics, "outputs/fold_metrics.csv")
calibration <- oof[, .(listings = .N, mean_predicted = mean(p), observed_share = mean(busy)),
  by = .(probability_bin = cut(p, c(0,.1,.2,.3,.4,.5,.6,1), include.lowest=TRUE))]
setorder(calibration, probability_bin)
fwrite(calibration, "outputs/calibration.csv")
# This file is working material with listing/host identifiers. Do not publish.
fwrite(oof, "working/oof_predictions_PRIVATE.csv")

# 50 random 70/30 splits by host.
hosts <- sort(unique(d$host_id))
rep_rows <- rbindlist(lapply(seq_len(REPEATS), function(i) {
  set.seed(SEED + i)
  test_hosts <- sample(hosts, round(TEST_SHARE * length(hosts)))
  pr <- fit_predict(FORMULA, d[!host_id %in% test_hosts], d[host_id %in% test_hosts])
  top_weights <- quota_weights(pr$p)
  data.table(split = i, test_listings = nrow(pr), auc = auc(pr$busy, pr$p),
             hit_rate_top_quarter = sum(top_weights * pr$busy) / sum(top_weights), test_busy_share = mean(pr$busy))
}))
fwrite(rep_rows, "outputs/final_logit_repeated_splits.csv")
rep_summary <- rep_rows[, .(
  metric = c("auc", "hit_rate_top_quarter", "test_busy_share"),
  mean = c(mean(auc), mean(hit_rate_top_quarter), mean(test_busy_share)),
  p05 = c(quantile(auc, 0.05), quantile(hit_rate_top_quarter, 0.05), quantile(test_busy_share, 0.05)),
  p95 = c(quantile(auc, 0.95), quantile(hit_rate_top_quarter, 0.95), quantile(test_busy_share, 0.95)),
  splits = .N)]
fwrite(rep_summary, "outputs/final_logit_repeated_splits_summary.csv")

# ---- Observed segment rates: separate descriptive analysis, not model ranking.
seg <- d[, .(listings = .N, hosts = uniqueN(host_id), busy_listings = sum(busy),
             busy_share = mean(busy)), by = .(lga = neighbourhood_cleansed, configuration)]
seg[, rank_busy_share := frank(-busy_share, ties.method = "min")]
ladder <- fread("reference/segment_ladder.csv")
ladder[, configuration := paste0(bedrooms, "BR ", dwelling_class)]
chk <- merge(seg, ladder[, .(lga, configuration, n_listings, observed_target_rate)],
             by = c("lga", "configuration"))
stopifnot(nrow(chk) == nrow(seg), all(chk$listings == chk$n_listings),
          all(abs(chk$busy_share - chk$observed_target_rate) < 1e-12))
seg <- merge(seg, ladder[, .(lga, configuration, busy_share_ci90_lo = ci90_lo,
                 busy_share_ci90_hi = ci90_hi)], by = c("lga", "configuration"), sort = FALSE)
setorder(seg, rank_busy_share)
fwrite(seg, "outputs/descriptive_segments.csv")
min_stay_tab <- d[, .(listings = .N, busy_listings = sum(busy), busy_share = mean(busy)),
                  by = min_stay][order(min_stay)]
fwrite(min_stay_tab, "outputs/minimum_stay_descriptive.csv")
capture.output(sessionInfo(), file="logs/R_session_info.txt")
cat("Retrospective logistic classification: validation complete\n")
print(comparison)
print(confusion)
print(fold_metrics)
print(rep_summary)
print(scen_out[, .(scenario, predicted_chance_busy, ci95_lo, ci95_hi)])
