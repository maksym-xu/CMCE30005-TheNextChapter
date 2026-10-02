#!/usr/bin/env python3
"""Check the generated deck's notes, slide structure and native transitions."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--pptx', type=Path, default=ROOT/'deliverables/TheNextChapter_Final.pptx')
args = ap.parse_args()
script = json.loads((ROOT/'code/script.json').read_text())
ns = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
checks = []
def check(condition, label):
    if not condition:
        raise AssertionError(label)
    checks.append(label)

check(len(script['slides']) == 10, 'Ten speaking sections')
check(sum(s['seconds'] for s in script['slides']) == 540, '540 seconds plus 60 seconds of contingency')
for presenter in script['team_summary']:
    check(sum(s['seconds'] for s in script['slides'] if s['speaker'] == presenter['speaker']) == 135,
          presenter['speaker'] + ': 135 seconds')
with ZipFile(args.pptx) as z:
    slides = [n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)]
    check(len(slides) == 10, 'Exactly ten PowerPoint slides')
    for i, s in enumerate(script['slides'], 1):
        root = ET.fromstring(z.read(f'ppt/slides/slide{i}.xml'))
        transition = root.find('p:transition', ns)
        check(transition is not None and transition.find('p:fade', ns) is not None
              and transition.get('advClick') == '1' and transition.get('advTm') is None,
              f'Slide {i}: native Fade, manual advancement')
        notes = ET.fromstring(z.read(f'ppt/notesSlides/notesSlide{i}.xml'))
        text = '\n'.join(t.text or '' for t in notes.findall('.//a:t', ns))
        check(s['script'] in text and f"{s['speaker']} | {s['seconds']} seconds" in text,
              f'Slide {i}: speaker notes match the current script and timing')
    for i in [4, 6, 7]:
        xml = z.read(f'ppt/slides/slide{i}.xml').decode()
        check('chart' in xml, f'Slide {i}: native chart retained')
    slide5 = ET.fromstring(z.read('ppt/slides/slide5.xml'))
    text5 = ' '.join(t.text or '' for t in slide5.findall('.//a:t', ns))
    check('logistic regression for clarity' in text5 and 'random forest remains a benchmark' in text5,
          'Model change explicitly disclosed on the methods slide')
    check('percentage chance' not in text5 and 'historical ranking score' in text5,
          'Score described as historical ranking, not individual future success probability')
    check('Accepts one-night stays' in text5 and 'Price above similar homes' in text5,
          'Two checked conditional associations are visible')
    texts = {}
    for i in [6, 7]:
        xml = ET.fromstring(z.read(f'ppt/slides/slide{i}.xml'))
        texts[i] = ' '.join(t.text or '' for t in xml.findall('.//a:t', ns))
    check('423 / 969' in texts[6] and '546 did not meet it' in texts[6] and 'Historical test' in texts[6],
          'Historical model selection counts and limitation visible')
    check('earlier reference sample sets 34' in texts[7] and 'surviving' in texts[7],
          'Separate temporal sample and 34-review reference threshold visible')
    check('all 3,873 eligible homes' in texts[6] and 'About 16 more' in texts[6],
          'Overall screening scope and absolute benefit visible')
    check('two windows from one snapshot' in texts[7].lower(),
          'Both review windows come from one supplied snapshot')
    for i, expected in [(2, 'plans to lease homes'), (3, 'first recorded review')]:
        xml = ET.fromstring(z.read(f'ppt/slides/slide{i}.xml'))
        text = ' '.join(t.text or '' for t in xml.findall('.//a:t', ns))
        check(expected in text, f'Slide {i}: client/history wording corrected')
    check('within those groups' not in script['slides'][1]['script']
          and 'within each group before shortlisting' not in script['slides'][3]['script'],
          'Main speech does not transfer the overall lift to within-group screening')

result = {'status':'passed', 'pptx':str(args.pptx),
          'sha256':hashlib.sha256(args.pptx.read_bytes()).hexdigest(),
          'checks':checks,
          'note':'Structural checks complement, and do not replace, visual and native PowerPoint inspection.'}
(ROOT/'qa').mkdir(exist_ok=True)
(ROOT/'qa/pptx-content-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'passed', 'checks':len(checks), 'sha256':result['sha256']}))
