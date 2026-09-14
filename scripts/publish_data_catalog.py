"""Publish staged artifacts using the owner's existing Hugging Face credential.

Never accepts a token argument, writes tokens, or changes existing repository visibility.
"""
import json
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from huggingface_hub import HfApi
from huggingface_hub.utils import disable_progress_bars

def main():
    disable_progress_bars();api=HfApi();owner=api.whoami()['name']
    if owner!='memo-ozdincer':raise ValueError('Authenticated account is not the requested owner')
    jobs=[('dataset','country-persona-data',False,Path('.cache/data-publication')),
          ('space','country-persona-explorer',False,Path('.cache/explorer-public-static')),
          ('space','country-persona-research',True,Path('.cache/explorer-private-static')),
          ('dataset','country-persona-research-files',True,Path('.cache/research-files-dataset'))]
    results=[]
    # Establish each exact destination and verify its visibility before sending any files.
    for typ,name,private,folder in jobs:
        assert folder.is_dir()
        rid=f'{owner}/{name}'
        api.create_repo(repo_id=rid,repo_type=typ,private=private,exist_ok=True,**({'space_sdk':'static'} if typ=='space' else {}))
        info=api.repo_info(rid,repo_type=typ)
        if info.private!=private:raise ValueError(f'Unexpected visibility for {rid}; not uploading')
    def upload(job):
        typ,name,private,folder=job;rid=f'{owner}/{name}'
        ignored=['catalog.sqlite','catalog.next.sqlite']+(['research.tar.gz'] if typ=='space' else [])
        result=api.upload_folder(repo_id=rid,repo_type=typ,folder_path=folder,
             ignore_patterns=ignored,
             commit_message='Publish country evidence catalog and decision comparisons')
        info=api.repo_info(rid,repo_type=typ,files_metadata=True)
        expected=[p for p in folder.rglob('*') if p.is_file() and p.name not in ignored]
        siblings={r.rfilename:r for r in info.siblings}
        for p in expected:
            rel=p.relative_to(folder).as_posix();assert rel in siblings,rel
            assert siblings[rel].size==p.stat().st_size,(rid,rel)
        return {'repo_id':rid,'repo_type':typ,'private':info.private,'author':info.author,'commit':result.oid,'files_verified_by_size':len(expected),'url':str(result.repo_url)}
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(upload,j) for j in jobs]):
            result=future.result();results.append(result);print(json.dumps(result),flush=True)
            Path('reports/data-publication.json').write_text(json.dumps({'owner':owner,'repositories':results,'four_h100_node_hours':0},indent=2)+'\n')
if __name__=='__main__':main()
