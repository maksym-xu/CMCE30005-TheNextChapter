# Melbourne Airbnb Market Screening

CMCE30005 Final Project Report | TheNextChapter Group 2

Eric Huang, Loc Le, Qihang Sun and Maksym Xu

## Current final report reviewed 7 October 2026

[Final report PDF](final-report/report-2026-10-04/Final_Report.pdf) · [Word](final-report/report-2026-10-04/Final_Report.docx) · [Matching report text](final-report/report-2026-10-04/Final_Report.md) · [Files and checks](final-report/report-2026-10-04/README.md)

The complete current report follows. Its analysis is pinned to revision e4c68ca. The 7 October refinement makes the writing more direct, explains the sample and dwelling types, and connects the findings to the property investigation plan. Analysis results, figures, presentation files and the archived interim submission remain unchanged.

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

![Three priority property groups](final-report/report-2026-10-04/figures/figure_1_priority_groups.png)

**Figure 1.** Homes reaching at least 30 annual reviews. Horizontal lines show 90% ranges from resampling hosts; the dashed line marks the overall 25.3%. Appendix B shows all 14 groups.

The same three groups lead when minimum group size changes to 30 or 75 homes, or when the price or history rule is removed. Their order can change, so use the three-group shortlist to guide the search. Adding specialised accommodation changes the shortlist and addresses a broader market than the client's residential search.

### 5.2 The model improves selection within the priority groups

The complete model helps decide which homes to investigate first. Selecting 25% within each priority group produces an average historical target rate of 49.6%, compared with 38.6% for the model without price and minimum stay and 32.4% for group rates alone.

The complete model adds 17.2 percentage points. For a list of 100 selected homes, that means about 17 more homes with at least 30 annual reviews. It directs investigation time towards homes with stronger recorded guest activity.

![Historical screening results within the priority groups](final-report/report-2026-10-04/figures/figure_2_paired_screening.png)

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

![Historical group advantage across two annual windows](final-report/report-2026-10-04/figures/figure_3_historical_persistence.png)

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

![All 14 eligible groups](final-report/report-2026-10-04/figures/appendix_all_14_groups.png)

**Figure B1.** All eligible groups, listing counts and pointwise 90% ranges from resampling hosts. Leading and lower-performing groups are shown.

## Presentation and analytical evidence

## Final presentation released 1 October 2026

The [final presentation package](final-presentation/README.md) contains the 10-slide PowerPoint, speaking script, updated analysis code and aggregate results. The [evidence map](final-presentation/EVIDENCE_MAP.md) links each slide to its supporting files and explains the limits of the checks.

The final main model is logistic regression for clearer explanation; random forest remains a benchmark. The client is framed as planning to lease homes. The interim report below is retained as the historical version, including its earlier model selection and wording.

## Final report screening evidence updated 3 October 2026

The [final report evidence guide](final-report/README.md) links the paired model comparison and the new [screening follow-up](final-report/screening-followup-2026-10-03/README.md). The follow-up tests selection within the three priority groups, the joint contribution of price and minimum-stay information, and 10%, 25% and 50% shortlist quotas on the same 50 host splits.

With a separate 25% quota inside each priority group, the full model averaged 49.62% historical review-target attainment against 32.43% for the group-rate baseline, a 17.19-point gain. It was better in 46 splits and worse in four. The package includes an English findings brief, figures, aggregate results, reproducible code and independent score and metric checks. These exploratory historical results remain distinct from the original five-fold presentation result and do not establish future profit.

<details>
<summary>Archived interim report and its original reproduction instructions</summary>

## Archived interim report

Interim Project Report

CMCE30005 Business Analytics Challenge | Semester 2 2026 | TheNextChapter Group 2

Eric Huang, Loc Le, Qihang Sun and Maksym Xu

Repository: https://github.com/maksym-xu/CMCE30005-TheNextChapter

## Introduction

Our client leases residential properties and runs them as Airbnb accommodation ("rental arbitrage"), which needs lease and council permission. With limited start-up funds, the client must choose which Melbourne areas and property types to investigate before signing leases; a poor choice ties up money.

We use the Inside Airbnb Melbourne snapshot of June 2026 supplied through the subject's LMS (Inside Airbnb, 2026): property details, locations and dated guest reviews. Dated reviews are a countable record of past guest activity; the calendar cannot separate bookings from host-blocked dates.

The shortlist helps the client decide where to spend limited search and due-diligence time before seeking lease quotations.

## Problem Definition and Objectives

Research questions: (1) Which Melbourne property segments, defined by council area (LGA), apartment or house, and number of bedrooms, show the strongest historical guest-review activity? (2) Can listing attributes improve prediction of high review activity beyond segment averages? "High" means at least 30 reviews in the year before the data were collected, the top quarter of a separate reference group of comparable listings.

Hypotheses: (H1) segments differ materially in the share of listings reaching that level; (H2) a model using listing attributes ranks listings better than the segment average alone.

Objectives: a segment comparison table, a model-versus-average test and a shortlist with ranges.

We study entire homes with one to three bedrooms (1–3BR), what a small operator can furnish and let whole; rental units and condos are the apartment group, homes and townhouses the house group. Each segment needs at least 50 listings as minimum comparison support; quoted prices of AUD 30–1,500 are an exploratory boundary; and a first review at least 365 days before collection gives at least one year of observable review history, not proof of continuous operation.

We call the share of listings reaching 30 reviews (at least 30 reviewed stays) "attainment". Attainment measures review activity, not bookings, occupancy or profit. For an operator paying fixed rent, the main risk is a property that attracts few stays; segments where more comparable listings reach high review activity show such demand is achievable.

## Data Description

The dataset contains 25,728 listings and 1,026,690 reviews, collected between 17 June and 1 July 2026. Its modelled occupancy and revenue fields are built from price, minimum stay and review counts, so ranking on them would reproduce that construction; we rank on review counts.

Cleaning converts price text to numbers and extracts bathroom and amenity counts; price is missing for 6,553 listings and bedrooms for 4,679. The supplied last-12-months review field spans 366 dates, so we rebuilt counts over exactly 365 days from review dates (Table 1).

Table 1. Sample funnel

| Stage | Listings |
| ---------------------------------------- | ---------- |
| All listings in the dataset | 25,728 |
| Entire homes, 1–3 bedrooms | 16,576 |
| Standard dwelling types | 14,895 |
| Quoted price AUD 30–1,500 | 11,099 |
| First review ≥ 365 days before collection | 6,891 |
| Analysis sample (50+ per segment, reference hosts excluded) | 3,873 |
| Reference group (separate, from the 6,891) | 906 |

The reference group's 75th percentile, 29.75 reviews, gives a threshold of 30. The analysis sample (3,873 listings from 1,726 hosts) has 14 segments across six LGAs, about 64% in Melbourne LGA, and keeps 334 listings with zero annual reviews. Overall, 981 listings (25.33%) reach the threshold, and attainment ranges from 8.25% to 36.60% across segments (Figure 1).

![Figure 1. Share of listings reaching 30 reviews by segment; lines are 90% host-resampled ranges, dashed line the pooled 25.33% rate.](reports/figures/16_segment_ladder.png)

Of the 6,801 listings with no usable price (missing or outside AUD 30–1,500), 82% had no review last year: the priced sample is the more active part of the market. Listings that left Airbnb before collection are absent, limiting generalisation to new entrants.

## Methodology and Analytical Approach

A fixed rule on host identifiers sets aside about 20% of hosts as the reference group that defines the 30-review target; they are excluded from all training and testing. We use five-fold validation, each part tested in turn on a model trained on the other four, with each host's properties kept in one fold so a host with many near-identical apartments cannot sit in both training and test data (scikit-learn developers, n.d.). Missing-value treatment and category encoding are learned from training data only.

Logistic regression is the reference; random forest and gradient boosting capture nonlinear patterns. Basic features are location, configuration, capacity, bathrooms and amenity count; an enhanced set adds coordinates, beds and nine amenities. We compare six variants, with and without probability calibration and with and without current price and minimum stay. Review-based predictors, ratings and host badges are excluded.

Every model is compared with a segment-average baseline: each listing gets its segment's training-host attainment. AUC is how well the model orders listings that reach the target above those that do not; 0.5 is a coin toss. Average precision summarises precision across prediction thresholds. Brier score is how far its percentages are from what happened; lower is better. R handles cleaning and tables; Python (scikit-learn 1.7.2) runs the models.

Because candidates were compared after seeing fold results, selection is repeated in a nested check where models are selected using only each outer training fold; property details may have changed during the outcome year.

## Analysis Plan and Progress to Date

Following Week 5 feedback, we dropped the earlier rent-versus-revenue (ROI) design, which needed external rental data.

Table 2. Predictive performance

| Predictor | AUC | Average precision | Brier score |
| --- | --- | --- | --- |
| Segment average (training hosts) | 0.581 | 0.285 | 0.1868 |
| Basic property-only logistic | 0.573 | 0.285 | 0.1886 |
| Enhanced property-only random forest | 0.640 | 0.350 | 0.1813 |

The enhanced random forest beats the segment average in all five folds and, across 20 further host splits on AUC every time and on Brier in 16. A nested check that re-selects the model inside each outer training fold chooses the forest every time: AUC +0.059 (host-resampled 95% range +0.02 to +0.10), Brier −0.0055 (−0.010 to −0.001). Across five probability bins, predicted and observed rates differ by about two percentage points.

Table 3. Initial search candidates (host-grouped forest predictions)

| Segment | Listings / hosts | Observed attainment | Predicted probability | 95% range |
| ---------------------------- | ------------ | ------------ | ------------ | ------------ |
| Melbourne 3BR apartments | 306 / 139 | 36.60% | 34.45% | 33.0–35.8% |
| Melbourne 2BR apartments | 1,235 / 482 | 32.79% | 31.41% | 29.6–33.0% |
| Yarra Ranges 3BR houses/townhouses | 90 / 77 | 30.00% | 27.82% | 26.1–29.3% |

All reported host-resampled ranges hold predictions fixed and exclude refitting, selection and threshold uncertainty; Table 3's are much narrower than Figure 1's observed-rate ranges. Descriptive evidence supports H1: segments differ (8.25% to 36.60%), though neighbours overlap. H2 is supported by nested host-grouped validation on ranking metrics: the model improves overall listing-level prediction but leaves the shortlist unchanged. Segment rates guide the search; the model provides a supplementary historical score for individual listings (within-segment AUC 0.555). Descriptively, the same three segments lead under support rules of 30, 50 and 75 listings, without the history or price rule, and at review targets of 25, 30, 34 and 35 (the top two swap at 34 and 35); the forest's top three recur in 19 of 20 host splits.

An out-of-time check (2,657 listings, 1,208 hosts, 10 segments) uses two non-overlapping 365-day windows and a 34-review target set from the reference hosts' earlier window. The earlier year's top three segments reached it in 27.1% of listings the following year against 14.9% elsewhere, a 12.3-point lead (host-resampled 95% range 5.1–20.1); the exact top-three set recurred in 51.5% of resamples: a persisting historical advantage, not a new operator's profit.

Before signing, the client must verify permissions, rent, costs and availability.

Remaining work:

1. Refit the fixed forest and re-rank under wider property-type and history rules: Eric Huang (modelling lead) and Maksym Xu (data lead), Weeks 9–10 (by 2 Oct).
2. One-page client brief with search priorities and pre-lease checklist: Loc Le (report lead), Week 11 (by 13 Oct).
3. Final report and presentation: all, Qihang Sun coordinating, Weeks 11–12.

If the gain does not persist under wider rules, segment rates remain the main screening tool; if rankings change, we present a broader candidate set.


## References

Inside Airbnb. (2026). Melbourne listings, calendar and reviews [June 2026 dataset supplied through CMCE30005 LMS].

Scikit-learn developers. (n.d.). Cross-validation and probability calibration. https://scikit-learn.org/stable/modules/cross_validation.html

OpenAI. (2026). ChatGPT/Codex assistance with project planning, report drafting and code review [Generative AI outputs, September 2026].

Anthropic. (2026). Claude Code assistance with analysis-code development [Generative AI outputs, September 2026].

## AI Use Acknowledgement

The business problem, research questions, scope rules, choice of methods, data decisions and interpretation of results are the group's own. We used OpenAI ChatGPT/Codex and Anthropic Claude Code to polish the English of report text written from our results, to implement and debug analysis scripts to our specification, and to check quoted figures against the repository tables. The group reviewed all AI-assisted text and code and is responsible for the accuracy and content of this submission.

## Project files

The submission files are `reports/Interim_Project_Report.docx` and its PDF. Both include the AI Use Acknowledgement. `reports/interim-project-report.md` is the matching text version. See the [report directory guide](reports/README.md) for current evidence and supporting analyses.

- [Interim report Word](reports/Interim_Project_Report.docx) · [PDF](reports/Interim_Project_Report.pdf)
- [Research design](reports/rq-analysis-plan.md) · [Methodology](reports/methodology.md) · [Data notes](reports/data-notes.md)
- [Raw-data validation](reports/data-validation-2026-09-15.md) · [Machine-readable checks](reports/validation/raw-rerun-2026-09-15.json) · [Figure 1](reports/figures/16_segment_ladder.png)
- [Sample funnel](reports/tables/rq_sample_funnel.csv) · [Descriptive segments](reports/tables/segment_ladder.csv)
- [Baseline metrics](reports/tables/rq_model_metrics.json) · [Extension comparison](reports/tables/rq_extension_metrics.csv) · [Extension rankings](reports/tables/rq_extension_ranking.csv)
- [Segment-rate baseline comparison](reports/tables/rq_baseline_comparison.csv) · [Per-fold differences](reports/tables/rq_baseline_fold_comparison.csv) · [Repeated host partitions](reports/tables/rq_repeated_split_top3.csv)
- [Support-rule sensitivity](reports/tables/rq_support_rule_sensitivity.csv) · [Nested model selection](reports/tables/rq_nested_selection_summary.json) · [Out-of-time check](reports/validation/temporal-holdout/method-note.md)

### Reproducing the analysis

Place the original school-supplied `listings_airbnb.csv`, `calendar_airbnb.csv` and `reviews_airbnb.csv` in `data/raw/`. The source rebuild used these restored original files on 15 September, followed by a cross-platform compatibility rerun on 16 September; their hashes are recorded in the validation output. Raw data and listing-level predictions are excluded from Git.

Install the R packages listed in `scripts/00_packages.R`, then run the following from the project root:

```sh
Rscript scripts/00_packages.R
Rscript scripts/01_data_cleaning.R
Rscript scripts/07_descriptive_analytics.R
python -m pip install -r requirements-analysis.txt
python scripts/rq_scope_feasibility.py
Rscript scripts/08_peer_ranking.R
Rscript scripts/09_probability_calibration.R      # supporting figure only
python scripts/10_model_extensions.py
python scripts/11_segment_rate_baseline.py --repeats 20
python scripts/12_support_rule_sensitivity.py
python scripts/13_nested_selection.py
python scripts/validation/temporal_holdout.py
Rscript scripts/supporting/04_revenue_analysis.R  # supplies the unpriced-listing review share
```

Supporting analyses of Inside Airbnb's modelled price and revenue fields (`scripts/supporting/02_exploratory_analysis.R`, `03_price_model.R`, `04_revenue_analysis.R`) are data-quality diagnostics, not part of the candidate ranking; the report cites one descriptive statistic from them (the share of unpriced listings with no recent review). They run from the project root after script 01 and write to `reports/supporting/`. See [reports/README.md](reports/README.md) for which files the report uses.

Script 01 stages cleaned files until all input checks pass and records their hashes. The supplied `number_of_reviews_ltm` matches a 366-date inclusive window; it is preserved. The primary `reviews_365d` outcome is reconstructed over `(last_scraped − 365 days, last_scraped]`. The Python workflow independently checks all source review counts and publishes results only after every baseline model finishes. Script 08 requires matching input and configuration hashes before ranking. Script 10 holds the primary sample, outcomes and outer host folds fixed while evaluating the six model variants in separate outputs. Script 11 scores a segment-rate baseline on those same folds, using training-host outcomes only, places it beside every model, and then reassigns hosts to folds under 20 further seeds to check how stable the metrics and the top-ranked segments are.

The main screening model provisionally uses detailed property features and random forest; the original baselines remain available for comparison. The supporting price/revenue scripts describe Inside Airbnb's modelled fields only and establish nothing about bookings, occupancy or profit. All numerical inputs come from the school data. References concern methodology, and no external market or rent observations are added.

The shared scope and benchmark rules are in [config/review_analysis.json](config/review_analysis.json). The reference-host P75 is calculated once and its integer cutoff is held fixed across all comparisons; the 30-review level in the research question is that computed cutoff, not an externally chosen number. Original identifiers, host-fold assignments and detailed review comparisons remain in ignored `data/processed/` files.

Run the regression checks separately; they use temporary synthetic data and do not overwrite report results:

```sh
python -m unittest discover -s tests -v
Rscript tests/test_cleaning_consistency.R
Rscript tests/test_peer_inputs.R
```

The dated 13–14 September validation records document the earlier cached-data analysis. The 15 September raw-data record, including the 16 September compatibility rerun, is the current verification.

</details>
