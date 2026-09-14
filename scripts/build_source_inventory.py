"""Project verified catalog pointers into source-level counts and character lengths."""
import collections
import hashlib
import json
import math
import sqlite3
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODES = ('CHN', 'DEU', 'FRA', 'GBR', 'IND', 'BRA')
EXCLUDED = ('training_views', 'review_and_lineage', 'evaluation', 'country_profiles')

def family_for(row, obj, aliases):
    if row['kind'] == 'decision_cases': return 'decision_cases'
    if row['kind'] == 'country_statistics': return 'world_bank'
    if row['kind'] in ('policy_positions','policy_applications'): return 'curated'
    return aliases.get(row['source'], row['source'])

def length_summary(values):
    if not values: return None
    values=sorted(values)
    return {'n':len(values), 'min':values[0], 'median':statistics.median(values), 'p95':values[math.ceil(.95*len(values))-1], 'max':values[-1], 'unit':'Unicode characters'}

def text_of(value):
    if isinstance(value,str): return value
    if isinstance(value,list): return '\n'.join(text_of(x) for x in value)
    if isinstance(value,dict): return text_of(value.get('content',''))
    return ''

def field_lengths(obj, task):
    """Measure only populated stored fields; never convert characters to guessed tokens."""
    if obj.get('messages'):
        return len(text_of(obj['messages'][:-1])),len(text_of(obj['messages'][-1:])),None
    if task in ('authentic_qa','upr_response','vote_prediction','upr_recommendation','statement_reconstruction'):
        prompt='\n'.join(filter(None,[text_of(obj.get(k)) for k in ('question','context','history')]))
        target=text_of(obj.get('text'))
        return len(prompt) if prompt else None,len(target) if target else None,None
    body=text_of(obj.get('text')) or text_of(obj.get('passage'))
    return None,None,len(body) if body else None

def task_for(row,obj):
    if row['kind'] in ('policy_positions','policy_applications','country_statistics','decision_cases'): return row['kind']
    if row['kind']=='evidence_passages': return 'policy_evidence'
    return obj.get('task') or 'policy_evidence'

def build_inventory():
    profiles=json.loads((ROOT/'explorer/source_profiles.json').read_text())
    aliases={alias:key for key,p in profiles.items() for alias in p['aliases']}
    db=sqlite3.connect(ROOT/'.cache/data-publication/catalog.sqlite');db.row_factory=sqlite3.Row
    placeholders=','.join('?' for _ in CODES);excluded=','.join('?' for _ in EXCLUDED)
    rows=db.execute(f'''SELECT r.uid,r.record_id,r.source,r.kind,r.language,r.date,r.title,r.source_url,r.locations,c.country
        FROM records r JOIN record_countries c ON r.uid=c.uid
        WHERE c.country IN ({placeholders}) AND r.kind NOT IN ({excluded})
        ORDER BY c.country,r.record_id,CASE WHEN r.release='canonical' THEN 0 ELSE 1 END,r.uid''', CODES+EXCLUDED)
    groups={c:{} for c in CODES};seen={c:set() for c in CODES};handles={};verified=set()
    try:
        for row in rows:
            country=row['country'];rid=row['record_id']
            if rid in seen[country]:continue
            seen[country].add(rid)
            loc=json.loads(row['locations'])[0];p=ROOT/loc['path']
            if p not in handles:handles[p]=p.open('rb')
            f=handles[p];f.seek(loc['offset']);obj=json.loads(f.read(loc['length']))
            if row['uid'] not in verified:
                digest=hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
                assert digest==row['uid'],f'Changed catalog source: {rid}'
                verified.add(row['uid'])
            family=family_for(row,obj,aliases)
            if family not in profiles:raise ValueError(f'Add source profile for {family}')
            source=groups[country].setdefault(family,{'id':family,'count':0,'source_ids':set(),'languages':set(),'dates':set(),'kinds':collections.Counter(),'tasks':{},'missing_values':0})
            source['count']+=1;source['source_ids'].add(row['source']);source['kinds'][row['kind']]+=1
            if row['language'] and row['language']!='unspecified':source['languages'].add(row['language'])
            if row['date']:source['dates'].add(row['date'])
            if obj.get('missing') is True:source['missing_values']+=1
            task=task_for(row,obj)
            t=source['tasks'].setdefault(task,{'id':task,'count':0,'lengths':{'input':[],'target':[],'body':[]},'sample':None,'groups':set(),'missing_input_fields':0})
            t['count']+=1
            group=obj.get('group_id') or obj.get('split_group')
            if group:t['groups'].add(group)
            for field,value in zip(('input','target','body'),field_lengths(obj,task)):
                if value is not None:t['lengths'][field].append(value)
            if not text_of(obj.get('question')) and not text_of(obj.get('context')) and not obj.get('messages'):t['missing_input_fields']+=1
            # Deterministic real record anchor, with metadata only in public output.
            if t['sample'] is None:
                t['sample']={'id':rid,'uid':row['uid'],'title':row['title'],'date':row['date'],'source_url':row['source_url'],
                             'file':loc['path'],'line':loc['line'],'task':task,'fields':sorted(obj),
                             'quality_flags':obj.get('quality_flags',[]),'rights_status':obj.get('rights_status','not_recorded'),
                             'review_status':obj.get('review_status','not_recorded'),'split':obj.get('split','not_recorded')}
    finally:
        for f in handles.values():f.close()
        db.close()
    out={'version':'source-inventory-v1','snapshot':'2026-09-14',
         'count_unit':'evidence record IDs',
         'count_definition':'Distinct record_id per country across source records, passages, actions, statistics and curated annotations. Excludes training-format copies, review/lineage, evaluation wrappers and profiles. Each ID is assigned once, preferring its canonical version. Translations and derived spans remain separate IDs; these are not independent training traces.',
         'length_definition':'Exact character counts of stored question/context/history fields, target text, or document body; before adding metadata and the chat template. No tokenizer estimates. n is the number with that field present; missing fields are not zero-length observations.',
         'environments':{'interactive':0,'multi_agent_trajectories':0,'implemented_verifiers':0,'preference_pairs':0},'countries':{}}
    for country,sources in groups.items():
        finished=[]
        for source in sources.values():
            for name in ('source_ids','languages'):source[name]=sorted(source[name])
            dates=sorted(source.pop('dates'));source['date_range']=[dates[0],dates[-1]] if dates else []
            tasks=[]
            for t in source['tasks'].values():
                t['lengths']={key:length_summary(vals) for key,vals in t['lengths'].items()}
                t['recorded_group_count']=len(t.pop('groups'));tasks.append(t)
            source['tasks']=sorted(tasks,key=lambda t:(-t['count'],t['id']));finished.append(source)
        finished.sort(key=lambda s:profiles[s['id']]['name'].casefold())
        assert sum(s['count'] for s in finished)==len(seen[country])
        out['countries'][country]={'count':len(seen[country]),'sources':finished}
    (ROOT/'explorer/sources.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'source_inventory':{c:out['countries'][c]['count'] for c in CODES},'verified_objects':len(verified)}))
    return out

if __name__=='__main__':build_inventory()
