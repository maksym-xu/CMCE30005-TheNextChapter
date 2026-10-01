# Final presentation and supporting evidence

TheNextChapter Group 2 · CMCE30005 · 1 October 2026

Our proposal is to investigate City of Melbourne two- and three-bedroom apartments first, with Yarra Ranges three-bedroom houses/townhouses as an alternative. The observed review rates and comparison sample sizes support this search order. Actual quotes and permissions may change it. Every candidate still needs permission and a conservative cash-flow assessment before a lease.

## Presentation files

- [PowerPoint presentation](deliverables/TheNextChapter_Final.pptx): 10 slides, editable charts, illustrative 3D images and manual fade transitions.
- [Speaking script and Q&A](deliverables/TheNextChapter_Final_Speaking_Script.docx): English main speech, Chinese rehearsal cues, handovers, ten prepared questions and technical source notes.
- [PDF slide preview](preview/Slide_Preview.pdf): a static rendering for quick review. Present and submit the PowerPoint when the assessment requires PPTX.
- [Evidence map](EVIDENCE_MAP.md): each slide's claims, source files, calculations and limits.
- [Analysis and reproduction guide](analysis/README.md): published aggregate checks and the separate route requiring authorised school data.

The main speech contains 920 whitespace-separated words. The four planned speaking slots are 135 seconds each, giving nine minutes plus one minute of contingency. This is a rehearsal plan, not an observed delivery time. All four members need to rehearse and participate.

## Main results and scope

| Check | Result | What it supports |
|---|---|---|
| Historical screening across all 3,873 eligible homes | Logistic 423/969 = 43.7%; group-rate benchmark 28.1% under the same expected quota | About 16 additional target-reaching homes per 100 selected in this historical comparison |
| Exploratory screening within the three recommended groups | 202/409 = 49.4%; uniform selection within the same group quotas has expected attainment of 33.4% | Supplementary support for focusing investigation within the chosen groups |
| Separate two-window check of 2,657 surviving homes | Earlier leading groups reach the later 34-review target at 27.1%, versus 14.9% elsewhere | Historical persistence of the proposed search groups |

The main model's target is 30 reviews in the preceding 365 days. The separate two-window check fixes its own reference-derived target at 34. Both windows come from dated reviews in one supplied snapshot. Neither result forecasts a new operator's profit, occupancy or individual chance of business success. The supplementary groups were chosen after exploration, and its resampling intervals condition on the existing predictions and group choice.

The interim report selected random forest. The final presentation uses logistic regression for a simpler explanation of the six inputs and retains a matched-input forest as a benchmark. The project does not establish one model family as universally best. See the evidence map for the comparison and limits.

## Check the public evidence

From this directory, using standard Python 3:

```sh
python3 analysis/scripts/check_publication.py
```

This reconciles 24 aggregate counts, quotas, percentages and related claims. It does not independently rerun the raw-data pipeline or train models. The saved earlier raw-input and independent subgroup-calculation reports are distinguished in the analysis guide. No new model was trained for this publication pass.

Raw school data, listing identifiers and listing-level predictions are excluded. Obtain authorised inputs through the course and follow [analysis/README.md](analysis/README.md) to reproduce the model computations.

## Rebuild the artifacts

The editable sources are `code/build_deck.mjs`, `code/script.json` and `code/build_script.py`. `code/prepare_slide_data.py` reads the aggregate evidence. This build uses the Codex bundled artifact runtime and skill helpers from version 26.909.12148; they are not vendored here. Required components include `@oai/artifact-tool`, Python `python-docx`, `reportlab`, `Pillow`, the presentation finalizer and the canonical document renderer. Fonts are Arial, Georgia and Noto Sans CJK SC (or compatible installed fonts).

In a compatible Codex desktop environment, run:

```sh
bash code/build_all.sh --artifacts-only
```

The default rebuild uses published aggregates. It preserves the released PPTX/DOCX by writing timestamped new files and refreshes generated previews. Inspect every new render before using it. Set `RUNTIME_ROOT`, `RUNTIME_PYTHON`, `RUNTIME_NODE`, `RUNTIME_NODE_MODULES`, `PRESENTATIONS_SKILL_DIR` and `DOCUMENTS_SKILL_DIR` if your installation uses different locations. `FONTCONFIG_FILE` is optional and can identify a local font configuration. For a full local model rerun, first prepare the authorised inputs, then use `--with-analysis`.

`MANIFEST.json` records hashes of the published files. The original interim report remains in the repository root for historical comparison. Its model choice and client wording should be read as the interim version; this folder contains the final presentation.

## AI assistance

OpenAI Codex assisted with drafting, evidence organisation, analysis-code checks, layout and consistency checks. AI-generated architecture images illustrate the scenario; they are not actual candidate properties or interactive 3D models. Group members remain responsible for reviewing, understanding and delivering the work and retaining applicable acknowledgements of earlier assistance.
