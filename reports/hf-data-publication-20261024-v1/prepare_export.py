"""Plan a bounded private HF export without copying or altering research payloads."""
from __future__ import annotations
from collections import Counter
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from zoneinfo import ZoneInfo

ROOT = Path('/mfs1/u/memo/country-persona-research/workspaces/persona-20260929-v1')
OUT = Path(__file__).resolve().parent
REPO = 'memo-ozdincer/country-persona-aurora-data'
PIN = 'fafbe6a52c944fe7ceb9abc473b7f7924566c1260d8d925691aedf20a915ea9b'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    if git('status', '--porcelain'):
        raise ValueError('Require a clean committed source workspace')
    source_commit = git('rev-parse', 'HEAD').decode().strip()
    frozen_raw = (ROOT / 'handoff/manifest.json').read_bytes()
    if hashlib.sha256(frozen_raw).hexdigest() != PIN:
        raise ValueError('Original snapshot manifest differs')
    frozen = json.loads(frozen_raw)
    tracked = {}
    for row in git('ls-files', '--stage', '-z').decode().split('\0'):
        if not row:
            continue
        meta, name = row.split('\t', 1)
        mode, oid, stage = meta.split()
        if mode not in ('100644', '100755') or stage != '0':
            raise ValueError('Nonregular/unmerged source Git file')
        tracked[name] = oid
    candidates = {}
    for name in sorted(set(frozen['files']) | set(tracked)):
        candidates[name] = {'local_path': str(ROOT / name),
                            'source': 'committed_git' if name in tracked else 'immutable_snapshot',
                            'expected_git_oid': tracked.get(name),
                            'expected': frozen['files'].get(name) if name not in tracked else None}

    def add(name, local_path, expected, source):
        if name in candidates:
            old = candidates[name]
            if old['local_path'] != str(local_path) or old['expected'] is None:
                raise ValueError('Unexpected supplement overlap: ' + name)
            if (old['expected']['bytes'], old['expected']['sha256']) != (expected['bytes'], expected['sha256']):
                raise ValueError('Conflicting pinned supplement bytes: ' + name)
            return
        candidates[name] = {'local_path': str(local_path), 'source': source,
                            'expected': expected, 'expected_git_oid': None}

    scenario = json.loads((ROOT / 'reports/scenario-checkpoint-delivery-20261018-v1.manifest.json').read_text())
    for name, expected in scenario['files'].items():
        add(name, ROOT / name, expected, 'verified_scenario_checkpoint')

    pairs = [
        ('research/native-plan-writer-20261019-v1/runtime-initial', 'runs/native-plan-writer-20261019-v1'),
        ('research/native-plan-writer-20261019-v1/runtime-fit', 'runs/native-plan-writer-resume-20261019-v1'),
        ('research/native-application-writer-20261019-v1/runtime', 'runs/native-application-writer-20261019-v1'),
        ('research/native-writer-revision-20261019-v1/runtime', 'runs/native-writer-revision-20261019-v1'),
    ]
    scope = json.loads((ROOT / 'reports/native-scope-partial-adapter-manifest-20261019-v1.json').read_text())
    pairs += scope['metadata_restore_pairs']
    for mirror, destination in pairs:
        for path in sorted((ROOT / mirror).rglob('*')):
            if not path.is_file():
                continue
            name = (Path(destination) / path.relative_to(ROOT / mirror)).as_posix()
            original = ROOT / name
            raw = path.read_bytes()
            if not original.is_file() or original.read_bytes() != raw:
                raise ValueError('Recorded runtime mirror differs: ' + name)
            add(name, original, {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}, 'exact_git_runtime_mirror')
    for manifest_path, destination in [
        ('reports/native-plan-writer-adapter-manifest-20261019-v1.json', 'runs/native-plan-writer-resume-20261019-v1/adapter'),
        ('reports/native-application-writer-adapter-manifest-20261019-v1.json', 'runs/native-application-writer-20261019-v1/adapter'),
        ('reports/native-scope-partial-adapter-manifest-20261019-v1.json', 'runs/native-scope-partial-writer-20261019-v1/adapter'),
    ]:
        data = json.loads((ROOT / manifest_path).read_text())
        for asset in data['assets']:
            name = destination + '/' + asset['name']
            add(name, ROOT / name, asset, 'verified_native_adapter')

    # Secret values stay in memory, never in commands, plans, receipts or uploads.
    token = Path(os.environ['HF_TOKEN_PATH']).read_bytes().strip()
    secret_pattern = re.compile(rb'hf_[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}')
    entries = []
    for index, (name, source) in enumerate(sorted(candidates.items()), 1):
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe selected path')
        if relative.parts[0] in ('models', 'envs', 'cache', 'audits', 'exports') or set(relative.parts) & {'.git', '.venv', '__pycache__', 'secrets'}:
            raise ValueError('Excluded scratch/secret/cache path selected: ' + name)
        path = Path(source['local_path'])
        if path.is_symlink() or not path.is_file():
            raise ValueError('Missing/nonregular source: ' + name)
        before = path.stat()
        digest = hashlib.sha256()
        oid = hashlib.sha1(('blob ' + str(before.st_size) + '\0').encode())
        tail = b''
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
                digest.update(chunk)
                oid.update(chunk)
                scan = tail + chunk
                if token in scan or secret_pattern.search(scan):
                    raise ValueError('Potential credential detected; export stopped before upload: ' + name)
                tail = scan[-256:]
        after = path.stat()
        if (before.st_ino, before.st_mtime_ns, before.st_size) != (after.st_ino, after.st_mtime_ns, after.st_size):
            raise ValueError('Source changed while reading: ' + name)
        expected = source['expected']
        if expected and (before.st_size != expected['bytes'] or digest.hexdigest() != expected['sha256']):
            raise ValueError('Pinned source bytes differ: ' + name)
        if source['expected_git_oid'] and oid.hexdigest() != source['expected_git_oid']:
            raise ValueError('Working bytes differ from committed Git: ' + name)
        entries.append({'path': 'workspace/' + name, 'bytes': before.st_size,
                        'sha256': digest.hexdigest(), 'git_blob_sha1': oid.hexdigest(),
                        'source': source['source'], 'local_path': str(path),
                        'source_stat': {'inode': before.st_ino, 'mtime_ns': before.st_mtime_ns}})
        if index % 1000 == 0:
            print(json.dumps({'hashed_and_scanned': index, 'of': len(candidates)}), flush=True)

    metadata = {'schema_version': 1, 'repo_id': REPO, 'repo_type': 'dataset', 'required_private': True,
                'created_at': datetime.now(ZoneInfo('America/Toronto')).isoformat(),
                'source_git_commit': source_commit, 'snapshot_manifest_sha256': PIN,
                'snapshot_base_commit': frozen['base_commit'],
                'file_count': len(entries), 'bytes': sum(e['bytes'] for e in entries),
                'sources': dict(Counter(e['source'] for e in entries)),
                'credential_scan': 'All selected bytes scanned; credential values never recorded.',
                'excluded': ['Credentials and private environment profiles', 'Base model weights',
                             'Installed environments, caches and unrelated scratch/audits',
                             'Large older/Reddit corpora omitted from the original v47 snapshot'],
                'legacy_private_dataset': 'memo-ozdincer/country-persona-research-files',
                'research_goal_status': 'paused', 'new_model_calls': 0, 'new_optimizer_updates': 0}
    local_plan = {**metadata, 'files': entries}
    with (OUT / 'local-upload-plan.json').open('x') as stream:
        json.dump(local_plan, stream, indent=2)
        stream.write('\n')
    public_manifest = {**metadata, 'files': [{k:v for k,v in e.items() if k not in ('local_path', 'source_stat')} for e in entries]}
    with (OUT / 'FILE_MANIFEST.json').open('x') as stream:
        json.dump(public_manifest, stream, indent=2)
        stream.write('\n')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
