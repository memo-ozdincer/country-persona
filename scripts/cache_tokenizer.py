"""Fetch only a pinned model's tokenizer/config, never its GPU weights."""
import json
import urllib.request
from pathlib import Path
import truststore
from country_persona.io import sha256, write_json
truststore.inject_into_ssl()
model='Qwen/Qwen2.5-7B-Instruct'
lock_path=Path('configs/posttraining/model.lock.json')
def get(url):
    with urllib.request.urlopen(url,timeout=60) as response:return response.read()
revision=json.loads(lock_path.read_text())['revision'] if lock_path.exists() else json.loads(get('https://huggingface.co/api/models/'+model))['sha']
root=Path('data/metadata/qwen25-7b-tokenizer');root.mkdir(parents=True,exist_ok=True)
files=[]
for name in ('tokenizer.json','tokenizer_config.json','vocab.json','merges.txt','config.json','generation_config.json'):
    url=f'https://huggingface.co/{model}/resolve/{revision}/{name}'
    path=root/name
    if not path.exists():path.write_bytes(get(url))
    files.append({'path':str(path),'sha256':sha256(path),'url':url})
lock={'model':model,'revision':revision,'tokenizer_path':str(root),'files':files,'weights_downloaded':False}
if lock_path.exists() and json.loads(lock_path.read_text())!=lock:raise ValueError('Existing tokenizer lock does not match bytes')
write_json(lock_path,lock)
print(model,revision)
