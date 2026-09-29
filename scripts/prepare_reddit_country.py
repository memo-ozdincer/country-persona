"""Stream pinned Reddit archives into country-context corpora and observed reply pairs.

Country context is assigned to communities, never to individual authors. No training
admission, political labels, sentiment labels, or synthetic replies are generated.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import html
import io
import json
from pathlib import Path
import re
import sqlite3
import xml.etree.ElementTree as ET

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import zstandard

ROOT=Path(__file__).resolve().parents[1]
RELEASE='reddit-country-20260923'
MAPPING=ROOT/'data/curation/reddit_country_communities.json'
MANIFEST=ROOT/f'data/manifests/{RELEASE}.json'
OUT=ROOT/f'data/prepared/{RELEASE}'
REMOVED={'[deleted]','[removed]','[removed by reddit]'}
HANDLE=re.compile(r'(?i)(?<![\w/])/?u/[A-Za-z0-9_-]{3,25}')
EMAIL=re.compile(r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b')
PHONE=re.compile(r'(?<!\w)\+\d[\d ()-]{8,20}\d(?!\w)')
USER_URL=re.compile(r'https?://(?:www\.)?reddit\.com/(?:u|user)/[^\s/)]+',re.I)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()


def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def dumps(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def truth(x):return x is True or str(x).lower() in {'true','1'}


def utc(x):
    if x in (None,''):return None
    try:
        return datetime.fromtimestamp(float(x),timezone.utc).isoformat().replace('+00:00','Z')
    except (ValueError,TypeError,OverflowError,OSError):
        try:return datetime.fromisoformat(str(x)).replace(tzinfo=timezone.utc).isoformat().replace('+00:00','Z')
        except ValueError:return None


def clean_text(text):
    text=html.unescape(text or '').strip()
    if not text or text.lower() in REMOVED:return '',[]
    changes=[]
    for name,pattern in [('user_url',USER_URL),('user_handle',HANDLE),('email',EMAIL),('phone',PHONE)]:
        text,n=pattern.subn('['+name.upper()+']',text)
        if n:changes.append(name)
    return text,changes


def standard_id(value,kind):
    value=str(value or '')
    if re.fullmatch(r't[13]_[a-z0-9]+',value):return value
    if re.fullmatch(r'[a-z0-9]+',value):return ('t3_' if kind=='post' else 't1_')+value
    return None


def normalize(r,kind,source,locator,mapping):
    sub=str(r.get('subreddit') or '').lower()
    if sub not in mapping:return None,'unmapped_community'
    if truth(r.get('over_18')):return None,'nsfw_tagged'
    author=str(r.get('author') or '').lower()
    if author in {'[deleted]','[removed]','automoderator'}:return None,'deleted_or_automoderator_author'
    title=str(r.get('title') or '').strip() if kind=='post' else ''
    body=str(r.get('selftext') or '') if kind=='post' else str(r.get('body') or '')
    if body.strip().lower() in REMOVED:return None,'deleted_or_removed_body'
    text,redactions=clean_text((title+'\n\n'+body).strip() if title and body else title or body)
    if len(text)<40:return None,'short_text_under_40_characters'
    if source['source_id']=='brazil_threads':
        key=r.get('thread_id') if kind=='post' else r.get('comment_id')
        if not key:return None,'missing_id'
        rid='bra_'+('post:' if kind=='post' else 'comment:')+key
        thread='bra_post:'+str(r.get('thread_id'))
        parent=None if kind=='post' else ('bra_post:' if r.get('parent_id')==r.get('thread_id') else 'bra_comment:')+str(r.get('parent_id'))
        origin_url=None
    else:
        rid=standard_id(r.get('id'),kind)
        thread=rid if kind=='post' else standard_id(r.get('link_id'),'post')
        parent=None if kind=='post' else standard_id(r.get('parent_id'),'comment')
        if not rid or not thread:return None,'invalid_reddit_id'
        origin_url='https://www.reddit.com/comments/'+thread[3:]+'/'+('' if kind=='post' else '_/'+rid[3:])
    country,scope=mapping[sub]
    when=utc(r.get('created_utc'))
    flags=['archived_content_not_currently_verified','community_not_population_sample','not_official_country_position']
    if r.get('over_18') is None:flags.append('nsfw_status_not_available')
    if not when:flags.append('date_unknown')
    if redactions:flags.append('identifier_patterns_redacted')
    if r.get('_xml_control_filter'):flags.append('xml_control_byte_filter_applied')
    if source['source_id']=='brazil_threads':flags.append('publisher_pseudonymized_ids_no_original_reddit_permalink')
    return {'id':rid,'record_type':'reddit_community_'+kind,'country_iso3':None,
            'country_context_iso3':country,'country_attribution_basis':'community_topic_only_not_author_nationality',
            'represented_entity':None,'subreddit':sub,'community_scope':scope,
            'thread_id':thread,'parent_id':parent,'created_at':when,'language':None,
            'text':text,'text_sha256':digest(text),'source_url':origin_url,
            'source_id':source['source_id'],'source_repository':source['repository'],
            'source_revision':source['revision'],'source_file':source['source_path'],
            'raw_sha256':source['sha256'],'raw_locator':locator,
            'source_retrieved_at':source['retrieved_at'],'score':r.get('score'),
            'score_use':'archive_metadata_not_preference_or_truth_label',
            'crosspost_parent':r.get('crosspost_parent'), 'redactions':redactions,
            'quality_flags':flags,'split_group':'reddit-thread:'+thread,'split':'quarantine',
            'training_admitted':False,'rights_status':'not_cleared_for_training_or_redistribution',
            'fresh_evaluation_eligible':False},None


def iter_parquet(path,subreddits,sub_ids,stats):
    f=pq.ParquetFile(path);offset=0
    for batch in f.iter_batches(batch_size=32768):
        names=pc.utf8_lower(batch.column('subreddit'))
        indices=pc.indices_nonzero(pc.is_in(names,value_set=pa.array(sorted(subreddits))))
        # Selected row indices preserve exact file-level row provenance, including nulls.
        for i,r in zip(indices.to_pylist(),batch.take(indices).to_pylist()):
            sub=(r.get('subreddit') or '').lower();sid=(r.get('subreddit_id') or '').removeprefix('t5_')
            if sid:
                if sid in sub_ids and sub_ids[sid]!=sub:raise ValueError('Conflicting subreddit ID mapping')
                sub_ids[sid]=sub
            yield r,'post',{'parquet_row_index':offset+i}
        stats['raw_rows_scanned']+=len(batch);offset+=len(batch)


def iter_csv(path,stats):
    csv.field_size_limit(16*1024*1024)
    with path.open(encoding='utf-8-sig',newline='') as f:
        for n,r in enumerate(csv.DictReader(f)):
            stats['raw_rows_scanned']+=1
            r['subreddit']='brasil'
            yield r,('comment' if 'comment_id' in r else 'post'),{'csv_record_index':n}


def iter_zst(path,stats):
    with path.open('rb') as f, zstandard.ZstdDecompressor(max_window_size=2**31).stream_reader(f) as stream:
        for n,line in enumerate(io.TextIOWrapper(stream,encoding='utf-8')):
            r=json.loads(line);stats['raw_rows_scanned']+=1
            yield r,('comment' if 'body' in r else 'post'),{'jsonl_line':n+1}


class XMLControlFilter:
    def __init__(self,stream,stats):self.stream=stream;self.stats=stats
    def read(self,size=-1):
        raw=self.stream.read(size)
        cleaned,n=re.subn(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]',b'',raw)
        self.stats['xml_illegal_control_bytes_removed']+=n
        return cleaned


def iter_xml(path,sub_ids,stats):
    # The publisher splits trees into overlapping paths. Original comment IDs deduplicate them.
    with path.open('rb') as raw:
      for n,(_,node) in enumerate(ET.iterparse(XMLControlFilter(raw,stats),events=('end',))):
          if node.tag!='s':continue
          sid=node.attrib.get('subreddit_id','').removeprefix('t5_')
          sub=sub_ids.get(sid)
          link=node.attrib.get('link_id')
          for j,u in enumerate(node.findall('utt')):
              stats['raw_rows_scanned']+=1
              if sub is None:
                  stats['unmapped_xml_subreddit:'+sid]+=1;continue
              parent=u.attrib.get('parent_id')
              r={'id':u.attrib.get('comment_id'),'subreddit':sub,'link_id':link,
                 'parent_id':standard_id(parent,'post' if parent==link else 'comment'),
                 'body':''.join(u.itertext()),'created_utc':u.attrib.get('create_utc'),'score':u.attrib.get('score'),'_xml_control_filter':True}
              yield r,'comment',{'xml_end_event_index':n,'utterance_index':j,'subreddit_id':sid}
          node.clear()


class GzipWriter:
    def __init__(self,path):
        path.parent.mkdir(parents=True,exist_ok=True)
        self.raw=path.open('wb');self.zip=gzip.GzipFile(filename='',mode='wb',fileobj=self.raw,mtime=0)
    def add(self,obj):self.zip.write((dumps(obj)+'\n').encode())
    def close(self):self.zip.close();self.raw.close()


def build(output):
    if output.exists():raise ValueError('Choose a fresh output directory')
    manifest=json.loads(MANIFEST.read_text())
    if manifest['failures']:raise ValueError('Acquisition contains failures')
    registry=json.loads((ROOT/'data/reddit_source_registry.json').read_text())
    if len(manifest['files'])!=sum(len(s['files']) for s in registry['sources']):raise ValueError('Acquisition incomplete')
    cm=json.loads(MAPPING.read_text());mapping={sub.lower():(c,scope) for c,v in cm['countries'].items() for sub,scope in v['subreddits'].items()}
    output.mkdir(parents=True);db=sqlite3.connect(output/'working.sqlite')
    db.execute('CREATE TABLE records(id TEXT PRIMARY KEY,thread TEXT,parent TEXT,country TEXT,sub TEXT,kind TEXT,created TEXT,hash TEXT,payload TEXT)')
    db.execute('CREATE TABLE variants(id TEXT PRIMARY KEY, occurrences INT, conflicts INT)')
    db.execute('CREATE TABLE blocked_threads(thread TEXT PRIMARY KEY)')
    lineage=GzipWriter(output/'lineage.jsonl.gz');sub_ids={};files_report=[]
    # Resolve subreddit IDs from actual archive rows before using the French XML.
    files=sorted(manifest['files'],key=lambda f:(0 if f['source_id']=='global_posts' else 2 if f['source_id']=='french_conversations' else 1,f['raw_file']))
    for source in files:
        path=ROOT/source['raw_file'];stats=Counter()
        if sha(path)!=source['sha256']:raise ValueError('Raw hash mismatch: '+str(path))
        if path.suffix=='.parquet':stream=iter_parquet(path,mapping,sub_ids,stats)
        elif path.suffix=='.csv':stream=iter_csv(path,stats)
        elif path.suffix=='.zst':stream=iter_zst(path,stats)
        elif path.suffix=='.xml':stream=iter_xml(path,sub_ids,stats)
        else:raise ValueError('Unsupported file')
        for r,kind,locator in stream:
            stats['selected_rows_seen']+=1
            record,reason=normalize(r,kind,source,locator,mapping)
            if reason:
                stats['excluded:'+reason]+=1
                if reason=='nsfw_tagged' and kind=='post':
                    thread=('bra_post:'+r['thread_id']) if source['source_id']=='brazil_threads' else standard_id(r.get('id'),'post')
                    if thread:db.execute('INSERT OR IGNORE INTO blocked_threads VALUES(?)',(thread,))
                continue
            t=record
            cursor=db.execute('INSERT OR IGNORE INTO records VALUES(?,?,?,?,?,?,?,?,?)',
                 (t['id'],t['thread_id'],t['parent_id'],t['country_context_iso3'],t['subreddit'],kind,t['created_at'],t['text_sha256'],dumps(t)))
            stats['unique_inserted' if cursor.rowcount else 'duplicate_id_occurrence']+=1
            if not cursor.rowcount:
                previous=db.execute('SELECT hash,thread,sub FROM records WHERE id=?',(t['id'],)).fetchone()
                conflict=int(previous!=(t['text_sha256'],t['thread_id'],t['subreddit']))
                db.execute('INSERT INTO variants VALUES(?,1,?) ON CONFLICT(id) DO UPDATE SET occurrences=occurrences+1,conflicts=conflicts+excluded.conflicts',(t['id'],conflict))
                stats['conflicting_version_occurrences']+=conflict
            lineage.add({'id':t['id'],'source_id':source['source_id'],'raw_file':source['raw_file'],'raw_sha256':source['sha256'],'locator':locator,'prepared_text_sha256':t['text_sha256']})
        db.commit();files_report.append({'raw_file':source['raw_file'],**dict(stats)})
        print(source['source_id'],path.name,dict(stats),flush=True)
    lineage.close()
    db.execute('CREATE INDEX thread_index ON records(thread)');db.execute('CREATE INDEX country_index ON records(country)')
    # Discard all descendants of a known NSFW root; unknown labels stay explicit.
    nsfw_desc=db.execute('SELECT COUNT(*) FROM records WHERE thread IN (SELECT thread FROM blocked_threads)').fetchone()[0]
    db.execute('DELETE FROM records WHERE thread IN (SELECT thread FROM blocked_threads)');db.commit()
    count=Counter();subs=defaultdict(Counter);dates={};chars=Counter();redactions=Counter();pair_count=Counter();pair_exclusions=Counter()
    doc_writers={c:GzipWriter(output/c/'community-records.jsonl.gz') for c in cm['countries']}
    pair_writers={c:GzipWriter(output/c/'reply-pairs.review.jsonl.gz') for c in cm['countries']}
    review={c:[] for c in cm['countries']}
    # Deterministic audit sample: smallest content-independent ID hashes per country/community.
    samples=defaultdict(list)
    for rid,payload,occ,conflict in db.execute('SELECT r.id,r.payload,coalesce(v.occurrences,0),coalesce(v.conflicts,0) FROM records r LEFT JOIN variants v ON r.id=v.id ORDER BY r.id'):
        r=json.loads(payload);c=r['country_context_iso3'];sub=r['subreddit']
        r['additional_source_occurrences']=occ
        if conflict:r['quality_flags'].append('conflicting_archive_versions')
        doc_writers[c].add(r);count[c]+=1;subs[c][sub]+=1;chars[c]+=len(r['text']);redactions[c]+=bool(r['redactions'])
        if r['created_at']:
            bounds=dates.setdefault(c,[r['created_at'],r['created_at']]);bounds[0]=min(bounds[0],r['created_at']);bounds[1]=max(bounds[1],r['created_at'])
        bucket=samples[(c,sub)];bucket.append((digest(rid),r));bucket.sort(key=lambda x:x[0]);del bucket[10:]
    for child_payload,parent_payload,child_conflicts,parent_conflicts in db.execute('SELECT c.payload,p.payload,coalesce(vc.conflicts,0),coalesce(vp.conflicts,0) FROM records c JOIN records p ON c.parent=p.id LEFT JOIN variants vc ON vc.id=c.id LEFT JOIN variants vp ON vp.id=p.id WHERE c.kind="comment" AND c.thread=p.thread AND c.sub=p.sub ORDER BY c.id'):
        child,parent=json.loads(child_payload),json.loads(parent_payload)
        if child_conflicts or parent_conflicts:pair_exclusions['conflicting_versions']+=1;continue
        if child['created_at'] and parent['created_at'] and child['created_at']<parent['created_at']:
            pair_exclusions['reply_predates_parent']+=1;continue
        if child['text']==parent['text']:pair_exclusions['identical_parent_reply']+=1;continue
        c=child['country_context_iso3']
        pair={'id':'reply:'+child['id'],'country_context_iso3':c,'country_iso3':None,'subreddit':child['subreddit'],
              'thread_id':child['thread_id'],'split_group':child['split_group'],'split':'quarantine','training_admitted':False,
              'record_type':'observed_parent_reply_review_pair','context_status':'direct_parent_only_not_complete_conversation',
              'parent':{'id':parent['id'],'text':parent['text'],'created_at':parent['created_at']},
              'reply':{'id':child['id'],'text':child['text'],'created_at':child['created_at']},
              'source_record_ids':[parent['id'],child['id']],
              'limitations':['Not an endorsed answer or factual gold label','Author identity and nationality unestablished','Earlier thread context may be missing','Independent content and use-rights review required']}
        pair_writers[c].add(pair);pair_count[c]+=1
    for w in list(doc_writers.values())+list(pair_writers.values()):w.close()
    for (c,_),bucket in sorted(samples.items()):review[c].extend(r for _,r in bucket)
    for c,rs in review.items():
        w=GzipWriter(output/c/'audit-sample.jsonl.gz')
        for r in rs:w.add(r)
        w.close()
    exact_duplicate_groups=db.execute('SELECT COUNT(*) FROM (SELECT hash FROM records GROUP BY hash HAVING COUNT(DISTINCT thread)>1)').fetchone()[0]
    kindcounts={c:{k:n for k,n in db.execute('SELECT kind,COUNT(*) FROM records WHERE country=? GROUP BY kind',(c,))} for c in cm['countries']}
    versions=db.execute('SELECT COUNT(*) FROM variants WHERE conflicts>0').fetchone()[0]
    missing_parents=db.execute('SELECT COUNT(*) FROM records c LEFT JOIN records p ON c.parent=p.id WHERE c.kind="comment" AND p.id IS NULL').fetchone()[0]
    report={'release':RELEASE,'country_basis':cm['basis'],'raw_bytes_verified':sum(f['bytes'] for f in manifest['files']),
            'raw_files_verified':len(files),'source_repositories':len(registry['sources']),
            'raw_rows_scanned':sum(f['raw_rows_scanned'] for f in files_report),'unique_prepared_records':sum(count.values()),
            'countries':{c:{'name':v['name'],'records':count[c],'record_types':kindcounts[c],
                'observed_reply_pairs':pair_count[c],'subreddits':dict(sorted(subs[c].items())),
                'date_bounds':dates.get(c),'text_characters':chars[c],'rows_with_pattern_redactions':redactions[c],
                'audit_sample_rows':len(review[c]),'planned_but_unobserved_subreddits':sorted(set(s.lower() for s in v['subreddits'])-set(subs[c]))} for c,v in cm['countries'].items()},
            'known_nsfw_thread_descendants_excluded':nsfw_desc,'conflicting_record_ids':versions,
            'cross_thread_exact_duplicate_text_groups':exact_duplicate_groups,'comments_with_missing_direct_parent':missing_parents,
            'reply_pair_exclusions':dict(pair_exclusions),'files':files_report,'subreddit_id_crosswalk':sub_ids,
            'training_admitted':0,'fresh_evaluation_eligible':False,'sft_or_preference_targets_created':0,
            'coverage_note':registry['selection'],
            'limitations':['Country labels describe communities, not author nationality or representative national opinion.',
                'Dates span discontinuous collections and must not be read as continuous coverage.',
                'Full original thread context is often missing; reply pairs are review material only.',
                'Pattern redaction is not comprehensive anonymization; original IDs remain for provenance.',
                'Current deletion status, consent and training/redistribution rights are unverified.',
                'All records remain quarantine. Merge thread, crosspost and duplicate components before any future split.'],
            'input_sha256':{'manifest':sha(MANIFEST),'community_mapping':sha(MAPPING),'registry':sha(ROOT/'data/reddit_source_registry.json')}}
    db.close()
    report['artifacts']={str(p.relative_to(output)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(output.rglob('*.gz'))}
    (output/'coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'reports/reddit-country-coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('COMPLETE',sum(count.values()),dict(count),'reply pairs',dict(pair_count),flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=OUT)
    build(parser.parse_args().output)
