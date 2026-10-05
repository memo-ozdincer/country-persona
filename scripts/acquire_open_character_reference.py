"""Acquire pinned public reference assets; keep credentials out of logs and receipts."""
import concurrent.futures
import hashlib
import json
import os
import time
from pathlib import Path
from datetime import datetime, timezone

from huggingface_hub import HfApi, snapshot_download

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    config_path = ROOT / 'configs/posttraining/open-character-humor-20261004.json'
    config = json.loads(config_path.read_text())
    output = ROOT / config['run'] / 'acquisition'
    output.mkdir(parents=True, exist_ok=True)
    token = Path(os.environ['HF_TOKEN_PATH']).read_text().strip()
    api = HfApi(token=token)

    def acquire(asset):
        prior_path = output / (asset['name'] + '.json')
        if prior_path.exists():
            prior = json.loads(prior_path.read_text())
            if prior['repo'] != asset['repo'] or prior['revision'] != asset['revision']:
                raise ValueError('Existing acquisition receipt has a different asset lock')
            dest = Path(prior['path'])
            for name, record in prior['files'].items():
                if (dest / name).stat().st_size != record['bytes'] or sha256(dest / name) != record['sha256']:
                    raise ValueError('Previously acquired public asset bytes changed')
            print(json.dumps({'asset': asset['name'], 'status': 'previous_receipt_reverified'}), flush=True)
            return prior
        info = api.repo_info(asset['repo'], revision=asset['revision'], repo_type=asset['repo_type'])
        if info.sha != asset['revision']:
            raise ValueError('Pinned repository revision changed')
        dest = Path(config['assets_root']) / asset['name']
        snapshot_download(asset['repo'], revision=asset['revision'], repo_type=asset['repo_type'],
                          allow_patterns=asset.get('patterns'), local_dir=dest, token=token,
                          max_workers=3)
        files = {str(p.relative_to(dest)): {'bytes': p.stat().st_size, 'sha256': sha256(p)}
                 for p in sorted(dest.rglob('*')) if p.is_file() and '.cache' not in p.parts}
        receipt = {**asset, 'path': str(dest), 'files': files, 'retrieved_utc': datetime.now(timezone.utc).isoformat()}
        (output / (asset['name'] + '.json')).write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps({'asset': asset['name'], 'files': len(files), 'bytes': sum(f['bytes'] for f in files.values())}), flush=True)
        return receipt

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        def retry(asset):
            for attempt in range(1, 4):
                try:
                    return acquire(asset)
                except Exception as exc:
                    failure = {'asset': asset['name'], 'attempt': attempt, 'error_type': type(exc).__name__,
                               'time_utc': datetime.now(timezone.utc).isoformat()}
                    with (output / 'failed-attempts.jsonl').open('a') as f: f.write(json.dumps(failure) + '\n')
                    if attempt == 3: raise
                    time.sleep(5 * attempt)
        receipts = list(pool.map(retry, config['assets']))
    summary = {'status': 'pinned_reference_assets_acquired_and_hashed', 'config_sha256': sha256(config_path),
               'assets': receipts, 'credentials_recorded': False}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'status': summary['status'], 'assets': len(receipts)}), flush=True)


if __name__ == '__main__':
    main()
