"""Build a public metadata catalog and a local full-record explorer from every data file.

Public exports deliberately exclude third-party transcript bodies and original QA text.
Exact local file offsets support full inspection without copying restricted text publicly.
"""
import collections
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from urllib.parse import urlparse
import pyarrow as pa
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.cache/data-publication'
COUNTRIES={'CHN':'China','DEU':'Germany','FRA':'France','GBR':'United Kingdom','IND':'India','BRA':'Brazil'}
OWNER='memo-ozdincer'
DATASET=f'{OWNER}/country-persona-data'
SPACE=f'{OWNER}/country-persona-explorer'

def dumps(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def strings(x):return [str(v) for v in (x if isinstance(x,list) else [x]) if v is not None and v!='']
def file_sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def valid_url(x):
    return x if isinstance(x,str) and urlparse(x).scheme in ('http','https') and not urlparse(x).username else ''
def kind_for(r,path):
    typ=str(r.get('record_type') or r.get('task') or '')
    if typ=='decision_case':return 'decision_cases'
    if 'review' in path or '.manifest.' in path or any(s in path for s in ['split_manifest','duplicates','excluded','document-families']):return 'review_and_lineage'
    if any(s in path for s in ['/eval-', '/un-parallel-eval/']):return 'evaluation'
    if r.get('indicator'):return 'country_statistics'
    if typ in ['stated_policy','policy_position'] or 'policy-positions' in path:return 'policy_positions'
    if typ in ['evidence_conditioned_application','authored_example'] or ('examples.jsonl' in path) or 'policy-applications' in path:return 'policy_applications'
    if 'prompt' in r or 'messages' in r or '/candidates/' in path:return 'training_views'
    if typ=='observed_vote' or 'vote' in path or typ=='upr_response':return 'observed_actions'
    if 'passages' in path:return 'evidence_passages'
    if 'profiles' in path:return 'country_profiles'
    return 'source_records'

def normalize(r,path,line,meta=None):
    base=r.get('record',r)
    if not isinstance(base,dict):base=r
    m=meta or {}
    country=base.get('country_iso3') or base.get('countries') or base.get('country') or m.get('country_iso3') or m.get('country')
    codes=strings(country)
    codes=[next((k for k,v in COUNTRIES.items() if v==c),c) for c in codes]
    if not codes:
        codes=[c for c in COUNTRIES if re.search(r'[/\.]'+c+r'[/\.]',path)]
    kind=kind_for(base,path)
    rid=str(base.get('id') or base.get('case_sha256') or base.get('group_id') or m.get('id') or f'{path}:{line}')
    source=str(base.get('source_id') or m.get('source_id') or '')
    evidence=base.get('evidence')
    ev=evidence[0] if isinstance(evidence,list) and evidence else evidence if isinstance(evidence,dict) else {}
    url=valid_url(base.get('source_url') or m.get('source_url') or ev.get('source_url'))
    title=str(base.get('title') or base.get('label') or base.get('issue') or base.get('task') or base.get('record_type') or rid)
    public={k:base[k] for k in ['represented_entity','institution','speaking_capacity','document_symbols','document_type','original_vote','amended_vote','observed_action','original_seat_name','current_seat_name','reviewed_states','recommending_states','response_labels','upr_cycle','translation_status','available_date','quality_flags','indicator','label','reference_year','value','unit','missing','database_last_updated','available_at_reference_year','group_id','split_group','parent_id','fresh_evaluation_eligible','review_status','rights_status','raw_sha256','pdf_page','pdf_start_page','pdf_end_page','start_char','end_char','derivation','rubric','conditions_status','source_coverage'] if k in base}
    public['source_text_status']='Full source text is available locally; use the publisher link for the public original.'
    # Only project-authored summaries/targets enter the public text columns.
    summary=''
    curated=path.startswith(('data/prepared/country-knowledge-','data/prepared/country-extension-','data/prepared/decision-cases-'))
    if curated and kind in ('policy_positions','policy_applications','decision_cases'):
        for key in ['claim','question','answer','proposal_summary','public_explanation','stated_considerations','requested_changes','conditions_for_agreement','missing_context','material_context','proposal_symbol','resolution_symbol','explanation_kind','use','private_motive']:
            if key in base:public[key]=base[key]
        if kind=='policy_applications' and isinstance(base.get('messages'),list):
            assistant=[x['content'] for x in base['messages'] if x.get('role')=='assistant']
            if assistant:public['answer']=assistant[-1]
            users=[x['content'] for x in base['messages'] if x.get('role')=='user']
            if users and '\nQuestion: ' in users[-1]:public['question']=users[-1].rsplit('\nQuestion: ',1)[1]
        for key in ['evidence','proposal_evidence','explanation_evidence','vote_evidence']:
            if key in base:public[key]=base[key]
        summary=str(public.get('claim') or public.get('answer') or public.get('public_explanation') or public.get('proposal_summary') or '')
    if kind=='country_statistics':summary=f"{base.get('label','')} = {base.get('value')} {base.get('unit','')} ({base.get('reference_year','')})"
    if kind=='observed_actions':summary=str(base.get('observed_action') or base.get('original_vote') or (base.get('text') if base.get('task')=='upr_response' else '') or '')
    if not summary:summary='Source-backed record; open its publisher link or inspect full content in the local explorer.'
    language=' / '.join(strings(base.get('language') or base.get('answer_language') or (list(base['translations']) if isinstance(base.get('translations'),dict) else '')))
    date=str(base.get('event_date') or base.get('date') or base.get('reference_year') or m.get('event_date') or '')
    if isinstance(base.get('date'),dict):date=''
    split=str(base.get('split') or m.get('split') or 'unspecified')
    explicit=base.get('training_admitted')
    readiness='admitted' if explicit is True else 'not_admitted' if explicit is False else 'not_recorded'
    public['proposed_split']=base.get('proposed_split')
    topics=' / '.join(strings(base.get('topics') or base.get('issue')))
    release=path.split('/')[2] if path.startswith('data/prepared/') else 'canonical'
    return {'record_id':rid,'country':' / '.join(codes) or 'Unattributed','countries':codes,'kind':kind,
      'language':language or 'unspecified','date':date,'title':title,'summary':summary,'source':source or 'unspecified',
      'source_url':url,'topic':topics or 'unspecified','split':split,'readiness':readiness,'release':release,
      'details':public,'topic_tags':strings(base.get('topics') or base.get('issue')) or ['unspecified']}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'tables').mkdir(exist_ok=True)
    dbpath=OUT/'catalog.next.sqlite';dbpath.unlink(missing_ok=True)
    db=sqlite3.connect(dbpath)
    db.executescript('''PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;
      CREATE TABLE records(uid TEXT PRIMARY KEY,record_id TEXT,country TEXT,kind TEXT,language TEXT,date TEXT,title TEXT,summary TEXT,source TEXT,source_url TEXT,topic TEXT,split TEXT,readiness TEXT,release TEXT,details TEXT,locations TEXT);
      CREATE TABLE record_countries(uid TEXT,country TEXT);
      CREATE TABLE record_topics(uid TEXT,topic TEXT);
      CREATE TABLE record_collections(uid TEXT,release TEXT);
      CREATE TABLE files(path TEXT PRIMARY KEY,collection TEXT,format TEXT,bytes INTEGER,sha256 TEXT,source_url TEXT,location TEXT);
      CREATE VIRTUAL TABLE search USING fts5(uid UNINDEXED,content,tokenize='unicode61');''')
    seen={};rows=[];counts=collections.Counter();input_count=0
    paths=sorted(list((ROOT/'data/canonical').glob('*.jsonl'))+list((ROOT/'data/prepared').rglob('*.jsonl')))
    for p in paths:
      rel=p.relative_to(ROOT).as_posix(); metas=[]
      mp=p.with_suffix('.manifest.jsonl')
      if '.manifest.' not in p.name and mp.exists():metas=[json.loads(s) for s in mp.open()]
      with p.open('rb') as f:
       line=0
       while True:
        offset=f.tell();raw=f.readline()
        if not raw:break
        line+=1
        if not raw.strip():continue
        r=json.loads(raw);input_count+=1
        uid=hashlib.sha256(dumps(r).encode()).hexdigest()
        loc={'path':rel,'line':line,'offset':offset,'length':len(raw)}
        if uid in seen:
          rows[seen[uid]]['locations'].append(loc);continue
        n=normalize(r,rel,line,metas[line-1] if line<=len(metas) else None)
        n['uid']=uid;n['locations']=[loc];seen[uid]=len(rows);rows.append(n)
      print(f'Indexed {rel}',flush=True) if rel.endswith('/cases.jsonl') else None
    columns=['uid','record_id','country','kind','language','date','title','summary','source','source_url','topic','split','readiness','release','details','locations']
    tables=collections.defaultdict(list)
    for r in rows:
      values=[dumps(r[k]) if k in ('details','locations') else r[k] for k in columns]
      db.execute('INSERT INTO records VALUES ('+','.join('?'*len(columns))+')',values)
      db.executemany('INSERT INTO record_countries VALUES (?,?)',[(r['uid'],c) for c in r['countries']])
      db.executemany('INSERT INTO record_topics VALUES (?,?)',[(r['uid'],v) for v in set(r['topic_tags'])])
      releases={loc['path'].split('/')[2] if loc['path'].startswith('data/prepared/') else 'canonical' for loc in r['locations']}
      r['release_tags']=sorted(releases)
      db.executemany('INSERT INTO record_collections VALUES (?,?)',[(r['uid'],v) for v in releases])
      db.execute('INSERT INTO search VALUES (?,?)',(r['uid'],' '.join(str(r[k]) for k in ['record_id','country','title','summary','source','topic','language'])))
      flat=dict(zip(columns,values));tables[r['kind']].append(flat);counts[r['kind']]+=1
    files=[]
    for base in ('raw','canonical','prepared'):
      for p in sorted((ROOT/'data'/base).rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(ROOT).as_posix();url=''
        receipt=p.with_name(p.name+'.receipt.json')
        if receipt.exists():url=valid_url(json.loads(receipt.read_text()).get('url'))
        record={'path':rel,'collection':base+'/'+rel.split('/')[2],'format':p.suffix.lstrip('.'),'bytes':p.stat().st_size,'sha256':file_sha(p),'source_url':url,'location':'local_and_trillium_research_copy; public_original_link_when_known'}
        files.append(record);db.execute('INSERT INTO files VALUES (?,?,?,?,?,?,?)',tuple(record.values()))
    db.executescript('CREATE INDEX ix_country ON record_countries(country,uid); CREATE INDEX ix_topics ON record_topics(topic,uid); CREATE INDEX ix_collections ON record_collections(release,uid); CREATE INDEX ix_kind ON records(kind); CREATE INDEX ix_date ON records(date); CREATE INDEX ix_release ON records(release);')
    db.commit();db.close();dbpath.replace(OUT/'catalog.sqlite')
    for kind,items in tables.items():
      pq.write_table(pa.Table.from_pylist(items),OUT/'tables'/f'{kind}.parquet',compression='zstd',row_group_size=128,write_page_index=True)
    pq.write_table(pa.Table.from_pylist(files),OUT/'tables/files.parquet',compression='zstd',row_group_size=128,write_page_index=True)
    stats={'owner':'Memo Ozdincer','account':OWNER,'dataset':DATASET,'space':SPACE,'snapshot':'2026-09-14',
      'input_jsonl_files':len(paths),'input_rows':input_count,'exact_unique_records':len(rows),'duplicate_occurrences':input_count-len(rows),
      'inventory_files':len(files),'inventory_bytes':sum(r['bytes'] for r in files),'record_kinds':dict(counts),
      'countries':COUNTRIES,'coverage_note':'All local raw/canonical/prepared files inventoried. Every nonblank canonical/prepared JSONL row indexed. Exact identical records share locations; distinct views and related events still overlap.',
      'publication_note':'Public metadata, factual values and project-authored summaries. Third-party full text stays in research copies; original publishers retain attribution. Full-record local mode uses indexed file offsets.',
      'language_counts':dict(collections.Counter(r['language'] for r in rows)),
      'readiness_counts':dict(collections.Counter(r['readiness'] for r in rows)),
      'country_counts':{c:sum(c in r['countries'] for r in rows) for c in COUNTRIES}}
    stats['filters']={}
    for k in ['kind','language','source','split','readiness','release','topic']:
      counter=collections.Counter(v for r in rows for v in (r['topic_tags'] if k=='topic' else r['release_tags'] if k=='release' else [r[k]]))
      stats['filters'][k]=[{'value':v,'count':n} for v,n in counter.most_common()]
    (OUT/'stats.json').write_text(json.dumps(stats,indent=2)+'\n')
    configs='\n'.join(f'  - config_name: {k}\n    data_files:\n      - split: catalog\n        path: tables/{k}.parquet' for k in [*sorted(tables),'files'])
    card=f'''---
pretty_name: Country Persona Data
language:
  - en
  - de
  - fr
  - zh
  - pt
  - ar
  - es
  - ru
  - ja
  - pl
  - uk
tags:
  - international-relations
  - provenance
  - country-personas
  - research
configs:
{configs}
---
# Country Persona Data

**Created and maintained by Memo Ozdincer** · [GitHub](https://github.com/{OWNER}/country-persona-data) · [Open the searchable explorer](https://huggingface.co/spaces/{SPACE})

Dated institutional country evidence for China, Germany, France, the United Kingdom, India and Brazil, with additional countries present in the underlying speech corpus. This is a research catalog, not a claim of trained persona quality.

Start with **decision_cases**, **policy_positions**, **policy_applications** or **country_statistics** in the subset selector. The `catalog` split is for browsing and is NOT a training split. Original and proposed allocations remain columns.

{len(rows):,} exact distinct record objects from {input_count:,} row occurrences in {len(paths)} JSONL files. {len(files):,} raw and prepared files inventoried. Alternative training views, translations, review wrappers and repeated event families overlap; these are not independent observations.

## What is public

Metadata, recorded vote labels, country statistics and project-authored policy/decision summaries. Third-party source bodies and original QA are not republished under an invented blanket license. Follow `source_url` and evidence references to the publishers. Full rows are available in the local research explorer. A row without substantive public text is labeled explicitly; it is not represented as a new training example.

## Attribution and limitations

Project ownership and publishing: **Memo Ozdincer** (`memo-ozdincer`). Government positions remain attributed to their government, UN records to the United Nations, statistics to their upstream publishers and research corpora to their providers. Assistant-prepared paraphrases retain derivation labels and are not authentic historical dialogue or independently reviewed expert annotations.

New decision cases are retrospective demonstrations. Post-vote statements are not valid pre-vote forecast inputs. Unknown constraints and private motives remain unknown. Most historical votes still lack joined proposal texts. Admission is read from an explicit field: missing is `not_recorded`, never silently approved.

## Reproduction and download

```python
from datasets import load_dataset
cases = load_dataset("{DATASET}", "decision_cases", split="catalog")
```

Each row includes source file/line locations and stable content hashes. The `files` subset inventories every raw/canonical/prepared file with SHA256 and publisher links when recorded. Public tables intentionally omit restricted source bodies; the inventory is not a claim that those bodies are publicly downloadable here.

Parquet subsets and explicit configuration follow the [Hugging Face format documentation](https://huggingface.co/docs/hub/datasets-data-files-configuration). Metadata does not grant new rights over underlying sources.
'''
    (OUT/'README.md').write_text(card)
    (ROOT/'reports/data-catalog.json').write_text(json.dumps(stats,indent=2)+'\n')
    print(json.dumps(stats,indent=2))
if __name__=='__main__':main()
