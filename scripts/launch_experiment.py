"""Print one experiment command; --run explicitly launches it on the current node."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
p=argparse.ArgumentParser();p.add_argument('recipe',choices=['smoke','pilot','pilot-3epochs','balanced','CHN','DEU','all-data-ablation']);p.add_argument('--run',action='store_true');p.add_argument('--seed',type=int,default=42);p.add_argument('--output');a=p.parse_args()
lock=json.loads(Path('configs/posttraining/model.lock.json').read_text());plan=json.loads(Path('configs/posttraining/recipes.json').read_text());r=plan['recipes'][a.recipe]
root=Path('data/prepared/posttraining-qwen3-v1');data=root/(r['dataset']+'.jsonl');manifest=data.with_suffix('.manifest.jsonl')
out=a.output or f'runs/{a.recipe}-s{a.seed}'
if Path(out).exists() and any(Path(out).iterdir()):raise ValueError('Use a fresh output directory')
cmd=[sys.executable,'-m','torch.distributed.run','--standalone','--nproc_per_node=4','--module','country_persona.train',
     '--model',os.environ.get('PERSONA_MODEL_PATH',lock['model']),'--revision',lock['revision'],'--research-prepared','--data',str(data),'--manifest',str(manifest),
     '--output',out,'--max-length','8192','--rank','16','--grad-accum','8','--lr','0.0001','--epochs',str(r['epochs']),'--seed',str(a.seed)]
if r.get('max_steps'):cmd+=['--max-steps',str(r['max_steps'])]
if r.get('dev'):
    dev=root/(r['dev']+'.jsonl');cmd+=['--dev-data',str(dev),'--dev-manifest',str(dev.with_suffix('.manifest.jsonl'))]
print(shlex.join(cmd),flush=True)
if a.run:subprocess.run(cmd,check=True)
