# Two targeted directional findings selected after the main model analysis.
# Run from this analysis directory:
# Rscript scripts/association_stability.R > logs/association_stability.log 2>&1
# This writes only association_stability files and does not alter main metrics.
library(data.table)
library(jsonlite)
library(sandwich)

dir.create('outputs',showWarnings=FALSE)
dir.create('logs',showWarnings=FALSE)
AREAS <- c('Melbourne','Yarra','Yarra Ranges','Port Phillip','Stonnington','Merri-bek')
TERMS <- c('one_nightYes','price_vs_similar_10')
d <- fread('private-inputs/analysis_input.csv',colClasses=c(id='character',host_id='character'))
stopifnot(nrow(d)==3873L,uniqueN(d$host_id)==1726L,
          all(d$host_role=='analysis'),!anyDuplicated(d$id),
          all(d[,uniqueN(fold),by=host_id]$V1==1L))
d[,busy:=as.integer(review_target_met)]
d[,area:=factor(neighbourhood_cleansed,levels=AREAS)]
d[,dwelling:=factor(ifelse(grepl('House',configuration),'House/townhouse','Apartment/unit'),
                     levels=c('Apartment/unit','House/townhouse'))]
d[,bedrooms:=factor(substr(configuration,1L,1L),levels=c('1','2','3'))]
d[,segment:=paste(neighbourhood_cleansed,configuration)]
d[,one_night:=factor(fifelse(!is.na(minimum_nights)&minimum_nights<=1,'Yes','No'),levels=c('No','Yes'))]
d[,amenities_10:=n_amenities/10]
FORMULA <- busy ~ area + dwelling + bedrooms + price_vs_similar_10 + one_night + amenities_10

add_training_price <- function(train) {
  med <- train[,.(segment_median_price=median(price_num)),by=segment]
  out <- merge(train,med,by='segment',all.x=TRUE,sort=FALSE)
  out[,price_vs_similar_10:=(price_num/segment_median_price-1)*10]
  stopifnot(!anyNA(out$price_vs_similar_10))
  out
}
fit_terms <- function(training,scope,omitted_fold=NA_integer_) {
  fit_data <- add_training_price(training)
  fitted <- glm(FORMULA,family=binomial(),data=fit_data)
  covariance <- vcovCL(fitted,cluster=fit_data$host_id)
  b <- coef(fitted)[TERMS]
  se <- sqrt(diag(covariance))[TERMS]
  data.table(scope=scope,omitted_host_fold=omitted_fold,
    training_listings=nrow(training),training_hosts=uniqueN(training$host_id),
    term=TERMS,coefficient=unname(b),host_clustered_se=unname(se),
    coefficient_ci95_lower=unname(b-1.96*se),coefficient_ci95_upper=unname(b+1.96*se),
    odds_ratio=unname(exp(b)),odds_ratio_ci95_lower=unname(exp(b-1.96*se)),
    odds_ratio_ci95_upper=unname(exp(b+1.96*se)),
    direction=ifelse(b>0,'positive',ifelse(b<0,'negative','zero')))
}

full <- fit_terms(d,'full_sample')
fold_results <- rbindlist(lapply(sort(unique(d$fold)),function(k) {
  train <- d[fold!=k]
  test <- d[fold==k]
  stopifnot(!length(intersect(train$host_id,test$host_id)))
  fit_terms(train,'host_training_fold',as.integer(k))
}))
results <- rbind(full,fold_results)

# Check the full-data association and clustered intervals against the existing
# model rather than inferring them from the hypothetical probability examples.
verified <- fread('outputs/final_logit_coefficients.csv')[term %in% TERMS]
compare <- merge(full,verified,by='term',suffixes=c('_recomputed','_verified'))
stopifnot(nrow(compare)==2L,
  max(abs(compare$coefficient_recomputed-compare$coefficient_verified))<1e-12,
  max(abs(compare$odds_ratio_recomputed-compare$odds_ratio_verified))<1e-12,
  max(abs(compare$odds_ratio_ci95_lower-compare$or_ci95_lo))<1e-12,
  max(abs(compare$odds_ratio_ci95_upper-compare$or_ci95_hi))<1e-12)

summary <- rbindlist(lapply(TERMS,function(term_name) {
  rows <- fold_results[term==term_name]
  expected <- if(term_name=='one_nightYes') 'positive' else 'negative'
  data.table(term=term_name,expected_direction=expected,training_folds=nrow(rows),
    folds_with_expected_direction=sum(rows$direction==expected),
    min_coefficient=min(rows$coefficient),max_coefficient=max(rows$coefficient),
    folds_ci95_excludes_zero_in_expected_direction=if(expected=='positive')
      sum(rows$coefficient_ci95_lower>0) else sum(rows$coefficient_ci95_upper<0))
}))
stopifnot(all(summary$folds_with_expected_direction==5L))

# Link the temporal evidence to the descriptive shortlist, not to this model.
segments <- fread('outputs/descriptive_segments.csv')[order(rank_busy_share)]
primary_names <- paste(segments$lga[1:3],segments$configuration[1:3],sep=' | ')
temporal <- fromJSON('reference/temporal-validation/validation_metrics.json')
earlier_names <- temporal$top3_vs_rest_recent_window$earlier_top3
stopifnot(setequal(primary_names,earlier_names),
  temporal$threshold$value==34,
  temporal$threshold$benchmark_earlier_p75==34,
  isTRUE(temporal$threshold$primary_design_threshold_not_reused))

one_night <- full[term=='one_nightYes']
relative_price <- full[term=='price_vs_similar_10']
finding <- function(row,plain_sentence) {
  stable <- summary[term==row$term]
  list(plain_english=plain_sentence,term=row$term,direction=row$direction,
    full_sample_coefficient=row$coefficient,odds_ratio=row$odds_ratio,
    host_clustered_or_ci95=c(row$odds_ratio_ci95_lower,row$odds_ratio_ci95_upper),
    training_folds_with_same_direction=stable$folds_with_expected_direction,
    training_folds_checked=stable$training_folds,
    training_fold_coefficient_range=c(stable$min_coefficient,stable$max_coefficient),
    training_folds_ci95_excludes_zero=stable$folds_ci95_excludes_zero_in_expected_direction)
}
output <- list(
  purpose='Targeted checks of two associations selected after the main analysis; no scenario probabilities are used',
  outcome='At least 30 guest reviews in the preceding 365 days, yes/no',
  method='Same simple logistic specification, full sample plus the five existing host-grouped training folds; no additional tuning or predictor selection',
  findings=list(
    one_night=finding(one_night,'Listings allowing one-night stays were more likely to have reached 30 reviews.'),
    relative_price=finding(relative_price,'Listings priced higher than similar homes were less likely to have reached 30 reviews.')
  ),
  suggested_slide_footnote='Associations after adjusting for the recorded model inputs. Both directions held in all five training folds. Current settings may differ from the review year.',
  important_limits=c(
    'This checks coefficient direction across the existing overlapping training subsets, not external validation or five independent studies.',
    'The fold directions are not a causal effect, a calibrated individual probability, or a forecast for a new operator.',
    'Longer stays can naturally generate fewer reviewed stays. A one-night rule could increase turnover costs; any trial must track actual margin.',
    'Current prices and settings may have changed during the outcome year or responded to past demand.',
    'Price is measured relative to the same area/type/bedroom segment median. Its coefficient unit is ten percentage points of that relative-price measure.',
    'The full-data odds ratios are available for backup questions; odds ratios are not risk ratios or causal percentage gains.'
  ),
  validation=list(full_coefficients_and_host_clustered_intervals_match_verified_output=TRUE,
    no_host_overlap_with_each_omitted_fold=TRUE,folds_checked=5,
    extra_repeated_splits_run=0,note='Five existing host training folds were sufficient for this directional check; no additional split search was run.'),
  temporal_link=list(
    same_three_segments_as_descriptive_shortlist=TRUE,primary_descriptive_top_three=as.list(primary_names),
    earlier_temporal_top_three=as.list(earlier_names),
    temporal_threshold=temporal$threshold$value,
    threshold_source=temporal$threshold$derived_from,
    earlier_reference_p75=temporal$threshold$benchmark_earlier_p75,
    sample_listings=temporal$sample$analysis_listings,segments=temporal$sample$segments_retained,
    validated_object='Historical persistence of the segment shortlist, not the simple logistic model',
    source_files=c('outputs/descriptive_segments.csv','reference/temporal-validation/validation_metrics.json',
      'reference/temporal-validation/method-note.md','reference/temporal-validation/segment_cross_period.csv'))
)
fwrite(results,'outputs/association_stability.csv')
fwrite(summary,'outputs/association_stability_summary.csv')
write_json(output,'outputs/association_stability.json',pretty=TRUE,auto_unbox=TRUE,digits=16)
capture.output(sessionInfo(),file='logs/association_stability_R_session.txt')
cat('FULL-SAMPLE COEFFICIENTS AND HOST-CLUSTERED INTERVALS VERIFIED\n')
print(full)
cat('\nDIRECTION ACROSS EXISTING HOST TRAINING FOLDS\n')
print(summary)
cat('\nTEMPORAL CHECK: SAME THREE SEGMENTS; DISTINCT THRESHOLD 34 FROM EARLIER REFERENCE P75\n')
print(primary_names)
