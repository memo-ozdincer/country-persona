"""Acquire pinned public research files; never bypass dataset access gates."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.utils import disable_progress_bars

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/'data/reddit_source_registry.json'
RAW=ROOT/'data/raw/reddit-country-20260923'
MANIFEST=ROOT/'data/manifests/reddit-country-20260923.json'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    disable_progress_bars()
    registry=json.loads(REGISTRY.read_text());api=HfApi();jobs=[]
    for s in registry['sources']:
        info=api.dataset_info(s['repository'],revision=s['revision'])
        if info.gated or info.private:raise ValueError('Source is not ungated public data')
        for file in s['files']:jobs.append((s,file))
        if any(f.rfilename=='README.md' for f in info.siblings):
            hf_hub_download(s['repository'],'README.md',repo_type='dataset',revision=s['revision'],local_dir=RAW/s['id'])
    result={'release':registry['release'],'selection':registry['selection'],'files':[],'failures':[]}
    def get(job):
        s,f=job
        path=Path(hf_hub_download(s['repository'],f['path'],repo_type='dataset',revision=s['revision'],local_dir=RAW/s['id']))
        if path.stat().st_size!=f['bytes']:raise ValueError('File size mismatch')
        return {'source_id':s['id'],'repository':s['repository'],'revision':s['revision'],'source_path':f['path'],
                'raw_file':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':sha(path),
                'download_url':f"https://huggingface.co/datasets/{s['repository']}/resolve/{s['revision']}/{f['path']}",
                'retrieved_at':datetime.now(timezone.utc).isoformat()}
    with ThreadPoolExecutor(max_workers=2) as pool:
        fs={pool.submit(get,j):j for j in jobs}
        for future in as_completed(fs):
            s,f=fs[future]
            try:
                item=future.result();result['files'].append(item);print('acquired',s['id'],f['path'],item['bytes'],flush=True)
            except Exception as e:
                result['failures'].append({'source_id':s['id'],'source_path':f['path'],'error_type':type(e).__name__})
                print('failed',s['id'],f['path'],type(e).__name__,flush=True)
            result['files'].sort(key=lambda r:r['raw_file'])
            MANIFEST.write_text(json.dumps(result,indent=2)+'\n')
    if result['failures']:raise RuntimeError('Some files failed; inspect manifest')


if __name__=='__main__':main()
