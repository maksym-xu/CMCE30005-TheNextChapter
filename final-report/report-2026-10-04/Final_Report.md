# Melbourne Airbnb Market Screening

**CMCE30005 Final Project Report | Group 2**
**Eric Huang and Maksym Xu**

**Project repository:** [https://github.com/maksym-xu/CMCE30005-TheNextChapter](https://github.com/maksym-xu/CMCE30005-TheNextChapter/tree/final-report-marking-fixes-2026-10-16) (branch final-report-marking-fixes-2026-10-16)

## 1. Introduction

Our client plans to lease homes in Greater Melbourne and let them as short stays through Airbnb. Rent and setup costs are paid before any guest income arrives, so a lease in the wrong place ties up scarce startup funds. This report shows where to search and which homes to inspect first.

We recommend searching two- and three-bedroom apartments in the City of Melbourne first, with three-bedroom houses and townhouses in Yarra Ranges as a second option. These groups had the highest shares of homes with strong guest activity, and their typical homes brought in an estimated AUD 30,600–48,600 a year, against AUD 24,700 for all homes studied.

Within these groups, a simple model picks homes that reach our activity target about half the time (49.6%), against one in three (32.4%) at random. It ranks only homes already on Airbnb; for other rentals, use the group order and the checks in Section 6.

## 2. Problem Definition and Objectives

The business question is: **where should a rent-to-rent operator with limited funds search, and which homes should it inspect first?** We set three objectives:

1. Rank property groups by the share of homes with strong guest activity, and translate this into estimated nights and revenue.
2. Test whether a simple model picks better homes within the leading groups than random picking.
3. Turn the results into a search order and a four-week inspection plan.

A **group** combines council area, dwelling type and bedroom count. A home is **busy** (it reaches our **target**) when it receives at least 30 guest reviews in the 365 days before data collection, a level reached by a quarter of separate reference homes (Section 3). Inside Airbnb (n.d.) assumes half of stays are reviewed, each lasting at least three nights, and caps estimated nights at 70% of the year (255); on that rule, 30 reviews means about 180 booked nights a year.

We rank on reviews rather than revenue because Inside Airbnb's revenue estimate multiplies these review-based nights by the advertised price, and without rents a higher price does not mean a better lease; we report revenue alongside. Rents, costs and profit are outside our data.

Building on the interim report, we keep its group comparison, replace its hard-to-explain random forest with one logistic regression, and add a test within the leading groups.

## 3. Data Description and Preparation

We use one Inside Airbnb snapshot of Melbourne, supplied through the subject LMS and collected between 17 June and 1 July 2026 (Inside Airbnb, 2026). It holds 25,728 listings with 90 fields and 1,026,690 dated reviews. We did not use the calendar, which cannot separate bookings from blocked nights.

Cleaning converted price text to numbers, treated "NA" as missing and counted amenities. We rebuilt annual review counts from review dates over exactly 365 days; the supplied count covers 366 days. Price is missing for 6,553 listings (25%) and bedrooms for 4,679 (18%); 4,477 listings (17%) have never been reviewed.

We keep entire rental units and condos (*apartments*) and entire homes and townhouses (*houses/townhouses*) with one to three bedrooms. Each home needs a nightly price of AUD 30–1,500, which removes unpriced listings and extreme prices, and a first review at least a year before collection, so a full year of activity is visible.

So that the target is not set by the homes we then compare, we set aside about one in five hosts. Their 906 homes in the final groups set the target: about one in four received 30 or more reviews (75th percentile 29.75, rounded up; Table 1).

**Table 1. From the supplied listings to the analysis sample**

| Step | Homes |
|---|---:|
| All listings in the snapshot | 25,728 |
| Entire homes with one to three bedrooms | 16,576 |
| Apartments, condos, houses and townhouses | 14,895 |
| Priced AUD 30–1,500 | 11,099 |
| First review at least a year before collection | 6,891 |
| After setting aside reference hosts | 5,549 |
| **Analysis sample: 14 groups with at least 50 homes** | **3,873** |
| Reference homes in the same 14 groups (target only) | 906 |

The 3,873 analysis homes belong to 1,726 hosts in six council areas; 64% are in the City of Melbourne. The price rule mainly removes inactive listings: 77.8% of the 3,796 residential listings it removes had no review in the past year, against 17.0% of those kept.

## 4. Methodology

**Group comparison.** We compare the share of busy homes in the 14 groups. To show how much a share could move by chance, we redraw hosts at random 1,000 times and report the middle 90% of results, keeping each host's homes together.

**Model.** Logistic regression estimates the chance that a home is busy. Each input adds to or subtracts from a score, which is turned into a chance between 0% and 100%. Table 2 lists the outcome and the six inputs.

**Table 2. Outcome and inputs of the model**

| Variable | Definition |
|---|---|
| **Outcome** | 1 if the home had at least 30 reviews in the year, otherwise 0 |
| Council area | One of six council areas |
| Dwelling type | Apartment, or house/townhouse |
| Bedrooms | One, two or three |
| Price compared with similar homes | Nightly price relative to the median of the same group, in steps of 10% |
| Accepts one-night stays | Minimum stay of one night (yes or no) |
| Amenity count | Number of amenities listed, in steps of ten |

We compare this **full model** with two simpler options. The **group rate**, a group's share of busy homes, scores all its homes equally; within a group, this is **random picking**. The **reduced model** drops price and minimum stay, which an unlisted home does not yet have.

**Assumptions.** A host's homes tend to perform alike; allowing for this widens each effect's margin of error 1.1–2.6 times, so every test keeps a host's homes together. The inputs barely overlap: a standard check (variance inflation factor) stays below 3, under the usual warning level of 5. Each input is assumed to have a steady effect; amenities flatten slightly at high counts, but not reliably once hosts are grouped.

**Testing.** We ran 50 tests. Each builds the model from 70% of hosts and scores the homes of the other 30%, which it has never seen. In each priority group, each method picks a quarter of the test homes, and we compare the share that were busy.

**Two-year check.** For 2,657 homes with two years of reviews, in ten groups, we chose the top three groups on the earlier year and followed them into the later year (target 34 reviews, set from the earlier year's reference homes).

## 5. Analysis and Results

### 5.1 Data exploration: most homes are quiet, and busy homes accept one-night stays

Guest activity is very uneven (Figure 1). The middle (median) home received 15 reviews, a quarter received 30 or more, and 334 homes (8.6%) received none.

![Figure 1](figures/figure_1_review_distribution.png)

**Figure 1.** Annual reviews per home, 3,873 analysis homes. Source: Inside Airbnb (2026); Group 2 analysis.

**Table 3. Busy homes compared with the rest**

| Characteristic | Busy (30+ reviews) | Below 30 | All homes |
|---|---:|---:|---:|
| Homes | 981 | 2,892 | 3,873 |
| Median nightly price (AUD) | 254 | 266 | 262 |
| Median amenity count | 44 | 43 | 43 |
| Accept one-night stays | 67.7% | 37.5% | 45.1% |
| Minimum stay seven nights or more | 0.0% | 5.7% | 4.3% |
| In the City of Melbourne | 76.9% | 59.6% | 64.0% |
| Median estimated nights booked (cap 255) | 255 | 60 | 96 |
| Median estimated revenue (AUD a year) | 58,400 | 16,600 | 24,700 |

Busy homes were slightly cheaper and listed about as many amenities (Table 3). They were far more likely to accept one-night stays and to be in the City of Melbourne, and none of the 165 homes requiring seven nights or more was busy. Their estimated revenue was 3.5 times higher, but it is built from reviews, and 255 nights is Inside Airbnb's cap.

### 5.2 Descriptive comparison: City apartments are the first search priority

Group rates range from 8.2% to 36.6% against 25.3% overall (Figure 2). City of Melbourne three-bedroom apartments lead at 36.6% (112 of 306 homes), followed by City two-bedroom apartments at 32.8% (405 of 1,235) and Yarra Ranges three-bedroom houses and townhouses at 30.0% (27 of 90).

![Figure 2](figures/figure_2_group_rates.png)

**Figure 2.** Share of busy homes in all 14 groups, with 90% ranges from redrawing hosts; priority groups in blue. Source: Inside Airbnb (2026); Group 2 analysis.

**Table 4. The three priority groups in nights and dollars**

| Group | Homes | Busy | Median price (AUD a night) | Accept one night | Median nights booked (estimated) | Median revenue (AUD a year, estimated) |
|---|---:|---:|---:|---:|---:|---:|
| City · 3-bed apartments | 306 | 36.6% | 450 | 58.8% | 126 | 48,600 |
| City · 2-bed apartments | 1,235 | 32.8% | 285 | 59.8% | 108 | 30,600 |
| Yarra Ranges · 3-bed houses | 90 | 30.0% | 426 | 22.2% | 120 | 46,100 |
| All 14 groups | 3,873 | 25.3% | 262 | 45.1% | 96 | 24,700 |

Each priority group's estimated revenue beats the all-group median, although City two-bedroom apartments rank only fifth of 14 (Table 4); prices are advertised nightly rates, not rents. The same three groups lead when the price rule or the review-history rule is removed. The two City groups are the most reliable, staying in the top three in 94% and 90% of 1,000 host redraws; Yarra Ranges houses did so in only 64%, a less certain second option.

### 5.3 Predictive screening: the model improves selection within the priority groups

Picking a quarter of homes within each priority group, the full model found busy homes 49.6% of the time, against 38.6% for the reduced model and 32.4% for random picking (Figure 3). That is five busy homes instead of three in a list of ten.

![Figure 3](figures/figure_3_screening.png)

**Figure 3.** Share of picked homes that were busy, averaged over 50 tests. Source: Inside Airbnb (2026); Group 2 analysis.

The full model beat random picking in 46 of the 50 tests; the middle 90% of its gains ran from −0.7 to +31.8 percentage points, so results depend on the homes available.

Table 5 splits hosts into five parts, scores each home with a model built from the other four, and picks the top quarter overall. Of picked homes, 43.7% were busy (the hit rate, or precision), against 25.3% of all homes; the picks found 43.1% of all busy homes (recall). Accuracy misleads: the model is right 71.5% of the time, yet calling every home "below target" scores 74.7% and finds no busy home.

**Table 5. Hits and misses (confusion matrix): top quarter picked across all 3,873 homes**

| | Busy | Below target | Total |
|---|---:|---:|---:|
| Picked by model | 423 | 546 | 969 |
| Not picked | 558 | 2,346 | 2,904 |

With other inputs unchanged, the model gives a typical City two-bedroom apartment a 42% chance of being busy if it accepts one-night stays and 18% if it requires two nights or more. With ten more amenities the chance is 48%; priced 20% above similar homes, it is 36% (odds ratios in Appendix A). These are associations in past data, not proof that changing a setting causes more bookings.

Price and minimum stay carry most of the gain; without them, the reduced model did worse than random in City three-bedroom apartments (33.9% against 35.9%).

### 5.4 Prescriptive trade-off: inspection capacity sets list length

Shorter lists have a higher hit rate; longer lists find more busy homes (Table 6).

**Table 6. Inspection capacity within the priority groups (averages of 50 tests)**

| Share of homes inspected in each group | Hit rate (precision) | Share of busy homes found (recall) | Gain over random picking (percentage points) |
|---|---:|---:|---:|
| 10% | 54.5% | 17.1% | +22.0 |
| 25% | 49.6% | 38.3% | +17.2 |
| 50% | 43.1% | 66.7% | +10.7 |

Our plan (Table 7) starts with ten candidates, adding more if checks rule homes out.

### 5.5 Over time: the leading groups stayed ahead

In the earlier year, 33.6% of homes in the top three groups reached 34 reviews, against 19.9% in the other seven; this gap reflects how the groups were chosen. In the later year they still led, 27.1% against 14.9%, a gap of about 12 percentage points, or 8.7 counting each host once (Figure 4).

![Figure 4](figures/figure_4_two_years.png)

**Figure 4.** The same 2,657 homes in two consecutive years; target 34 reviews. Source: Inside Airbnb (2026); Group 2 analysis.

## 6. Key Findings and Recommendations

**Key findings**

1. **Where:** City of Melbourne two- and three-bedroom apartments had the highest shares of busy homes and above-median estimated revenue; Yarra Ranges three-bedroom houses follow but are less certain. All three stayed ahead a year later (Figures 2 and 4, Table 4).
2. **How homes are run:** busy homes more often accept one-night stays and charge slightly less than similar homes (Table 3, Section 5.3).
3. **Which home first:** within the priority groups, the model raises the hit rate from one in three to one in two (Figure 3).

**Recommendations**

1. **Search City of Melbourne two- and three-bedroom apartments first**; use Yarra Ranges three-bedroom houses only if City leases are unsuitable.
2. **Order candidates with the model where comparable listings exist.** For an unlisted rental, price near similar listings and trial one-night stays where allowed, tracking paid nights and cleaning costs.
3. **Drop a candidate whose weekly rent and running costs exceed its group's typical weekly gross estimated revenue**: about AUD 590 for City two-bedroom apartments, AUD 930 for City three-bedroom apartments and AUD 890 for Yarra Ranges houses (Table 4, divided by 52). Then obtain the landlord's written consent and confirm that the owners' corporation has not banned stays under 28 days (Consumer Affairs Victoria, n.d.). Such stays also attract Victoria's 7.5% short-stay levy, collected through Airbnb (State Revenue Office Victoria, n.d.).

**Table 7. Proposed four-week first inspection round**

| Timing and owner | Action | Decision condition |
|---|---|---|
| **Week 1** (Operator) | Find ten available candidates in the priority groups; order established homes with the model | Use the group order alone for unlisted rentals |
| **Weeks 2–3** (Operator & Analyst) | Confirm consent and building rules, obtain cost quotes, compare rent with Table 4 | Replace homes that fail any check |
| **Week 4** (Client) | Compare cash flow under expected demand and weak demand (60 nights a year, the below-target median in Table 3) | Sign only if both cases cover rent and keep a cash buffer |
| **First 30 days of operation** (Operator) | Record paid nights, stay length, workload and net cash flow alongside reviews | Expand only if results match the plan |

## 7. Limitations and Future Work

- **Reviews are not bookings or profit.** Inside Airbnb's 50% review rate sits within published estimates of 30.5–72% (Inside Airbnb, n.d.), so the dollar figures are rough, and activity fell in the later year (Figure 4).
- **One snapshot of surviving homes.** Homes that left Airbnb are missing, including from the two-year check, and revenue uses June–July prices. New entrants, unpriced listings and outer areas are not covered.
- **Short stays inflate reviews and revenue.** A one-night minimum allows more stays for the same nights booked, so part of its effect is built into the measure; counting each stay as three nights may also overstate these homes' revenue.
- **Associations, not causes.** Settings were recorded at collection and may respond to earlier performance. We chose the one-night input after seeing no seven-night home reach the target, and chose the priority groups from all homes, so the 50 tests may overstate the gain.
- **No rent, cost or regulation data.** Recommendation 3 relies on the client's own quotes.

Future work should freeze the groups, model and selection rule, then test them on the next snapshot and the client's own homes.

## 8. References

Consumer Affairs Victoria. (n.d.). *Making rules to ban short stay accommodation*. Retrieved October 16, 2026, from [https://www.consumer.vic.gov.au/housing/owners-corporations/rules/making-rules-to-ban-short-stay-accommodation](https://www.consumer.vic.gov.au/housing/owners-corporations/rules/making-rules-to-ban-short-stay-accommodation)

Huang, E., & Xu, M. (2026). *Melbourne Airbnb market screening* [Source code and analysis results]. GitHub. [https://github.com/maksym-xu/CMCE30005-TheNextChapter/tree/final-report-marking-fixes-2026-10-16](https://github.com/maksym-xu/CMCE30005-TheNextChapter/tree/final-report-marking-fixes-2026-10-16)

Inside Airbnb. (n.d.). *Data assumptions*. Retrieved October 16, 2026, from [https://insideairbnb.com/data-assumptions/](https://insideairbnb.com/data-assumptions/)

Inside Airbnb. (2026). *Melbourne, Victoria, Australia: Listings and reviews* (snapshot of 16 June 2026, supplied through the CMCE30005 LMS) [Data set]. [https://insideairbnb.com/get-the-data/](https://insideairbnb.com/get-the-data/)

R Core Team. (2026). *R: A language and environment for statistical computing* (Version 4.5.3) [Computer software]. R Foundation for Statistical Computing. [https://www.R-project.org/](https://www.R-project.org/)

State Revenue Office Victoria. (n.d.). *Understanding the short stay levy*. Retrieved October 16, 2026, from [https://www.sro.vic.gov.au/owning-property/short-stay-levy/understanding-short-stay-levy](https://www.sro.vic.gov.au/owning-property/short-stay-levy/understanding-short-stay-levy)

### AI acknowledgement

ChatGPT, Gemini and Claude Code assisted with writing and coding; Eric Huang and Maksym Xu reviewed the outputs.

### Author contributions

Maksym Xu led data preparation, modelling and validation; Eric Huang led report drafting and review. Loc Le and Qihang Sun co-authored the interim report and presentation before leaving; Qihang Sun also set up the repository.

## Appendix A. Model Details

The model is a standard logistic regression fitted in R (R Core Team, 2026). Group median prices and the three missing minimum stays are filled from training homes only. The group rate is smoothed as (group successes + 10 × overall rate) / (group homes + 10). Odds are the chance of being busy divided by the chance of not being busy. Table A1 gives each input's odds ratio (mean of 50 test fits) and its range; above 1 means a higher chance of being busy, below 1 a lower one.

**Table A1. Odds ratios for all inputs across 50 fits**

| Input (compared with) | Odds ratio | Range across fits |
|---|---:|---:|
| Accepts one-night stays (no) | 3.27 | 2.53–4.05 |
| Ten more amenities | 1.27 | 1.15–1.41 |
| Price 10% above similar homes | 0.88 | 0.83–0.94 |
| Port Phillip (City of Melbourne) | 0.50 | 0.33–0.66 |
| Stonnington (City of Melbourne) | 0.48 | 0.26–0.68 |
| Yarra (City of Melbourne) | 0.83 | 0.59–1.11 |
| Yarra Ranges (City of Melbourne) | 1.22 | 0.76–1.97 |
| Merri-bek (City of Melbourne) | 0.75 | 0.36–1.19 |
| House or townhouse (apartment) | 0.78 | 0.57–1.30 |
| Two bedrooms (one) | 1.16 | 0.89–1.41 |
| Three bedrooms (one) | 1.31 | 0.86–1.84 |

Across the 50 tests on all 14 groups, the model ranked a random busy home above a random quiet one 71% of the time, against 60% for group rates (AUC 0.71 and 0.60). Other evaluation designs are in `final-report/report-2026-10-04/README.md` (Huang & Xu, 2026).
