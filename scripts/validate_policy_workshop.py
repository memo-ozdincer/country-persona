"""Independently check a workshop release, its source receipts and export alignment."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def check(ok,message):
    if not ok:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def validate(output,root=ROOT):
    report=json.loads((output/'build-report.json').read_text())
    for name,expected in report['artifacts'].items():
        check(sha(output/name)==expected,'Artifact changed: '+name)
    for name,expected in report['inputs'].items():
        check(sha(root/name)==expected,'Build input changed: '+name)
    evidence={e['evidence_id']:e for e in rows(output/'evidence.jsonl')}
    for eid,e in evidence.items():
        check(e['country_iso3'] in {'FRA','GBR','IND','BRA'},'Excluded country')
        check(sha(root/e['raw_file'])==e['raw_sha256'],'Raw hash mismatch')
        check(sha(root/e['text_file'])==e['text_sha256'],'Text hash mismatch')
        full=(root/e['text_file']).read_text()
        check(0<=e['char_start']<e['char_end']<=len(full),'Invalid offsets')
        check(full[e['char_start']:e['char_end']]==e['excerpt'],'Span differs from evidence')
        check(digest(e['excerpt'])==e['excerpt_sha256'],'Excerpt hash mismatch')
    components={}
    source_components={}
    exported={}
    audit_verdicts={}
    for name,count in report['formats'].items():
        bucket=rows(output/(name+'.jsonl'))
        manifest=rows(output/(name+'.manifest.jsonl'))
        check(len(bucket)==len(manifest)==count,'Export count mismatch')
        for index,(row,m) in enumerate(zip(bucket,manifest)):
            check(m['row_index']==index and m['example_sha256']==digest(row),'Manifest row alignment failure')
            check(m['id'] not in exported,'Duplicate example ID')
            check(m['split']=='quarantine' and m['training_admitted'] is False,'Unexpected training admission')
            check(m['fresh_evaluation_eligible'] is False,'Unexpected evaluation eligibility')
            check(row['chat_template_kwargs']=={'enable_thinking':False},'Unexpected template policy')
            check([p['role'] for p in row['prompt']]==['system','user'],'Invalid prompt roles')
            check(set(m['evidence_ids']) <= set(evidence),'Unknown evidence')
            for eid in m['evidence_ids']:
                check(components.setdefault(eid,m['split_group'])==m['split_group'],'Cross-format leakage component mismatch')
                group=evidence[eid]['source_split_group']
                check(source_components.setdefault(group,m['split_group'])==m['split_group'],'Shared document crosses components')
                check(evidence[eid]['excerpt'] in row['prompt'][1]['content'],'Source missing from prompt')
            targets=('chosen','rejected') if name.endswith('dpo') else ('completion',)
            for key in targets:
                check(len(row[key])==1 and row[key][0]['role']=='assistant','Invalid completion')
                refs=set(re.findall(r'\[([A-Z]{3}-[a-z][a-z0-9-]*)\]',row[key][0]['content']))
                check(refs<=set(m['evidence_ids']),'Unknown answer citation')
                if name in {'revision.sft','preference.dpo'}:
                    check(refs==set(m['evidence_ids']),'Missing answer citation')
            if name=='audit.sft':
                a=json.loads(row['completion'][0]['content'])
                check(set(a)=={'verdict','issues','corrected_draft','source_facts','evidence_ids','evidence_limit'},'Invalid audit schema')
                check(a['evidence_ids']==m['evidence_ids'],'Audit citation mismatch')
                check(a['verdict'] in {'supported','needs_revision'},'Invalid verdict')
                check(bool(a['issues'])==(a['verdict']=='needs_revision'),'Inconsistent audit')
                audit_verdicts[a['verdict']]=audit_verdicts.get(a['verdict'],0)+1
                for issue in a['issues']:
                    check(set(issue['evidence_ids'])<=set(m['evidence_ids']),'Issue citation mismatch')
            if name.endswith('dpo'):
                check(row['chosen']!=row['rejected'],'Identical preference pair')
                check('preference_basis' in m and m['error_type'],'Missing preference reason')
            exported[m['id']]=(row,m)
    episodes=rows(output/'episodes.jsonl')
    for ep in episodes:
        seen=set()
        for turn in ep['turns']:
            check(set(turn['depends_on'])<=seen,'Forward dependency in workflow')
            row,m=exported[turn['id']]
            check(m['episode_id']==ep['id'] and m['agent_id']==turn['agent_id'],'Agent attribution mismatch')
            check(m['split_group']==ep['split_group'],'Team leakage mismatch')
            check(m['evidence_ids']==turn['visible_evidence_ids'],'Agent visibility mismatch')
            target=row['completion'][0]['content']
            check((json.loads(target) if isinstance(turn['output'],dict) else target)==turn['output'],'Episode/export disagreement')
            if turn['role']=='analyst':
                check(len(turn['visible_evidence_ids'])==1 and not turn['depends_on'],'Analyst sees extra context')
                for other in set(ep['evidence_ids'])-set(turn['visible_evidence_ids']):
                    check(evidence[other]['excerpt'] not in row['prompt'][1]['content'],'Analyst sees another source')
            if turn['role']=='verifier':
                check(ep['turns'][-1]['output'] not in row['prompt'][1]['content'],'Future editor output leaked')
            seen.add(turn['id'])
    check(audit_verdicts.get('supported')==audit_verdicts.get('needs_revision')==len(evidence),'Unbalanced audit controls')
    check(len(set(components.values()))==report['leakage_components'],'Component count mismatch')
    return {'status':'passed','export_rows_checked':len(exported),'source_spans_checked':len(evidence),
            'workflow_episodes_checked':len(episodes),'audit_verdicts':audit_verdicts,
            'leakage_components':len(set(components.values())),
            'scope':'Structural, provenance and visibility checks; not independent semantic adjudication or model evaluation.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    print(json.dumps(validate(args.output),indent=2))
