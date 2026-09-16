"""Publish staged explorer assets; uses existing owner login, never stores credentials."""
import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from huggingface_hub import HfApi, CommitOperationAdd, get_token

ROOT=Path(__file__).resolve().parents[1]
FILES=['index.html','advanced.html','overview.js','overview.css','overview-narrow.css','overview.json','sources.json','source_profiles.json','trace_types.json','decision-showcase.json','README.md']

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish',action='store_true',help='Upload the staged UI to the existing public/private Spaces')
    args=parser.parse_args()
    if not args.publish:
        print('Staged assets:', ', '.join(FILES));print('Use --publish after staging and validation.');return
    api=HfApi();assert api.whoami()['name']=='memo-ozdincer'
    report={'version':'decision-posttraining-v1','files':FILES,'spaces':[]}
    for mode,name in [('public','country-persona-explorer'),('private','country-persona-research')]:
        repo='memo-ozdincer/'+name;folder=ROOT/'.cache'/f'explorer-{mode}-static'
        info=api.repo_info(repo,repo_type='space');assert info.private==(mode=='private')
        commit=api.create_commit(repo,repo_type='space',operations=[CommitOperationAdd(path_in_repo=n,path_or_fileobj=str(folder/n)) for n in FILES],commit_message='Show source-grounded decision post-training examples')
        item={'repo':repo,'private':info.private,'commit':commit.oid,'assets':{}}
        # HTML contains a small HF-injected configuration script; verify authored bytes after removing it.
        host='https://'+repo.replace('/','-')+'.static.hf.space/'
        for name in FILES:
            if name=='README.md':continue
            headers={'Cache-Control':'no-cache'}
            if info.private:headers['Authorization']='Bearer '+get_token()
            request=urllib.request.Request(host+name+'?v='+commit.oid[:8],headers=headers)
            with urllib.request.urlopen(request,timeout=30) as response:
                body=response.read();normalized=re.sub(rb'<script>window\.huggingface=\{variables:\{[^<]*?\}\};</script>',b'',body,count=1) if name.endswith('.html') else body
                expected=(folder/name).read_bytes();assert normalized==expected,(repo,name,'Deployment differs from staged asset; reverify before retrying upload')
                item['assets'][name]={'status':response.status,'sha256':hashlib.sha256(expected).hexdigest()}
        if info.private:
            try:
                urllib.request.urlopen(host+'sources.json',timeout=20)
                raise AssertionError('Private Space unexpectedly accessible anonymously')
            except urllib.error.HTTPError as error:
                assert error.code in (401,403,404);item['anonymous_status']=error.code
        report['spaces'].append(item)
        (ROOT/'reports/explorer-sources-publication.json').write_text(json.dumps(report,indent=2)+'\n')
        print(repo,commit.oid,'verified',flush=True)

if __name__=='__main__':main()
