"""Download one pinned official model to scratch; verify Hub hashes without exposing credentials."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'configs/posttraining/qwen35-smoke-20260930.json'


def hash_file(path, algorithm='sha256', prefix=b''):
    h = hashlib.new(algorithm)
    h.update(prefix)
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


config = json.loads(CONFIG.read_text())
target = Path(config['model_path'])
assert target.is_relative_to(Path('/mfs1/u/memo/country-persona-research/models'))
token = Path(os.environ['HF_TOKEN_PATH']).read_text().strip()
api = HfApi(token=token)
metadata = api.model_info(config['model'], revision=config['revision'], files_metadata=True)
assert metadata.sha == config['revision']
snapshot_download(config['model'], revision=config['revision'], local_dir=target, token=token,
                  allow_patterns=['*.json', '*.safetensors', '*.jinja', '*.txt', '*.model'], max_workers=2)
files = {}
for member in metadata.siblings:
    path = target / member.rfilename
    if not path.is_file():
        continue
    size = path.stat().st_size
    digest = hash_file(path)
    if member.lfs:
        expected = member.lfs.sha256
        assert size == member.lfs.size and digest == expected, member.rfilename
        method = 'hub_lfs_sha256'
    else:
        git_hash = hash_file(path, 'sha1', f'blob {size}\0'.encode())
        assert git_hash == member.blob_id, member.rfilename
        expected = member.blob_id
        method = 'hub_git_blob_sha1'
    files[member.rfilename] = {'bytes': size, 'sha256': digest, 'hub_hash': expected, 'verification': method}
assert any(name.endswith('.safetensors') for name in files)
receipt = ROOT / 'reports/qwen35-model-verification-20260930.json'
assert not receipt.exists(), 'Preserve earlier download receipts'
receipt.write_text(json.dumps({'status': 'verified_current_official_model_bytes',
    'created_at': datetime.now(timezone.utc).isoformat(), 'model': config['model'],
    'revision': config['revision'], 'path': str(target), 'files': files,
    'config_sha256': hash_file(CONFIG), 'credentials_included': False}, indent=2) + '\n')
print(json.dumps({'status': 'verified_current_official_model_bytes', 'model': config['model'],
                  'revision': config['revision'], 'files': len(files),
                  'bytes': sum(f['bytes'] for f in files.values()), 'receipt': str(receipt)}, indent=2))
