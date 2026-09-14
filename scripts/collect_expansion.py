#!/usr/bin/env python3
"""Bounded official-source expansion; all successful downloads have hash receipts.

Run from repository root. Existing releases are never modified. The optional
--refresh flag is deliberately absent: delete neither raw files nor receipts.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import random
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from country_persona.acquire import download
from country_persona.io import digest, write_json

ROOT = Path('data/raw/expansion-20260913')
ARCHIVES = {
    'mfa_zh': ('https://www.fmprc.gov.cn/fyrbt_673021/jzhsl_673025/', 'shtml', 'zh'),
    'mfa_fr': ('https://www.fmprc.gov.cn/fra/wjdt/fyrth/lxjzzdh/', 'html', 'fr'),
    'mfa_es': ('https://www.fmprc.gov.cn/esp/xwfw/lxjzzdh/', 'html', 'es'),
    'mfa_ru': ('https://www.fmprc.gov.cn/rus/mtfw/ce_cegw_chn/lxjzhzhdh/', 'html', 'ru'),
    'china_mission_zh': ('https://un.china-mission.gov.cn/chn/hyyfy/', 'htm', 'zh'),
}


def fetch(source, url, path):
    return download(url, path, source_id=source, max_bytes=15_000_000, timeout=25)


def acquire_items(source, items, discovery, errors):
    docs = []
    for i, item in enumerate(items):
        url = item['url']
        path = ROOT / source / 'pages' / (digest(url)[:20] + '.html')
        cached = path.exists()
        try:
            receipt = fetch(source, url, path)
            docs.append(dict(item, source_id=source, path=str(path), sha256=receipt['sha256']))
        except Exception as exc:
            errors.append({'url': url, 'error': str(exc)})
        if not cached: time.sleep(.2)
        if (i + 1) % 50 == 0:
            print(source, i+1, '/', len(items), 'acquired', len(docs), flush=True)
    report = dict(source_id=source, selection=discovery, documents=docs, errors=errors,
                  acquisition_finished=True, exhaustive=False)
    write_json(ROOT / source / 'collection.json', report)
    return {'source': source, 'documents': len(docs), 'errors': len(errors)}


def collect_archive(source, pages, limit):
    base, ext, lang = ARCHIVES[source]
    links, errors = {}, []
    for i in range(pages):
        url = base if i == 0 else urljoin(base, f'index_{i}.{ext}')
        path = ROOT / source / ('index_' + digest(url)[:16] + '.html')
        try:
            fetch(source, url, path)
            soup = BeautifulSoup(path.read_bytes(), 'html.parser')
            for a in soup.select('a[href]'):
                u = urljoin(url, a['href'])
                if not u.startswith(base) or not re.search(r'/t\d{8}_\d+\.(?:shtml|html|htm)$', u):
                    continue
                title = a.get_text(' ', strip=True)
                links.setdefault(u, dict(url=u, title=title, language=lang, discovery_url=url))
        except Exception as exc:
            errors.append(dict(url=url, error=str(exc)))
        time.sleep(.2)
    items = sorted(links.values(), key=lambda x: x['url'], reverse=True)[:limit]
    return acquire_items(source, items, dict(pages=pages, discovered=len(links), limit=limit,
                         method='bounded newest-first archive; no claim of representative sampling'), errors)


def collect_aa(limit):
    source = 'germany_aa'
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'h': 'http://www.w3.org/1999/xhtml'}
    url = 'https://www.auswaertiges-amt.de/service-sitemap-en-sitemap1.xml.gz'
    path = ROOT / source / 'sitemap.xml.gz'
    fetch(source, url, path)
    candidates = []
    for n in ET.fromstring(gzip.decompress(path.read_bytes())):
        u = n.find('s:loc', ns).text
        # Numeric CMS ID is a discovery heuristic, never treated as an event date.
        m = re.search(r'-(\d+)$', u)
        if '/en/newsroom/news/' not in u or not m or int(m[1]) < 2580000:
            continue
        alternates = {a.attrib['hreflang']: a.attrib['href'] for a in n.findall('h:link', ns)}
        candidates.append(dict(url=u, language='en', title='', alternates=alternates,
                               discovery_url=url, translation_group='aa:alternate:'+digest(sorted(alternates.values()))[:20]))
    selected = random.Random(42).sample(sorted(candidates, key=lambda x:x['url']), min(limit, len(candidates)))
    items = {}
    for x in selected:
        items[x['url']] = x
        for lang, u in x['alternates'].items():
            if lang not in ('de', 'fr') or urlparse(u).netloc != 'www.auswaertiges-amt.de': continue
            items.setdefault(u, dict(x, url=u, language=lang))
    return acquire_items(source, list(items.values()), dict(discovered_english=len(candidates),
                         english_limit=limit, seed=42, method='uniform seeded sample of English newsroom CMS IDs >=2580000 plus publisher-linked de/fr versions'), [])


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--sources', nargs='+', choices=[*ARCHIVES, 'germany_aa'], default=[*ARCHIVES, 'germany_aa'])
    p.add_argument('--pages', type=int, default=16)
    p.add_argument('--limit', type=int, default=400)
    p.add_argument('--aa-limit', type=int, default=250)
    args = p.parse_args()
    # Two concurrent source workers bound pressure on the MFA host.
    with ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(lambda s: collect_aa(args.aa_limit) if s=='germany_aa' else collect_archive(s,args.pages,args.limit), args.sources):
            print(result, flush=True)

if __name__ == '__main__': main()
