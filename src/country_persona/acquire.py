"""Public, bounded downloads. No credentials, browser challenges, or access-control bypass."""
from __future__ import annotations
import json
import time
import urllib.error
import urllib.request
import ssl
import truststore
from datetime import datetime, timezone
from pathlib import Path
from .io import sha256, write_json


def download(url, path, *, source_id, max_bytes=1024**3, expected_sha256=None, timeout=60):
    path = Path(path)
    receipt = path.with_name(path.name + '.receipt.json')
    if path.exists() and receipt.exists():
        old = json.loads(receipt.read_text())
        if old['url'] != url or sha256(path) != old['sha256']:
            raise ValueError(f'Existing download differs from receipt: {path}')
        if expected_sha256 and old['sha256'] != expected_sha256:
            raise ValueError(f'Locked hash mismatch: {path}')
        return old
    if path.exists():
        raise ValueError(f'Existing file has no receipt; use a new destination: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.part')
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'country-persona-research/0.1 (public dataset acquisition)'})
            with urllib.request.urlopen(req, timeout=timeout, context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)) as response, temp.open('wb') as out:
                size = 0
                while block := response.read(1024 * 1024):
                    size += len(block)
                    if size > max_bytes:
                        raise ValueError(f'Download exceeds {max_bytes} bytes: {url}')
                    out.write(block)
                info = {'source_id': source_id, 'url': url, 'resolved_url': response.url,
                        'retrieved_at': datetime.now(timezone.utc).isoformat(),
                        'content_type': response.headers.get('Content-Type'),
                        'etag': response.headers.get('ETag'), 'bytes': size}
            if not size:
                raise ValueError(f'Empty response: {url}')
            info['sha256'] = sha256(temp)
            if expected_sha256 and info['sha256'] != expected_sha256:
                raise ValueError(f'Checksum mismatch: {url}')
            temp.replace(path)
            write_json(receipt, info)
            return info
        except Exception as exc:
            temp.unlink(missing_ok=True)
            retry = isinstance(exc, (TimeoutError, ConnectionError)) or (
                isinstance(exc, urllib.error.HTTPError) and exc.code in (429, 500, 502, 503, 504))
            if not retry or attempt == 2:
                raise
            time.sleep(2 ** attempt)


def fetch_lock(lock_path, root=Path('.')):
    lock = json.loads(Path(lock_path).read_text())
    successes, failures = [], []
    for item in lock['files']:
        try:
            result = download(item['url'], Path(root) / item['path'], source_id=item['source_id'],
                              expected_sha256=item.get('sha256'), max_bytes=item.get('max_bytes', 1024**3))
            successes.append({**item, 'sha256': result['sha256'], 'bytes': result['bytes']})
        except Exception as exc:
            failures.append({**item, 'error': str(exc)})
    return {'files': successes, 'failures': failures}
