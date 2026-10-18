# Final report and evidence

## Current final report (revised 18 October 2026)

The [report package](report-2026-10-04/README.md) holds the [PDF](report-2026-10-04/Final_Report.pdf), [Word](report-2026-10-04/Final_Report.docx) and [Markdown](report-2026-10-04/Final_Report.md) versions, the four figures, the scripts that build and check them, and the evidence added in the 16–18 October revision. The root [README](../README.md) carries the complete report.

The report's main model result picks 25% of test homes separately within each of the three priority groups: 49.6% of the full model's picks reached 30 annual reviews, against 38.6% for the reduced model without price and minimum stay, and 32.4% for group rates (random picking within a group). The package README lists the other evaluation designs and why their numbers differ.

## Analysis packages

| Package | What it tests |
|---|---|
| [screening-followup-2026-10-03](screening-followup-2026-10-03/README.md) | Within-group picking at 10%, 25% and 50% quotas over the same 50 host splits; the reduced model without price and minimum stay |
| [paired-analysis-2026-10-02](paired-analysis-2026-10-02/README.md) | The six-input logistic model against group rates over 50 host splits on all groups: shortlist rates, AUC and Brier score |
| [../final-presentation/analysis](../final-presentation/analysis/README.md) | The model as presented on 6 and 13 October: pooled five-fold scores (423 of 969 picks reached the target), scenario chances and the two-year check |

All repeated-split results are retrospective. Test sets overlap, and the groups and inputs were chosen after earlier exploration of the same snapshot, so the results are somewhat optimistic. Reviews do not measure bookings or profit. Row-level private inputs are not published.
