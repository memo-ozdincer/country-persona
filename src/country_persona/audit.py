from __future__ import annotations
import json
from collections import Counter, defaultdict
from pathlib import Path
from .io import digest, read_jsonl, sha256, write_json
from .schema import validate


def audit(path,verify_raw=False):
    counts=Counter();countries=Counter();languages=Counter();tasks=Counter();flags=Counter()
    years=defaultdict(Counter);group_splits=defaultdict(set);text_splits=defaultdict(set)
    ids=set();errors=[];raw_checked={};size=Counter()
    for r in read_jsonl(path):
        try:validate(r)
        except ValueError as e:errors.append({'id':r.get('id'),'error':str(e)});continue
        if r['id'] in ids:errors.append({'id':r['id'],'error':'duplicate ID'})
        ids.add(r['id']);counts[r['source_id']]+=1;countries[r['country_iso3'] or 'unmapped']+=1
        languages[r['language']]+=1;tasks[r['task']]+=1;flags.update(r['quality_flags'])
        years[r['source_id']][r['event_date'][:4] or 'unknown']+=1
        size[r['source_id']]+=len(r['text'])
        split=r['split'];group=r.get('split_group',r['group_id'])
        if split not in ('unassigned','quarantine'):
            group_splits[group].add(split)
            if len(r['text'])>=200:text_splits[digest(' '.join(r['text'].casefold().split()))].add(split)
        if verify_raw:
            p=r['raw_file']
            if p not in raw_checked:
                raw_checked[p]=sha256(p) if Path(p).exists() else None
            if raw_checked[p]!=r['raw_sha256']:errors.append({'id':r['id'],'error':'raw file hash mismatch'})
            for key in ('draft_provenance','meeting_date_provenance'):
                join=r.get(key)
                if join:
                    p=join['raw_file']
                    if p not in raw_checked:raw_checked[p]=sha256(p) if Path(p).exists() else None
                    if raw_checked[p]!=join['raw_sha256']:errors.append({'id':r['id'],'error':'joined source hash mismatch','join':key})
        if r.get('source_char_span'):
            start,end=r['source_char_span']
            if not 0<=start<end:errors.append({'id':r['id'],'error':'invalid source span'})
    for g,s in group_splits.items():
        if len(s)>1:errors.append({'group':g,'error':'cross-split group'})
    for h,s in text_splits.items():
        if len(s)>1:errors.append({'text_hash':h,'error':'cross-split exact long text'})
    return {'records':len(ids),'by_source':dict(counts),'by_country':dict(countries),'by_language':dict(languages),
            'by_task':dict(tasks),'quality_flags':dict(flags),'years':{k:dict(sorted(v.items())) for k,v in years.items()},
            'target_characters':dict(size),'errors':errors,'verified_raw_files':len(raw_checked),
            'limits':'Characters are not tokenizer counts. Exact duplicate detection does not certify semantic independence.'}


def source_inventory(root=Path('.')):
    root=Path(root);receipts=[]
    from .snapshot import save_manifests
    save_manifests(root)
    for path in sorted((root/'data/raw').rglob('*.receipt.json')):
        r=json.loads(path.read_text())
        raw=path.with_name(path.name.removesuffix('.receipt.json'))
        # Do not persist expiring redirect URLs in the reproducibility lock.
        receipts.append({'source_id':r['source_id'],'url':r['url'],'path':str(raw.relative_to(root)),
                         'sha256':r['sha256'],'bytes':r['bytes'],'retrieved_at':r['retrieved_at']})
    write_json(root/'data/sources.lock.json',{'schema_version':'1.0','files':receipts,
                   'note':'Exact downloaded snapshot. Receipt hashes validate bytes; dynamic URLs may later change.'})
    groups=defaultdict(lambda: {'files':0,'bytes':0})
    for r in receipts:groups[r['source_id']]['files']+=1;groups[r['source_id']]['bytes']+=r['bytes']
    write_json(root/'reports/acquisition_inventory.json',dict(groups))
    return dict(groups)
