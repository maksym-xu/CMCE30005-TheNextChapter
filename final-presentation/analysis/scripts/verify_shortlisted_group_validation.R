# Independent R arithmetic check of the Python subgroup analysis, using frozen
# OOF data only. Does not fit a model or change the primary analysis outputs.
library(data.table)
library(jsonlite)
d<-fread('working/oof_predictions_PRIVATE.csv',colClasses=c(id='character',host_id='character'))
groups<-c('Melbourne 2BR Apartment/unit','Melbourne 3BR Apartment/unit','Yarra Ranges 3BR House/townhouse')
d<-d[segment %in% groups]
stopifnot(nrow(d)==1631L,uniqueN(d$host_id)==625L,sum(d$busy)==544L)
checks<-c('Subgroup population: 1,631 listings / 625 distinct hosts / 544 positives')
equal_quota<-function(y,score) {
  n<-length(y); k<-ceiling(n/4)
  boundary<-sort(score,decreasing=TRUE)[k]
  over<-score>boundary; tied<-score==boundary
  w<-(k-sum(over))/sum(tied)
  positives<-sum(y[over])+w*sum(y[tied])
  list(quota=k,positives=positives,rate=positives/k)
}
near<-function(x,y) abs(as.numeric(x)-as.numeric(y))<1e-10
python<-fromJSON('outputs/shortlisted_group_validation.json')
main<-python$comparisons
pooled_model<-equal_quota(d$busy,d$p)
pooled_baseline<-equal_quota(d$busy,d$p_segment_mean)
stopifnot(near(pooled_model$quota,main$quota[1]),near(pooled_model$positives,main$model_expected_positive[1]),
  near(pooled_baseline$positives,main$segment_mean_expected_positive[1]))
checks<-c(checks,'Pooled three-group expected quota and both hit counts independently reproduced')
by_group<-rbindlist(lapply(groups,function(group) {
  part<-d[segment==group]
  model<-equal_quota(part$busy,part$p)
  base<-equal_quota(part$busy,part$p_segment_mean)
  data.table(segment=group,quota=model$quota,model_tp=model$positives,
    baseline_tp=base$positives,random_tp=model$quota*mean(part$busy))
}))
for(i in seq_len(nrow(by_group))) {
  p<-python$by_group[python$by_group$segment==by_group$segment[i],]
  stopifnot(near(by_group$quota[i],p$quota),near(by_group$model_tp[i],p$model_expected_positive),
    near(by_group$baseline_tp[i],p$segment_mean_expected_positive),near(by_group$random_tp[i],p$random_expected_positive))
}
stopifnot(sum(by_group$quota)==409L,sum(by_group$model_tp)==202L,
  near(sum(by_group$baseline_tp),main$segment_mean_expected_positive[2]),
  near(sum(by_group$random_tp),main$random_expected_positive[2]))
checks<-c(checks,'Each fixed group quota and model, frozen baseline and random expected counts reproduced',
  'Combined fixed-group quota 409 and 202 model positives reproduced')
cells<-d[,{
  stopifnot(uniqueN(p_segment_mean)==1L)
  model<-equal_quota(busy,p)
  base<-equal_quota(busy,p_segment_mean)
  stopifnot(near(base$positives,base$quota*mean(busy)))
  list(quota=model$quota,model_tp=model$positives,baseline_tp=base$positives)
},by=.(segment,fold)]
secondary<-python$group_by_fold_sensitivity$overall
stopifnot(sum(cells$quota)==416L,sum(cells$model_tp)==222L,
  near(sum(cells$baseline_tp),secondary$baseline_expected_positive),
  near(sum(cells$model_tp)/sum(cells$quota),secondary$model_precision),
  near(sum(cells$baseline_tp)/sum(cells$quota),secondary$baseline_precision))
checks<-c(checks,'All 15 group-by-fold baselines are constant and equal uniform-random expected selection',
  'Group-by-fold sensitivity: 416 quota / 222 model positives / 138.700462 expected baseline positives reproduced')
stopifnot(file.exists('outputs/association_stability.json'))
associations<-fromJSON('outputs/association_stability.json')
stopifnot(associations$findings$one_night$training_folds_with_same_direction==5,
  associations$findings$relative_price$training_folds_with_same_direction==5)
checks<-c(checks,'Association stability artifact is present with both five-fold directional checks')
write_json(list(status='passed',method='Independent R calculations from frozen OOF data; no fitting or tuning',
  checks=as.list(checks),check_count=length(checks)),
  'logs/shortlisted_group_validation_independent_check.json',pretty=TRUE,auto_unbox=TRUE)
cat(paste('PASS:',checks),sep='\n')
