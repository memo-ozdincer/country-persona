from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from .io import write_json, write_jsonl
from .schema import validate
from .parsers import parse_mfa, parse_mission, parse_german_press, parse_ungdc
from .bulk import parse_unga_rdata, parse_unbench, parse_uhri, parse_unga_dm, unga_meeting_dates


def normalize(root=Path('.')):
    root=Path(root);raw=root/'data/raw';out=root/'data/canonical'
    from .snapshot import restore_generated_sources
    restore_generated_sources(root)
    reports={}
    for source,fn in [('mfa',parse_mfa),('china_mission',lambda x:parse_mission(x,'china_mission')),
                      ('germany_mission',lambda x:parse_mission(x,'germany_mission')),
                      ('germany_press',parse_german_press),('ungdc',parse_ungdc)]:
        listing=raw/source/('sitemap_collection.json' if source=='germany_mission' else 'collection.json')
        if not listing.exists():continue
        listing=json.loads(listing.read_text())
        if not listing.get('complete'):raise ValueError(f'{source} acquisition still running')
        records=[];errors=[]
        for item in listing['documents']:
            try:records.extend(validate(r) for r in fn(item))
            except Exception as exc:errors.append({'url':item['url'],'path':item['path'],'error':str(exc)})
        write_jsonl(out/(source+'.jsonl'),records)
        reports[source]={'parsed_records':len(records),'source_documents':len(listing['documents']),
                         'tasks':dict(Counter(r['task'] for r in records)), 'parse_errors':errors}
    if (raw/'unga_speech_corpus/unga_speech_corpus.RData').exists():
        count=Counter()
        votes_path=raw/'unga_dm/votes.csv'
        dates=unga_meeting_dates(votes_path) if votes_path.exists() else {}
        def rows():
            for r in parse_unga_rdata(raw/'unga_speech_corpus/unga_speech_corpus.RData','https://www.linneaturco.com/research',dates,votes_path if dates else None):
                validate(r);count[r['task']]+=1;yield r
        write_jsonl(out/'unga_speech_corpus.jsonl',rows())
        reports['unga_speech_corpus']={'parsed_records':sum(count.values()),'tasks':dict(count)}
    if (raw/'unbench/data/task2.csv').exists():
        records=[validate(r) for r in parse_unbench(raw/'unbench')]
        write_jsonl(out/'unbench.jsonl',records)
        reports['unbench']={'parsed_records':len(records),'tasks':dict(Counter(r['task'] for r in records))}
    if (raw/'unga_dm/votes.csv').exists():
        records=[validate(r) for r in parse_unga_dm(raw/'unga_dm/votes.csv')]
        write_jsonl(out/'unga_dm.jsonl',records)
        reports['unga_dm']={'parsed_records':len(records),'tasks':dict(Counter(r['task'] for r in records))}
    if (raw/'uhri/export-full-en.json').exists():
        count=Counter()
        def rows():
            for r in parse_uhri(raw/'uhri/export-full-en.json',countries_only=True):
                validate(r);count[r['task']]+=1;yield r
        write_jsonl(out/'uhri.jsonl',rows())
        reports['uhri']={'parsed_records':sum(count.values()),'tasks':dict(count),
                         'scope':'China/Germany mentioned as reviewed or recommending states; full raw export retained'}
    write_json(root/'reports/normalization.json',reports)
    return reports
