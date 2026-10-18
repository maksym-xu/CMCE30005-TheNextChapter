"""Build the five report figures from committed aggregate tables.

Run from anywhere: python final-report/report-2026-10-04/build_figures.py
Needs matplotlib and numpy. No model is refitted and no listing-level data is read.
Sources:
  Figure 1  outputs/revision/review_histogram_bins.csv and revision_summary.json
  Figure 2  final-presentation/analysis/reference/segment_ladder.csv
  Figure 3  final-report/screening-followup-2026-10-03/outputs/screening_summary.csv
  Figure 4  final-presentation/analysis/reference/temporal-validation/validation_metrics.json
  Figure 5  outputs/revision/weekly_revenue_reach.csv
"""
from pathlib import Path
import csv
import json

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
FIG = ROOT / 'figures'
FIG.mkdir(exist_ok=True)
BLUE = '#2166A1'
LIGHT = '#9EC3DF'
GREY = '#89939D'
GRID = '#e5e8ec'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'svg.fonttype': 'none',
                     'svg.hashsalt': 'cmce30005', 'savefig.facecolor': 'white'})


def readcsv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def finish(fig, name):
    fig.savefig(FIG / (name + '.png'), dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(FIG / (name + '.svg'), bbox_inches='tight', facecolor='white',
                metadata={'Date': None})
    plt.close(fig)


def tidy(ax, axis='x'):
    for side in ['top', 'right'] + (['left'] if axis == 'x' else []):
        ax.spines[side].set_visible(False)
    ax.grid(axis=axis, color=GRID)
    ax.set_axisbelow(True)


AREA = {'Melbourne': 'City of Melbourne'}
KIND = {'Apartment/unit': 'apartments', 'House/townhouse': 'houses/townhouses'}

# Figure 1: distribution of annual reviews across the 3,873 analysis homes.
bins = readcsv(ROOT / 'outputs/revision/review_histogram_bins.csv')
summary = json.loads((ROOT / 'outputs/revision/revision_summary.json').read_text())['review_distribution']
starts = np.array([int(r['bin_start']) for r in bins])
homes = np.array([int(r['homes']) for r in bins])
fig, ax = plt.subplots(figsize=(7.2, 2.9))
colors = [BLUE if s >= 30 else GREY for s in starts]
ax.bar(starts + 2.5, homes, width=4.6, color=colors)
ax.axvline(30, color='#333', ls='--', lw=1)
ax.text(31, homes.max() * 0.93, f"Target: 30 reviews\n{summary['reaching_target']:,} homes "
        f"({summary['reaching_target'] / summary['homes']:.1%}) reach it", fontsize=10, va='top')
ax.axvline(summary['median'], color=GREY, ls=':', lw=1)
ax.text(summary['median'] + 0.8, homes.max() * 0.62, f"Median {summary['median']:.0f}", fontsize=9.5, color='#555')
ax.set_xlim(0, 105)
ax.set_xticks([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100], ['0', '10', '20', '30', '40', '50', '60', '70', '80', '90', '100+'])
ax.set_xlabel('Guest reviews in the 365 days before collection (bins of five)')
ax.set_ylabel('Homes')
tidy(ax, 'y')
finish(fig, 'figure_1_review_distribution')

# Figure 2: all 14 groups, the three priority groups highlighted.
ladder = sorted(readcsv(REPO / 'final-presentation/analysis/reference/segment_ladder.csv'),
                key=lambda r: float(r['observed_target_rate']), reverse=True)
fig, ax = plt.subplots(figsize=(4.0, 5.8))
labels = []
for i, r in enumerate(ladder):
    p = float(r['observed_target_rate']) * 100
    lo = float(r['ci90_lo']) * 100
    hi = float(r['ci90_hi']) * 100
    color = BLUE if i < 3 else GREY
    ax.errorbar(p, i, xerr=[[p - lo], [hi - p]], fmt='o', color=color, markersize=6, capsize=3, lw=1.5)
    labels.append(f"{AREA.get(r['lga'], r['lga'])} · {r['bedrooms']}-bed {KIND[r['dwelling_class']]}")
    ax.text(1.01, i, f"{p:.1f}%  (n={int(r['n_listings']):,})", transform=ax.get_yaxis_transform(),
            va='center', fontsize=11, color=color if i < 3 else '#444')
ax.set_yticks(range(len(ladder)), labels, fontsize=11)
for tick, i in zip(ax.get_yticklabels(), range(len(ladder))):
    if i < 3:
        tick.set_color(BLUE)
        tick.set_fontweight('bold')
ax.set_xlim(0, 50)
ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
overall = 981 / 3873 * 100
ax.axvline(overall, color='#555', ls='--', lw=1)
ax.set_ylim(len(ladder) - 0.5, -1.2)
ax.text(overall + 0.5, -0.85, f'All homes {overall:.1f}%', fontsize=10.5, color='#555')
ax.set_xlabel('Homes with 30+ reviews in the year\n(dot) and 90% range', fontsize=11)
ax.tick_params(axis='y', length=0)
tidy(ax, 'x')
finish(fig, 'figure_2_group_rates')

# Figure 3: within-group screening at a 25% quota, mean of 50 tests.
screening = readcsv(REPO / 'final-report/screening-followup-2026-10-03/outputs/screening_summary.csv')
models = ['baseline', 'property_only', 'full']
vals = [float(next(r for r in screening if r['scope'] == 'priority_fixed_quota' and float(r['fraction']) == .25
                   and r['metric'] == 'precision' and r['model'] == m)['mean']) * 100 for m in models]
fig, ax = plt.subplots(figsize=(7.2, 2.6))
ax.barh([2, 1, 0], vals, color=[GREY, LIGHT, BLUE], height=.52)
ax.set_yticks([2, 1, 0], ['Group rates alone\n(random pick within group)', 'Reduced model\n(no price or minimum stay)', 'Full model'])
ax.set_xlim(0, 60)
ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
ax.set_xlabel('Picked homes reaching 30 reviews (25% picked in each priority group)')
for y, p in zip([2, 1, 0], vals):
    ax.text(p + 1, y, f'{p:.1f}%', va='center', fontsize=12)
ax.tick_params(axis='y', length=0)
tidy(ax, 'x')
finish(fig, 'figure_3_screening')

# Figure 4: the same 2,657 surviving homes in two consecutive years.
temporal = json.loads((REPO / 'final-presentation/analysis/reference/temporal-validation/validation_metrics.json').read_text())
tt = temporal['top3_vs_rest_recent_window']
x = np.arange(2)
w = .32
fig, ax = plt.subplots(figsize=(7.2, 2.3))
sets = [('Top three groups (chosen on the earlier year)', BLUE,
         [tt['top3_earlier_rate_listing_weighted'], tt['listing_weighted']['top3_recent_rate']], -w / 2),
        ('Other seven groups', GREY,
         [tt['rest_earlier_rate_listing_weighted'], tt['listing_weighted']['rest_recent_rate']], w / 2)]
for label, color, values, offset in sets:
    v = np.array(values) * 100
    bars = ax.bar(x + offset, v, width=w, color=color, label=label)
    ax.bar_label(bars, labels=[f'{a:.1f}%' for a in v], padding=3, fontsize=11)
ax.set_xticks(x, ['Year to mid-2025', 'Year to mid-2026'])
ax.set_ylim(0, 42)
ax.yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
ax.set_ylabel('Homes with 34+ reviews')
ax.legend(loc='upper center', bbox_to_anchor=(.5, 1.25), ncol=2, frameon=False, fontsize=10)
tidy(ax, 'y')
finish(fig, 'figure_4_two_years')

# Figure 5: share of each priority group's homes whose estimated weekly revenue reached a weekly cost.
reach = readcsv(ROOT / 'outputs/revision/weekly_revenue_reach.csv')
fig, ax = plt.subplots(figsize=(7.2, 2.6))
lines = [('Melbourne 3BR Apartment/unit', 'City 3-bed apartments', BLUE, '-'),
         ('Melbourne 2BR Apartment/unit', 'City 2-bed apartments', BLUE, '--'),
         ('Yarra Ranges 3BR House/townhouse', 'Yarra Ranges 3-bed houses', GREY, '-')]
for key, label, color, style in lines:
    pts = [(float(r['weekly_cost_aud']), float(r['share_reaching']) * 100) for r in reach if r['group'] == key]
    xs, ys = zip(*[p for p in pts if p[0] <= 1600])
    ax.plot(xs, ys, color=color, ls=style, lw=2, label=label)
ax.axhline(50, color='#555', ls=':', lw=1)
ax.text(1600, 51.5, 'half of homes', ha='right', fontsize=10, color='#555')
ax.set_xlim(0, 1600)
ax.set_ylim(0, 100)
ax.yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
ax.set_xlabel('Weekly rent and running costs of a lease (AUD)')
ax.set_ylabel('Homes earning\nat least this')
ax.xaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter('{x:,.0f}'))
ax.legend(loc='upper right', bbox_to_anchor=(1, .93), frameon=False, fontsize=10)
tidy(ax, 'y')
finish(fig, 'figure_5_weekly_reach')

print('Built five report figures from committed aggregate tables; no models refitted.')
