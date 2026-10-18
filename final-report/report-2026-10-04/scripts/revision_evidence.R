# CMCE30005 Group 2: evidence added in the 16-17 October 2026 report revision.
# Run from the repository root:
#   Rscript final-report/report-2026-10-04/scripts/revision_evidence.R
# Private inputs (not published): final-report/report-2026-10-04/private-inputs/analysis_input.csv
# (same file as the screening and paired packages, SHA-256 bf286ed7...) and
# data/processed/listings_clean.rds from scripts/01_data_cleaning.R.
# Writes aggregate tables only (no listing or host identifiers) to
# final-report/report-2026-10-04/outputs/revision/.
# Associations are descriptive; nothing here estimates a causal effect.

library(data.table)
library(jsonlite)
library(sandwich)

PKG <- "final-report/report-2026-10-04"
OUT <- file.path(PKG, "outputs/revision")
dir.create(OUT, showWarnings = FALSE, recursive = TRUE)
cfg <- fromJSON("config/review_analysis.json")
SEED <- as.integer(cfg$seed)
BOOT <- 1000L
TARGET <- 30L
PRIORITY <- c("Melbourne 2BR Apartment/unit", "Melbourne 3BR Apartment/unit",
              "Yarra Ranges 3BR House/townhouse")
AREAS <- c("Melbourne", "Yarra", "Yarra Ranges", "Port Phillip", "Stonnington", "Merri-bek")

# Exact identifier expansion used by every earlier package (some raw ids are in
# scientific notation).
original <- readLines("final-presentation/analysis/reference/14_simple_logistic_original.R")
start <- grep("^canonical_id <- function", original)
end <- grep("^# Probability", original) - 1L
eval(parse(text = original[start:end]))

# ---- Analysis homes -----------------------------------------------------------
d <- fread(file.path(PKG, "private-inputs/analysis_input.csv"),
           colClasses = c(id = "character", host_id = "character"))
stopifnot(nrow(d) == 3873L, all(d$host_role == "analysis"), !anyDuplicated(d$id))
d[, busy := as.integer(review_target_met)]
stopifnot(all(d$busy == as.integer(d$reviews_365d >= TARGET)))
d[, group := paste(neighbourhood_cleansed, configuration)]

listings <- as.data.table(readRDS("data/processed/listings_clean.rds"))
listings[, id := vapply(id, canonical_id, character(1))]
stopifnot(!anyDuplicated(listings$id))
d <- merge(d, listings[, .(id, est_revenue = as.numeric(estimated_revenue_l365d),
                           est_nights = as.numeric(estimated_occupancy_l365d))],
           by = "id", all.x = TRUE, sort = FALSE)
stopifnot(nrow(d) == 3873L, !anyNA(d$est_revenue), !anyNA(d$est_nights))

# ---- 1. Distribution of annual reviews ---------------------------------------
bands <- c(-Inf, 0, 9, 19, 29, 49, Inf)
labels <- c("0", "1-9", "10-19", "20-29", "30-49", "50+")
d[, review_band := cut(reviews_365d, bands, labels = labels)]
dist <- d[, .(homes = .N), by = review_band][order(review_band)]
dist[, share := homes / sum(homes)]
fwrite(dist, file.path(OUT, "review_distribution.csv"))
q <- quantile(d$reviews_365d, c(0.25, 0.5, 0.75, 0.9), type = 7)
review_summary <- list(homes = nrow(d), zero_reviews = sum(d$reviews_365d == 0),
                       p25 = q[[1]], median = q[[2]], p75 = q[[3]], p90 = q[[4]],
                       max = max(d$reviews_365d), mean = mean(d$reviews_365d),
                       reaching_target = sum(d$busy))
# Histogram counts in 5-review bins (capped at 100+) for the figure.
d[, bin5 := pmin(reviews_365d %/% 5L * 5L, 100L)]
fwrite(d[, .(homes = .N), by = .(bin_start = bin5)][order(bin_start)],
       file.path(OUT, "review_histogram_bins.csv"))

# ---- 2. Homes that reach the target versus the rest --------------------------
profile <- function(x, label) {
  x[, .(homes_label = label, homes = .N,
        median_price_aud = median(price_num),
        median_amenities = median(n_amenities),
        one_night_percent = 100 * mean(minimum_nights[!is.na(minimum_nights)] <= 1),
        min_stay_7plus_percent = 100 * mean(minimum_nights[!is.na(minimum_nights)] >= 7),
        two_or_three_bed_percent = 100 * mean(substr(configuration, 1, 1) %in% c("2", "3")),
        city_of_melbourne_percent = 100 * mean(neighbourhood_cleansed == "Melbourne"),
        median_est_nights = median(est_nights),
        median_est_revenue_aud = median(est_revenue))]
}
target_profile <- rbind(profile(d[busy == 1L], "Reached 30 reviews"),
                        profile(d[busy == 0L], "Below 30 reviews"),
                        profile(d, "All analysis homes"))
fwrite(target_profile, file.path(OUT, "target_profile.csv"))

# Estimated nights at the target for homes with a one- to three-night minimum.
at_target <- d[reviews_365d == TARGET & !is.na(minimum_nights) & minimum_nights <= 3,
               .(homes = .N, min_nights = min(est_nights), max_nights = max(est_nights))]

# ---- 3. Data quality across the whole snapshot --------------------------------
quality <- data.table(
  field = c("price", "bedrooms", "first_review", "review_scores_rating", "minimum_nights"),
  missing = c(sum(is.na(listings$price_num)), sum(is.na(listings$bedrooms)),
              sum(is.na(listings$first_review)), sum(is.na(listings$review_scores_rating)),
              sum(is.na(listings$minimum_nights))))
quality[, share := missing / nrow(listings)]
quality[, listings := nrow(listings)]
fwrite(quality, file.path(OUT, "data_quality.csv"))

# Residential scope: does the price rule remove quiet listings?
prop_map <- unlist(cfg$property_map)
res <- listings[room_type == "Entire home/apt" & bedrooms %in% 1:3 &
                  property_type %in% names(prop_map)]
res[, price_ok := !is.na(price_num) & price_num >= cfg$minimum_price & price_num <= cfg$maximum_price]
price_check <- res[, .(listings = .N, zero_recent_review_percent = 100 * mean(number_of_reviews_ltm == 0)),
                   by = .(price_rule = fifelse(price_ok, "Kept by price rule", "Removed by price rule"))]
fwrite(price_check, file.path(OUT, "residential_price_check.csv"))

# ---- 4. Estimated nights and revenue by group (all homes and below target) ----
group_money <- d[, .(homes = .N, target_share = mean(busy),
                     median_est_nights = median(est_nights),
                     median_est_revenue_aud = median(est_revenue),
                     median_est_revenue_reached_aud = median(est_revenue[busy == 1L]),
                     median_est_nights_below_target = median(est_nights[busy == 0L]),
                     median_est_revenue_below_target_aud = median(est_revenue[busy == 0L])),
                 by = group][order(-target_share)]
group_money[, median_weekly_aud := median_est_revenue_aud / 52]
group_money[, median_weekly_below_target_aud := median_est_revenue_below_target_aud / 52]
group_money[, rank_target_share := frank(-target_share, ties.method = "min")]
group_money[, rank_median_revenue := frank(-median_est_revenue_aud, ties.method = "min")]
group_money[, priority := group %in% PRIORITY]
fwrite(group_money, file.path(OUT, "group_estimated_revenue.csv"))

# Share of each priority group's homes whose estimated weekly revenue reached a given weekly cost.
cost_grid <- seq(0, 2000, by = 10)
weekly_curve <- d[group %in% PRIORITY,
                  .(weekly_cost_aud = cost_grid,
                    share_reaching = vapply(cost_grid, function(x) mean(est_revenue / 52 >= x), numeric(1))),
                  by = group]
fwrite(weekly_curve, file.path(OUT, "weekly_revenue_reach.csv"))

# ---- 5. Model assumptions (full-sample fit of the six-input model) ------------
d[, area := factor(neighbourhood_cleansed, levels = AREAS)]
d[, dwelling := factor(ifelse(grepl("House", configuration), "House/townhouse", "Apartment/unit"),
                       levels = c("Apartment/unit", "House/townhouse"))]
d[, bedrooms := factor(substr(configuration, 1L, 1L), levels = c("1", "2", "3"))]
mode_stay <- d[!is.na(minimum_nights), names(which.max(table(minimum_nights <= 1)))]
d[, one_night := factor(fifelse(is.na(minimum_nights), mode_stay == "TRUE", minimum_nights <= 1),
                        levels = c(FALSE, TRUE), labels = c("No", "Yes"))]
d[, amenities_10 := n_amenities / 10]
med <- d[, .(seg_median = median(price_num)), by = group]
d <- merge(d, med, by = "group", sort = FALSE)
d[, price_vs_similar_10 := (price_num / seg_median - 1) * 10]
f_main <- busy ~ area + dwelling + bedrooms + price_vs_similar_10 + one_night + amenities_10
fit <- glm(f_main, family = binomial(), data = d)

# Generalised variance inflation factor, computed from the model matrix.
gvif <- function(model) {
  X <- model.matrix(model)[, -1, drop = FALSE]
  assign <- attr(model.matrix(model), "assign")[-1]
  terms <- attr(terms(model), "term.labels")
  R <- cor(X)
  detR <- det(R)
  rbindlist(lapply(seq_along(terms), function(j) {
    idx <- which(assign == j)
    g <- det(R[idx, idx, drop = FALSE]) * det(R[-idx, -idx, drop = FALSE]) / detR
    data.table(term = terms[j], df = length(idx), gvif = g,
               gvif_adjusted = g^(1 / (2 * length(idx))))
  }))
}
vif_table <- gvif(fit)
fwrite(vif_table, file.path(OUT, "model_gvif.csv"))

# Linearity in the log-odds: add squared terms and compare.
fit_sq <- update(fit, . ~ . + I(price_vs_similar_10^2) + I(amenities_10^2))
lr <- anova(fit, fit_sq, test = "LRT")
# The same squared terms with host-clustered standard errors.
vc_sq <- vcovCL(fit_sq, cluster = ~host_id)
sq_terms <- c("I(price_vs_similar_10^2)", "I(amenities_10^2)")
sq_clustered <- data.table(term = sq_terms, coefficient = coef(fit_sq)[sq_terms],
                           se_host_clustered = sqrt(diag(vc_sq))[sq_terms])
sq_clustered[, p_value_host_clustered := 2 * pnorm(-abs(coefficient / se_host_clustered))]
fwrite(sq_clustered, file.path(OUT, "model_linearity_check.csv"))
# Host clustering: compare ordinary and host-clustered standard errors.
se_ord <- sqrt(diag(vcov(fit)))
se_cl <- sqrt(diag(vcovCL(fit, cluster = ~host_id)))
se_ratio <- data.table(term = names(se_ord), se_ordinary = se_ord, se_host_clustered = se_cl,
                       ratio = se_cl / se_ord)
fwrite(se_ratio, file.path(OUT, "model_se_ratio.csv"))
# Separation check that motivated the yes/no one-night input.
stay_check <- d[!is.na(minimum_nights), .(homes = .N, reaching_target = sum(busy)),
                by = .(minimum_stay = fifelse(minimum_nights <= 1, "1 night",
                                       fifelse(minimum_nights <= 6, "2-6 nights", "7+ nights")))]
fwrite(stay_check[order(minimum_stay)], file.path(OUT, "minimum_stay_check.csv"))

# ---- 6. How often do the same three groups lead? (host bootstrap) -------------
set.seed(SEED)
hosts <- sort(unique(d$host_id))
by_host <- split(d[, .(group, busy)], d$host_id)
top3_hits <- integer(BOOT)
in_top3 <- setNames(numeric(uniqueN(d$group)), sort(unique(d$group)))
for (b in seq_len(BOOT)) {
  draw <- rbindlist(by_host[sample(hosts, length(hosts), replace = TRUE)])
  rates <- draw[, .(rate = mean(busy), n = .N), by = group]
  setorder(rates, -rate, -n)
  top <- rates$group[1:3]
  top3_hits[b] <- as.integer(setequal(top, PRIORITY))
  in_top3[top] <- in_top3[top] + 1
}
top3 <- data.table(group = names(in_top3), share_in_top3 = as.numeric(in_top3) / BOOT)[order(-share_in_top3)]
fwrite(top3, file.path(OUT, "top3_resample_shares.csv"))

summary <- list(
  date = "2026-10-16",
  scope = "Aggregate evidence for the 16 Oct 2026 revision; analysis homes = 3,873 (1,726 hosts).",
  review_distribution = review_summary,
  nights_at_30_reviews = at_target,
  model_assumptions = list(
    max_gvif_adjusted = max(vif_table$gvif_adjusted),
    squared_terms_lr_test = list(chisq = lr$Deviance[2], df = lr$Df[2], p_value = lr$`Pr(>Chi)`[2]),
    squared_terms_coefficients = coef(summary(fit_sq))[c("I(price_vs_similar_10^2)", "I(amenities_10^2)"), ],
    squared_terms_host_clustered_p = setNames(sq_clustered$p_value_host_clustered, sq_terms),
    se_ratio_range = range(se_ratio$ratio[-1])),
  same_top3_share = mean(top3_hits),
  bootstrap = list(draws = BOOT, seed = SEED, unit = "analysis hosts, with replacement",
                   tie_rule = "rank by rate, then by number of homes")
)
write_json(summary, file.path(OUT, "revision_summary.json"), auto_unbox = TRUE, pretty = TRUE, digits = 8)

cat("Review distribution:\n"); print(dist); print(unlist(review_summary))
cat("\nTarget profile:\n"); print(target_profile)
cat("\nNights at exactly 30 reviews (min stay <= 3):\n"); print(at_target)
cat("\nData quality:\n"); print(quality)
cat("\nResidential price check:\n"); print(price_check)
cat("\nGroup money:\n"); print(group_money)
cat("\nGVIF:\n"); print(vif_table); print(lr); print(se_ratio)
cat("\nMinimum stay:\n"); print(stay_check)
cat("\nSame top three share:", mean(top3_hits), "\n"); print(top3)

# ---- 7. All model terms across the 50 repeated training fits (Appendix A) -----
coefs <- fread("final-report/screening-followup-2026-10-03/reference/prior_full_coefficients.csv")
coefs <- coefs[design == "repeated_host_split"]
stopifnot(uniqueN(coefs$split) == 50L)
term_summary <- coefs[, .(mean_coefficient = mean(coefficient),
                          odds_ratio = exp(mean(coefficient)),
                          odds_ratio_min = exp(min(coefficient)),
                          odds_ratio_max = exp(max(coefficient)),
                          same_sign_fits = max(sum(coefficient > 0), sum(coefficient < 0))),
                      by = term]
fwrite(term_summary, file.path(OUT, "all_term_odds_ratios.csv"))
cat("\nAll terms across 50 fits:\n"); print(term_summary)
