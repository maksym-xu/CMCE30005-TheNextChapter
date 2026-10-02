# Small invariant checks for the train/test boundary and fair shortlist quota.
source("scripts/model_helpers.R")
checks <- character()
check <- function(label, condition) {
  stopifnot(isTRUE(condition)); checks <<- c(checks, label)
}
train <- data.table(segment = c("A", "A", "B", "B"),
                    price_num = c(100, 200, 400, 600),
                    one_night_raw = c("Yes", "Yes", "No", NA_character_),
                    busy = c(1L, 0L, 1L, 0L))
prep <- training_preprocessor(train)
check("Training majority Yes overrides the former fixed No fill", prep$fill == "Yes")
tr <- apply_preprocessor(train, prep)
check("Missing training value is imputed without dropping the row", nrow(tr) == 4L && tr$one_night[4] == "Yes")

test <- data.table(segment = c("A", "NEW"), price_num = c(300, 3000),
                   one_night_raw = c(NA_character_, "No"), busy = c(0L, 1L))
te <- apply_preprocessor(test, prep)
check("Known-segment price uses training median", te$training_segment_median_price[1] == 150)
check("Unseen-segment price uses training overall median", te$training_segment_median_price[2] == 300 && te$unseen_segment[2] == 1L)
check("Missing test value receives the training fill", te$one_night[1] == "Yes")

# Reverse held-out outcomes; neither transformed features nor baseline scores may change.
test_flipped <- copy(test); test_flipped[, busy := 1L - busy]
te_flipped <- apply_preprocessor(test_flipped, prep)
check("Held-out labels cannot change preprocessing", identical(te[, !"busy"], te_flipped[, !"busy"]))
check("Held-out labels cannot change the fitted baseline", identical(segment_predict(train, test), segment_predict(train, test_flipped)))
check("Unseen-segment baseline is training prevalence", segment_predict(train, test)[2] == mean(train$busy))

# A different held-out feature distribution must not change the fitted training rule.
different_test <- rbindlist(list(test, data.table(segment = rep("A", 20), price_num = rep(1e9, 20),
  one_night_raw = rep("No", 20), busy = rep(0L, 20))))
apply_preprocessor(different_test, prep)
check("Held-out feature distribution leaves fitted training rules unchanged", identical(prep, training_preprocessor(train)))

tied_train <- copy(train); tied_train[, one_night_raw := c("No", "Yes", NA_character_, NA_character_)]
check("Training mode tie is resolved by fixed No rule", training_preprocessor(tied_train)$fill == "No")
missing_train <- copy(train); missing_train[, one_night_raw := NA_character_]
check("All-missing training values fail instead of reading test data", inherits(try(training_preprocessor(missing_train), silent = TRUE), "try-error"))
check("Outcome columns are rejected by feature-only fitting helper", inherits(try(fit_preprocessor(train), silent = TRUE), "try-error"))

w <- quota_weights(c(.9, .8, .8, .8, .4, .3, .2, .1))
check("Boundary ties preserve exact quota with equal weights", abs(sum(w) - 2) < 1e-12 && all(w[2:4] == 1/3) && w[1] == 1)
perm <- c(4, 1, 3, 6, 7, 8, 2, 5)
check("Boundary-tie selection is invariant to row order", identical(w[perm], quota_weights(c(.9, .8, .8, .8, .4, .3, .2, .1)[perm])))

dir.create("outputs", showWarnings = FALSE)
jsonlite::write_json(list(status = "PASS", checks = checks, count = length(checks)),
                    "outputs/helper_tests.json", pretty = TRUE, auto_unbox = TRUE)
cat(length(checks), "preprocessing and quota invariants passed.\n")
