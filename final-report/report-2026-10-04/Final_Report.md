# Melbourne Airbnb Market Screening

## 1. Introduction

Our client plans to lease homes and offer short stays through Airbnb. Rent and setup costs commit scarce startup funds before guest income arrives. The first task is to focus the property search on areas and home types with stronger evidence of guest activity.

We recommend starting with two- and three-bedroom apartments in the City of Melbourne. Three-bedroom houses and townhouses in Yarra Ranges provide a second search option. These groups have the strongest historical review activity in our residential comparison.

We then test how to narrow the search within these groups. When selecting a quarter of homes in each group, a simple model produces lists where 49.6% reach at least 30 annual reviews, compared with 32.4% using group rates alone. This gives the client an evidence-based order for investigating established homes with comparable operating information. Lease permissions, quotes and cash flow determine which candidates to pursue.

## 2. Problem Definition and Objectives

The client needs to decide where to search and which properties to investigate first. We address two questions:

1. Which property groups have the strongest historical guest-review activity?
2. Does information about individual homes improve selection beyond each group's historical rate?

A group combines council area, dwelling type and bedroom count. We compare entire apartments, houses and townhouses with one to three bedrooms and at least one year of recorded review history. A home reaches our target when it receives at least 30 reviews in the preceding 365 days. The target reflects the upper quarter of a separate reference sample, giving every group the same benchmark.

The final analysis builds on the interim report with a simpler logistic regression model and 50 repeated comparisons, including selection within the three priority groups. All analysis uses the Melbourne Inside Airbnb dataset supplied through the subject LMS.

## 3. Data Description and Preparation

The snapshot contains 25,728 listings collected between 17 June and 1 July 2026 (Inside Airbnb, 2026). We link property details to dated reviews and count reviews in the year before each listing's collection date. Reviews record past guest activity. Calendar availability combines bookings and host-blocked dates, making reviews the clearer measure for this comparison.

Our residential scope includes four recorded property types: entire rental units, condos, homes and townhouses. Rental units and condos form the apartment/unit category; homes and townhouses form the house/townhouse category. We keep one to three bedrooms, quoted nightly prices of AUD30-1,500 and a first review at least 365 days before collection. The price range sets an exploratory boundary, while the history rule gives each home a full year of observable review history.

These rules leave 6,891 eligible homes. We set aside 1,342 homes from separate reference hosts, leaving 5,549 for analysis. Retaining groups with at least 50 analysis homes leaves 3,873 homes in 14 groups. The reference sample then contains 906 homes in those same groups. Table 1 separates the analysis path from the reference branch.

**Table 1. From the supplied listings to the comparison sample**

| Sample stage | Listings |
|---|---:|
| Supplied snapshot covering all listing types | 25,728 |
| Entire homes with one to three bedrooms | 16,576 |
| Rental units, condos, homes and townhouses | 14,895 |
| Nightly price AUD30-1,500 and at least 365 days of review history | 6,891 |
| Analysis homes after reference hosts are set aside | 5,549 |
| Final analysis homes in groups with at least 50 homes each | 3,873 |
| Separate reference branch before group restriction | 1,342 |
| Reference homes within the same 14 groups | 906 |

The 3,873 homes belong to 1,726 hosts across six council areas; about 64% are in the City of Melbourne. The median home has 15 annual reviews. We retain all 334 homes with zero annual reviews, or 8.6%, so the comparison includes quieter properties.

A separate check across the full snapshot finds 6,801 listings with missing or out-of-range prices. The supplied recent-review count is zero for 82% of these listings, against 23.7% of listings retained by the price check. The price rule therefore shifts the sample towards more active properties. The findings describe established, priced residential homes in the covered areas.

The 906 reference homes have an upper-quarter cutoff of 29.75 reviews, rounded up to 30. Their hosts remain separate from model training and testing. Category definitions were fixed after earlier exploration; each training sample supplies missing-value replacements and comparable-price medians. Three missing minimum-stay values are filled using the most common training category. Appendix A records the preparation details.

## 4. Methodology

We first compare the share of homes reaching 30 annual reviews in each group. Repeating the calculation on resampled hosts shows how much those shares vary. Each host's properties stay together because they can share management practices.

We use logistic regression in R to rank individual homes (R Core Team, n.d.). Its outcome is whether a home reaches 30 annual reviews. The six inputs are council area, dwelling type, bedroom count, price relative to similar homes, acceptance of one-night stays and amenity count. The model learns a weight for each input from training homes and combines their contributions into a score. Higher scores move homes earlier in the investigation list.

Our comparison method assigns every home its group's training success rate, adjusted towards the overall training rate. Homes in one group receive equal scores. A second model removes price and minimum-stay information, showing how much these operating details add to selection.

We compare the methods over 50 host splits. Each split uses 70% of hosts for training and 30% for testing. All properties belonging to a host stay on the same side. The methods select equal numbers from the same test homes, keeping the comparison fair.

The main comparison selects 25% of homes separately within each priority group and averages the selected homes' target rate across the 50 tests. We also test 10% and 50% to show how investigation capacity affects the results. Appendix A explains rounding and tied scores.

To check whether the search priorities hold across time, we reconstruct two consecutive annual review windows from the same snapshot. We choose the earlier leading groups and follow their activity in the later window. This separate comparison uses a 34-review target, fixed from the earlier reference window.

## 5. Analysis and Results

### 5.1 City apartments are the first search priority

Across the analysis sample, 981 of 3,873 homes reach 30 annual reviews, or 25.3%. Group rates range from 8.2% to 36.6%, giving the client a clear reason to focus the search.

City of Melbourne three-bedroom apartments lead at 36.6%, with 112 of 306 homes reaching the target. Two-bedroom apartments follow at 32.8%, or 405 of 1,235. Yarra Ranges three-bedroom houses and townhouses reach 30.0%, or 27 of 90. The city groups combine stronger observed activity with larger samples, supporting their position as the first search priority.

![Three priority property groups](figures/figure_1_priority_groups.png)

**Figure 1.** Homes reaching at least 30 annual reviews. Horizontal lines show 90% ranges from resampling hosts; the dashed line marks the overall 25.3%. Appendix B shows all 14 groups.

The same three groups lead when minimum group size changes to 30 or 75 homes, or when the price or history rule is removed. Their order can change, so use the three-group shortlist to guide the search. Adding specialised accommodation changes the shortlist and addresses a broader market than the client's residential search.

### 5.2 The model improves selection within the priority groups

The complete model helps decide which homes to investigate first. Selecting 25% within each priority group produces an average historical target rate of 49.6%, compared with 38.6% for the model without price and minimum stay and 32.4% for group rates alone.

The complete model adds 17.2 percentage points. For a list of 100 selected homes, that means about 17 more homes with at least 30 annual reviews. It directs investigation time towards homes with stronger recorded guest activity.

![Historical screening results within the priority groups](figures/figure_2_paired_screening.png)

**Figure 2.** Average historical target rates over 50 tests. Each method selects 25% within each priority group. The reduced model leaves out price and minimum-stay information.

The complete model leads in 46 of the 50 tests and trails in four. Gains fluctuate: the middle 90% run from -0.7 to 31.8 percentage points. These overlapping historical tests support prioritising investigations while showing how much performance varies with the homes available.

Price and minimum-stay information add 11.0 percentage points over the reduced model. Within a fixed group, that reduced model ranks homes using amenity count alone. For city three-bedroom apartments, it reaches 33.9%, below the baseline's 35.9%. The full six-input model is therefore the stronger tool for established homes with comparable operating details. New rental searches start with the group priorities.

### 5.3 Investigation capacity determines list size and coverage

Shorter lists concentrate on stronger historical activity. Longer lists capture more qualifying homes. Table 2 shows the choice available to a client with limited investigation time.

**Table 2. Results at different investigation capacities**

| Share investigated in each group | Share of selected homes reaching 30 reviews | Share of all qualifying homes found |
|---|---:|---:|
| 10% | 54.5% | 17.1% |
| 25% | 49.6% | 38.3% |
| 50% | 43.1% | 66.7% |

Values are averages over the 50 tests. Investigating 10% gives a list where more than half reach the target, while capturing 17.1% of all qualifying homes. At 50%, the list captures about two-thirds. Average gains over group rates are 22.0, 17.2 and 10.7 percentage points at the three capacities.

The 25% result is a reference for allocating investigation effort. Our proposed first round starts with ten available candidates, checked in priority order. The operator chooses how many detailed checks the budget supports and expands the pool when suitable homes are scarce.

### 5.4 Earlier leading groups retain their advantage

The two-year comparison follows the same 2,657 homes across ten groups. In the later year, 27.1% of homes in the earlier leading three groups reach the fixed 34-review target, compared with 14.9% in the other seven groups. The advantage is 12.3 percentage points.

![Historical group advantage across two annual windows](figures/figure_3_historical_persistence.png)

**Figure 3.** The same homes are compared in both years. The earlier leading groups remain ahead, although their qualifying share falls from 33.6% to 27.1%.

The leading groups retain their relative advantage as overall activity falls. This supports keeping them as search priorities and assessing current demand for each candidate property.

## 6. Key Findings and Recommendations

Search City of Melbourne two- and three-bedroom apartments first. Use Yarra Ranges three-bedroom houses and townhouses as an alternative when city lease terms or availability are unsuitable.

For established homes, collect comparable nightly prices, minimum-stay rules and amenity information, then use the complete model to order investigations. For new rentals, use group priorities and compare permissions, rent and operating costs. Scores based on proposed settings are scenario estimates; their use for selecting new openings needs a prospective test.

Before signing, obtain written confirmation of permitted short-stay use and quotes for rent, setup and operating costs. Estimate cash flow using achievable nightly rates and paid nights under expected and weaker-demand conditions. Choose a property that meets the client's agreed return and cash-buffer requirements under both conditions.

**Table 3. Proposed first investigation round**

| Timing and owner | Action | Decision condition |
|---|---|---|
| Week 1 operator | Find ten available candidates in the priority groups and order investigations using comparable operating details | Use group priorities for new rentals |
| Weeks 2 and 3 operator and analyst | Confirm permissions, obtain cost quotes and assess current guest demand | Keep incomplete cases pending; reject homes that fail the client's requirements |
| Week 4 client | Compare qualified homes using expected and weaker-demand cash flows | Select a home that meets return and cash-buffer requirements |
| Operating trial operator | Record paid nights, workload and net cash flow | Review actual performance before expanding |

Ten homes form the initial search pool. Investigate higher-priority candidates first and replace rejected homes. Ten candidates and 30 days set the first round's workload; extend the search when necessary. If the model adds little value in the trial, continue using group rates to direct the search.

## 7. Limitations and Future Work

Reviews measure recorded guest activity. Paid nights, stay length and costs determine profit. The operating trial should collect these measures alongside reviews to connect our search priorities to financial performance.

The sample covers established, priced homes in selected council areas. The first-review rule establishes the length of the review record; continuous operation remains unknown. The next coverage test should include new entrants, other areas and homes excluded by price screening. Removing price as a model input still uses the original price-filtered sample.

Price and minimum-stay settings were recorded at collection and may reflect earlier performance. Across the 50 fits, lower relative prices, one-night acceptance and more amenities raise model scores when other inputs stay fixed. Test planned changes prospectively to establish their effect on guest activity.

For the next validation, fix the search groups, model and selection rule before collecting new outcomes. This creates a fresh test beyond the overlapping historical comparisons and earlier exploration. Check whether model scores match observed rates before using them as individual probabilities. Appendix A provides the full comparison evidence.

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
