"""Publish the existing verified Hub dataset at the user's explicit request.

Only root access metadata changes; research payload and previous tags stay exact.
Credentials are read privately from HF_TOKEN_PATH and never recorded.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

from huggingface_hub import CommitOperationAdd, HfApi

ROOT = Path('/mfs1/u/memo/country-persona-research')
PRIOR = ROOT / 'exports/hf-aurora-20261024-v1'
AUDIT = ROOT / 'audits/hf-public-access-20261024-v1'
REPO = 'memo-ozdincer/country-persona-aurora-data'
BASE = 'https://huggingface.co/datasets/' + REPO
TAG = 'aurora-20261024-v3'
PREVIOUS_COMMIT = '6db3089d7efde0bb2441e370a16c8b40c8a57853'
MANIFEST_SHA = '385e82820ea10ddebdeae7e1053918aad06185f0b7f2673531cc08ee5c25dbc5'


def save(name, value):
    with (AUDIT / name).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def download(url):
    # urllib supplies no Hugging Face authentication header or cookie.
    with urllib.request.urlopen(url, timeout=60) as response:
        assert response.status == 200
        return response.read()


assert not (AUDIT / 'public-access-receipt.json').exists()
api = HfApi(token=Path(os.environ['HF_TOKEN_PATH']).read_text().strip())
before = api.repo_info(REPO, repo_type='dataset')
assert before.sha == PREVIOUS_COMMIT and before.private is True
assert not before.gated
prior = json.loads((PRIOR / 'publication-receipt.json').read_text())
assert prior['commit'] == PREVIOUS_COMMIT
save('visibility-before.json', {'repo_id': REPO, 'private': before.private,
                              'commit': before.sha, 'user_requested_public': True})

card = (PRIOR / 'README.md').read_text()
card = card.replace('# Country Persona: private Aurora research data',
                    '# Country Persona: Aurora research data')
card = card.replace('This private dataset contains', 'This public dataset contains')
card = card.replace('Authenticate with your own authorized Hugging Face account (`hf auth login`), then use the Hub client:',
                    'No login or access request is required. Use the Hub client:')
card = card.replace('aurora-20261024-v2', TAG).replace('    token=True,', '    token=False,')
old_note = '- **This Hugging Face dataset is private. GitHub currently reports `memo-ozdincer/country-persona` as public, and an anonymous check could access an existing v47 release asset. Existing GitHub copies are not made private by this upload.** No GitHub visibility or collaborator permissions were changed by this task. Access to this dataset, Aurora and model weights remains separate.'
assert old_note in card
card = card.replace(old_note,
    '- **This dataset was made public on 24 October 2026 at the project owner\'s request. Anyone can browse or download it without signing in.** GitHub is also public; cluster access and base model weights remain separate. The older private research-files dataset was not changed.\n'
    '- Earlier tags, pinned workspace documentation and `FILE_MANIFEST.json` record the original private export. Its `required_private` field is historical; current visibility is recorded in `STATUS.json`. Original payload bytes, manifest and prior tags remain unchanged.')
assert 'This Hugging Face dataset is private' not in card
with (AUDIT / 'README.md').open('x') as stream:
    stream.write(card)
status = json.loads((PRIOR / 'STATUS.json').read_text())
status.update({'private': False, 'public_access_requested_by_user': True,
               'metadata_updated_at': datetime.now(timezone.utc).isoformat(),
               'metadata_revision_note': 'User-authorized public access; only root README/STATUS changed, research payload and original manifest unchanged.',
               'recommended_tag': TAG, 'previous_verified_tag': prior['tag'],
               'previous_verified_commit': PREVIOUS_COMMIT,
               'original_manifest_private_requirement_is_historical': True})
save('STATUS.json', status)
commit = api.create_commit(REPO, repo_type='dataset', parent_commit=PREVIOUS_COMMIT,
    operations=[CommitOperationAdd(path_in_repo=name, path_or_fileobj=str(AUDIT / name))
                for name in ['README.md', 'STATUS.json']],
    commit_message='Document public access requested by the project owner')
save('metadata-commit.json', {'commit': commit.oid, 'parent': PREVIOUS_COMMIT,
                            'changed_paths': ['README.md', 'STATUS.json'],
                            'payload_unchanged': True})
api.create_tag(REPO, repo_type='dataset', tag=TAG, revision=commit.oid)
api.update_repo_settings(REPO, repo_type='dataset', private=False)

info = json.loads(download('https://huggingface.co/api/datasets/' + REPO + '/revision/' + TAG))
assert info['private'] is False and info['sha'] == commit.oid
assert not info.get('gated')
page = download(BASE).decode()
assert 'Aurora research data' in page
raw_manifest = download(BASE + '/resolve/' + TAG + '/FILE_MANIFEST.json')
assert hashlib.sha256(raw_manifest).hexdigest() == MANIFEST_SHA
manifest = json.loads(raw_manifest)
prefix = 'workspace/data/prepared/minimal-country-20261005-v2/'
pack = [entry for entry in manifest['files'] if entry['path'].startswith(prefix)]
assert len(pack) == 7
destination = AUDIT / 'anonymous-download'
destination.mkdir()
(destination / 'FILE_MANIFEST.json').write_bytes(raw_manifest)
verifier = download(BASE + '/resolve/' + TAG + '/VERIFY_DOWNLOAD.py')
assert hashlib.sha256(verifier).hexdigest() == prior['download_verifier_sha256']
(destination / 'VERIFY_DOWNLOAD.py').write_bytes(verifier)
for entry in pack:
    raw = download(BASE + '/resolve/' + TAG + '/' + entry['path'])
    assert len(raw) == entry['bytes']
    assert hashlib.sha256(raw).hexdigest() == entry['sha256']
    path = destination / entry['path']
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
verification = subprocess.run([sys.executable, '-B', str(destination / 'VERIFY_DOWNLOAD.py'),
                               '--prefix', prefix], text=True, capture_output=True, check=True)
save('anonymous-download-verification.json', json.loads(verification.stdout))
receipt = dict(prior)
receipt.update({'status': 'public_dataset_and_anonymous_download_verified',
                'verified_at': datetime.now(timezone.utc).isoformat(),
                'private': False, 'commit': commit.oid, 'tag': TAG,
                'files_url': BASE + '/tree/' + TAG + '/workspace',
                'previous_verified_tag': prior['tag'],
                'previous_verified_hub_commit': PREVIOUS_COMMIT,
                'visibility_changed_at_user_request': True,
                'changed_hub_paths': ['README.md', 'STATUS.json'],
                'research_payload_and_manifest_unchanged': True,
                'anonymous_dataset_api_http_status': 200,
                'anonymous_dataset_page_http_status': 200,
                'anonymous_manifest_sha256_verified': True,
                'anonymous_training_pack_files_verified': len(pack),
                'anonymous_training_pack_bytes_verified': sum(e['bytes'] for e in pack),
                'gated': False,
                'prior_remote_payload_checks_retained': True})
receipt['github_visibility_observation']['huggingface_export_remains_private'] = False
receipt['github_visibility_observation']['huggingface_access_changed_by_later_explicit_request'] = True
save('public-access-receipt.json', receipt)
print(json.dumps(receipt, indent=2))
