#!/usr/bin/env python3
"""Acquire two fourth-cycle national reports through the public UN document API.

All language versions stay in the existing UPR cycle-4 test partition. These are
national submissions, not findings by an independent human-rights body.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode
from country_persona.acquire import download
from country_persona.io import write_json
ROOT=Path('data/raw/expansion-20260913/upr_national_reports')
REPORTS=[('CHN','A/HRC/WG.6/45/CHN/1'),('DEU','A/HRC/WG.6/44/DEU/1')]

def get(item):
    country,symbol,lang=item
    url='https://documents.un.org/api/symbol/access?'+urlencode(dict(l=lang,s=symbol,t='pdf'))
    path=ROOT/(country+'-'+lang+'.pdf')
    try:
        rec=download(url,path,source_id='upr_national_reports',max_bytes=15_000_000,timeout=30)
        if not path.read_bytes().startswith(b'%PDF'):raise ValueError('Not a PDF')
        return dict(source_id='upr_national_reports',country=country,symbol=symbol,language=lang,
            url=url,path=str(path),sha256=rec['sha256'],publisher_split='test',upr_cycle=4)
    except Exception as e:return dict(url=url,error=str(e))

def main():
    with ThreadPoolExecutor(max_workers=2) as ex:
        results=list(ex.map(get,[(c,s,l) for c,s in REPORTS for l in ('en','zh','fr','es','ru','ar')]))
    write_json(ROOT/'collection.json',dict(documents=[r for r in results if 'error' not in r],errors=[r for r in results if 'error' in r]))
    print('UPR documents',len([r for r in results if 'error' not in r]), 'errors', [r for r in results if 'error' in r])

if __name__=='__main__':main()
