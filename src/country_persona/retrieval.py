"""Local FTS evidence index; date-unknown and same-event material are excluded at query time."""
import json
import re
import sqlite3
from pathlib import Path
from .io import read_jsonl


def create_index(canonical,output):
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():raise ValueError('Use a new index filename for each snapshot')
    conn=sqlite3.connect(output)
    conn.execute('CREATE VIRTUAL TABLE evidence USING fts5(id UNINDEXED, source_id UNINDEXED, country UNINDEXED, available_date UNINDEXED, split_group UNINDEXED, url UNINDEXED, title, body)')
    n=0
    for r in read_jsonl(canonical):
        if r['split']=='quarantine' or not r['available_date']:continue
        if r['task'] not in ('press_conference','statement_reconstruction','human_rights_evidence','upr_recommendation'):continue
        conn.execute('INSERT INTO evidence VALUES (?,?,?,?,?,?,?,?)',
                     (r['id'],r['source_id'],r['country_iso3'],r['available_date'],r.get('split_group',r['group_id']),r['source_url'],r['title'],r['text']))
        n+=1
    conn.commit();conn.close();return {'documents':n,'path':str(output)}


def search(index,query,before,exclude_group,country=None,limit=5):
    from datetime import date
    date.fromisoformat(before)
    if not exclude_group:raise ValueError('A target event/split group must be supplied')
    tokens=re.findall(r'\w+',query,flags=re.UNICODE)[:20]
    if not tokens:return []
    expression=' OR '.join('"'+t+'"' for t in tokens)
    conn=sqlite3.connect('file:'+str(Path(index).resolve())+'?mode=ro',uri=True)
    sql='SELECT id,source_id,country,available_date,split_group,url,title,body,bm25(evidence) FROM evidence WHERE evidence MATCH ? AND available_date < ? AND split_group != ?'
    params=[expression,before,exclude_group]
    if country:sql+=' AND country = ?';params.append(country)
    sql+=' ORDER BY bm25(evidence) LIMIT ?';params.append(limit)
    rows=conn.execute(sql,params).fetchall();conn.close()
    return [dict(zip(['id','source_id','country','available_date','split_group','source_url','title','text','score'],r)) for r in rows]
