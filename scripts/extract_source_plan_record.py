"""Extract S/PV.9214 from the acquired primary PDF, checking column coverage."""
from collections import Counter
import json
from pathlib import Path
import shutil
import sys
import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, sha256, write_json


def main():
    src = ROOT / 'runs/source-plan-preparation-20261002-v1'
    out = ROOT / 'data/raw/source-plan-grounding-20261002-v1'
    if out.exists() or fitz.VersionBind != '1.26.7':
        raise ValueError('Fresh output and pinned PDF runtime required')
    pdf = src / 'record-9214.pdf'
    receipt = json.loads((src / 'ods-download.json').read_text())
    if receipt['status'] != 'primary_pdf_downloaded' or sha256(pdf) != receipt['sha256']:
        raise ValueError('Acquired primary PDF changed')
    doc = fitz.open(pdf)
    text, sections, coverage = '', [], []
    for i, page in enumerate(doc):
        if tuple(page.rect) != (0, 0, 612, 792):
            raise ValueError('Unexpected page layout')
        parts = [('cover', page.rect)] if i == 0 else [
            ('left', fitz.Rect(50, 80, 307, 710)), ('right', fitz.Rect(307, 80, 563, 710))]
        if i:
            whole = Counter(w[4] for w in page.get_text('words', clip=fitz.Rect(50, 80, 563, 710)))
            split = Counter(w[4] for _, c in parts for w in page.get_text('words', clip=c))
            if whole != split:
                raise ValueError('Column split changes body word coverage')
            coverage.append({'page': i+1, 'body_words': sum(whole.values()), 'equal': True})
        for column, clip in parts:
            s = ' '.join(page.get_text('text', clip=clip, sort=True).split())
            if text:
                text += '\n\n'
            start = len(text)
            text += s
            sections.append({'page': i+1, 'column': column, 'start': start, 'end': len(text)})
    statements = {}
    boundaries = {
        'BRA': ('Mr. De Almeida Filho (Brazil):', 'Ms. Heimerback (Norway):'),
        'IND': ('I shall now make a statement as the representative of India.',
                'I now resume my functions as President of the Council.')}
    for country, (begin, end) in boundaries.items():
        if text.count(begin) != 1 or text.count(end) != 1:
            raise ValueError('Speech boundary ambiguous')
        a = text.index(begin)
        b = text.index(end, a)
        statements[country] = {'start': a, 'end': b, 'text': text[a:b].strip(),
                              'text_digest': digest(text[a:b].strip()),
                              'pages_columns': [s for s in sections if s['start'] < b and s['end'] > a]}
    out.mkdir(parents=True)
    shutil.copy2(pdf, out / pdf.name)
    shutil.copy2(__file__, out / 'extractor.py')
    (out / 'record-9214.txt').write_text(text)
    write_json(out / 'columns.json', {'text_digest': digest(text), 'sections': sections})
    write_json(out / 'statements.json', statements)
    write_json(out / 'acquisition.json', {
        **receipt, 'symbol': 'S/PV.9214', 'document_date': '2022-12-09', 'pages': len(doc),
        'method': 'PyMuPDF 1.26.7; columns left [50,80,307,710], right [307,80,563,710]; sort=True; whitespace normalized',
        'coverage': coverage, 'visual_review': 'Same assistant inspected pages 4, 7 and 8, including both speech boundaries.',
        'benchmark_defects': ['India national statement mislabeled The President / Unknown country'],
        'corrected_preview_observation': 'Brazil closing balance paragraph IS present in the benchmark statement; the initial assistant preview overlooked it.',
        'independent_review_complete': False,
        'files_sha256': {p.name: sha256(p) for p in out.iterdir()}})
    print(json.dumps({'statements': {c: len(s['text']) for c,s in statements.items()},
                      'pdf_sha256': sha256(pdf), 'coverage_equal': True}))


if __name__ == '__main__':
    main()
