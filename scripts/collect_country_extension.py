"""Collect a bounded, source-led extension for France, UK, India and Brazil.

Raw documents are evidence, not automatically national-response supervision.
Public downloads use receipts; failed or non-PDF responses remain exclusions.
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode

from country_persona.acquire import download
from country_persona.io import write_json

ROOT = Path('data/raw/country-extension-20260914')
REGISTRY = Path('data/country_extension_registry.json')


def acquire(item):
    path = ROOT / 'documents' / (item['id'] + '.' + item['format'])
    try:
        receipt = download(item['url'], path, source_id=item['source_id'],
                           max_bytes=80_000_000, timeout=40)
        if item['format'] == 'pdf' and b'%PDF-' not in path.read_bytes()[:1024]:
            raise ValueError('Publisher response is not a PDF')
        return {**item, 'raw_file': str(path), 'raw_sha256': receipt['sha256'],
                'retrieved_at': receipt['retrieved_at'], 'status': 'acquired'}
    except Exception as exc:
        return {**item, 'raw_file': str(path), 'status': 'excluded', 'error': str(exc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    registry = json.loads(REGISTRY.read_text())
    items = list(registry['documents'])
    for country, symbol in registry['upr_cycle4'].items():
        for lang in ['en', 'fr', 'es', 'zh', 'ru', 'ar']:
            items.append({'id': f'upr4-{country}-{lang}', 'source_id': 'un_upr_national_report',
                'countries': [country], 'represented_entity': registry['countries'][country],
                'format': 'pdf', 'language': lang, 'date': None,
                'date_basis': 'issue_date_requires_PDF_header_extraction',
                'document_symbol': symbol, 'upr_cycle': 4,
                'group_id': 'un:document:' + symbol, 'proposed_split': 'test',
                'kind': 'national_self_report', 'title': f'{country} fourth-cycle UPR national report',
                'attribution': 'national_government_submission_not_independent_finding',
                'url': 'https://documents.un.org/api/symbol/access?' + urlencode({'l': lang, 's': symbol, 't': 'pdf'})})
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 3))) as pool:
        results = list(pool.map(acquire, items))
    write_json(ROOT / 'collection.json', {'registry': str(REGISTRY), 'documents': results})
    for r in results:
        print(r['status'], r['id'], r.get('error', ''))


if __name__ == '__main__':
    main()
