#!/usr/bin/env python3
"""Add a manual, medium-speed native fade to all ten slides.

Usage: bundled-python add_transitions.py INPUT.pptx OUTPUT.pptx
All package parts other than slide XML remain byte-identical. Existing slide
transitions are replaced; existing timing, shapes, text and chart references are
preserved. This does not claim to verify playback in PowerPoint.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import re
import tempfile
from zipfile import ZipFile

from lxml import etree


P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS = {"p": P, "a": A}
SLIDE_RE = re.compile(r"ppt/slides/slide(\d+)\.xml\Z")
PARSER = etree.XMLParser(resolve_entities=False, no_network=True, remove_blank_text=False)


def parse(data: bytes):
    return etree.fromstring(data, parser=PARSER)


def without_transition(node) -> bytes:
    clone = copy.deepcopy(node)
    for child in list(clone):
        if child.tag == f"{{{P}}}transition":
            clone.remove(child)
    return etree.tostring(clone, method="c14n", with_comments=True)


def add_fade(data: bytes) -> bytes:
    root = parse(data)
    if root.tag != f"{{{P}}}sld":
        raise ValueError("Expected a p:sld document")
    original_content = without_transition(root)
    original_text = root.xpath("//a:t/text()", namespaces=NS)
    original_namespaces = dict(root.nsmap)
    for child in list(root):
        if child.tag == f"{{{P}}}transition":
            root.remove(child)

    transition = etree.Element(f"{{{P}}}transition", spd="med", advClick="1")
    etree.SubElement(transition, f"{{{P}}}fade")
    # CT_Slide child order: cSld, clrMapOvr?, transition?, timing?, extLst?.
    index = len(root)
    for i, child in enumerate(root):
        if child.tag in (f"{{{P}}}timing", f"{{{P}}}extLst"):
            index = i
            break
    root.insert(index, transition)

    if without_transition(root) != original_content:
        raise ValueError("Slide content changed beyond the transition")
    if root.xpath("//a:t/text()", namespaces=NS) != original_text:
        raise ValueError("Slide text, including numbers, changed")
    if dict(root.nsmap) != original_namespaces:
        raise ValueError("Slide namespace bindings changed")
    result = etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)
    check = parse(result)
    transitions = check.findall(f"{{{P}}}transition")
    if len(transitions) != 1:
        raise ValueError("Each slide must contain exactly one transition")
    t = transitions[0]
    if t.attrib != {"spd": "med", "advClick": "1"} or len(t) != 1 or t[0].tag != f"{{{P}}}fade":
        raise ValueError("Expected medium manual fade without automatic advance")
    if without_transition(check) != original_content:
        raise ValueError("Serialized slide content did not remain identical")
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    source, destination = args.input.resolve(), args.output.resolve()
    if source == destination:
        raise ValueError("Use a separate output path to preserve the source presentation")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(source, "r") as zin:
        infos = zin.infolist()
        if len({i.filename for i in infos}) != len(infos):
            raise ValueError("Duplicate ZIP package parts are not supported")
        slides = sorted((i.filename for i in infos if SLIDE_RE.fullmatch(i.filename)),
                        key=lambda n: int(SLIDE_RE.fullmatch(n).group(1)))
        if len(slides) != 10:
            raise ValueError(f"Expected exactly 10 slides, found {len(slides)}")
        originals = {i.filename: zin.read(i.filename) for i in infos}
        changes = {name: add_fade(originals[name]) for name in slides}
        fd, temp_name = tempfile.mkstemp(prefix=f".{destination.stem}-", suffix=".pptx", dir=destination.parent)
        os.close(fd)
        temporary = Path(temp_name)
        try:
            with ZipFile(temporary, "w") as zout:
                zout.comment = zin.comment
                for info in infos:
                    zout.writestr(info, changes.get(info.filename, originals[info.filename]))
            with ZipFile(temporary, "r") as check:
                if check.testzip() is not None:
                    raise ValueError("Output ZIP integrity check failed")
                if check.namelist() != [i.filename for i in infos]:
                    raise ValueError("Package part membership or order changed")
                for name, before in originals.items():
                    after = check.read(name)
                    if name in changes:
                        node = parse(after)
                        if len(node.findall(f"{{{P}}}transition")) != 1:
                            raise ValueError(f"Incorrect transition count in {name}")
                        if without_transition(parse(before)) != without_transition(node):
                            raise ValueError(f"Unexpected slide modification: {name}")
                    elif after != before:
                        raise ValueError(f"Unexpected package modification: {name}")
            temporary.replace(destination)
        finally:
            if temporary.exists():
                temporary.unlink()

    print(json.dumps({
        "input": str(source), "output": str(destination), "slides": len(slides),
        "transition": "native fade", "speed": "medium", "advance_on_click": True,
        "automatic_advance": False, "transitions_per_slide": 1,
        "slide_content_preserved": True, "all_other_parts_byte_identical": True,
        "chart_parts_preserved": True, "powerpoint_playback_verified": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
