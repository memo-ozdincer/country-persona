"""Add Reddit country-context collection to existing HF repositories and explorer.

Full prepared text remains private. Public assets contain coverage and provenance only.
Existing repository visibility and unrelated files are preserved.
"""
import argparse
import hashlib
import json
from pathlib import Path
from huggingface_hub import HfApi,CommitOperationAdd,hf_hub_download
from huggingface_hub.utils import disable_progress_bars

ROOT=Path(__file__).resolve().parents[1];PREFIX='reddit-country-20260923';OWNER='memo-ozdincer'
PUBLIC=ROOT/'.cache/reddit-publication/public';PREPARED=ROOT/'data/prepared'/PREFIX


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()


def index_links(text):
    nav=f'<a href="{PREFIX}/index.html">Reddit datasets ↗</a>'
    script='<script src="reddit-coverage.js" defer></script>'
    if nav not in text:
        if '</nav>' not in text:raise ValueError('Missing navigation anchor')
        text=text.replace('</nav>',nav+'</nav>',1)
    if script not in text:
        if '</head>' not in text:raise ValueError('Missing head')
        text=text.replace('</head>',script+'\n</head>',1)
    return text


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--publish',action='store_true')
    args=parser.parse_args();api=HfApi()
    if api.whoami()['name']!=OWNER:raise ValueError('Unexpected account')
    validation=json.loads((ROOT/'reports/reddit-country-validation.json').read_text())
    report=json.loads((PREPARED/'coverage.json').read_text())
    if validation['status']!='passed' or validation['records_checked']!=report['unique_prepared_records']:raise ValueError('Missing successful validation')
    for rel,receipt in report['artifacts'].items():
        if sha(PREPARED/rel)!=receipt['sha256']:raise ValueError('Artifact changed since validation')
    jobs=[('dataset',OWNER+'/country-persona-research-files',True),('dataset',OWNER+'/country-persona-data',False),
          ('space',OWNER+'/country-persona-research',True),('space',OWNER+'/country-persona-explorer',False)]
    results={'release':PREFIX,'repositories':[]}
    for kind,repo,private in jobs:
        info=api.repo_info(repo,repo_type=kind)
        if info.private!=private:raise ValueError('Unexpected repository visibility')
        files={f'{PREFIX}/{p.name}':p for p in PUBLIC.iterdir() if p.is_file()}
        if kind=='dataset' and private:
            files.update({f'{PREFIX}/{rel}':PREPARED/rel for rel in report['artifacts']})
            files[f'{PREFIX}/coverage.json']=PREPARED/'coverage.json'
            files[f'{PREFIX}/ACQUISITION.json']=ROOT/'data/manifests/reddit-country-20260923.json'
            files[f'{PREFIX}/METHODS.md']=ROOT/'docs/REDDIT_COUNTRY_DATA.md'
            files[f'{PREFIX}/validation.json']=ROOT/'reports/reddit-country-validation.json'
            files[f'{PREFIX}/community-mapping.json']=ROOT/'data/curation/reddit_country_communities.json'
            for name in ['collect_reddit_country.py','prepare_reddit_country.py','validate_reddit_country.py']:
                files[f'{PREFIX}/scripts/{name}']=ROOT/'scripts'/name
        if kind=='space':
            remote=Path(hf_hub_download(repo,'index.html',repo_type=kind,revision=info.sha))
            staged=ROOT/'.cache/reddit-publication'/f'{repo.split("/")[-1]}-index.html'
            staged.write_text(index_links(remote.read_text()));files['index.html']=staged
            files['reddit-coverage.js']=ROOT/'explorer/reddit-coverage.js'
        if not args.publish:
            print(repo,len(files),'files');continue
        result=api.create_commit(repo,repo_type=kind,parent_commit=info.sha,
            operations=[CommitOperationAdd(path_in_repo=n,path_or_fileobj=str(p)) for n,p in files.items()],
            commit_message='Add six-country Reddit archives, observed reply pairs and coverage explorer')
        info=api.repo_info(repo,repo_type=kind,revision=result.oid,files_metadata=True)
        remote={f.rfilename:f for f in info.siblings};checked={}
        for name,path in files.items():
            f=remote[name];expected=sha(path)
            if f.size!=path.stat().st_size:raise ValueError('Remote size differs: '+name)
            # Large LFS objects expose SHA256 without re-downloading the entire corpus.
            lfs_hash=(f.lfs or {}).get('sha256') if isinstance(f.lfs,dict) else getattr(f.lfs,'sha256',None)
            if lfs_hash:
                if lfs_hash!=expected:raise ValueError('Remote SHA256 differs: '+name)
                method='lfs_sha256'
            else:
                downloaded=Path(hf_hub_download(repo,name,repo_type=kind,revision=result.oid))
                if sha(downloaded)!=expected:raise ValueError('Remote bytes differ: '+name)
                method='download_sha256'
            checked[name]={'sha256':expected,'verification':method,'bytes':path.stat().st_size}
        results['repositories'].append({'repo':repo,'repo_type':kind,'private':private,'commit':result.oid,'files':checked})
        (ROOT/'reports/reddit-country-publication.json').write_text(json.dumps(results,indent=2)+'\n')
        print(json.dumps({'repo':repo,'commit':result.oid,'verified_files':len(checked)}),flush=True)
    if args.publish:
        for path in [ROOT/'explorer/index.html',ROOT/'.cache/explorer-public-static/index.html',ROOT/'.cache/explorer-private-static/index.html']:
            if path.exists():path.write_text(index_links(path.read_text()))
        for mode in ['public','private']:
            folder=ROOT/f'.cache/explorer-{mode}-static'
            if folder.exists():(folder/'reddit-coverage.js').write_bytes((ROOT/'explorer/reddit-coverage.js').read_bytes())


if __name__=='__main__':
    disable_progress_bars();main()
