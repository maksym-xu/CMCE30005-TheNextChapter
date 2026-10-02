#!/usr/bin/env python3
"""Create the deck's display values directly from verified analysis outputs."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'analysis/outputs/presentation_metrics.json').read_text())
segments=[]
for s in m['segments']['top_three']:
    is_city=s['lga']=='Melbourne'
    bedroom=s['configuration'].split()[0]
    label=('City of Melbourne\n'+bedroom+' apartments' if is_city else 'Yarra Ranges\n3BR houses / townhouses')
    segments.append({'label':label,'n':s['listings'],'share':s['observed_share'],'lo':s['ci90_lower'],'hi':s['ci90_upper'],'share_label':f"{s['observed_share']*100:.1f}%",'range_label':f"{s['ci90_lower']*100:.1f}–{s['ci90_upper']*100:.1f}%"})
d={
 'sample':{'source_listings':m['sample']['source_listings'],'analysis_listings':m['sample']['analysis_listings'],'hosts':m['sample']['analysis_hosts']},
 'segments':segments,
 'screening':{'values':[m['sample']['busy_share'],m['model']['baseline_segment_mean']['top_quarter_precision'],m['model']['full']['top_quarter_precision']]},
 'temporal':{'values':[m['temporal_validation']['earlier_top_three_recent_share'],m['temporal_validation']['others_recent_share']]},
 'provenance':[
   {'source':'analysis/outputs/presentation_metrics.json','section':'segments','note':'Prioritisation is a client workflow proposal, not a statistically certain ordering.'},
   {'source':'Project/Airbnb project brief.pdf; analysis/outputs/presentation_metrics.json','section':'segments'},
   {'source':'analysis/outputs/presentation_metrics.json','section':'sample and outcome','filters':'Entire apartment/condo/house/townhouse, 1–3 bedrooms; AUD30–1500 price; first review at least365days before collection;>=50 analysis listings per group.'},
   {'source':'analysis/reference/final_segment_summary.csv','note':'Observed proportions; 90% host-bootstrap intervals, overlapping. Not model-generated ranks.'},
   {'source':['analysis/scripts/14_simple_logistic.R','analysis/outputs/association_stability.json'],'model':m['model']['family'],'inputs':m['model']['inputs'],'scope':m['model']['scope'],'interpretation':'Learned probabilities are used only as a historical ranking score. Associations are conditional and non-causal.'},
   {'source':'analysis/outputs/model_comparison.csv','baseline':m['model']['baseline_segment_mean'],'full':m['model']['full'],'note':'Threshold30. Same expected screening quota969; fractional weights at tied boundary for baselines. All-listing mean is a context benchmark. Evaluation followed earlier exploration.'},
   {'source':'analysis/reference/temporal-validation/','details':m['temporal_validation']},
   {'source':'Client decision framework','note':'No estimated-revenue-derived rent ceiling is used. Revenue inputs for any candidate require explicit scenarios and external verification.'},
   {'source':'Proposed implementation plan','note':'10 candidates and30days are planning choices; not model-derived optima. Actual work and approvals have not happened.'},
   {'source':'Group2 recommendations','note':'Established priced surviving listings; current details vs past reviews; review activity is not profit.'}
 ]
}
(ROOT/'code/slide_data.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))
print('Verified analysis metrics linked to code/slide_data.json')
