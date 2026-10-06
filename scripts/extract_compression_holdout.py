"""Extract primary ICC/Libya meeting columns; preserve columns and word coverage."""
from collections import Counter
import json
import re
import shutil
import sys
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, sha256, write_json


def main():
    out = ROOT / 'data/raw/compression-libya-grounding-20261006-v1'
    assert fitz.VersionBind == '1.26.7'
    assert not (out / 'record-9469.txt').exists()
    receipt = json.loads((out / 'download.json').read_text())
    pdf = out / 'record-9469.pdf'
    assert sha256(pdf) == receipt['sha256']
    doc = fitz.open(pdf)
    assert 'Security Council' in doc[0].get_text() and 'S/PV.9469' in doc[0].get_text(), 'English edition required'
    text, sections, coverage = '', [], []
    for i, page in enumerate(doc):
        assert tuple(page.rect) == (0, 0, 612, 792)
        parts = [('cover', page.rect)] if i == 0 else [
            ('left', fitz.Rect(50, 80, 307, 710)), ('right', fitz.Rect(307, 80, 563, 710))]
        if i:
            whole = Counter(w[4] for w in page.get_text('words', clip=fitz.Rect(50, 80, 563, 710)))
            split = Counter(w[4] for _, clip in parts for w in page.get_text('words', clip=clip))
            assert whole == split
            coverage.append({'page': i + 1, 'words': sum(whole.values()), 'equal': True})
        for column, clip in parts:
            body = ' '.join(page.get_text('text', clip=clip, sort=True).split())
            if text:
                text += '\n\n'
            start = len(text); text += body
            sections.append({'page': i + 1, 'column': column, 'start': start, 'end': len(text)})
        if i:
            page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).save(str(out / f'page-{i + 1}.png'))
    (out / 'record-9469.txt').write_text(text)
    write_json(out / 'columns.json', {'text_digest': digest(text), 'sections': sections, 'coverage': coverage})
    shutil.copy2(__file__, out / 'extractor.py')
    print(json.dumps({'pages':len(doc),'chars':len(text),'body_word_counters_equal':True}))


if __name__ == '__main__':
    main()
