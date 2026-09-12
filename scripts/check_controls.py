"""Exact checks for the small neutral arithmetic/format control set."""
import argparse
from pathlib import Path
from country_persona.io import read_jsonl,write_json
p=argparse.ArgumentParser();p.add_argument('--cases',required=True);p.add_argument('--run',required=True);p.add_argument('--output',required=True);a=p.parse_args()
expected={c['id']:c for c in read_jsonl(a.cases) if c['suite']=='general_control'}
results={}
for path in Path(a.run).glob('predictions.rank*.jsonl'):
    for r in read_jsonl(path):
        if r['id'] in expected:
            if r['id'] in results:raise ValueError('Duplicate control prediction')
            if r['case_sha256']!=expected[r['id']]['case_sha256']:raise ValueError('Changed control case')
            results[r['id']]={'correct':r['output'].strip()==expected[r['id']]['expected_exact'],'output':r['output']}
if not expected or set(results)!=set(expected):raise ValueError('Missing control cases')
write_json(a.output,{'correct':sum(r['correct'] for r in results.values()),'total':len(results),'results':results,'scope':'arithmetic/format sanity only'})
