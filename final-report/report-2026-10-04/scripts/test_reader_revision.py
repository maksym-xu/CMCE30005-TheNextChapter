"""Public-input regression checks for report-first navigation and Figure 5."""
from pathlib import Path
import csv, hashlib, unittest, zipfile
from collections import defaultdict

PKG=Path(__file__).resolve().parents[1]
ROOT=PKG.parents[1]


class ReaderRevisionTests(unittest.TestCase):
    def test_report_repository_links_point_to_main(self):
        import re
        from pypdf import PdfReader
        md=(PKG/'Final_Report.md').read_text(encoding='utf-8')
        expected='https://github.com/maksym-xu/CMCE30005-TheNextChapter/tree/main'
        links=re.findall(r'\]\((https://github.com/[^)]+)\)',md)
        self.assertEqual(links,[expected,expected])
        pdf_links=[]
        for page in PdfReader(PKG/'Final_Report.pdf').pages:
            for ref in page.get('/Annots',[]):
                action=ref.get_object().get('/A',{})
                url=action.get('/URI','')
                if 'github.com/' in url:
                    pdf_links.append(str(url))
        self.assertTrue(pdf_links)
        self.assertEqual(set(pdf_links),{expected})

    def test_figures_and_direct_links_present(self):
        import re
        md=(PKG/'Final_Report.md').read_text(encoding='utf-8')
        figures=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',md)
        self.assertEqual(len(figures),5)
        self.assertTrue(all((PKG/path).is_file() for path in figures))
        self.assertNotIn('google.com/search',md)
        self.assertNotIn('all-market',md.lower())

    def test_report_precedes_repository_guide(self):
        md=(PKG/'Final_Report.md').read_text(encoding='utf-8')
        readme=(ROOT/'README.md').read_text(encoding='utf-8')
        self.assertLess(readme.index('## 1. Introduction'),readme.index('## Repository guide'))
        body=readme.split('<!-- final report starts here -->',1)[1].split('<!-- final report ends here -->',1)[0].strip()
        body=body.replace('](final-report/report-2026-10-04/figures/','](figures/')
        self.assertEqual(body,md[md.index('## 1. Introduction'):].strip())

    def test_weekly_curve_is_complete_and_monotone(self):
        by_group=defaultdict(list)
        with (PKG/'outputs/revision/weekly_revenue_reach.csv').open(encoding='utf-8-sig',newline='') as f:
            for row in csv.DictReader(f):
                by_group[row['group']].append((float(row['weekly_cost_aud']),float(row['share_reaching'])))
        self.assertEqual(len(by_group),3)
        for points in by_group.values():
            points.sort()
            self.assertEqual([x for x,y in points],list(range(0,2001,10)))
            self.assertTrue(all(0<=y<=1 for x,y in points))
            self.assertEqual(points[0][1],1)
            self.assertTrue(all(a[1]>=b[1] for a,b in zip(points,points[1:])))

    def test_figure_five_embedded_in_word(self):
        expected=hashlib.sha256((PKG/'figures/figure_5_weekly_reach.png').read_bytes()).digest()
        with zipfile.ZipFile(PKG/'Final_Report.docx') as z:
            media={hashlib.sha256(z.read(n)).digest() for n in z.namelist() if n.startswith('word/media/')}
        self.assertIn(expected,media)


if __name__=='__main__':
    unittest.main()
