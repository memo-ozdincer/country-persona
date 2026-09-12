"""Emit a readable paired answer sheet; never fabricate scores or model outputs."""
import argparse
from pathlib import Path
from country_persona.io import read_jsonl
from country_persona.evaluate import check_case
p=argparse.ArgumentParser();p.add_argument('--cases',required=True);p.add_argument('--before',required=True);p.add_argument('--after',required=True);p.add_argument('--output',required=True);a=p.parse_args()
cases=list(read_jsonl(a.cases))
def load(root):
    rows={}
    for path in sorted(Path(root).glob('predictions.rank*.jsonl')):
        for r in read_jsonl(path):
            if r['id'] in rows:raise ValueError('Duplicate prediction')
            rows[r['id']]=r
    return rows
before=load(a.before);after=load(a.after)
if set(before)!=set(after) or set(before)!={c['id'] for c in cases}:raise ValueError('Missing/extra cases; comparison requires complete matched runs')
lines=['# Paired persona inspection','',f'Before: {a.before}. After: {a.after}.','', 'Outputs below are generated model responses, not verified policy statements.','']
for c in cases:
    check_case(c)
    if any(run[c['id']]['case_sha256']!=c['case_sha256'] for run in (before,after)):raise ValueError('Changed evaluation prompt')
    lines += [f'## {c["id"]}','',f'Country: {c["country"]}; condition: {c["condition"]}.', '',c['prompt'][-1]['content'],'','### Before','',before[c['id']]['output'],'','### After','',after[c['id']]['output'],'','### Review evidence','',f'Source: {c["source_url"]}','',str(c.get('expected_claims',[])),'', 'Check supported claims, position fidelity, attribution and invented commitments. Record ratings in review.csv.','']
Path(a.output).write_text('\n'.join(lines))
