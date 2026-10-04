# Melbourne Airbnb Market Screening

## 1. Introduction

Our client plans to rent residential properties and offer short stays through Airbnb. Choosing a property means committing to rent and setup costs before knowing how much guest income it will generate. With limited startup funds, the client needs to decide where to look and which homes deserve a closer inspection.

We use the Melbourne Inside Airbnb dataset supplied through the subject LMS to help make these choices. Dated guest reviews provide a record of past guest activity. We compare this activity across property groups, then test whether a simple model helps select homes within the most promising groups.

We recommend starting with two- and three-bedroom apartments in the City of Melbourne. Three-bedroom houses and townhouses in Yarra Ranges offer another search option. Within these groups, 49.6% of homes selected by the model reach at least 30 annual reviews on average, compared with 32.4% using group rates alone. We explain how the client can use these findings to organise a search and assess candidates before signing a lease.

## 2. Problem Definition and Objectives

The client faces two decisions. First, which parts of the market deserve attention? Second, how should the client narrow the list of properties found there? We address them through two research questions:

1. Which property groups have the strongest historical guest-review activity?
2. Does information about individual homes improve selection beyond each group's historical rate?

A group combines council area, dwelling type and bedroom count. Our analysis covers standard entire homes with one to three bedrooms and at least one year of recorded review history. We define high review activity as at least 30 reviews in the preceding 365 days. This threshold comes from the upper quarter of a separate reference sample.

Since the interim report, we have replaced the more complex model with logistic regression and added 50 repeated comparisons, including tests within the three priority groups. All completed analysis uses the supplied dataset.

## 3. Data Description and Preparation

The dataset contains 25,728 listings collected between 17 June and 1 July 2026 (Inside Airbnb, 2026). We match property details to dated reviews and count reviews in the 365 days before each property's collection date. Calendar availability cannot separate bookings from dates blocked by the host, so we use dated reviews to measure recorded guest activity.

We keep entire rental units, condos, homes and townhouses with one to three bedrooms. We combine rental units and condos as apartments/units, and homes and townhouses as houses/townhouses. These types fit the client's leasing business. Homes need a quoted nightly price of AUD30-1,500 and a first review at least 365 days before collection. The price range is an initial analysis boundary; the history rule provides a longer review record.

We set aside reference hosts before modelling, dividing the 6,891 eligible homes into 5,549 analysis homes and 1,342 reference homes. Keeping groups with at least 50 analysis homes provides a minimum base for comparison. Table 1 shows the sample.

**Table 1. How the comparison sample is formed**

| Population | Listings |
|---|---:|
| Supplied snapshot | 25,728 |
| Entire homes with one to three bedrooms | 16,576 |
| Four standard dwelling types | 14,895 |
| Eligible prices and review history | 6,891 |
| Analysis population before minimum group size | 5,549 |
| Final analysis sample in 14 groups | 3,873 |
| Separate reference population before group restriction | 1,342 |
| Reference within the same 14 groups | 906 |

The final comparison uses 3,873 homes from 1,726 hosts across six council areas. About 64% are in the City of Melbourne. The median home has 15 annual reviews, and 334 homes, or 8.6%, have none. Keeping these zero-review homes makes quieter listings part of the comparison.

A separate full-snapshot price check excludes 6,801 listings with missing or out-of-range prices. The supplied recent-review count is zero for 82% of these listings, compared with 23.7% of retained listings. Price screening therefore favours more active homes. Our comparison focuses on established, priced homes.

The 906 reference homes give an upper-quarter cutoff of 29.75 reviews, rounded up to 30. Their hosts stay outside model training and testing. Category definitions were fixed after earlier exploration. Each training sample supplies missing-value replacements and comparable-price medians. Three homes lack minimum-stay values; we fill their one-night acceptance category with the most common training category. Appendix A gives the preparation details.

## 4. Methodology

We begin with a straightforward comparison: what share of homes in each group reach 30 annual reviews? We also resample hosts and recalculate the shares to show how much the results vary. Each host's properties stay together because they can share management practices.

For individual homes, we use logistic regression in R (R Core Team, n.d.). It suits our two possible outcomes: a home either reaches 30 reviews or falls below that level. The model learns weights from training homes for six inputs: council area, dwelling type, bedrooms, price compared with similar homes, acceptance of one-night stays and number of amenities. It adds their weighted contributions to form a ranking score. Across the 50 fits, lower relative prices, one-night acceptance and more amenities raise the score when other inputs stay the same. Higher-scoring homes come earlier in the investigation list.

The group-rate baseline uses each group's training rate, adjusted towards the overall training rate. Homes in the same group receive the same score, leaving them equally ranked. We also test a reduced model without price and minimum-stay information to measure how much those two inputs add together.

We test the methods 50 times. Each time, 70% of hosts provide training homes and the remaining 30% provide test homes. Homes from the same host always stay on the same side. All methods see the same test homes and select the same number for investigation.

Our main test selects 25% of homes separately within each priority group, asking whether the model helps once the search areas are decided. We average the selected homes' target rate over 50 tests. Trying 10% and 50% lists shows the effect of changing investigation capacity. Appendix A explains rounding and equal treatment of tied scores.

Finally, we reconstruct two annual review windows from the same snapshot for homes with longer histories. We identify the earlier leading groups and check their performance in the later year. That comparison uses its own 34-review target, set from the earlier reference window.

## 5. Analysis and Results

### 5.1 City apartments provide a clear starting point

Across the full analysis sample, 981 of 3,873 homes reach 30 annual reviews, or 25.3%. Group rates range from 8.2% to 36.6%. A single average would hide these differences.

City of Melbourne three-bedroom apartments have the highest observed rate: 112 of 306 homes reach the target, or 36.6%. Two-bedroom apartments follow at 32.8%, with 405 of 1,235 homes qualifying. Yarra Ranges three-bedroom houses and townhouses reach 30.0%, or 27 of 90 homes. The two city groups combine stronger observed activity with larger samples, making them our first search priority.

![Three priority property groups](figures/figure_1_priority_groups.png)

**Figure 1.** Homes reaching at least 30 annual reviews. Horizontal lines show 90% ranges from resampling hosts; the dashed line marks the overall 25.3%. Appendix B shows all 14 groups.

The same three groups remain when the minimum size is 30 or 75 homes, or when we remove the price or history restriction. Broader rules can swap second and third place. The useful result is the shortlist of three groups. Specialised accommodation changes that list, so we keep the residential scope that matches the client's search.

### 5.2 The model helps narrow the list within these groups

Choosing a group still leaves many homes to investigate. The complete model helps with this next decision. When each method selects 25% within each priority group, the selected homes' average historical target rate is 49.6% for the complete model, 38.6% for the reduced model and 32.4% for the group-rate baseline.

The complete model's gain is 17.2 percentage points. In practical terms, a list of 100 selected homes contains about 17 more homes with at least 30 annual reviews than a list selected using group rates alone. The model improves the concentration of past guest activity in the investigation list.

![Historical screening results within the priority groups](figures/figure_2_paired_screening.png)

**Figure 2.** Average historical target rates over 50 tests. Each method selects 25% within each priority group. The reduced model leaves out price and minimum-stay information.

The complete model beats the baseline in 46 of the 50 tests and falls behind in four. This supports using it to prioritise investigations within the chosen groups. Gains vary across the overlapping test samples, so use the average improvement as a planning reference.

Price and minimum-stay information make a substantial difference. Including them raises the average selected rate by 11.0 percentage points over the reduced model. Within a fixed group, the reduced model can distinguish homes only by amenity count. In City of Melbourne three-bedroom apartments, its rate is 33.9%, below the baseline's 35.9%. Our recommendation is therefore to use the complete model for homes with comparable operating information. Group comparisons provide the starting point when that information is unavailable.

### 5.3 Investigation capacity changes what the client finds

A smaller list concentrates attention on homes with stronger historical activity. A larger list finds more of the homes that reach the target. Table 2 shows this trade-off for the complete model within the three priority groups.

**Table 2. Results at different investigation capacities**

| Share investigated in each group | Share of selected homes reaching 30 reviews | Share of all qualifying homes found |
|---|---:|---:|
| 10% | 54.5% | 17.1% |
| 25% | 49.6% | 38.3% |
| 50% | 43.1% | 66.7% |

Values are averages over the 50 tests. At 10% capacity, more than half the selected homes reach the target, but the list finds only 17.1% of all qualifying homes in these groups. At 50%, it finds about two-thirds. The model improves on the baseline at every tested capacity on average, by 22.0, 17.2 and 10.7 percentage points respectively.

Use the 25% results to assess investigation capacity. Begin the practical search with ten candidates, then prioritise detailed checks according to available operating information. Widen the pool when too few homes meet the client's requirements.

### 5.4 Earlier leading groups stay ahead in the following year

The two-year comparison follows 2,657 homes across ten groups. At the fixed 34-review target, 27.1% of homes in the earlier top-three groups qualify in the later year, compared with 14.9% elsewhere. They retain an advantage of around 12 percentage points.

![Historical group advantage across two annual windows](figures/figure_3_historical_persistence.png)

**Figure 3.** The same homes are compared in both years. The earlier leading groups remain ahead, although their qualifying share falls from 33.6% to 27.1%.

The earlier leaders stay ahead as activity falls. Keep them on the search list and check current conditions for each property.

## 6. Key Findings and Recommendations

Search City of Melbourne two- and three-bedroom apartments first. Consider Yarra Ranges three-bedroom houses and townhouses when city homes have unsuitable lease terms or limited availability.

Use the complete model to rank established homes with comparable price, minimum-stay and amenity information. For new rental candidates, use the priority groups to organise the search and compare permissions, rent and operating costs. Scores from proposed settings serve as scenario comparisons. Test these rankings on new openings before using them to choose properties.

Before signing, confirm permitted short-stay use in writing and obtain rent, setup and operating cost quotes. Assess achievable nightly rates and paid nights. Proceed when the expected and downside cash flows meet the client's agreed return and cash-buffer requirements.

**Table 3. Proposed first investigation round**

| Timing and owner | Action | Decision condition |
|---|---|---|
| Week 1 operator | Find ten initial candidates and prioritise checks using available operating information | Confirm availability; use group priorities for new rentals |
| Weeks 2 and 3 operator and analyst | Check permissions, obtain quotes and assess guest demand | Keep incomplete cases pending and reject homes that fail requirements |
| Week 4 client | Compare the qualified homes and their cash-flow estimates | Proceed when downside cash flow and cash-buffer requirements are met |
| Operating trial operator | Record paid nights, workload and net cash flow | Review actual results before expanding |

The ten homes form the initial pool. Investigate higher-priority homes first and replace rejected candidates. Ten candidates and 30 days are planning limits; extend the search when needed. If practical testing finds little benefit from the model, use group rates as the main guide.

## 7. Limitations and Future Work

The findings support a focused search. Profitability still depends on paid nights, stay length and costs, which reviews do not measure directly. A trial should record these outcomes alongside review activity.

Our sample covers established homes in selected areas. A first review shows the length of the review record, and continuous operation remains unknown. The next coverage check should include new entrants and other areas. Leaving price out of the model also leaves the original price-filtered sample unchanged.

Price and minimum-stay settings were recorded at collection and can reflect earlier performance. Their combined contribution supports screening with that information; the effect of changing either setting needs a separate prospective test.

The next validation should freeze the chosen groups, model and selection rule before testing newly observed outcomes. The current 50 comparisons reuse records and follow earlier exploration. We should also check how well scores match observed rates before presenting them as individual probabilities. Appendix A records the uncertainty in the published comparisons.

## 8. References

Inside Airbnb. (2026). *Melbourne listings and dated reviews* [Dataset supplied through CMCE30005 LMS, collected 17 June-1 July 2026].

R Core Team. (n.d.). *Fitting generalized linear models glm*. [R documentation](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/glm.html).

TheNextChapter. (2026). *Project analysis and screening follow-up*, revision e4c68ca. [Frozen analysis repository](https://github.com/maksym-xu/CMCE30005-TheNextChapter/tree/e4c68cae863e35bd1e7df0af4738c41b589f0bad).

OpenAI. (2026). *ChatGPT assistance with project planning, interpretation, drafting and editing* [Project-specific generative AI outputs].

Anthropic. (2026). *Claude Code assistance with analysis-code development* [Project-specific generative AI outputs].

### AI acknowledgement

The group used ChatGPT for planning, interpreting results, drafting and editing, and Claude Code for analysis-code development. The group reviewed AI-assisted text and code. Numerical results come from analysis of the supplied dataset. The group remains responsible for the submission.

## Appendix A. Model specification and comparison evidence

The complete model uses unpenalised logistic regression. Area, dwelling type, bedrooms and one-night acceptance are categorical. Reference levels are Melbourne, apartment/unit, one bedroom and no one-night acceptance. Relative price is `(price / training group median - 1) * 10`; amenities are divided by ten. Training modes fill missing acceptance categories, and the overall training median covers an unseen price group. The baseline is `(group positives + 10 * overall positive share) / (group count + 10)`. The reduced model retains area, dwelling type, bedrooms and amenities and is refitted on each training set. All 50 reduced fits converge without warnings.

**Table A1. Separate evaluation designs at 25 percent capacity**

| Evaluation | Complete model | Baseline | Gain in percentage points |
|---|---:|---:|---:|
| Pooled five-fold all eligible homes | 43.65% | 28.07% | 15.58 |
| Mean of 50 allocations all eligible homes | 43.42% | 31.96% | 11.46 |
| Mean of 50 allocations three groups in one pool | 48.91% | 32.37% | 16.54 |
| Mean of 50 allocations separate group quotas | 49.62% | 32.43% | 17.19 |

Five-fold evaluation gives each home one held-out score. Its 969 model selections include 423 reaching target and 546 below, with another 558 target-reaching homes outside the list. Repeated tests reuse saved full-model scores. Rates combine counts within each allocation before averaging allocations equally. Separate group rounding changes total capacity slightly relative to pooling. Methods have equal quotas within each comparison. Quotas round upward and tied scores share boundary places equally without using outcomes. Tied selections contribute expected counts.

Within separate group quotas, complete-model gains average 16.37 points in Melbourne two-bedroom apartments, 17.60 in three-bedroom apartments and 24.99 in Yarra Ranges houses/townhouses. Reduced-model gains are 7.21, -2.05 and 19.35 points respectively. At 25%, the complete model captures 38.29% of target-reaching homes. Its gain over the reduced model is positive in 42 allocations and negative in eight. The middle 90% of paired full-versus-baseline gains span -0.7 to 31.8 percentage points. These percentiles describe allocation sensitivity across overlapping samples.

For all eligible homes, mean AUC is 0.7084 versus 0.6035, improving in all 50 allocations. AUC measures ranking discrimination. Mean Brier score, squared probability error, is 0.17151 versus 0.18406, improving in 44. The five-fold, repeated full-population and priority-group results answer different comparisons.

The later-year gap is 12.3 percentage points using unrounded rates, with a conditional 95% range of 5.1-20.1 points. The exact earlier top-three set returns in 51.5% of host resamples. The range holds candidates fixed; reselecting them gives 5.4-20.2 points. Group ranges are pointwise 90%. All ranges hold the eligibility rules and review thresholds fixed.

Price diagnostics in `reports/supporting/revenue-analysis.md` use the supplied count, including one extra boundary date. Main results use reconstructed 365-day counts. Group and temporal checks are in `reports/tables` and `final-presentation/analysis/reference`. Model code and results are in `final-report/paired-analysis-2026-10-02` and `final-report/screening-followup-2026-10-03`. The published verifier reconstructs scores and metrics without refitting models or rebuilding raw reviews.

## Appendix B. Full group comparison

![All 14 eligible groups](figures/appendix_all_14_groups.png)

**Figure B1.** All eligible groups, listing counts and pointwise 90% ranges from resampling hosts. Leading and lower-performing groups are shown.
