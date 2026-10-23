# CMCE30005 Group 2: checks added after the final-presentation feedback (23 October 2026).
#   1. Guest ratings of busy homes and the rest (review counts say nothing about
#      whether guests were satisfied).
#   2. A two-setting rule in the priority groups (does a simple summary of one-night
#      stays and price do as well as the model?).
# Run from the repository root:
#   Rscript final-report/report-2026-10-04/scripts/feedback_checks.R
# Private inputs (not published): final-report/report-2026-10-04/private-inputs/analysis_input.csv
# and data/raw/listings_airbnb.csv (the LMS snapshot).
# Writes two aggregate tables (no listing or host identifiers) to
# final-report/report-2026-10-04/outputs/revision/: rating_check.csv and two_setting_rule.csv.
# review_scores_rating is the listing's average overall guest rating (1-5 stars)
# over its whole history, as published by Inside Airbnb.

library(data.table)

PKG <- "final-report/report-2026-10-04"
OUT <- file.path(PKG, "outputs/revision")
PRIORITY <- c("Melbourne 2BR Apartment/unit", "Melbourne 3BR Apartment/unit",
              "Yarra Ranges 3BR House/townhouse")

original <- readLines("final-presentation/analysis/reference/14_simple_logistic_original.R")
start <- grep("^canonical_id <- function", original)
end <- grep("^# Probability", original) - 1L
eval(parse(text = original[start:end]))

d <- fread(file.path(PKG, "private-inputs/analysis_input.csv"),
           colClasses = c(id = "character", host_id = "character"))
stopifnot(nrow(d) == 3873L, all(d$host_role == "analysis"))
d[, busy := review_target_met == 1L]
d[, group := paste(neighbourhood_cleansed, configuration)]

raw <- fread("data/raw/listings_airbnb.csv", select = c("id", "review_scores_rating"),
             colClasses = c(id = "character"), na.strings = c("NA", "", "N/A"))
raw[, id := vapply(id, canonical_id, character(1))]
stopifnot(!anyDuplicated(raw$id))
d <- merge(d, raw, by = "id", all.x = TRUE, sort = FALSE)
stopifnot(nrow(d) == 3873L)

summarise <- function(x) x[, .(homes = .N, rated = sum(!is.na(review_scores_rating)),
                               mean_rating = mean(review_scores_rating, na.rm = TRUE),
                               share_4_8_plus = mean(review_scores_rating >= 4.8, na.rm = TRUE),
                               share_below_4_5 = mean(review_scores_rating < 4.5, na.rm = TRUE)),
                           by = .(status = fifelse(busy, "Busy (30+ reviews)", "Below 30"))]
ratings <- rbind(
  cbind(scope = "All 14 groups", summarise(d)),
  cbind(scope = "Three priority groups", summarise(d[group %in% PRIORITY])),
  rbindlist(lapply(PRIORITY, function(g) cbind(scope = g, summarise(d[group == g]))))
)
setorder(ratings, scope, status)
fwrite(ratings, file.path(OUT, "rating_check.csv"))
print(ratings)

# ---- 2. Two-setting rule in the three priority groups --------------------------
# Accepts one-night stays, and nightly price at or below the group's median.
# Checked on the same homes that suggested it; no weights are fitted.
p <- d[group %in% PRIORITY]
stopifnot(!anyNA(p$minimum_nights), !anyNA(p$price_num))
p[, one_night := minimum_nights == 1L]
p[, at_or_below_median := price_num <= median(price_num), by = group]
cells <- p[, .(homes = .N, busy = sum(busy), share_busy = mean(busy)),
           by = .(one_night, at_or_below_median)]
setorder(cells, -one_night, -at_or_below_median)
both <- p[one_night & at_or_below_median]
rule <- data.table(one_night = NA, at_or_below_median = NA,
                   homes = nrow(both), busy = sum(both$busy), share_busy = mean(both$busy),
                   share_of_homes_picked = nrow(both) / nrow(p),
                   share_of_busy_found = sum(both$busy) / sum(p$busy),
                   share_busy_rest = mean(p[!(one_night & at_or_below_median)]$busy))
fwrite(rbind(cells, rule, fill = TRUE), file.path(OUT, "two_setting_rule.csv"))
print(rbind(cells, rule, fill = TRUE))
