"""Primary-PDF extraction for a fresh Mali withdrawal application checkpoint."""
from collections import Counter
from pathlib import Path
import json
import shutil
import sys
import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from country_persona.io import digest, sha256, write_json


def main():
    preparation = ROOT/'runs/coverage-objective-preparation-20261003-v1'
    out = ROOT/'data/raw/coverage-objective-grounding-20261003-v1'
    if out.exists() or fitz.VersionBind != '1.26.7':
        raise ValueError('Fresh output and pinned PDF runtime required')
    download = json.loads((preparation/'download.json').read_text())
    pdf = preparation/'record-9365.pdf'
    if sha256(pdf) != download['sha256']:
        raise ValueError('Downloaded bytes changed')
    doc = fitz.open(pdf)
    text, sections, coverage = '', [], []
    for i, page in enumerate(doc):
        parts = [('cover', page.rect)] if i == 0 else [('left',fitz.Rect(50,80,307,710)),('right',fitz.Rect(307,80,563,710))]
        if i:
            whole = Counter(w[4] for w in page.get_text('words',clip=fitz.Rect(50,80,563,710)))
            split = Counter(w[4] for _, rect in parts for w in page.get_text('words',clip=rect))
            if whole != split:
                raise ValueError('Body words lost or duplicated')
            coverage.append({'page':i+1,'words':sum(whole.values()),'equal':True})
        for column, rect in parts:
            segment = ' '.join(page.get_text('text',clip=rect,sort=True).split())
            text += '\n\n' if text else ''
            a = len(text)
            text += segment
            sections.append({'page':i+1,'column':column,'start':a,'end':len(text)})
    statements = {}
    for country, (begin,end) in {'BRA':('Mr. De Almeida Filho (Brazil):','Mr. Hauri (Switzerland)'), 'GBR':('Dame Barbara Woodward (United Kingdom):','Mr. Spasse (Albania)')}.items():
        a = text.index(begin)
        b = text.index(end,a+len(begin))
        statement = text[a:b].strip()
        statements[country] = {'text':statement,'text_digest':digest(statement),'start':a,'end':b,
            'pages_columns':[s for s in sections if s['start'] < b and s['end'] > a],
            'scope':'complete post-adoption national speech; no other speakers are national evidence'}
    out.mkdir(parents=True)
    shutil.copy2(pdf,out/pdf.name)
    shutil.copy2(__file__,out/'extractor.py')
    (out/'record-9365.txt').write_text(text)
    write_json(out/'columns.json',sections)
    write_json(out/'statements.json',statements)
    benchmark = ROOT/'data/raw/unbench-audit-20260926/full/UNBench-all/meetings_adopted/2492/S_PV.9365-EN_statements.json'
    write_json(out/'acquisition.json',{**download,'document_date':'2023-06-30','pages':len(doc),
        'body_column_coverage':coverage,'visual_review':'Assistant inspected PDF pages 4,5,6; full Brazil and UK speech boundaries.',
        'benchmark_file':str(benchmark.relative_to(ROOT)),'benchmark_sha256':sha256(benchmark),
        'primary_governs':'UNBench parser cross-pools neighboring speakers in this event; primary column extraction is used.',
        'independent_review_complete':False,'files_sha256':{p.name:sha256(p) for p in out.iterdir()}})
    print({c:len(s['text']) for c,s in statements.items()})


if __name__ == '__main__':
    main()
