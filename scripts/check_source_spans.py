"""Check all authentic QA targets occur verbatim after whitespace normalization in source HTML."""
from collections import Counter
from pathlib import Path
from bs4 import BeautifulSoup
from country_persona.io import read_jsonl,write_json

def norm(s):return ' '.join(s.replace('\u200b','').split())
cache={};counts=Counter();failures=[]
for source in ('mfa','germany_press'):
    for r in read_jsonl(Path('data/canonical')/(source+'.jsonl')):
        if r['task']!='authentic_qa':continue
        path=r['raw_file']
        if path not in cache:cache[path]=norm(BeautifulSoup(Path(path).read_bytes(),'html.parser').get_text(' ',strip=True))
        if norm(r['text']) not in cache[path]:failures.append({'id':r['id'],'raw_file':path})
        counts[source]+=1
report={'targets_checked':dict(counts),'failures':failures,
        'meaning':'Literal target grounding only; not an expert assessment of interpretation, historical availability or all turn boundaries.'}
write_json('reports/source_span_audit.json',report)
print(report if failures else {'targets_checked':dict(counts),'failures':0})
if failures:raise SystemExit(1)
