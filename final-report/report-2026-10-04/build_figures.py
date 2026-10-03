from pathlib import Path
import csv, re, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
E=REPO
FIG=ROOT/'figures'; FIG.mkdir(exist_ok=True)
def readcsv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
ladder=readcsv(E/'final-presentation/analysis/reference/segment_ladder.csv')
top=sorted(ladder,key=lambda x:float(x['observed_target_rate']),reverse=True)[:3]
followup=REPO/'final-report/screening-followup-2026-10-03'
summary=readcsv(followup/'outputs/screening_summary.csv')
temporal=json.loads((E/'final-presentation/analysis/reference/temporal-validation/validation_metrics.json').read_text())
BLUE='#2166A1'; GREY='#89939D'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none'})
def finish(fig,name):
    fig.savefig(FIG/(name+'.png'),dpi=300,bbox_inches='tight',facecolor='white')
    fig.savefig(FIG/(name+'.svg'),bbox_inches='tight',facecolor='white');plt.close(fig)
fig,ax=plt.subplots(figsize=(7.2,3.25));fig.subplots_adjust(left=.43,right=.90,bottom=.22,top=.93)
for i,x in enumerate(top):
    p=float(x['observed_target_rate'])*100;lo=float(x['ci90_lo'])*100;hi=float(x['ci90_hi'])*100
    ax.errorbar(p,i,xerr=[[p-lo],[hi-p]],fmt='o',color=BLUE,capsize=4,lw=1.7,markersize=7)
    ax.text(1.03,i,f'{p:.1f}%',transform=ax.get_yaxis_transform(),va='center',fontsize=11)
ax.set_yticks(range(3),['City of Melbourne\n3-bedroom apartments/units','City of Melbourne\n2-bedroom apartments/units','Yarra Ranges\n3-bedroom houses/townhouses'])
ax.set_ylim(2.4,-.4);ax.set_xlim(0,48);ax.set_xticks([0,10,20,30,40]);ax.xaxis.set_major_formatter(PercentFormatter(100,decimals=0))
ax.axvline(981/3873*100,ls='--',color=GREY,lw=1)
ax.set_xlabel('Homes with at least 30 annual reviews',fontsize=11)
for s in ['top','right','left']:ax.spines[s].set_visible(False)
ax.tick_params(axis='y',length=0);ax.grid(axis='x',color='#e5e8ec');ax.set_axisbelow(True)
finish(fig,'figure_1_priority_groups')

fig,ax=plt.subplots(figsize=(7.2,2.8));fig.subplots_adjust(left=.31,right=.96,bottom=.24,top=.96)
models=['baseline','property_only','full']
vals=[float(next(r for r in summary if r['scope']=='priority_fixed_quota' and float(r['fraction'])==.25
       and r['metric']=='precision' and r['model']==model)['mean'])*100 for model in models]
ax.barh([2,1,0],vals,color=[GREY,'#9EC3DF',BLUE],height=.52)
ax.set_yticks([2,1,0],['Group rates alone','Model without price\nor minimum stay','Complete model']);ax.set_xlim(0,60)
ax.xaxis.set_major_formatter(PercentFormatter(100,decimals=0));ax.set_xlabel('Selected homes reaching at least 30 annual reviews')
for y,p in zip([2,1,0],vals):ax.text(p+1,y,f'{p:.1f}%',va='center',fontsize=12)
for s in ['top','right','left']:ax.spines[s].set_visible(False)
ax.tick_params(axis='y',length=0);ax.grid(axis='x',color='#e5e8ec');ax.set_axisbelow(True)
finish(fig,'figure_2_paired_screening')

fig,ax=plt.subplots(figsize=(7.2,2.8));fig.subplots_adjust(left=.13,right=.98,bottom=.20,top=.79)
tt=temporal['top3_vs_rest_recent_window'];x=np.arange(2);w=.32
sets=[('Earlier top-three groups',BLUE,[tt['top3_earlier_rate_listing_weighted'],tt['listing_weighted']['top3_recent_rate']],-w/2),
      ('Other eligible groups',GREY,[tt['rest_earlier_rate_listing_weighted'],tt['listing_weighted']['rest_recent_rate']],w/2)]
for label,color,values,offset in sets:
    vals=np.array(values)*100;bars=ax.bar(x+offset,vals,width=w,color=color,label=label)
    ax.bar_label(bars,labels=[f'{v:.1f}%' for v in vals],padding=3,fontsize=11)
ax.set_xticks(x,['Earlier annual window','Later annual window']);ax.set_ylim(0,40)
ax.yaxis.set_major_formatter(PercentFormatter(100,decimals=0));ax.set_ylabel('Homes with at least 34 annual reviews')
ax.legend(loc='upper center',bbox_to_anchor=(.5,1.30),ncol=2,frameon=False,fontsize=10)
for s in ['top','right']:ax.spines[s].set_visible(False)
ax.grid(axis='y',color='#e5e8ec');ax.set_axisbelow(True);finish(fig,'figure_3_historical_persistence')


plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.titlesize':17,
 'axes.labelsize':12,'svg.fonttype':'none','savefig.facecolor':'white'})
GREY='#949DA7'
def clean(ax):
    for edge in ['top','right','left']: ax.spines[edge].set_visible(False)
    ax.spines['bottom'].set_color('#b8bec5')
    ax.tick_params(axis='y',length=0)
    ax.set_axisbelow(True)
    ax.grid(axis='x',color='#e7eaed',linewidth=.8)
save=finish
ordered=sorted(ladder,key=lambda x:float(x['observed_target_rate']),reverse=True)
fig,ax=plt.subplots(figsize=(11,9));fig.subplots_adjust(left=.36,right=.79,bottom=.13,top=.89)
labels=[]
for i,x in enumerate(ordered):
    p=float(x['observed_target_rate'])*100;lo=float(x['ci90_lo'])*100;hi=float(x['ci90_hi'])*100
    color=BLUE if i<3 else GREY
    ax.errorbar(p,i,xerr=[[p-lo],[hi-p]],fmt='o',color=color,markersize=7,capsize=3,lw=1.7)
    labels.append(f"{x['lga']} | {x['bedrooms']} bedrooms\n{x['dwelling_class']}")
    ax.text(1.035,i,f"{p:.1f}%   n={int(x['n_listings']):,}",transform=ax.get_yaxis_transform(),va='center',ha='left',fontsize=10)
ax.set_yticks(range(14),labels,fontsize=10);ax.invert_yaxis();ax.set_xlim(0,50)
ax.xaxis.set_major_formatter(PercentFormatter(100));ax.axvline(981/3873*100,color='#555',ls='--',lw=1)
ax.set_xlabel('Share with at least 30 reviews in the preceding year');clean(ax)
fig.suptitle('All 14 eligible groups: rates and comparison support',x=.03,y=.98,ha='left')
fig.text(.03,.03,'Dots: observed shares. Lines: pointwise 90% host-resampled ranges (1,000 draws).\nDashed line: pooled 25.3%. n counts homes; group host counts must not be added across groups.',fontsize=10)
save(fig,'appendix_all_14_groups')

print('Built four report charts from published aggregate tables; no models refitted.')
