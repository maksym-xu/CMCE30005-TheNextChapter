# Supplementary comparison: identical data, validation hosts, predictor columns
# and screening quota. Does not alter the main presentation or model outputs.
# Run from the analysis package root: Rscript scripts/matched_rf_comparison.R
library(data.table)
library(jsonlite)
library(randomForest)

dir.create('outputs', showWarnings=FALSE)
dir.create('working', showWarnings=FALSE)
dir.create('logs', showWarnings=FALSE)
SEED <- 30005L
NTREE <- 250L
MTRY <- 3L
NODESIZE <- 10L
BOOTSTRAPS <- 1000L
AREAS <- c('Melbourne','Yarra','Yarra Ranges','Port Phillip','Stonnington','Merri-bek')
d <- fread('private-inputs/analysis_input.csv',colClasses=c(id='character',host_id='character'))
stopifnot(nrow(d)==3873L,uniqueN(d$host_id)==1726L,!anyDuplicated(d$id),
          all(d$host_role=='analysis'),all(d[,uniqueN(fold),by=host_id]$V1==1L))
d[,busy:=as.integer(review_target_met)]
d[,area:=factor(neighbourhood_cleansed,levels=AREAS)]
d[,dwelling:=factor(ifelse(grepl('House',configuration),'House/townhouse','Apartment/unit'),
                     levels=c('Apartment/unit','House/townhouse'))]
d[,bedrooms:=factor(substr(configuration,1L,1L),levels=c('1','2','3'))]
d[,segment:=paste(neighbourhood_cleansed,configuration)]
d[,one_night:=factor(fifelse(!is.na(minimum_nights)&minimum_nights<=1,'Yes','No'),levels=c('No','Yes'))]
d[,amenities_10:=n_amenities/10]
FORMULA <- busy ~ area + dwelling + bedrooms + price_vs_similar_10 + one_night + amenities_10
add_price <- function(target,reference) {
  med <- reference[,.(segment_median_price=median(price_num)),by=segment]
  out <- merge(target,med,by='segment',all.x=TRUE,sort=FALSE)
  out[,price_vs_similar_10:=(price_num/segment_median_price-1)*10]
  stopifnot(!anyNA(out$price_vs_similar_10))
  out
}
auc <- function(y,p) {
  n1 <- sum(y==1L); n0 <- sum(y==0L)
  (sum(rank(p)[y==1L])-n1*(n1+1)/2)/(n1*n0)
}
quota_weights <- function(p) {
  k<-ceiling(length(p)/4)
  boundary<-sort(p,decreasing=TRUE)[k]
  above<-p>boundary; tied<-p==boundary
  w<-as.numeric(above)
  w[tied]<-(k-sum(above))/sum(tied)
  stopifnot(abs(sum(w)-k)<1e-10)
  w
}
scores <- function(y,p) {
  w<-quota_weights(p)
  list(auc=auc(y,p),brier_score=mean((y-p)^2),
       precision_top_quarter=sum(w*y)/sum(w),
       recall_top_quarter=sum(w*y)/sum(y),
       expected_screened_n=sum(w),expected_true_positives=sum(w*y))
}

predictor_columns <- NULL
fold_rows<-list()
predictions<-rbindlist(lapply(sort(unique(d$fold)),function(k) {
  tr<-add_price(d[fold!=k],d[fold!=k])
  te<-add_price(d[fold==k],d[fold!=k])
  stopifnot(!length(intersect(tr$host_id,te$host_id)))
  lr<-glm(FORMULA,family=binomial(),data=tr)
  train_matrix<-model.matrix(lr)[,-1,drop=FALSE]
  test_matrix<-model.matrix(delete.response(terms(lr)),te,xlev=lr$xlevels)[,-1,drop=FALSE]
  stopifnot(identical(colnames(train_matrix),colnames(test_matrix)),ncol(train_matrix)==11L,
            !anyNA(train_matrix),!anyNA(test_matrix))
  if(is.null(predictor_columns)) predictor_columns <<- colnames(train_matrix)
  stopifnot(identical(predictor_columns,colnames(train_matrix)))
  # Both algorithms receive the exact same 11 predictor columns. The intercept
  # is part of logistic regression, not an input feature for the forest.
  set.seed(SEED+as.integer(k))
  rf<-randomForest(x=train_matrix,y=factor(tr$busy,levels=0:1),
      ntree=NTREE,mtry=MTRY,nodesize=NODESIZE,importance=FALSE)
  lr_p<-as.numeric(predict(lr,newdata=te,type='response'))
  rf_p<-as.numeric(predict(rf,newdata=test_matrix,type='prob')[,'1'])
  fold_rows[[as.character(k)]] <<- data.table(fold=k,train_listings=nrow(tr),test_listings=nrow(te),
    train_hosts=uniqueN(tr$host_id),test_hosts=uniqueN(te$host_id),
    logistic_auc=auc(te$busy,lr_p),rf_auc=auc(te$busy,rf_p),
    logistic_brier=mean((te$busy-lr_p)^2),rf_brier=mean((te$busy-rf_p)^2))
  data.table(id=te$id,host_id=te$host_id,fold=k,busy=te$busy,logistic=lr_p,random_forest=rf_p)
}))
stopifnot(nrow(predictions)==nrow(d),!anyDuplicated(predictions$id),!anyNA(predictions))
main_oof<-fread('working/oof_predictions_PRIVATE.csv',colClasses=c(id='character',host_id='character'))
stopifnot(setequal(predictions$id,main_oof$id))
max_logit_delta<-max(abs(predictions$logistic-main_oof$p[match(predictions$id,main_oof$id)]))
stopifnot(max_logit_delta<1e-12)
stopifnot(all(predictions$busy==main_oof$busy[match(predictions$id,main_oof$id)]),
          all(predictions$host_id==main_oof$host_id[match(predictions$id,main_oof$id)]),
          all(predictions$fold==main_oof$fold[match(predictions$id,main_oof$id)]))

comparison<-rbindlist(lapply(c('logistic','random_forest'),function(nm) {
  cbind(data.table(model=nm),as.data.table(scores(predictions$busy,predictions[[nm]])))
}))
fold_metrics<-rbindlist(fold_rows)
fold_metrics[,`:=`(auc_difference_rf_minus_logistic=rf_auc-logistic_auc,
                  brier_difference_rf_minus_logistic=rf_brier-logistic_brier)]
rf_weights<-quota_weights(predictions$random_forest)
cutoff<-sort(predictions$random_forest,decreasing=TRUE)[ceiling(nrow(predictions)/4)]
ties_n<-sum(predictions$random_forest==cutoff)
screening<-data.table(model=c('logistic','random_forest'),expected_screened_n=comparison$expected_screened_n,
  expected_true_positives=comparison$expected_true_positives,
  expected_false_positives=comparison$expected_screened_n-comparison$expected_true_positives,
  expected_false_negatives=sum(predictions$busy)-comparison$expected_true_positives,
  expected_true_negatives=nrow(predictions)-sum(predictions$busy)-comparison$expected_screened_n+comparison$expected_true_positives)

# Paired host resampling of fixed OOF predictions: descriptive uncertainty only.
# Does not refit either model and does not account for earlier model selection.
host_rows<-split(seq_len(nrow(predictions)),predictions$host_id)
set.seed(SEED+10000L)
boot<-rbindlist(lapply(seq_len(BOOTSTRAPS),function(b) {
  idx<-unlist(host_rows[sample.int(length(host_rows),length(host_rows),replace=TRUE)],use.names=FALSE)
  part<-predictions[idx]
  lo<-scores(part$busy,part$logistic); rf<-scores(part$busy,part$random_forest)
  data.table(replicate=b,auc_difference=rf$auc-lo$auc,
    brier_difference=rf$brier_score-lo$brier_score,
    precision_difference=rf$precision_top_quarter-lo$precision_top_quarter)
}))
intervals<-rbindlist(lapply(c('auc','brier','precision'),function(metric) {
  col<-paste0(metric,'_difference')
  point<-switch(metric,
    auc=comparison[model=='random_forest',auc]-comparison[model=='logistic',auc],
    brier=comparison[model=='random_forest',brier_score]-comparison[model=='logistic',brier_score],
    precision=comparison[model=='random_forest',precision_top_quarter]-comparison[model=='logistic',precision_top_quarter])
  data.table(metric=metric,difference_rf_minus_logistic=point,
    ci95_lower=as.numeric(quantile(boot[[col]],.025)),ci95_upper=as.numeric(quantile(boot[[col]],.975)))
}))

fwrite(comparison,'outputs/matched_rf_comparison.csv')
fwrite(fold_metrics,'outputs/matched_rf_comparison_folds.csv')
fwrite(screening,'outputs/matched_rf_comparison_confusion_expected.csv')
fwrite(intervals,'outputs/matched_rf_comparison_intervals.csv')
fwrite(predictions,'working/matched_rf_comparison_oof_PRIVATE.csv')
fwrite(boot,'working/matched_rf_comparison_host_bootstrap.csv')
metadata<-list(
  purpose='Supplementary like-for-like predictor comparison; does not change the presentation model or its existing outputs',
  data=list(listings=nrow(d),hosts=uniqueN(d$host_id),positive_listings=sum(d$busy),review_threshold=30,folds=5),
  same_inputs=list(columns=as.list(predictor_columns),design='Same model-matrix predictors for both learners; host-grouped folds frozen; segment price medians learned inside each training fold'),
  random_forest=list(implementation=paste0('R randomForest ',as.character(packageVersion('randomForest'))),
    ntree=NTREE,mtry=MTRY,nodesize=NODESIZE,bootstrap_replace=TRUE,class_weights='none',seed_rule='30005 + fold',
    tuning='None. Parameters fixed before inspecting this supplementary comparison.'),
  checks=list(logistic_max_probability_difference_from_verified_main=max_logit_delta,
    host_overlap=FALSE,same_listing_ids=TRUE,same_outcomes=TRUE,same_folds=TRUE,same_expected_quota=969),
  quota=list(method='Exactly ceil(n/4) in expectation, sharing remaining quota uniformly across boundary ties',
    rf_score_boundary=cutoff,rf_boundary_tied_listings=ties_n,
    rf_boundary_selection_weight=unique(rf_weights[predictions$random_forest==cutoff])),
  metrics=comparison,folds=fold_metrics,paired_host_bootstrap=list(replicates=BOOTSTRAPS,
    predictions_held_fixed=TRUE,intervals=intervals,
    limitation='Intervals omit refitting, tuning, model-selection and threshold uncertainty.'),
  limitations=c('This uses R randomForest, not the interim Python scikit-learn implementation; it is a new matched-input benchmark, not a reproduction of the old forest.',
    'nodesize in randomForest is not identical to min_samples_leaf in scikit-learn.',
    'One fixed RF configuration and one seed rule are evaluated; neither family is exhaustively tuned.',
    'The same exploratory snapshot and folds have been used in prior analyses.',
    'Current listing settings explain historical review activity; these are not causal or future-profit predictions.')
)
write_json(metadata,'outputs/matched_rf_comparison.json',pretty=TRUE,auto_unbox=TRUE,digits=16)
capture.output(sessionInfo(),file='logs/matched_rf_comparison_R_session.txt')
cat('MATCHED RANDOM-FOREST COMPARISON\n')
print(comparison)
print(fold_metrics)
print(intervals)
cat('Verified logistic maximum probability difference:',max_logit_delta,'\n')
cat('RF cutoff tie count:',ties_n,'; quota weight:',unique(rf_weights[predictions$random_forest==cutoff]),'\n')
