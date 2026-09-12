"""Verify a pre-existing public model snapshot against the locked HF revision, without downloading weights."""
import argparse
import hashlib
import json
from pathlib import Path
from huggingface_hub import HfApi
from country_persona.io import sha256,write_json
p=argparse.ArgumentParser();p.add_argument('--model-path',required=True);p.add_argument('--output',required=True);a=p.parse_args()
lock=json.loads(Path('configs/posttraining/model.lock.json').read_text());root=Path(a.model_path)
info=HfApi(token=False).model_info(lock['model'],revision=lock['revision'],files_metadata=True)
needed={'config.json','generation_config.json','tokenizer.json','tokenizer_config.json','vocab.json','merges.txt','model.safetensors.index.json'}
index=json.loads((root/'model.safetensors.index.json').read_text());needed.update(index['weight_map'].values())
remote={f.rfilename:f for f in info.siblings};results=[]
for name in sorted(needed):
    path=root/name;meta=remote[name]
    if meta.lfs:
        observed=sha256(path);expected=meta.lfs.sha256;algorithm='sha256'
    else:
        raw=path.read_bytes();observed=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest();expected=meta.blob_id;algorithm='git-blob-sha1'
    if observed!=expected:raise ValueError(f'Existing model differs from pinned revision: {name}')
    results.append({'file':name,'algorithm':algorithm,'digest':observed,'bytes':path.stat().st_size})
write_json(a.output,{'status':'verified','model':lock['model'],'revision':lock['revision'],'path':str(root),'files':results})
print('Verified existing model:',len(results),'files;',sum(x['bytes'] for x in results),'bytes')
