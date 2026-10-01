# CMCE30005: one simple, explainable model for the final presentation and report.
# Run from the repository root after scripts 01 and rq_scope_feasibility.py.
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

dir.create("reports/tables", showWarnings = FALSE, recursive = TRUE)
cfg <- fromJSON("config/review_analysis.json")
SEED <- as.integer(cfg$seed)
REPEATS <- 50L
TEST_SHARE <- 0.3
AREAS <- c("Melbourne", "Yarra", "Yarra Ranges", "Port Phillip", "Stonnington", "Merri-bek")

# Same exact-integer expansion as scripts/08_peer_ranking.R: a few raw listing
# identifiers are stored in scientific notation.
canonical_id <- function(s) {
  if (is.na(s) || !nzchar(trimws(s))) stop("Missing identifier")
  s <- trimws(s)
  pieces <- strsplit(tolower(s), "e", fixed = TRUE)[[1]]
  if (length(pieces) > 2L) stop("Invalid identifier: ", s)
  exponent <- if (length(pieces) == 2L) as.integer(pieces[2]) else 0L
  if (is.na(exponent) || abs(exponent) > 100L) stop("Invalid identifier exponent")
  mantissa <- sub("^\\+", "", pieces[1])
  if (!grepl("^[0-9]+(\\.[0-9]*)?$", mantissa)) stop("Invalid identifier: ", s)
  decimal <- strsplit(mantissa, ".", fixed = TRUE)[[1]]
  fraction <- if (length(decimal) == 2L) decimal[2] else ""
  digits <- paste0(decimal[1], fraction)
  end <- nchar(decimal[1]) + exponent
  if (end <= 0L) {
    if (grepl("[1-9]", digits)) stop("Non-integer identifier")
    answer <- "0"
  } else if (end < nchar(digits)) {
    if (grepl("[1-9]", substring(digits, end + 1L))) stop("Non-integer identifier")
    answer <- substr(digits, 1L, end)
  } else {
    answer <- paste0(digits, strrep("0", end - nchar(digits)))
  }
  answer <- sub("^0+", "", answer)
  if (!nzchar(answer)) "0" else answer
}

# Probability that a random busy listing scores above a random quiet one.
auc <- function(y, p) {
  r <- rank(p)
  n1 <- sum(y == 1L)
  n0 <- sum(y == 0L)
  (sum(r[y == 1L]) - n1 * (n1 + 1) / 2) / (n1 * n0)
}

# ---- Data -------------------------------------------------------------------
manifest <- fread("data/processed/rq_analysis_main_manifest.csv",
                  colClasses = c(id = "character", host_id = "character"))
stopifnot(all(manifest$host_role == "analysis"), !anyDuplicated(manifest$id))

listings <- as.data.table(readRDS("data/processed/listings_clean.rds"))
listings[, id := vapply(id, canonical_id, character(1))]
stopifnot(!anyDuplicated(listings$id))
keep <- c("id", "accommodates", "bathrooms_num", "n_amenities", "price_num",
          "minimum_nights", "estimated_revenue_l365d", "estimated_occupancy_l365d")
d <- merge(manifest, listings[, ..keep], by = "id", all.x = TRUE, sort = FALSE)
stopifnot(nrow(d) == nrow(manifest), !anyNA(d$price_num), !anyNA(d$n_amenities),
          !anyNA(d$estimated_revenue_l365d))

d[, `:=`(estimated_revenue_l365d = as.numeric(estimated_revenue_l365d),
         estimated_occupancy_l365d = as.numeric(estimated_occupancy_l365d))]
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
fwrite(coef_table, "reports/tables/final_logit_coefficients.csv")

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
fwrite(scen_out, "reports/tables/final_logit_scenarios.csv")

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

cutoff <- quantile(oof$p, 0.75, type = 7)
oof[, flagged := as.integer(p >= cutoff)]
tp <- oof[flagged == 1L & busy == 1L, .N]
fp <- oof[flagged == 1L & busy == 0L, .N]
fn <- oof[flagged == 0L & busy == 1L, .N]
tn <- oof[flagged == 0L & busy == 0L, .N]
fold_auc <- oof[, .(auc = auc(busy, p), auc_location_only = auc(busy, p_location_only)), by = fold]
oof_metrics <- data.table(
  metric = c("listings", "hosts", "busy_share",
             "auc_full_model", "auc_location_and_size_only",
             "folds_where_full_beats_location_only",
             "flag_rule", "flagged_listings", "flagged_and_busy", "flagged_not_busy",
             "not_flagged_but_busy", "not_flagged_not_busy",
             "hit_rate_in_flagged_top_quarter", "share_of_busy_caught",
             "hit_rate_top_quarter_location_only"),
  value = c(nrow(oof), uniqueN(oof$host_id), mean(oof$busy),
            auc(oof$busy, oof$p), auc(oof$busy, oof$p_location_only),
            fold_auc[, sum(auc > auc_location_only)],
            NA, tp + fp, tp, fp, fn, tn,
            tp / (tp + fp), tp / (tp + fn),
            oof[p_location_only >= quantile(p_location_only, 0.75, type = 7), mean(busy)]),
  note = c("", "", "Share with 30+ reviews in 365 days", "Pooled out-of-fold, five host-grouped folds",
           "Area, dwelling type and bedrooms only", "Per-fold AUC comparison",
           "Top quarter of out-of-fold predicted chances", "", "", "", "", "",
           "Precision", "Recall", "")
)
oof_metrics[metric == "flag_rule", value := 0.75]
fwrite(oof_metrics, "reports/tables/final_logit_test_metrics.csv")
fwrite(fold_auc, "reports/tables/final_logit_fold_auc.csv")

# 50 random 70/30 splits by host.
hosts <- sort(unique(d$host_id))
rep_rows <- rbindlist(lapply(seq_len(REPEATS), function(i) {
  set.seed(SEED + i)
  test_hosts <- sample(hosts, round(TEST_SHARE * length(hosts)))
  pr <- fit_predict(FORMULA, d[!host_id %in% test_hosts], d[host_id %in% test_hosts])
  top <- pr[p >= quantile(p, 0.75, type = 7)]
  data.table(split = i, test_listings = nrow(pr), auc = auc(pr$busy, pr$p),
             hit_rate_top_quarter = mean(top$busy), test_busy_share = mean(pr$busy))
}))
fwrite(rep_rows, "reports/tables/final_logit_repeated_splits.csv")
rep_summary <- rep_rows[, .(
  metric = c("auc", "hit_rate_top_quarter", "test_busy_share"),
  mean = c(mean(auc), mean(hit_rate_top_quarter), mean(test_busy_share)),
  p05 = c(quantile(auc, 0.05), quantile(hit_rate_top_quarter, 0.05), quantile(test_busy_share, 0.05)),
  p95 = c(quantile(auc, 0.95), quantile(hit_rate_top_quarter, 0.95), quantile(test_busy_share, 0.95)),
  splits = .N)]
fwrite(rep_summary, "reports/tables/final_logit_repeated_splits_summary.csv")

# ---- Descriptive tables used on the slides --------------------------------------
# Inside Airbnb's estimated revenue is price x estimated nights, and estimated
# nights are built from review counts, so these figures translate review activity
# into dollars; they are not independent evidence or actual income.
seg <- d[, .(listings = .N, hosts = uniqueN(host_id), busy_listings = sum(busy),
             busy_share = mean(busy),
             median_price = median(price_num),
             median_est_revenue = median(estimated_revenue_l365d),
             median_est_revenue_busy = median(estimated_revenue_l365d[busy == 1L]),
             median_est_nights = median(estimated_occupancy_l365d)),
         by = .(lga = neighbourhood_cleansed, configuration)]
seg[, rank_busy_share := frank(-busy_share, ties.method = "min")]
seg[, rank_median_revenue := frank(-median_est_revenue, ties.method = "min")]
setorder(seg, rank_busy_share)
ladder <- fread("reports/tables/segment_ladder.csv")
ladder[, configuration := paste0(bedrooms, "BR ", dwelling_class)]
chk <- merge(seg, ladder[, .(lga, configuration, n_listings, observed_target_rate, ci90_lo, ci90_hi)],
             by = c("lga", "configuration"))
stopifnot(nrow(chk) == nrow(seg), all(chk$listings == chk$n_listings),
          all(abs(chk$busy_share - chk$observed_target_rate) < 1e-12))
seg <- merge(seg, ladder[, .(lga, configuration, busy_share_ci90_lo = ci90_lo, busy_share_ci90_hi = ci90_hi)],
             by = c("lga", "configuration"), sort = FALSE)
setorder(seg, rank_busy_share)
fwrite(seg, "reports/tables/final_segment_summary.csv")

by_busy <- d[, .(listings = .N, median_est_revenue = median(estimated_revenue_l365d),
                 median_est_nights = median(estimated_occupancy_l365d),
                 median_price = median(price_num)), by = .(busy)]
setorder(by_busy, -busy)
by_busy <- rbind(by_busy, d[, .(busy = NA_integer_, listings = .N,
                                median_est_revenue = median(estimated_revenue_l365d),
                                median_est_nights = median(estimated_occupancy_l365d),
                                median_price = median(price_num))])
fwrite(by_busy, "reports/tables/final_revenue_by_busy.csv")

full[, price_position := cut(price_vs_similar_10 * 10, c(-Inf, -20, -5, 5, 20, Inf),
                             labels = c("More than 20% below", "5-20% below", "Within 5%",
                                        "5-20% above", "More than 20% above"))]
price_pos <- full[, .(listings = .N, busy_share = mean(busy),
                      median_est_revenue = median(estimated_revenue_l365d)),
                  by = price_position][order(price_position)]
fwrite(price_pos, "reports/tables/final_price_position_revenue.csv")

min_stay_tab <- d[, .(listings = .N, busy_listings = sum(busy), busy_share = mean(busy)), by = min_stay][order(min_stay)]
fwrite(min_stay_tab, "reports/tables/final_min_stay_summary.csv")

cat("Final logistic model\n")
print(coef_table[, .(plain_label, odds_ratio = round(odds_ratio, 3),
                     lo = round(or_ci95_lo, 3), hi = round(or_ci95_hi, 3), p = signif(p_value, 2))])
print(oof_metrics)
print(rep_summary)
print(scen_out[, .(scenario, chance = round(predicted_chance_busy, 3), lo = round(ci95_lo, 3), hi = round(ci95_hi, 3))])
print(seg)
print(by_busy)
print(price_pos)
print(min_stay_tab)
