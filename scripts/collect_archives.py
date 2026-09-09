#!/usr/bin/env python3
"""Collect bounded official archives; raw pages and receipts are the source of truth."""
import argparse
import concurrent.futures
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from country_persona.acquire import download
from country_persona.io import write_json

SOURCES = {
    'mfa': ('https://www.fmprc.gov.cn/eng/xw/fyrbt/lxjzh/', 'html', 'Regular Press Conference'),
    'china_mission': ('https://un.china-mission.gov.cn/eng/hyyfy/', 'htm', None),
    'germany_mission': ('https://new-york-un.diplo.de/un-en/2290000-2290000', None, None),
}


def collect(source, pages, limit):
    base, extension, title_filter = SOURCES[source]
    root = Path('data/raw') / source
    links, errors = {}, []
    for i in range(pages if extension else 1):
        url = base if i == 0 else urljoin(base, f'index_{i}.{extension}')
        path = root / f'index_{i}.html'
        try:
            download(url, path, source_id=source, max_bytes=5_000_000)
            soup = BeautifulSoup(path.read_bytes(), 'html.parser')
            for a in soup.select('a[href]'):
                href = a['href']
                title = a.get_text(' ', strip=True)
                if extension:
                    valid = re.search(r'/t\d{8}_\d+\.html?$', href) and (not title_filter or title_filter in title)
                else:
                    valid = 'Speech' in title and re.search(r'/un-en/\d+-\d+$', href)
                if valid:
                    links[urljoin(url, href)] = title
        except Exception as exc:
            errors.append({'url': url, 'error': str(exc)})
        time.sleep(.25)
    items = list(links.items())[:limit]
    acquired = []
    for i, (url, title) in enumerate(items):
        name = url.rstrip('/').rsplit('/', 1)[-1]
        if '.' not in name:
            name += '.html'
        path = root / 'pages' / name
        cached = path.exists()
        try:
            receipt = download(url, path, source_id=source, max_bytes=5_000_000, timeout=30)
            acquired.append({'url': url, 'title': title, 'path': str(path), 'sha256': receipt['sha256']})
        except Exception as exc:
            errors.append({'url': url, 'error': str(exc)})
        if i % 25 == 0:
            print(source, i + 1, '/', len(items), 'downloaded', len(acquired), flush=True)
            write_json(root / 'collection.json', {'source_id': source, 'discovered': len(links), 'pages_requested': pages,
                       'documents': acquired, 'errors': errors, 'complete': False})
        if not cached:time.sleep(.2)
    report = {'source_id': source, 'discovered': len(links), 'pages_requested': pages,
              'documents': acquired, 'errors': errors, 'complete': True, 'limit': limit}
    write_json(root / 'collection.json', report)
    return {'source': source, 'acquired': len(acquired), 'errors': len(errors)}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--sources', nargs='+', choices=list(SOURCES), default=list(SOURCES))
    p.add_argument('--pages', type=int, default=30)
    p.add_argument('--limit', type=int, default=600)
    args = p.parse_args()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(args.sources)) as pool:
        for result in pool.map(lambda s: collect(s, args.pages, args.limit), args.sources):
            print(result, flush=True)
