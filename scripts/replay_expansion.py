#!/usr/bin/env python3
"""Replay the frozen acquisition manifest after cloning, without crawling new pages."""
from collections import defaultdict
from pathlib import Path
import json
from country_persona.acquire import download
from country_persona.io import write_json

manifest=json.loads(Path('data/manifests/expansion-20260913.json').read_text())
collections=defaultdict(list)
for item in manifest['documents']:
    download(item['url'],item['path'],source_id=item['source_id'],expected_sha256=item['sha256'],max_bytes=35_000_000,timeout=30)
    collections[item['source_id']].append(item)
for source,items in collections.items():
    write_json(Path('data/raw/expansion-20260913')/source/'collection.json',dict(documents=items,errors=[],selection='frozen manifest replay'))
print('Replayed',sum(map(len,collections.values())),'documents with pinned SHA256 checks')
