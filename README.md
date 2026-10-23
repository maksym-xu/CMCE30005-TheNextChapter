# Melbourne Airbnb Market Screening

CMCE30005 Final Project Report | Group 2 | Eric Huang and Maksym Xu

We help a rent-to-rent operator choose where to search and which homes to inspect. One Melbourne Airbnb snapshot identifies City two- and three-bedroom apartments as the first search priority, with Yarra Ranges three-bedroom houses as a less certain alternative. Within these groups, half of the homes that accept one-night stays and are priced at or below similar homes were busy (50.4%), close to the share among homes our logistic model picked from unseen hosts (49.6%), against a third of all their homes (33.4%).

**Final report (revised 23 October 2026):** [PDF](final-report/report-2026-10-04/Final_Report.pdf) · [Word](final-report/report-2026-10-04/Final_Report.docx) · [Markdown](final-report/report-2026-10-04/Final_Report.md) · [Report package and checks](final-report/report-2026-10-04/README.md)

After the report: [Repository guide](#repository-guide) · [How to reproduce the results](#how-to-reproduce-the-results) · [Contributions](#contributions)

<!-- final report starts here -->

## 1. Introduction

Our client plans to lease Melbourne homes and let them on Airbnb as short stays (rent-to-rent). Rent and setup costs come before any guest income, so a poor lease ties up scarce funds. Our main answers are:

- **Where:** City of Melbourne two- and three-bedroom apartments, then Yarra Ranges three-bedroom houses. These groups had the highest shares of busy homes (30 or more reviews a year, about 180 booked nights).
- **Which homes:** those that can take one-night stays at a price at or below similar listings. Half of such homes were busy, against a third of all homes in these groups.
- **Which leases:** only those whose weekly costs sit below the group's typical weekly revenue (AUD 590–930).

## 2. Problem Definition and Objectives

The business question is: **where should a rent-to-rent operator with limited funds search, and which homes should it inspect first?** We set three objectives:

1. Rank property groups by their share of busy homes, and express this in nights and revenue.
2. Find which home settings go with being busy, and whether they help choose homes within the leading groups.
3. Turn the results into a search order, a checklist and a four-week inspection plan.

A **group** combines council area, dwelling type and bedroom count. A home is **busy** if it received at least 30 guest reviews in the year before data collection. Inside Airbnb (n.d.) assumes half of stays are reviewed, so with three-night stays, 30 reviews means about 180 booked nights, roughly half the year.

**Why reviews?** Guests can review only after a stay, so review counts track completed bookings, the best public guide to demand and occupancy. Empty nights are the operator's main risk. Review counts do not show profit (rents and costs are not in the data) or satisfaction, so we translate them into nights and revenue and check what guests wrote (Section 5.1).

Since the interim report (in the project repository), we replaced its random forest with one explainable logistic regression and moved technical checks to Appendix A.

## 3. Data Description and Preparation

We use one Inside Airbnb snapshot of Melbourne, supplied through the subject LMS and collected 17 June–1 July 2026 (Inside Airbnb, 2026). It holds 25,728 listings and 1,026,690 dated reviews. We did not use the calendar, because it cannot separate bookings from nights the host blocked.

Cleaning converted prices to numbers, standardized missing entries, counted amenities and rebuilt each home's annual review count from review dates. Price is missing for 6,553 listings (25%) and bedrooms for 4,679 (18%); 4,477 listings (17%) have never been reviewed.

We kept homes a small operator could lease (Table 1):

- entire apartments, houses or townhouses with one to three bedrooms;
- prices of AUD 30–1,500, since unpriced and extreme listings are mostly inactive: 77.8% of those removed had no review in the past year, against 17.0% of those kept;
- a first review at least a year before collection, so each home has a full year of reviews;
- groups of at least 50 homes, so each group's share is stable.

To avoid setting the bar with the homes we compare, we first set aside one host in five (1,342 homes). The busiest quarter of their homes had 30 or more reviews, so 30 became the target. The final sample has 3,873 homes, 1,726 hosts and 14 groups in six council areas.

**Table 1. From supplied listings to analysis sample**

| Step | Homes |
|---|---:|
| All listings | 25,728 |
| Entire homes with one to three bedrooms | 16,576 |
| Apartments, condos, houses and townhouses | 14,895 |
| Priced AUD 30–1,500 | 11,099 |
| First review at least a year before collection | 6,891 |
| After setting aside 1,342 reference-host homes | 5,549 |
| **Analysis sample: 14 groups with at least 50 homes** | **3,873** |

## 4. Methodology

**Descriptive (Objective 1).** We compare the share of busy homes across the 14 groups and translate it into Inside Airbnb's estimated nights and revenue.

**Predictive (Objective 2).** A logistic regression estimates each home's chance of being busy from six inputs, holding the others fixed (Table 2; R Core Team, 2026). This separates location from how a home is run. We also test a simpler two-setting rule: one-night stays, and a price at or below the group median.

**Table 2. Outcome and inputs of the model**

| Variable | Definition |
|---|---|
| **Outcome** | 1 if the home had at least 30 reviews in the year, otherwise 0 |
| Council area | One of six |
| Dwelling type | Apartment, or house/townhouse |
| Bedrooms | One, two or three |
| Price compared with similar homes | Price relative to the group median, per 10% |
| Accepts one-night stays | Minimum stay of one night (yes or no) |
| Amenity count | Amenities listed, per ten |

**Prescriptive (Objective 3).** We turn the results into a checklist, a cost test and an inspection plan.

**Checks against luck.** Three checks each answer one question:

1. *Is the group ranking stable?* We redraw hosts at random 1,000 times.
2. *Does the model work on unseen homes?* In 50 tests, it is built on 70% of hosts and picks a quarter of each priority group's homes among the rest. We compare its picks with a reduced model (no price or minimum stay) and with random picking.
3. *Do leading groups stay ahead?* We rank groups on one year and follow them into the next.

Homes of one host stay together in every check, because they can perform alike. The model assumes each 10% price step, or ten amenities, has the same effect anywhere; Appendix A finds little overlap between inputs and only weak curvature.

## 5. Analysis and Results

### 5.1 Data exploration: activity is uneven, and busy homes are well reviewed

Guest activity is very uneven (Figure 1). The median home received 15 reviews in the year; a quarter (981 homes, 25.3%) were busy, and 334 (8.6%) received none.

![Figure 1](final-report/report-2026-10-04/figures/figure_1_review_distribution.png)

**Figure 1.** Annual reviews per home, 3,873 analysis homes. Source of all figures and tables: Inside Airbnb (2026); Group 2 analysis.

Busy homes were slightly cheaper, but far more often accepted one-night stays and sat in the City of Melbourne (Table 3). Their higher revenue estimate comes from their review counts, not prices.

**Table 3. Busy homes compared with the rest**

| Characteristic | Busy (30+ reviews) | Not busy | All homes |
|---|---:|---:|---:|
| Homes | 981 | 2,892 | 3,873 |
| Median nightly price (AUD) | 254 | 266 | 262 |
| Accept one-night stays | 67.7% | 37.5% | 45.1% |
| In the City of Melbourne | 76.9% | 59.6% | 64.0% |
| Median estimated nights (cap 255) | 255 | 60 | 96 |
| Median estimated revenue (AUD a year) | 58,400 | 16,600 | 24,700 |
| Mean guest rating (out of 5 stars) | 4.84 | 4.69 | 4.73 |
| Reviews in the year with a negative tone | 1.6% | 2.9% | 2.2% |

Busy homes also had happier guests: a higher mean rating (4.84 against 4.69 stars) and fewer negative reviews (1.6% against 2.9%). We scored the 78,288 reviews with VADER, a standard word-list tool (Hutto & Gilbert, 2014); about 90% read as positive in both groups. High review counts therefore reflect satisfied guests, not complaints.

### 5.2 Descriptive analysis: City apartments lead

Shares of busy homes range from 8.2% to 36.6% across groups, and three groups lead (Figure 2, Table 4). The City groups stayed in the top three in 94% and 90% of host redraws, but Yarra Ranges houses in only 64%, so they are a less certain option (more checks in Table A3).

![Figure 2](final-report/report-2026-10-04/figures/figure_2_group_rates.png)

**Figure 2.** Share of busy homes in all 14 groups, with 90% ranges from redrawing hosts; priority groups in blue.

**Table 4. Priority groups: median estimated nights and annual revenue (AUD)**

| Group | Homes | Share busy | Nights, all homes | Revenue, all homes | Revenue rank | Revenue, not busy |
|---|---:|---:|---:|---:|---:|---:|
| City 3-bed apartments | 306 | 36.6% | 126 | 48,600 | 1 | 32,100 |
| City 2-bed apartments | 1,235 | 32.8% | 108 | 30,600 | 5 | 16,600 |
| Yarra Ranges 3-bed houses | 90 | 30.0% | 120 | 46,100 | 2 | 31,100 |
| All 14 groups | 3,873 | 25.3% | 96 | 24,700 | – | 16,600 |

**Activity and revenue rank groups differently.** On median revenue, Yarra Ranges houses rank second of 14 and City two-bedroom apartments fifth, because the houses charge more a night (AUD 426 against 285). Without rents, revenue cannot show which lease is better, so activity guides the search and revenue tests each lease.

### 5.3 Predictive analysis: one-night stays and price go with busy homes

Holding other inputs fixed, a typical City two-bedroom apartment has a **42%** chance of being busy with one-night stays, but **18%** with a two-night minimum or longer (Figure 3). Pricing 20% above similar homes lowers the chance to **36%**, and ten more amenities raise it to **48%**. The same apartment would score 26–27% in Port Phillip or Stonnington. These are associations, not guarantees.

![Figure 3](final-report/report-2026-10-04/figures/figure_3_factors.png)

**Figure 3.** Model-estimated chance that a typical City two-bedroom apartment is busy when one input changes, with 95% confidence intervals.

A two-setting rule captures most of this (Table 5). In the priority groups, half (50.4%) of homes with one-night stays priced at or below their group median were busy, against a third (33.4%) of all their homes and 9.3% with neither setting. Only 20 of 90 Yarra Ranges houses accept one-night stays, so the rule rests mainly on City apartments.

**Table 5. Share of busy homes in the three priority groups, by two settings**

| Minimum stay | Price at or below group median | Price above group median |
|---|---:|---:|
| One night accepted | 50.4% (462 homes) | 36.1% (477 homes) |
| Two nights or more | 30.2% (358 homes) | 9.3% (334 homes) |

On unseen hosts, 49.6% of the model's picks were busy, against 38.6% for the reduced model and 32.4% for random picking (Figure 4; full results in Tables A2 and A3). The rule matched the model (it picks 28% of homes), though we checked it only on the homes that suggested it. The model's value is in finding which settings matter; the client can apply them as a checklist.

![Figure 4](final-report/report-2026-10-04/figures/figure_4_screening.png)

**Figure 4.** Share of picked homes that were busy (a quarter of each priority group), averaged over 50 tests.

### 5.4 Over time: the leading groups stayed ahead

Ranked on the earlier year, the same three groups led ten groups (2,657 homes with two years of reviews): 33.6% of their homes reached 34 reviews, the earlier year's reference level, against 19.9% elsewhere (Figure 5). A year later they still led (27.1% against 14.9%), although Yarra Ranges houses fell to 21.4%.

![Figure 5](final-report/report-2026-10-04/figures/figure_5_two_years.png)

**Figure 5.** The same 2,657 homes in two consecutive years; target 34 reviews.

## 6. Key Findings and Recommendations

### Key findings

1. **Where:** City of Melbourne two- and three-bedroom apartments had the most busy homes, then, less certainly, Yarra Ranges three-bedroom houses. All three stayed ahead a year later and had above-median revenue (Figures 2 and 5, Table 4).
2. **What goes with being busy:** one-night stays and a price at or below similar homes (Figure 3, Table 5), though shorter stays partly inflate review counts.
3. **Satisfied guests:** busy homes were rated higher and drew fewer negative reviews (Table 3).
4. **Which home first:** the two settings picked busy homes about as well as the model (50.4% against 49.6%), though only the model was tested on unseen hosts (Table 5, Figure 4).

### Recommendations

1. **Search City of Melbourne two- and three-bedroom apartments first, then Yarra Ranges three-bedroom houses** (Figure 2, Table 4). Between leases that pass Recommendation 3, choose the larger cash-flow margin; if margins are similar, choose the group with more busy homes.
2. **Favour homes that can take one-night stays at a price at or below similar listings** (Figure 3, Table 5). At inspection, check that building rules allow one-night stays and that this price covers costs. Trial these settings and track the results (Table 6).
3. **Drop leases whose weekly costs exceed the group's typical revenue** (Figure 6). Typical weekly revenue is **AUD 590** for City two-bedroom apartments, **930** for City three-bedroom apartments and **890** for Yarra Ranges houses, but only half of homes reach it; homes that were not busy earned **AUD 320, 620 and 600**. Assess the remaining leases with their own cash-flow plans, and hold enough cash for a year at that lower level.

**Table 6. Four-week inspection plan**

| Timing and owner | Action | Decision condition |
|---|---|---|
| **Week 1** (Operator) | Pool ten candidate homes in the priority groups; check one-night stays and price | Inspect homes meeting both first, in group order |
| **Weeks 2–3** (Operator & Analyst) | Get written landlord consent; check owners' corporation rules on stays under 28 days (Consumer Affairs Victoria, n.d.); negotiate rent; get cost quotes | Replace homes that fail any check |
| **Week 4** (Client) | Cash-flow plan: quotes and Victoria's 7.5% short-stay levy (State Revenue Office Victoria, n.d.) against typical and not-busy revenue (Recommendation 3) | Sign only if the plan covers setup costs, required return and a year at the not-busy level |
| **First 30 days** (Operator) | Record paid nights, stay length, workload, net cash flow and reviews | Expand only if results match the plan |

![Figure 6](final-report/report-2026-10-04/figures/figure_6_weekly_reach.png)

**Figure 6.** Share of each priority group's homes whose estimated weekly revenue reached a given weekly cost.

**Worked example (illustrative costs).** A City two-bedroom apartment costing **AUD 620** a week in rent and running costs exceeds its group's typical AUD 590, so it is dropped. A Yarra Ranges house costing **AUD 700** clears its typical AUD 890. Earning like a home that is not busy (AUD 600), it would need a buffer of AUD 5,200 for the year.

## 7. Limitations and Future Work

- **Reviews are not bookings, profit or satisfaction.** Inside Airbnb's 50% review rate sits within published estimates of 30.5%–72% (Inside Airbnb, n.d.), so dollar figures are rough. Ratings are lifetime averages, and the text tool reads English best.
- **One snapshot of surviving homes.** Departed, new, unpriced and outer-area listings are missing, and revenue uses June–July prices. The two-year check uses the same snapshot.
- **Short stays inflate reviews.** A one-night minimum allows more stays for the same nights booked.
- **Associations, not causes.** Settings may respond to past performance, and we chose the inputs, rule and priority groups after seeing all homes.
- **No rent, cost or regulation data.** Recommendation 3 relies on the client's own quotes.

Future work should:

1. collect rent and cost quotes and track paid nights and net cash flow, to test whether busy homes are also profitable;
2. retest the groups, model and two-setting rule, unchanged, on the next snapshot;
3. read the negative reviews of priority-group homes to find problems an operator can fix.

## 8. References

Consumer Affairs Victoria. (n.d.). *Making rules to ban short stay accommodation*. Retrieved October 16, 2026, from [https://www.consumer.vic.gov.au/housing/owners-corporations/rules/making-rules-to-ban-short-stay-accommodation](https://www.consumer.vic.gov.au/housing/owners-corporations/rules/making-rules-to-ban-short-stay-accommodation)

Huang, E., & Xu, M. (2026). *Melbourne Airbnb market screening* [Source code]. GitHub. [https://github.com/maksym-xu/CMCE30005-TheNextChapter/tree/main](https://github.com/maksym-xu/CMCE30005-TheNextChapter/tree/main)

Hutto, C., & Gilbert, E. (2014). VADER: A parsimonious rule-based model for sentiment analysis of social media text. *Proceedings of the International AAAI Conference on Web and Social Media, 8*(1), 216–225. [https://doi.org/10.1609/icwsm.v8i1.14550](https://doi.org/10.1609/icwsm.v8i1.14550)

Inside Airbnb. (n.d.). *Data assumptions*. Retrieved October 16, 2026, from [https://insideairbnb.com/data-assumptions/](https://insideairbnb.com/data-assumptions/)

Inside Airbnb. (2026). *Melbourne, Victoria, Australia: Listings and reviews* (June 2026 snapshot, via CMCE30005 LMS) [Data set]. [https://insideairbnb.com/get-the-data/](https://insideairbnb.com/get-the-data/)

R Core Team. (2026). *R: A language and environment for statistical computing* (Version 4.5.3) [Computer software]. R Foundation for Statistical Computing. [https://www.R-project.org/](https://www.R-project.org/)

State Revenue Office Victoria. (n.d.). *Understanding the short stay levy*. Retrieved October 16, 2026, from [https://www.sro.vic.gov.au/owning-property/short-stay-levy/understanding-short-stay-levy](https://www.sro.vic.gov.au/owning-property/short-stay-levy/understanding-short-stay-levy)

### AI acknowledgement

ChatGPT, Gemini and Claude Code assisted with writing and coding; Eric Huang and Maksym Xu reviewed the outputs.

### Author contributions

Maksym Xu led data preparation, modelling and validation; Eric Huang led report drafting and review. Earlier team contributions are recorded in the repository guide.

## Appendix A. Model Details and Further Checks

In Table A1, each odds ratio multiplies the odds of being busy (busy homes per home that is not busy), averaged over the 50 fits; above 1 raises the chance, below 1 lowers it.

**Table A1. Odds ratios across 50 fits**

| Input (compared with) | Odds ratio | Range across fits |
|---|---:|---:|
| Accepts one-night stays (no) | 3.27 | 2.53–4.05 |
| Ten more amenities | 1.27 | 1.15–1.41 |
| Price 10% above similar homes | 0.88 | 0.83–0.94 |
| **Council area (City of Melbourne)** | | |
| Port Phillip | 0.50 | 0.33–0.66 |
| Stonnington | 0.48 | 0.26–0.68 |
| Yarra | 0.83 | 0.59–1.11 |
| Yarra Ranges | 1.22 | 0.76–1.97 |
| Merri-bek | 0.75 | 0.36–1.19 |
| House or townhouse (apartment) | 0.78 | 0.57–1.30 |
| Two bedrooms (one) | 1.16 | 0.89–1.41 |
| Three bedrooms (one) | 1.31 | 0.86–1.84 |

Ranges show stability across fits, not confidence intervals; those including 1 (for example, Yarra Ranges) leave the direction uncertain. Across all 14 groups, the model ranked a random busy home above a random home that was not busy 71% of the time, against 60% for group rates (AUC 0.71 and 0.60). Treating same-host homes as related widens margins of error to 1.1–2.6 times ordinary ones. Inputs overlap little (variance inflation factors below 3). An ordinary test of curved price and amenity effects suggests slight curvature (p = 0.03; amenities alone, p = 0.011), but this is unclear once same-host homes are treated as related (amenities, p = 0.17). Full evaluation tables are in the repository (Huang & Xu, 2026).

**Table A2. Hits and misses: top quarter picked across all 14 groups**

| Selection | Busy | Not busy | Total |
|---|---:|---:|---:|
| Picked by model | 423 | 546 | 969 |
| Not picked | 558 | 2,346 | 2,904 |

Each home was scored by a model built without its host (five folds of hosts). Of the 969 picked, 43.7% were busy (precision), against 25.3% overall, and they included 43.1% of busy homes (recall). Accuracy (71.5%) misleads: calling every home "not busy" scores 74.7%.

**Table A3. Further checks**

| Check | Result |
|---|---|
| Top three in 1,000 host redraws | City 3-bed 94%, City 2-bed 90%, Yarra Ranges 64% of redraws |
| Without the price rule, or without the one-year review rule | Same three groups; Yarra Ranges houses rank second |
| Minimum group size of 30 or 75 homes | Same three groups, same order |
| Two-year check with hosts weighted equally | Later-year lead of 8.7 points |
| Model against random picking, 50 tests | Model better in 46 tests |
| Reduced model (amenities only) against random picking | City 2-bed 38.9% vs 31.7%; City 3-bed 33.9% vs 35.9%; Yarra Ranges 49.7% vs 30.4% |

<!-- final report ends here -->

---

## Repository guide

| Folder | What it holds |
|---|---|
| `final-report/report-2026-10-04/` | The final report (PDF, Word, Markdown), its six figures, the revision and feedback evidence scripts and their outputs, and the scripts that build and check the report |
| `final-report/screening-followup-2026-10-03/` | The main model test: picking 25% of homes within each priority group (49.6% / 38.6% / 32.4%), plus 10% and 50% quotas |
| `final-report/paired-analysis-2026-10-02/` | The 50 repeated host splits comparing the model with group rates across all groups (AUC, Brier score, shortlist rates) |
| `final-presentation/` | The final presentation, its speaking script and its analysis package (the six-input logistic model, scenario chances, confusion counts) |
| `scripts/` | Data cleaning (`01`), sample and review target (`rq_scope_feasibility.py`), group ranking with host resampling (`08`), interim-stage models (`09`–`13`) and the two-year check (`validation/temporal_holdout.py`) |
| `reports/` | The interim report, interim-stage tables and figures, and supporting analyses |
| `config/review_analysis.json` | Eligibility rules, review-target design and random seed |
| `tests/` | Unit tests for cleaning, sample design and the group-rate baseline |

## How to reproduce the results

The three course CSV files (listings, reviews and calendar) are not published. Place them in `data/raw/` as `listings_airbnb.csv`, `reviews_airbnb.csv` and `calendar_airbnb.csv`. Software: R 4.5.3 with data.table, jsonlite, sandwich, ggplot2, scales, digest and stringr; Python 3.12 with the packages in `requirements-analysis.txt`, plus matplotlib, python-docx and pypdf for the report files. Run from the repository root:

1. `Rscript scripts/01_data_cleaning.R` (cleaned listings and review counts in `data/processed/`)
2. `python scripts/rq_scope_feasibility.py` (sample, reference hosts and the 30-review target)
3. `Rscript scripts/08_peer_ranking.R` (14 group rates with host-resampled ranges)
4. `python scripts/validation/temporal_holdout.py` (two-year check)
5. In `final-presentation/analysis/`: `mkdir -p private-inputs && Rscript scripts/prepare_private_input.R ../..`, then `sh run.sh` (six-input model)
6. In `final-report/paired-analysis-2026-10-02/`: copy `analysis_input.csv` and `../../final-presentation/analysis/working/oof_predictions_PRIVATE.csv` (renamed `legacy_oof_predictions_PRIVATE.csv`) into `private-inputs/`, then `bash run.sh`
7. In `final-report/screening-followup-2026-10-03/`: copy `analysis_input.csv` and the paired package's `working/test_predictions_PRIVATE.csv` and `working/split_membership_PRIVATE.csv` (prefixed `prior_`) into `private-inputs/`, then `bash run.sh`
8. Copy `analysis_input.csv` into `final-report/report-2026-10-04/private-inputs/`, then run `Rscript final-report/report-2026-10-04/scripts/revision_evidence.R`, `Rscript final-report/report-2026-10-04/scripts/feedback_checks.R`, `python final-report/report-2026-10-04/scripts/review_sentiment.py` (needs `vaderSentiment`), `python final-report/report-2026-10-04/build_figures.py` and `python final-report/report-2026-10-04/scripts/build_report_docx.py`; export the PDF from Word; check with `python final-report/report-2026-10-04/scripts/check_report_package.py`

On 17 October 2026, all eight steps were re-run from the three course CSV files, whose SHA-256 fingerprints match those in `data/processed/cleaning_manifest.json`. Every committed number and figure was reproduced; the only differences were run dates, software version labels and rounding below 10⁻¹⁵ in the interim-stage random forest. All unit tests passed.

## Contributions

Maksym Xu led data preparation, modelling and validation; Eric Huang led report drafting and review.

Project history: Qihang Sun and Loc Le were members until the interim stage and co-authored the interim report and presentation; Qihang Sun also set up the repository and contributed early analysis. Earlier files keep the original four-member team details.
