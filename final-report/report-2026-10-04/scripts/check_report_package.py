#!/usr/bin/env python3
"""Check the final report package for the 16-18 October 2026 revision.

Run from the repository root (needs pypdf for the PDF checks):
    python final-report/report-2026-10-04/scripts/check_report_package.py

Checks that
  * Final_Report.md, Final_Report.docx, Final_Report.pdf and the root README.md carry the same report;
  * the AI acknowledgement is unchanged from the 14 October report (commit 3e6e043);
  * the whole document stays under the 3,000-word limit (simple count and Microsoft Word's recorded count);
  * every font in the PDF is embedded;
  * the report's key numbers match the committed aggregate outputs.
Writes the results to final-report/report-2026-10-04/package_checks.json.
"""
import csv
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path.cwd()
PKG = ROOT / 'final-report/report-2026-10-04'
# SHA-256 of the AI acknowledgement paragraph in the 14 October report (commit 3e6e043).
AI_ACK_SHA256 = '6c48239a46ec3932fb81333a9531c23f9fc389aa0bcbed1a47edb0d314db3fd0'
WORD_LIMIT = 3000


def norm(text):
    text = text.replace('−', '-').replace('‑', '-').replace(' ', ' ')
    return re.sub(r'\s+', ' ', text).strip()


def md_plain(text, tables=True):
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    if tables:
        text = re.sub(r'(?m)^\|?\s*[-:| ]+\|?\s*$', '', text)
        text = text.replace('|', ' ')
    text = text.replace('**', '').replace('`', '')
    text = re.sub(r'(?<!\w)\*([^*]+)\*', r'\1', text)
    text = re.sub(r'(?m)^#+\s*', '', text)
    text = re.sub(r'(?m)^- ', '', text)
    return norm(text)


def word_count(text):
    return len([w for w in re.split(r'\s+', text) if re.search(r'[A-Za-z0-9]', w)])


def docx_text(path):
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read('word/document.xml'))
    parts = []
    for p in root.iter('{%s}p' % ns['w']):
        parts.append(''.join(t.text or '' for t in p.iter('{%s}t' % ns['w'])))
    return norm(' '.join(parts))


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def fail(failures, message):
    failures.append(message)


def main():
    failures = []
    md = (PKG / 'Final_Report.md').read_text(encoding='utf-8')
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    plain = md_plain(md)

    # 1. README carries the report from Section 1 to the end (figure paths differ only).
    body = md[md.index('## 1. Introduction'):]
    readme_body = readme[readme.index('## 1. Introduction'):] if '## 1. Introduction' in readme else ''
    if readme_body.replace('final-report/report-2026-10-04/figures/', 'figures/') != body:
        fail(failures, 'README.md report text differs from Final_Report.md')

    # 2. Word text matches the Markdown text, paragraph by paragraph.
    docx = docx_text(PKG / 'Final_Report.docx')
    missing = []
    for block in re.split(r'\n\s*\n', md):
        block = block.strip()
        if not block or block.startswith('|') or block.startswith('!['):
            continue
        for line in block.splitlines():
            text = md_plain(line, tables=False)
            text = re.sub(r'^\d+\.\s*', '', text)
            if text and norm(text) not in docx.replace('\t', ' '):
                missing.append(text[:80])
    if missing:
        fail(failures, f'{len(missing)} Markdown lines not found in the Word file, e.g. {missing[:3]}')

    # 3. AI acknowledgement unchanged and present once.
    import hashlib
    AI_ACK = md.split('### AI acknowledgement')[1].strip().split('\n\n')[0].strip()
    if hashlib.sha256(AI_ACK.encode()).hexdigest() != AI_ACK_SHA256:
        fail(failures, 'AI acknowledgement differs from the 14 October report')
    for name, text in (('Markdown', norm(md)), ('Word', docx), ('README', norm(readme))):
        if text.count(AI_ACK) != 1:
            fail(failures, f'AI acknowledgement changed or duplicated in {name}')

    # 4. Word limit (simple count; Microsoft Word's own count is recorded separately).
    words = word_count(plain)
    if words >= WORD_LIMIT:
        fail(failures, f'Word count {words} is not under {WORD_LIMIT}')

    # 5. PDF: same text and every font embedded.
    pdf_info = {}
    try:
        from pypdf import PdfReader
        reader = PdfReader(PKG / 'Final_Report.pdf')
        pdf = norm(' '.join(page.extract_text() or '' for page in reader.pages))
        pdf_info['pages'] = len(reader.pages)
        if AI_ACK not in pdf.replace('- ', '-'):
            compact = re.sub(r'\s', '', pdf)
            if re.sub(r'\s', '', AI_ACK) not in compact:
                fail(failures, 'AI acknowledgement not found in the PDF')
        unembedded = set()
        for page in reader.pages:
            fonts = page.get('/Resources', {}).get('/Font', {})
            for ref in fonts.values():
                font = ref.get_object()
                desc = font.get('/FontDescriptor')
                if font.get('/Subtype') == '/Type0':
                    desc = font['/DescendantFonts'][0].get_object().get('/FontDescriptor')
                if desc is not None:
                    desc = desc.get_object()
                    if not any(k in desc for k in ('/FontFile', '/FontFile2', '/FontFile3')):
                        unembedded.add(str(font.get('/BaseFont')))
        if unembedded:
            fail(failures, f'PDF fonts not embedded: {sorted(unembedded)}')
        pdf_info['unembedded_fonts'] = sorted(unembedded)
    except ImportError:
        pdf_info['skipped'] = 'pypdf not installed'

    # 6. Key numbers against committed outputs.
    out = PKG / 'outputs/revision'
    expect = []
    screening = read_csv(ROOT / 'final-report/screening-followup-2026-10-03/outputs/screening_summary.csv')
    for model in ('full', 'property_only', 'baseline'):
        row = next(r for r in screening if r['scope'] == 'priority_fixed_quota' and float(r['fraction']) == .25
                   and r['metric'] == 'precision' and r['model'] == model)
        expect.append(f"{float(row['mean']) * 100:.1f}%")
    profile = {r['homes_label']: r for r in read_csv(out / 'target_profile.csv')}
    expect += [f"{float(profile['Reached 30 reviews']['one_night_percent']):.1f}%",
               f"{float(profile['Below 30 reviews']['one_night_percent']):.1f}%",
               f"{float(profile['Reached 30 reviews']['city_of_melbourne_percent']):.1f}%"]
    money = {r['group']: r for r in read_csv(out / 'group_estimated_revenue.csv')}
    for group in ('Melbourne 3BR Apartment/unit', 'Melbourne 2BR Apartment/unit', 'Yarra Ranges 3BR House/townhouse'):
        expect.append(f"{round(float(money[group]['median_est_revenue_aud']), -2):,.0f}")
        expect.append(f"{round(float(money[group]['median_weekly_aud']), -1):,.0f}")
        # Table 4: rank on revenue and the below-target median, side by side in the group's row.
        expect.append(f"| {int(money[group]['rank_median_revenue'])} | "
                      f"{round(float(money[group]['median_est_revenue_below_target_aud']), -2):,.0f} |")
        expect.append(f"{round(float(money[group]['median_weekly_below_target_aud']), -1):,.0f}")
    confusion = read_csv(ROOT / 'final-presentation/analysis/outputs/test_confusion.csv')[0]
    expect += [f"{int(confusion[k]):,}" for k in ('true_positives', 'false_positives', 'false_negatives', 'true_negatives')]
    for r in read_csv(out / 'all_term_odds_ratios.csv'):
        if r['term'] != '(Intercept)':
            expect.append(f"{float(r['odds_ratio']):.2f}")
    shares = {r['group']: float(r['share_in_top3']) for r in read_csv(out / 'top3_resample_shares.csv')}
    expect += [f"{shares['Melbourne 3BR Apartment/unit'] * 100:.0f}%", f"{shares['Melbourne 2BR Apartment/unit'] * 100:.0f}%",
               f"{shares['Yarra Ranges 3BR House/townhouse'] * 100:.0f}%"]
    price = {r['price_rule']: r for r in read_csv(out / 'residential_price_check.csv')}
    expect += [f"{float(price['Removed by price rule']['zero_recent_review_percent']):.1f}%",
               f"{float(price['Kept by price rule']['zero_recent_review_percent']):.1f}%"]
    absent = [e for e in expect if e not in md]
    if absent:
        fail(failures, f'Values from committed outputs not found in the report: {absent}')

    result = {
        'revision_date': '2026-10-18',
        'branch': 'final-report-marking-fixes-2026-10-16',
        'checks_passed': not failures,
        'failures': failures,
        'simple_word_count_full_document': words,
        'values_checked_against_outputs': len(expect),
        'ai_acknowledgement_unchanged': not any('AI acknowledgement' in f for f in failures),
        'pdf': pdf_info,
    }
    previous = json.loads((PKG / 'package_checks.json').read_text()) if (PKG / 'package_checks.json').exists() else {}
    for key in ('microsoft_word_count_full_document', 'render_method'):
        if key in previous:
            result[key] = previous[key]
    if result.get('microsoft_word_count_full_document', 0) >= WORD_LIMIT:
        fail(failures, f"Microsoft Word count {result['microsoft_word_count_full_document']} is not under {WORD_LIMIT}")
        result['checks_passed'] = False
        result['failures'] = failures
    (PKG / 'package_checks.json').write_text(json.dumps(result, indent=2) + '\n')
    if failures:
        print('FAIL:\n  ' + '\n  '.join(failures))
        sys.exit(1)
    print(f'PASS: report package consistent; {words} words; {len(expect)} values match committed outputs.')


if __name__ == '__main__':
    main()
