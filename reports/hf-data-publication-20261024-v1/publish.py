"""Upload a preverified explicit file plan to a private HF dataset; resumable."""
from __future__ import annotations
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import socket
import time
from zoneinfo import ZoneInfo

from huggingface_hub import HfApi, CommitOperationAdd, RepoFile, hf_hub_download
from huggingface_hub.utils import disable_progress_bars

OUT = Path(__file__).resolve().parent
PLAN_PATH = OUT / 'local-upload-plan.json'
TAG = 'aurora-20261024-v1'


def now():
    return datetime.now(ZoneInfo('America/Toronto')).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, obj):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(obj, indent=2) + '\n')
    temp.replace(path)


def lfs_sha(file):
    value = file.lfs
    return value.get('sha256') if isinstance(value, dict) else getattr(value, 'sha256', None)


def matches(file, expected):
    if file is None or file.size != expected['bytes']:
        return False
    digest = lfs_sha(file)
    return digest == expected['sha256'] if digest else file.blob_id == expected['git_blob_sha1']


def main():
    disable_progress_bars()
    token = Path(os.environ['HF_TOKEN_PATH']).read_text().strip()
    api = HfApi(token=token)
    owner = api.whoami()['name']
    plan = json.loads(PLAN_PATH.read_text())
    repo = plan['repo_id']
    if owner != 'memo-ozdincer' or repo != owner + '/country-persona-aurora-data':
        raise ValueError('Unexpected authenticated owner or upload destination')
    api.create_repo(repo, repo_type='dataset', private=True, exist_ok=True)
    info = api.repo_info(repo, repo_type='dataset')
    if info.private is not True:
        raise ValueError('Destination is not private; refusing upload')
    state = {'repo_id': repo, 'plan_sha256': sha(PLAN_PATH.read_bytes()),
             'source_git_commit': plan['source_git_commit'], 'started_at': now(),
             'host': socket.gethostname(), 'pid': os.getpid(), 'gpu_use': False,
             'head': info.sha, 'completed_batches': [], 'status': 'uploading'}
    state_path = OUT / 'upload-state.json'
    if state_path.exists():
        old = json.loads(state_path.read_text())
        if old['plan_sha256'] != state['plan_sha256']:
            raise ValueError('Existing upload state binds a different source plan')
        state['completed_batches'] = old['completed_batches']
        state['started_at'] = old['started_at']

    def remote_index(revision):
        return {f.path: f for f in api.list_repo_tree(repo, repo_type='dataset',
                revision=revision, recursive=True, expand=False) if isinstance(f, RepoFile)}

    remote = remote_index(info.sha)
    allowed = {e['path'] for e in plan['files']} | {'.gitattributes', 'README.md', 'FILE_MANIFEST.json', 'VERIFY_DOWNLOAD.py', 'STATUS.json'}
    if set(remote) - allowed:
        raise ValueError('Destination contains unrelated files; refusing to overwrite it')
    if 'FILE_MANIFEST.json' in remote:
        original = Path(hf_hub_download(repo, 'FILE_MANIFEST.json', repo_type='dataset', revision=info.sha, token=token))
        if original.read_bytes() != (OUT / 'FILE_MANIFEST.json').read_bytes():
            raise ValueError('Destination binds a different export manifest')

    def commit(paths, message):
        for path, local in paths:
            if path.startswith('workspace/'):
                entry = by_path[path]
                stat = local.stat()
                if (stat.st_ino, stat.st_mtime_ns, stat.st_size) != (entry['source_stat']['inode'], entry['source_stat']['mtime_ns'], entry['bytes']):
                    raise ValueError('Source stat changed after preflight: ' + path)
        for attempt in range(6):
            try:
                head = api.repo_info(repo, repo_type='dataset').sha
                result = api.create_commit(repo, repo_type='dataset', parent_commit=head,
                    operations=[CommitOperationAdd(path_in_repo=p, path_or_fileobj=str(f)) for p,f in paths],
                    commit_message=message, num_threads=4)
                state['head'] = result.oid
                state['updated_at'] = now()
                save(state_path, state)
                return result.oid
            except Exception as exc:
                status = getattr(getattr(exc, 'response', None), 'status_code', None)
                if attempt == 5 or status not in (None, 409, 429, 500, 502, 503, 504):
                    save(OUT / 'last-upload-error.json', {'at': now(), 'type': type(exc).__name__,
                         'http_status': status, 'message': message, 'attempt': attempt + 1})
                    raise
                print(json.dumps({'retry': attempt + 1, 'http_status': status, 'operation': message}), flush=True)
                time.sleep(min(2 ** attempt, 20))
        raise AssertionError('Unreachable')

    by_path = {e['path']: e for e in plan['files']}
    pending = [e for e in plan['files'] if not matches(remote.get(e['path']), e)]
    for e in plan['files']:
        if e['path'] in remote and not matches(remote[e['path']], e):
            raise ValueError('Existing payload path has different bytes: ' + e['path'])
    state['already_verified_files'] = len(plan['files']) - len(pending)
    save(state_path, state)
    if pending:
        (OUT / 'STATUS.json').write_text(json.dumps({'status':'uploading','expected_files':plan['file_count'],
             'expected_bytes':plan['bytes'],'source_git_commit':plan['source_git_commit']},indent=2)+'\n')
        metadata = [(name, OUT / name) for name in ['README.md','FILE_MANIFEST.json','VERIFY_DOWNLOAD.py','STATUS.json']]
        commit(metadata, 'Initialize private Aurora research export and exact file manifest')
    batches = []
    batch = []
    small_bytes = 0
    for entry in pending:
        weight = entry['bytes'] if entry['bytes'] < 10 * 1024 * 1024 else 0
        if batch and (len(batch) >= 200 or small_bytes + weight > 16 * 1024 * 1024):
            batches.append(batch)
            batch = []
            small_bytes = 0
        batch.append(entry)
        small_bytes += weight
    if batch:
        batches.append(batch)
    print(json.dumps({'uploading_files':len(pending),'resumed_verified_files':state['already_verified_files'],
                      'batches':len(batches),'payload_bytes':plan['bytes'],'private':True}),flush=True)
    for index, batch in enumerate(batches, 1):
        commit([(e['path'], Path(e['local_path'])) for e in batch],
               f'Upload Aurora research files {index}/{len(batches)}')
        state['completed_batches'].append({'files':len(batch),'bytes':sum(e['bytes'] for e in batch),'commit':state['head']})
        save(state_path, state)
        print(json.dumps({'completed_batch':index,'of':len(batches),
              'uploaded_files_this_pass':sum(len(b) for b in batches[:index]),'commit':state['head']}),flush=True)

    info = api.repo_info(repo, repo_type='dataset')
    if info.private is not True:
        raise ValueError('Unexpected destination visibility')
    remote = remote_index(info.sha)
    lfs_count = 0
    git_count = 0
    for entry in plan['files']:
        file = remote.get(entry['path'])
        if not matches(file, entry):
            raise ValueError('Remote payload verification failed: ' + entry['path'])
        if lfs_sha(file):
            lfs_count += 1
        else:
            git_count += 1
    samples = ['workspace/data/prepared/minimal-country-20261005-v2/train.jsonl',
               'workspace/data/prepared/minimal-country-20261005-v2/cases.jsonl',
               'workspace/runs/aurora-minimal-country-extension-fit-20261005-v1/transcript.jsonl',
               'workspace/research/scenario-role-sft-20261017-v1/pack/train.jsonl',
               'workspace/docs/onboarding/SFT_TRIALS.md']
    for name in samples:
        downloaded = Path(hf_hub_download(repo,name,repo_type='dataset',revision=info.sha,token=token))
        if sha(downloaded.read_bytes()) != by_path[name]['sha256']:
            raise ValueError('Downloaded sample hash differs: ' + name)
    verification = {'status':'complete_remote_payload_verified','verified_at':now(),
        'repo_id':repo,'repo_type':'dataset','private':True,'payload_commit':info.sha,
        'source_git_commit':plan['source_git_commit'],'snapshot_manifest_sha256':plan['snapshot_manifest_sha256'],
        'payload_files':plan['file_count'],'payload_bytes':plan['bytes'],
        'lfs_sha256_verified':lfs_count,'git_blob_sha1_and_size_verified':git_count,
        'downloaded_samples_sha256_verified':len(samples),'manifest_sha256':sha((OUT/'FILE_MANIFEST.json').read_bytes()),
        'new_model_calls':0,'new_optimizer_updates':0,'research_goal_status':'paused'}
    save(OUT/'STATUS.json', verification)
    commit([('README.md',OUT/'README.md'),('STATUS.json',OUT/'STATUS.json')],
           'Mark private Aurora export complete after full remote verification')
    api.create_tag(repo,tag=TAG,repo_type='dataset',revision=state['head'],exist_ok=True)
    tagged = api.repo_info(repo,repo_type='dataset',revision=TAG)
    if tagged.sha != state['head'] or tagged.private is not True:
        raise ValueError('Published tag or visibility differs')
    verification.update({'commit':state['head'],'tag':TAG,
        'url':f'https://huggingface.co/datasets/{repo}',
        'files_url':f'https://huggingface.co/datasets/{repo}/tree/{TAG}/workspace',
        'download_verifier_sha256':sha((OUT/'VERIFY_DOWNLOAD.py').read_bytes())})
    save(OUT/'publication-receipt.json', verification)
    state['status']='complete_verified'
    save(state_path,state)
    print(json.dumps(verification,indent=2),flush=True)


if __name__ == '__main__':
    main()
