"""Deterministic event splits, traceable candidate exports, and explicit admission ledger."""
from __future__ import annotations
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from .io import digest, read_jsonl, write_json, write_jsonl
from .schema import validate


class UnionFind:
    def __init__(self):self.parents={}
    def find(self,x):
        self.parents.setdefault(x,x)
        if self.parents[x]!=x:self.parents[x]=self.find(self.parents[x])
        return self.parents[x]
    def union(self,a,b):
        a,b=self.find(a),self.find(b)
        if a!=b:self.parents[max(a,b)]=min(a,b)


def normalized(text):return ' '.join(text.casefold().split())


def split_records(records,config,families=None):
    uf=UnionFind();owners={};seen=set()
    for r in records:
        validate(r)
        if r['id'] in seen:raise ValueError(f'Duplicate record ID: {r["id"]}')
        seen.add(r['id']);group=r['group_id'];uf.find(group)
        keys=['id:'+r['id']]
        if r.get('parent_id'):keys.append('id:'+r['parent_id'])
        keys+=['symbol:'+x for x in r.get('document_symbols',[])]
        # Same long target across mirrors, countries and derived records stays together.
        if len(r['text'])>=200:keys.append('text:'+digest(normalized(r['text'])))
        if families and r['id'] in families:keys.append('family:'+families[r['id']])
        for key in keys:
            if key in owners:uf.union(group,owners[key])
            else:owners[key]=group
    groups=defaultdict(list)
    for r in records:groups[uf.find(r['group_id'])].append(r)
    for gid,rows in groups.items():
        dates=[];quarantine=False;benchmark=False
        for r in rows:
            if r['date_precision']=='day':when=r['event_date']
            elif r['date_precision']=='year':when=r['event_date']+'-12-31'
            else:quarantine=True;continue
            if when>config['snapshot_date'] or (r['available_date'] and r['available_date']>config['snapshot_date']):quarantine=True
            if 'not_PRC_training' in r['quality_flags']:quarantine=True
            dates.append(when)
            benchmark |= 'benchmark_reserved' in r['quality_flags']
        if quarantine:split='quarantine'
        elif benchmark:split='test'
        elif max(dates)>config['dev_end']:split='test'
        elif max(dates)>config['train_end']:split='dev'
        else:split='train'
        if split!='quarantine':
            order={'train':0,'dev':1,'test':2}
            for r in rows:
                match=re.search(r'Cycle\s*(\d+)',r.get('upr_cycle') or '',re.I)
                if match:
                    requested=config.get('upr_cycle_splits',{}).get(match[1])
                    if requested and order[requested]>order[split]:split=requested
        for r in rows:r.update(split=split,split_group=gid)
    return records


def as_sft(r):
    system=(f"Research simulation of {r['represented_entity']}. Institution: {r['institution']}. "
            f"Capacity: {r['speaking_capacity']}. Date: {r['event_date']} ({r['date_precision']} precision). "
            f"Language: {r['language']}. Represent documented public positions. "
            'Do not invent commitments or private motivations. Distinguish evidence from inference.')
    question=r.get('question') or f"Reconstruct the documented statement for: {r['title']}"
    if r['task']=='upr_response':question='State the recorded response to the following recommendation:\n'+question
    if r['context']:question=r['context']+'\n\n'+question
    history=r.get('history',[])
    if history and all(m['role']=='user' for m in history):
        question='Earlier conference exchanges (speaker-labelled context):\n\n'+'\n\n'.join(m['content'] for m in history)+'\n\nCurrent question:\n'+question
        history=[]
    prompt=[{'role':'system','content':system}]+history+[{'role':'user','content':question}]
    return {'prompt':prompt,'completion':[{'role':'assistant','content':r['text']}]}


def build(config_path,canonical_dir,output_dir,families_path=None):
    config=json.loads(Path(config_path).read_text());out=Path(output_dir)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Output already exists; choose a new --output to preserve the snapshot and review decisions')
    records=[]
    for path in sorted(Path(canonical_dir).glob('*.jsonl')):
        # The pilot includes all rows concerning either focus country; source-wide originals stay canonical.
        for r in read_jsonl(path):
            involved=set(r.get('reviewed_states',[])+r.get('recommending_states',[]))
            if r['country_iso3'] in config['countries'] or involved.intersection({'China','Germany'}) or r['source_id']=='unbench':records.append(r)
    families={}
    if families_path:
        with Path(families_path).open() as f:
            for r in csv.DictReader(f):
                if r['id'] in families:raise ValueError('Duplicate family assignment')
                families[r['id']]=r['family_id']
    records=split_records(records,config,families)
    seen={};duplicates=[]
    for r in sorted(records,key=lambda r:r['id']):
        if r['task'] in ('press_conference','unverified_speech_segment','human_rights_evidence','domain_text','vote_prediction','upr_response') or len(r['text'])<200:continue
        # Do not de-duplicate ubiquitous short action labels across distinct proposals.
        fingerprint=digest([r['country_iso3'],r['task'],normalized(r.get('question','')),normalized(r['text'])])
        if fingerprint in seen:
            r['duplicate_of']=seen[fingerprint];duplicates.append({'id':r['id'],'duplicate_of':seen[fingerprint]})
        else:seen[fingerprint]=r['id']
    write_jsonl(out/'pilot.canonical.jsonl',records)
    write_jsonl(out/'split_manifest.jsonl',({'id':r['id'],'group_id':r['group_id'],'split_group':r['split_group'],
                  'split':r['split'],'source_id':r['source_id'],'event_date':r['event_date']} for r in records))
    write_jsonl(out/'duplicates.jsonl',duplicates)
    buckets=defaultdict(list);metadata=defaultdict(list);excluded=Counter()
    candidate_tasks={'authentic_qa','statement_reconstruction','vote_prediction','upr_recommendation','upr_response'}
    blocking_flags={'coalition_attribution_review','not_PRC_training','unparsed_exchange','multiple_recommending_states'}
    for r in records:
        if r['country_iso3'] not in config['countries']:excluded['outside_focus_country_role']+=1;continue
        if r['task'] not in candidate_tasks:excluded['evidence_or_domain_only']+=1;continue
        if r.get('duplicate_of'):excluded['duplicate']+=1;continue
        if r['split']=='quarantine':excluded['quarantine']+=1;continue
        if blocking_flags.intersection(r['quality_flags']):excluded['attribution_or_parse_flag']+=1;continue
        ex=as_sft(r)
        if sum(len(m['content']) for m in ex['prompt'])>config['max_prompt_characters'] or len(r['text'])>config['max_target_characters']:
            excluded['over_character_budget']+=1;continue
        # Task/source/country directories make skew visible and enable deliberate mixtures.
        key=f"{r['country_iso3']}/{r['task']}/{r['split']}"
        buckets[key].append(ex)
        metadata[key].append({'row_index':len(buckets[key])-1,'id':r['id'],'split':r['split'],
             'split_group':r['split_group'],'country_iso3':r['country_iso3'],'source_id':r['source_id'],
             'source_url':r['source_url'],'raw_sha256':r['raw_sha256'],'event_date':r['event_date'],
             'quality_flags':r['quality_flags'],'rights_status':r['rights_status'],
             'review_status':r['review_status'],'example_sha256':digest(ex),'status':'candidate_not_training_approved'})
    for key,rows in buckets.items():
        write_jsonl(out/'candidates'/f'{key}.sft.jsonl',rows)
        write_jsonl(out/'candidates'/f'{key}.manifest.jsonl',metadata[key])
    report={'pilot_records':len(records),'split_counts':dict(Counter(r['split'] for r in records)),
            'source_counts':dict(Counter(r['source_id'] for r in records)),
            'country_task_counts':dict(Counter(f"{r['country_iso3']}/{r['task']}" for r in records)),
            'candidates':{k:len(v) for k,v in sorted(buckets.items())},'excluded':dict(excluded),
            'duplicate_records':len(duplicates),'config':config,
            'limitations':['Candidate exports are not rights-cleared or expert-adjudicated.',
                           'Assigned families, document symbols and exact duplicates only; semantic leakage needs further review.',
                           'Retrieval validity and temporal forecasting are distinct from statement reconstruction.']}
    write_json(out/'build_report.json',report)
    if out==Path('data/prepared/pilot'):write_json('reports/build_report.json',report)
    review_dir=out/'review';review_dir.mkdir(parents=True,exist_ok=True)
    with (review_dir/'admission.csv').open('w',newline='',encoding='utf-8') as f:
        fields=['id','quality_approved','use_permission','reviewer','reason','source_url','quality_flags']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for items in metadata.values():
            for m in items:w.writerow({'id':m['id'],'quality_approved':'','use_permission':'',
                      'reviewer':'','reason':'','source_url':m['source_url'],'quality_flags':'|'.join(m['quality_flags'])})
    return report


def admit(candidate,manifest,ledger,output):
    rows=list(read_jsonl(candidate));metas=list(read_jsonl(manifest))
    if len(rows)!=len(metas):raise ValueError('Manifest alignment mismatch')
    approvals={}
    with Path(ledger).open() as f:
        for row in csv.DictReader(f):
            if row['id'] in approvals:raise ValueError('Duplicate admission ID')
            approvals[row['id']]=row
    output_rows=[];output_meta=[]
    for i,(row,m) in enumerate(zip(rows,metas)):
        if m['row_index']!=i or m['example_sha256']!=digest(row):raise ValueError('Candidate manifest integrity failure')
        a=approvals.get(m['id'],{})
        if (a.get('quality_approved')=='yes' and a.get('use_permission') in ('research','unrestricted')
            and a.get('reviewer') and a.get('reason')):
            output_rows.append(row)
            output_meta.append({**m,'row_index':len(output_rows)-1,'status':'admitted',
                                'quality_approved':True,'use_permission':a['use_permission'],
                                'reviewer':a['reviewer'],'reason':a['reason']})
    if not output_rows:raise ValueError('No admitted examples; ledger decisions are required')
    output=Path(output)
    write_jsonl(output,output_rows);write_jsonl(output.with_suffix('.manifest.jsonl'),output_meta)
    return {'admitted':len(output_rows),'candidate_count':len(rows)}
