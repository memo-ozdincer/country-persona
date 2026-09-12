"""Paired, event-group bootstrap of actual human review; does not call an LLM judge."""
import argparse
import csv
from collections import defaultdict
import random
from pathlib import Path
from country_persona.io import read_jsonl,write_json

def summarize(cases,reviews,before,after):
    by_id={c['id']:c for c in cases};ratings={}
    for r in reviews:
        if r['case_id'] not in by_id:raise ValueError('Unknown review case')
        if r['run'] not in (before,after):continue
        key=(r['case_id'],r['run'])
        if key in ratings:raise ValueError('One adjudicated rating per case/run required')
        if not r['reviewer']:raise ValueError('Missing reviewer identity')
        fidelity=int(r['position_fidelity_0_to_2']);unsupported=int(r['unsupported_commitment']);attribution=int(r['attribution_error'])
        supported=int(r['supported_claims']);total=int(r['total_checkable_claims'])
        if fidelity not in (0,1,2) or unsupported not in (0,1) or attribution not in (0,1) or not 0<=supported<=total:raise ValueError('Invalid rating')
        ratings[key]={'fidelity':fidelity/2,'unsupported_commitment':unsupported,'attribution_error':attribution,'claim_precision':supported/total if total else None}
    buckets=defaultdict(lambda:defaultdict(list));paired=0
    for case in cases:
        key=case['id']
        if (key,before) not in ratings or (key,after) not in ratings:continue
        paired+=1
        bucket=(case['country'],case['suite'],case['condition'])
        buckets[bucket][case['split_group']].append((ratings[key,before],ratings[key,after]))
    results=[]
    for bucket,groups in sorted(buckets.items()):
        for metric in ('fidelity','unsupported_commitment','attribution_error','claim_precision'):
            pairs=[]
            for rows in groups.values():
                values=[(a[metric],b[metric]) for a,b in rows if a[metric] is not None and b[metric] is not None]
                if values:pairs.append((sum(a for a,b in values)/len(values),sum(b for a,b in values)/len(values)))
            if not pairs:continue
            delta=[b-a for a,b in pairs];rng=random.Random(42)
            boot=sorted(sum(rng.choices(delta,k=len(delta)))/len(delta) for _ in range(2000))
            results.append({'country':bucket[0],'suite':bucket[1],'condition':bucket[2],'metric':metric,
                'event_groups':len(pairs),'before':sum(a for a,b in pairs)/len(pairs),'after':sum(b for a,b in pairs)/len(pairs),
                'paired_change':sum(delta)/len(delta),'group_bootstrap_95pct':[boot[50],boot[1949]],
                'interpretation':'descriptive only: fewer than 20 groups' if len(pairs)<20 else 'exploratory interval; inspect assumptions and multiple comparisons'})
    if not paired:raise ValueError('No paired completed reviews')
    return {'paired_cases':paired,'unpaired_cases':len(cases)-paired,'results':results,
        'method':'Equal event weights; paired bootstrap with 2000 draws, seed 42. Positive fidelity/precision and negative error-rate change are improvements. Missing reviews are not treated as success.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cases',required=True);p.add_argument('--reviews',required=True);p.add_argument('--before',required=True);p.add_argument('--after',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    with Path(a.reviews).open() as f:reviews=list(csv.DictReader(f))
    write_json(a.output,summarize(list(read_jsonl(a.cases)),reviews,a.before,a.after))
