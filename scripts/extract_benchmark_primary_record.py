"""Extract the downloaded benchmark record in an isolated PDF runtime with coverage checks."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil

import fitz
from run_aurora_qwen35_smoke import ROOT
from country_persona.io import digest, sha256, write_json


def extract(output):
    if output.exists():
        raise ValueError('Fresh source directory required')
    if fitz.VersionBind != '1.26.7':
        raise ValueError('PDF extraction backend must match the recorded version')
    predecessor = ROOT / 'data/raw/benchmark-plan-grounding-20260930-v1'
    old = json.loads((predecessor / 'acquisition.json').read_text())['sources'][0]
    pdf = predecessor / 'record-9499.pdf'
    if sha256(pdf) != '0575967053afc398fa946fa282366ab4c56a8f44244d415bf261b8576d0742b9':
        raise ValueError('Primary PDF bytes changed')
    document = fitz.open(pdf)
    text, sections, word_counts = '', [], []
    for i, page in enumerate(document):
        if (page.rect.width, page.rect.height) != (612, 792):
            raise ValueError('Column recipe requires the visually checked page dimensions')
        if i == 0:
            parts = [('cover', page.rect)]
        else:
            parts = [('left', fitz.Rect(50, 80, 307, 710)),
                     ('right', fitz.Rect(307, 80, 563, 710))]
            body = fitz.Rect(50, 80, 563, 710)
            full = Counter(w[4] for w in page.get_text('words', clip=body))
            cropped = Counter(w[4] for _, clip in parts for w in page.get_text('words', clip=clip))
            if cropped != full:
                raise ValueError('Column split loses or duplicates body words')
            word_counts.append({'page': i + 1, 'body_words': sum(full.values()),
                                'column_word_coverage_equal': True})
        for column, clip in parts:
            segment = ' '.join(page.get_text('text', clip=clip, sort=True).split())
            if text:
                text += '\n\n'
            start = len(text)
            text += segment
            sections.append({'page': i + 1, 'column': column, 'start': start,
                             'end': len(text), 'text': segment})
    output.mkdir(parents=True)
    shutil.copy2(pdf, output / pdf.name)
    shutil.copy2(Path(__file__), output / 'extractor.py')
    method = 'PyMuPDF 1.26.7; separate cropped columns; sort=True; normalized whitespace'
    write_json(output / 'record-9499.columns.json', {'pdf_sha256': sha256(pdf),
        'text': text, 'text_digest': digest(text), 'sections': sections,
        'method': method, 'crop_points': {'left': [50, 80, 307, 710], 'right': [307, 80, 563, 710]}})
    (output / 'record-9499.txt').write_text(text)
    write_json(output / 'acquisition.json', {'status': 'primary_pdf_and_checked_column_extraction',
        'url': old['url'], 'final_url': old['final_url'], 'symbol': 'S/PV.9499',
        'document_date': '2023-12-08', 'pdf_sha256': sha256(pdf), 'pages': len(document),
        'method': method, 'body_column_word_coverage': word_counts,
        'visual_checks': 'Assistant inspected PDF pages 5, 6 and 8 for speech boundaries and column layout.',
        'failed_predecessor': str(predecessor.relative_to(ROOT)),
        'superseded_narrow_crop': 'data/raw/benchmark-plan-grounding-20260930-v2',
        'independent_review_complete': False,
        'files_sha256': {p.name: sha256(p) for p in output.iterdir() if p.is_file()}})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    extract(parser.parse_args().output)
