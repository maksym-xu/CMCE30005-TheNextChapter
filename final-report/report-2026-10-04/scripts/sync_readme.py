"""Copy the final report into the root README between its two report markers.

Run from the repository root:
    python final-report/report-2026-10-04/scripts/sync_readme.py
Everything above '<!-- final report starts here -->' (title, summary and links) and
everything below '<!-- final report ends here -->' (repository guide, reproduction steps
and contributions) is kept; the text between them is replaced by Final_Report.md from
Section 1 onwards, with figure paths adjusted for the repository root.
"""
from pathlib import Path

START = '<!-- final report starts here -->'
END = '<!-- final report ends here -->'
root = Path.cwd()
readme = root / 'README.md'
report = (root / 'final-report/report-2026-10-04/Final_Report.md').read_text(encoding='utf-8')
text = readme.read_text(encoding='utf-8')
head = text.split(START)[0].rstrip() + '\n\n' + START + '\n\n'
tail = text.split(END)[1] if END in text else '\n'
body = report[report.index('## 1. Introduction'):].rstrip('\n')
body = body.replace('](figures/', '](final-report/report-2026-10-04/figures/')
readme.write_text(head + body + '\n\n' + END + tail, encoding='utf-8')
print('README.md now carries the final report from Section 1.')
