#!/usr/bin/env python3
"""Check public aggregate arithmetic only; no raw records or model fitting.

Run with Python 3 from any directory. A pass does not reproduce data cleaning,
training, host separation, raw review windows or uncertainty intervals.
"""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []
def require(value, label):
    if not value:
        raise AssertionError(label)
    checks.append(label)
def read_json(name):
    return json.loads((ROOT / name).read_text())
def read_csv(name):
    with (ROOT / name).open(newline='') as f:
        return list(csv.DictReader(f))
def near(a, b):
    return math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-9)

m = read_json('outputs/presentation_metrics.json')
require(m['sample']['analysis_listings'] == 3873 and m['sample']['segments'] == 14,
        'Published main scope is 3,873 listings in 14 groups')
require(near(m['sample']['busy_share'], 981/3873), 'Published main share is 981/3873')
require(math.ceil(m['outcome']['reference_group_p75']) == m['outcome']['threshold'] == 30,
        'Main reference percentile rounds upward to 30')
for g in m['segments']['top_three']:
    require(near(g['observed_share'], g['positive_listings']/g['listings']),
            'Observed rate matches counts: '+g['lga']+' '+g['configuration'])
models = {r['model']:r for r in read_csv('outputs/model_comparison.csv')}
for name in ['simple_logistic','segment_mean']:
    r = models[name]
    require(near(r['expected_top_quarter_n'],969), name+': expected quota is 969')
    require(near(r['precision_top_quarter'],float(r['expected_true_positives_top_quarter'])/969),
            name+': published precision matches expected counts')
require(near(models['simple_logistic']['expected_true_positives_top_quarter'],423),
        'Model selected 423 target-reaching homes')
delta=100*(float(models['simple_logistic']['precision_top_quarter'])-float(models['segment_mean']['precision_top_quarter']))
require(round(delta,1)==15.6, 'Main absolute difference rounds to 15.6 percentage points')
conf=read_csv('outputs/test_confusion.csv')[0]
require([int(conf[k]) for k in ['true_positives','false_positives','false_negatives','true_negatives']]==[423,546,558,2346],
        'Published confusion matrix matches 423 / 546 / 558 / 2346')
s=read_json('outputs/shortlisted_group_validation.json')
rows=s['by_group']; fixed=s['comparisons'][1]
require(sum(r['listings'] for r in rows)==1631 and sum(r['quota'] for r in rows)==409,
        'Recommended groups total 1,631 listings and 409 fixed places')
require(sum(r['model_expected_positive'] for r in rows)==202 and near(fixed['model_precision'],202/409),
        'Fixed-group model rate is 202/409')
expected=sum(r['quota']*r['positive_listings']/r['listings'] for r in rows)
require(near(expected,fixed['random_expected_positive']) and near(expected/409,fixed['random_expected_precision']),
        'Within-group uniform-selection expectation is derived from group counts')
cells=read_csv('outputs/shortlisted_group_validation_group_fold_cells.csv')
require(len(cells)==15, 'Group-by-fold sensitivity has 15 aggregate cells')
o=s['group_by_fold_sensitivity']['overall']
require(o['quota']==416 and o['model_expected_positive']==222 and near(o['model_precision'],222/416),
        'Sensitivity model rate is 222/416')
a=read_csv('outputs/association_stability.csv')
for term,positive in [('one_nightYes',True),('price_vs_similar_10',False)]:
    rows=[r for r in a if r['scope']=='host_training_fold' and r['term']==term]
    require(len(rows)==5 and all((float(r['coefficient'])>0)==positive for r in rows),
            term+': five published training-fold directions agree')
t=read_json('reference/temporal-validation/validation_metrics.json')
require(t['sample']['analysis_listings']==2657 and t['threshold']['value']==34,
        'Separate historical check uses 2,657 listings and threshold 34')
require(set(t['top3_vs_rest_recent_window']['earlier_top3'])==
        {g['lga']+' | '+g['configuration'] for g in m['segments']['top_three']},
        'Temporal candidates match the three descriptive search groups')
for label,select in [('top3_recent_rate',True),('rest_recent_rate',False)]:
    rows=[r for r in read_csv('reference/temporal-validation/segment_cross_period.csv')
          if (r['candidate_earlier']=='True')==select]
    rate=sum(float(r['n_listings'])*float(r['recent_rate']) for r in rows)/sum(float(r['n_listings']) for r in rows)
    require(near(rate,t['top3_vs_rest_recent_window']['listing_weighted'][label]),
            'Temporal aggregate weighted rate reconciles: '+label)
result={'status':'passed','scope':'Public aggregate consistency only; not independent raw-data or model reproduction',
        'check_count':len(checks),'checks':checks}
(ROOT/'checks').mkdir(exist_ok=True)
(ROOT/'checks/publication_check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'passed','checks':len(checks),'scope':result['scope']}))
