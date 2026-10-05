"""Publish only the homepage UI to the existing public static Space.

Retain catalog chunks, policy workshop, Reddit assets, and the private Space.
Credentials come from the existing private environment profile.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import urllib.request
from pathlib import Path

from huggingface_hub import HfApi, CommitOperationAdd, hf_hub_download

ROOT = Path(__file__).resolve().parents[1]
REPO = 'memo-ozdincer/country-persona-explorer'
HOST = 'https://memo-ozdincer-country-persona-explorer.static.hf.space/'
FILES = ['index.html', 'data.html', 'homepage.css', 'homepage.js',
         'homepage-data.json', 'catalog-summary.json', 'training-samples.html']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--receipt', type=Path, default=ROOT/'reports/research-homepage-publication-20261005.json')
    args = parser.parse_args()
    token_path = os.environ.get('HF_TOKEN_PATH')
    token = Path(token_path).read_text().strip() if token_path else None
    api = HfApi(token=token)
    assert api.whoami()['name'] == 'memo-ozdincer'
    info = api.repo_info(REPO, repo_type='space')
    assert not info.private
    args.output.mkdir(parents=True, exist_ok=True)
    stage = args.output / 'site'
    stage.mkdir(exist_ok=False)
    files = FILES + [str(p.relative_to(ROOT/'explorer'))
                     for p in sorted((ROOT/'explorer/assets').rglob('*')) if p.is_file()]
    for name in files:
        target = stage / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'explorer' / name, target)
    # Keep the prior homepage and use the existing static catalog adapter.
    for name in ['index.html', 'advanced.html']:
        prior = Path(hf_hub_download(REPO, name, repo_type='space',
            revision=info.sha, token=token))
        shutil.copyfile(prior, args.output / ('prior-live-'+name))
        if name == 'advanced.html':
            html = prior.read_text()
            html = html.replace('href="index.html">Country overview', 'href="data.html">Country overview')
            if 'href="index.html">Research home</a>' not in html:
                html = html.replace('<nav>', '<nav><a href="index.html">Research home</a>', 1)
            (stage/name).write_text(html)
            files.append(name)
    # The existing explorer data and runtime are dependencies, not new data releases.
    dependencies = ['overview.json','sources.json','source_profiles.json','trace_types.json',
                    'decision-showcase.json','training-examples.json','overview.js',
                    'overview.css','overview-narrow.css','reddit-coverage.js']
    for name in dependencies:
        remote = Path(hf_hub_download(REPO, name, repo_type='space',revision=info.sha,token=token))
        assert remote.read_bytes() == (ROOT/'explorer'/name).read_bytes(), f'Reconcile existing live dependency before publishing: {name}'
    receipt = dict(repo=REPO, prior_revision=info.sha, files={name:
        hashlib.sha256((stage/name).read_bytes()).hexdigest() for name in files},
        existing_dependencies_match=True, new_model_calls=0, new_optimizer_steps=0)
    (args.output/'preparation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if not args.publish:
        print(json.dumps(dict(status='prepared', **receipt)))
        return
    commit = api.create_commit(REPO, repo_type='space', parent_commit=info.sha,
        operations=[CommitOperationAdd(path_in_repo=name,path_or_fileobj=str(stage/name)) for name in files],
        commit_message='Remove introductory project labels and preliminary-status line')
    receipt['revision'] = commit.oid
    receipt['url'] = HOST+'index.html'
    receipt['status'] = 'uploaded_live_verification_pending'
    args.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    verified = {}
    for name in files:
        request = urllib.request.Request(HOST+name+'?v='+commit.oid[:12],headers={'Cache-Control':'no-cache'})
        with urllib.request.urlopen(request,timeout=30) as response:
            body=response.read()
            if name.endswith('.html'):
                body=re.sub(rb'<script>window\.huggingface=\{variables:\{[^<]*?\}\};</script>',b'',body,count=1)
            assert body==(stage/name).read_bytes(), f'Live asset differs: {name}; verify before retrying upload'
            verified[name]=dict(status=response.status, sha256=receipt['files'][name])
    receipt.update(status='published_and_live_bytes_verified', live_assets=verified)
    args.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(status=receipt['status'],url=receipt['url'],revision=commit.oid,assets=len(files))))


if __name__=='__main__':
    main()
