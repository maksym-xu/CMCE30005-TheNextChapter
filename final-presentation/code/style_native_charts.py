#!/usr/bin/env python3
"""Preserve native chart colors and explicit axis formats in PowerPoint.

The renderer shows series-colored dots, while native PowerPoint uses the
marker's explicit noFill and theme outline unless marker spPr is set.
Only display styles change; all chart data and all other package parts stay.
"""
import copy
import json
from pathlib import Path
import sys
from zipfile import ZipFile
from lxml import etree as E

source, target = map(Path, sys.argv[1:3])
ns = {'c':'http://schemas.openxmlformats.org/drawingml/2006/chart',
      'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
markers = 0
with ZipFile(source) as inp, ZipFile(target, 'w') as out:
    for info in inp.infolist():
        data = inp.read(info.filename)
        if '/charts/' in info.filename and info.filename.endswith('.xml'):
            root = E.fromstring(data)
            values_before = [E.tostring(n) for n in root.findall('.//c:pt',ns)]
            for series in root.findall('.//c:ser', ns):
                symbol = series.find('c:marker/c:symbol', ns)
                fill = series.find('c:spPr/a:solidFill', ns)
                if symbol is None or symbol.get('val') != 'circle' or fill is None:
                    continue
                marker = series.find('c:marker', ns)
                sp = marker.find('c:spPr', ns)
                if sp is None:
                    sp = E.SubElement(marker, '{'+ns['c']+'}spPr')
                for child in list(sp):
                    sp.remove(child)
                sp.append(copy.deepcopy(fill))
                line = E.SubElement(sp, '{'+ns['a']+'}ln', w='0')
                E.SubElement(line, '{'+ns['a']+'}noFill')
                markers += 1
            for axis in root.findall('.//c:valAx',ns) + root.findall('.//c:catAx',ns):
                fmt = axis.find('c:numFmt',ns)
                if fmt is not None:
                    fmt.set('sourceLinked','0')
            assert values_before == [E.tostring(n) for n in root.findall('.//c:pt',ns)]
            data = E.tostring(root, encoding='UTF-8', xml_declaration=True, standalone=True)
        out.writestr(info,data)
assert markers == 3, f'Expected three observed-share markers, found {markers}'
print(json.dumps({'filled_native_markers':markers,'chart_values_unchanged':True}))
