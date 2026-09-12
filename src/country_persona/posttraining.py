"""Model-specific, immutable research exports; no synthetic targets or truncation."""
from collections import Counter, defaultdict
import argparse
import json
from pathlib import Path
from .io import digest, read_jsonl, sha256, write_json, write_jsonl


def event_order(items, seed=42):
    groups=defaultdict(list)
    for row,meta in items:groups[meta['split_group']].append((row,meta))
    for group in groups:groups[group].sort(key=lambda x:digest([seed,x[1]['id']]))
    keys=sorted(groups,key=lambda g:digest([seed,g]))
    result=[]
    for position in range(max(map(len,groups.values()),default=0)):
        for key in keys:
            if position<len(groups[key]):result.append(groups[key][position])
    return result


def tokenize_example(tokenizer,row):
    full=tokenizer.apply_chat_template(row['prompt']+row['completion'],tokenize=True,add_generation_prompt=False,**row.get('chat_template_kwargs',{}))
    prompt=tokenizer.apply_chat_template(row['prompt'],tokenize=True,add_generation_prompt=True,**row.get('chat_template_kwargs',{}))
    if full[:len(prompt)]!=prompt or len(full)<=len(prompt):raise ValueError('Chat template does not support the required completion boundary')
    return len(full),len(full)-len(prompt)


def export(path,items):
    rows=[];meta=[]
    for row,m in items:
        rows.append(row);meta.append({**m,'row_index':len(rows)-1,'example_sha256':digest(row),
            'status':'research_prepared','machine_checks_passed':True,
            'human_reviewed':False,'preparation_policy':'full-history-authentic-qa-v1'})
    if not rows:raise ValueError('Empty export')
    write_jsonl(path,rows);manifest=path.with_suffix('.manifest.jsonl');write_jsonl(manifest,meta)
    return {'examples':len(rows),'event_groups':len({m['split_group'] for m in meta}),
        'countries':dict(Counter(m['country_iso3'] for m in meta)),
        'sequence_tokens':sum(m['sequence_tokens'] for m in meta),
        'supervised_tokens':sum(m['supervised_tokens'] for m in meta),
        'max_sequence_tokens':max(m['sequence_tokens'] for m in meta),
        'data_sha256':sha256(path),'manifest_sha256':sha256(manifest)}


def build_release(source,output,lock_path,max_length=8192):
    from transformers import AutoTokenizer
    out=Path(output)
    if out.exists() and any(out.iterdir()):raise ValueError('Choose an empty release directory')
    lock=json.loads(Path(lock_path).read_text())
    for item in lock['files']:
        if sha256(item['path'])!=item['sha256']:raise ValueError('Tokenizer lock mismatch')
    tokenizer=AutoTokenizer.from_pretrained(lock['tokenizer_path'],local_files_only=True)
    buckets=defaultdict(list);rejected=[];inputs={}
    for path in sorted(Path(source).glob('*/authentic_qa/*.sft.jsonl')):
        mp=path.with_name(path.name.replace('.sft.jsonl','.manifest.jsonl'))
        inputs[str(path)]=sha256(path);inputs[str(mp)]=sha256(mp)
        rows=list(read_jsonl(path));metas=list(read_jsonl(mp))
        if len(rows)!=len(metas):raise ValueError('Misaligned candidate input')
        for i,(row,m) in enumerate(zip(rows,metas)):
            if m['row_index']!=i or m['example_sha256']!=digest(row):raise ValueError('Candidate hash mismatch')
            if m['source_id'] not in ('mfa','germany_press'):raise ValueError('Unexpected QA source')
            if set(m['quality_flags'])-{'event_publication_dates_differ'}:
                rejected.append({'id':m['id'],'reason':'quality_flags','flags':m['quality_flags']});continue
            row={**row,'chat_template_kwargs':lock['chat_template_kwargs']}
            n,target=tokenize_example(tokenizer,row)
            if n>max_length:
                rejected.append({'id':m['id'],'reason':'over_token_budget','sequence_tokens':n});continue
            buckets[(m['country_iso3'],m['split'])].append((row,{**m,'sequence_tokens':n,'supervised_tokens':target,
                'model_revision':lock['revision'],'tokenizer_lock_sha256':sha256(lock_path)}))
    if not buckets:raise ValueError('No QA candidates found')
    for key in buckets:buckets[key]=event_order(buckets[key])
    groups={split:{m['split_group'] for (country,s),items in buckets.items() if s==split for _,m in items} for split in ('train','dev','test')}
    if any(groups[a]&groups[b] for a,b in (('train','dev'),('train','test'),('dev','test'))):raise ValueError('Event leakage')
    counts={country:len(buckets[country,'train']) for country in ('CHN','DEU')};n=min(counts.values())
    if n<250:raise ValueError('Fewer than 250 eligible examples per country; revise pilot explicitly')
    outputs={}
    def save(name,items):outputs[name]=export(out/(name+'.jsonl'),items)
    save('shared-250.train',sum((buckets[c,'train'][:250] for c in ('CHN','DEU')),[]))
    save('shared-balanced.train',sum((buckets[c,'train'][:n] for c in ('CHN','DEU')),[]))
    save('shared-all.train',sum((buckets[c,'train'] for c in ('CHN','DEU')),[]))
    for country in ('CHN','DEU'):save(country+'.train',buckets[country,'train'][:n])
    for split,limit in (('dev',100),('test',100)):
        for country in ('CHN','DEU'):save(country+'.'+split,buckets[country,split][:limit])
        save('shared.'+split,sum((buckets[c,split][:limit] for c in ('CHN','DEU')),[]))
    write_jsonl(out/'excluded.jsonl',rejected)
    report={'model':lock['model'],'revision':lock['revision'],'max_length':max_length,
        'chat_template_kwargs':lock['chat_template_kwargs'],
        'selection':'Full previous history and literal final answer; over-length rows excluded, no truncation. Event-round-robin selection, seed 42.',
        'input_hashes':inputs,'eligible':{c+'/'+s:len(v) for (c,s),v in buckets.items()},
        'rejected':dict(Counter(x['reason'] for x in rejected)),
        'outputs':outputs,'status':'machine_prepared_research_release; no human or source-rights clearance asserted'}
    write_json(out/'release.json',report);write_json('reports/posttraining_release.json',report)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',default='data/prepared/long-context/candidates');p.add_argument('--output',default='data/prepared/posttraining-qwen3-v1');p.add_argument('--lock',default='configs/posttraining/model.lock.json');p.add_argument('--max-length',type=int,default=8192)
    a=p.parse_args();r=build_release(a.source,a.output,a.lock,a.max_length);print(json.dumps({k:v for k,v in r.items() if k!='input_hashes'},indent=2))
