"""Tone of guest review text for busy homes and the rest (23 October 2026).

Answers the presentation feedback that review counts ignore what guests wrote.
Each review in the 365 days before a home's collection date is scored with VADER
(Hutto & Gilbert, 2014), a published word-list scorer for short English text:
compound >= 0.05 counts as positive, <= -0.05 as negative, anything between as
neutral. Reviews not written in English mostly score neutral.

Run from the repository root (needs vaderSentiment==3.3.2):
    python final-report/report-2026-10-04/scripts/review_sentiment.py
Private inputs (not published): final-report/report-2026-10-04/private-inputs/analysis_input.csv,
data/raw/listings_airbnb.csv and data/raw/reviews_airbnb.csv (the LMS snapshot).
Writes one aggregate table (no listing, host or reviewer identifiers) to
final-report/report-2026-10-04/outputs/revision/review_sentiment.csv.
"""
import csv
import sys
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

csv.field_size_limit(sys.maxsize)
PKG = Path('final-report/report-2026-10-04')
PRIORITY = {'Melbourne 2BR Apartment/unit', 'Melbourne 3BR Apartment/unit',
            'Yarra Ranges 3BR House/townhouse'}


def canonical_id(s):
    """Same expansion as canonical_id() in the R scripts (some raw ids use scientific notation)."""
    return str(int(Decimal(s.strip())))


homes = {}
with (PKG / 'private-inputs/analysis_input.csv').open(newline='') as f:
    for r in csv.DictReader(f):
        homes[r['id']] = {'busy': r['review_target_met'] == '1',
                          'group': f"{r['neighbourhood_cleansed']} {r['configuration']}",
                          'reviews_365d': int(r['reviews_365d'])}
assert len(homes) == 3873

scraped = {}
with open('data/raw/listings_airbnb.csv', newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        i = canonical_id(r['id'])
        if i in homes:
            scraped[i] = date.fromisoformat(r['last_scraped'])
assert len(scraped) == len(homes)

analyzer = SentimentIntensityAnalyzer()
scores = defaultdict(list)
with open('data/raw/reviews_airbnb.csv', newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        i = canonical_id(r['listing_id'])
        if i not in homes:
            continue
        end = scraped[i]
        if not end - timedelta(days=365) < date.fromisoformat(r['date']) <= end:
            continue
        text = (r['comments'] or '').strip()
        scores[i].append(analyzer.polarity_scores(text)['compound'] if text else 0.0)

# The window must reproduce the review counts used for the target.
mismatch = sum(len(scores[i]) != h['reviews_365d'] for i, h in homes.items())
assert mismatch == 0, f'{mismatch} homes do not match reviews_365d'


def summarise(scope, ids):
    rows = []
    for label, flag in (('Busy (30+ reviews)', True), ('Below 30', False), ('All homes', None)):
        sel = [i for i in ids if flag is None or homes[i]['busy'] == flag]
        vals = [v for i in sel for v in scores[i]]
        per_home = [sum(v <= -0.05 for v in scores[i]) / len(scores[i]) for i in sel if scores[i]]
        rows.append({'scope': scope, 'status': label, 'homes': len(sel), 'reviews_scored': len(vals),
                     'share_positive': sum(v >= 0.05 for v in vals) / len(vals),
                     'share_negative': sum(v <= -0.05 for v in vals) / len(vals),
                     'mean_compound': sum(vals) / len(vals),
                     'mean_home_share_negative': sum(per_home) / len(per_home)})
    return rows


rows = summarise('All 14 groups', list(homes))
rows += summarise('Three priority groups', [i for i, h in homes.items() if h['group'] in PRIORITY])
with (PKG / 'outputs/revision/review_sentiment.csv').open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
for r in rows:
    print(r)
