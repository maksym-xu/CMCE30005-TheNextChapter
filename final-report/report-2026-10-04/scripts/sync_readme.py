"""Copy the final report into the root README below its repository guide.

Run from the repository root:
    python final-report/report-2026-10-04/scripts/sync_readme.py
Everything above the line '<!-- final report starts here -->' in README.md is kept;
everything below it is replaced by Final_Report.md from Section 1 onwards, with
figure paths adjusted for the repository root.
"""
from pathlib import Path

MARKER = '<!-- final report starts here -->'
root = Path.cwd()
readme = root / 'README.md'
report = (root / 'final-report/report-2026-10-04/Final_Report.md').read_text(encoding='utf-8')
head = readme.read_text(encoding='utf-8').split(MARKER)[0].rstrip() + '\n\n' + MARKER + '\n\n'
body = report[report.index('## 1. Introduction'):]
body = body.replace('](figures/', '](final-report/report-2026-10-04/figures/')
readme.write_text(head + body, encoding='utf-8')
print('README.md now carries the final report from Section 1.')
