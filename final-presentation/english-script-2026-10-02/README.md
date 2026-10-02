# English presentation script

This edition follows the ten-slide final presentation and adds the 2 October paired comparison to the spoken explanation and questions. The main script has 940 whitespace-counted words, divided across four presenters. The planned speaking time is nine minutes, with one minute available for pauses and handoffs; confirm the timing in rehearsal.

- [Word script with questions and evidence notes](deliverables/TheNextChapter_English_Speaking_Script.docx)
- [Plain-text spoken passages](deliverables/TheNextChapter_English_Speaking_Script.txt)
- [Editable source](code/script.json)
- [Repeated model comparison](../../final-report/paired-analysis-2026-10-02/README.md)

The Word document contains nine pages: a schedule, one page for each presenter, three pages of questions, and one evidence page. Read only the main passages during the presentation. The twelve prepared answers and evidence table are for discussion afterwards.

## Relationship to the slides

Slide 6 still shows the original five-fold comparison: 43.7% versus 28.1%, with 423 of 969 selected listings reaching the review target. Those results were reproduced after the preprocessing correction. The new spoken sentence reports that logistic screening performed better in 48 of 50 repeated host splits. The repeated-split mean of 43.42% versus 31.96%, and its 11.46 percentage-point gain, remain in the questions and evidence notes.

The answers disclose training-only imputation and the earlier outcome-informed choice of the one-night indicator. They distinguish the two tests and identify the random-forest, priority-group and historical-window analyses as earlier supplementary checks. This edition does not change the PowerPoint file or its embedded notes.

## Rebuild

Install `python-docx` and run from this directory:

```sh
python3 code/build_script.py
```

The builder uses `code/script.json` and writes the Word and plain-text files under `deliverables/`. The document was rendered to nine pages and inspected for text fit and pagination. Main-script word counts use whitespace-separated tokens and may differ from Microsoft Word's count.
