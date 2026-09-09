from __future__ import annotations
import hashlib
import json
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def read_jsonl(path):
    with Path(path).open(encoding='utf-8-sig') as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                try:
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise ValueError('expected an object')
                    yield row
                except (ValueError, TypeError) as exc:
                    raise ValueError(f'{path}:{n}: {exc}') from exc


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.part')
    with temp.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
    temp.replace(path)
