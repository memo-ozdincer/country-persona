"""Check every prepared row, provenance link, country mapping and reply boundary."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def rows(p):
    with gzip.open(p,'rt') as f:
        for line in f:yield json.loads(line)


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()


def require(ok,message):
    if not ok:raise ValueError(message)


def validate(output):
    report=json.loads((output/'coverage.json').read_text())
    mapping=json.loads((ROOT/'data/curation/reddit_country_communities.json').read_text())['countries']
    manifest=json.loads((ROOT/'data/manifests/reddit-country-20260923.json').read_text())
    receipts={(r['source_id'],r['source_path']):r['sha256'] for r in manifest['files']}
    counts={};pairs={};total=0
    for rel,item in report['artifacts'].items():
        p=output/rel;require(p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],'Artifact integrity: '+rel)
    for c,expected in report['countries'].items():
        seen={};subs=Counter()
        allowed={s.lower() for s in mapping[c]['subreddits']}
        for r in rows(output/c/'community-records.jsonl.gz'):
            require(r['id'] not in seen,'Duplicate record ID')
            require(r['country_context_iso3']==c and r['country_iso3'] is None and r['represented_entity'] is None,'National attribution error')
            require(r['subreddit'] in allowed,'Subreddit mapping error')
            require('author' not in r and 'author_fullname' not in r and 'uid' not in r,'Author field retained')
            require(r['split']=='quarantine' and r['training_admitted'] is False,'Unexpected admission')
            require(r['text_sha256']==hashlib.sha256(r['text'].encode()).hexdigest(),'Text hash mismatch')
            require(len(r['text'])>=40,'Short text passed filter')
            require(receipts[(r['source_id'],r['source_file'])]==r['raw_sha256'],'Invalid source receipt')
            require(r['split_group']=='reddit-thread:'+r['thread_id'],'Thread grouping mismatch')
            seen[r['id']]=(r['thread_id'],r['parent_id'],r['text_sha256'],r['created_at'],r['subreddit'])
            subs[r['subreddit']]+=1
        n=0
        for p in rows(output/c/'reply-pairs.review.jsonl.gz'):
            parent,child=p['parent'],p['reply'];a,b=seen[parent['id']],seen[child['id']]
            require(a[0]==b[0]==p['thread_id'] and b[1]==parent['id'],'Reply linked to wrong parent or thread')
            require(a[4]==b[4]==p['subreddit'],'Reply crosses communities')
            require(a[2]==hashlib.sha256(parent['text'].encode()).hexdigest() and b[2]==hashlib.sha256(child['text'].encode()).hexdigest(),'Reply text mismatch')
            require(not a[3] or not b[3] or a[3]<=b[3],'Future parent in pair')
            require(p['training_admitted'] is False and p['country_iso3'] is None,'Pair attribution or admission error')
            require(p['context_status']=='direct_parent_only_not_complete_conversation','Missing context warning')
            n+=1
        require(len(seen)==expected['records'] and dict(subs)==expected['subreddits'],'Coverage totals differ')
        require(n==expected['observed_reply_pairs'],'Reply counts differ')
        counts[c]=len(seen);pairs[c]=n;total+=len(seen)
    require(total==report['unique_prepared_records'],'Total count differs')
    result={'status':'passed','records_checked':total,'records_by_country':counts,'reply_pairs_by_country':pairs,
            'artifact_hashes_checked':len(report['artifacts']),'checks':['source receipts','exact community mapping','no author identity fields','quarantine admission','deduplicated record IDs','text hashes','direct parent joins','reply chronology'],
            'limitations':'These checks do not validate truth, consent, current deletion status, comprehensive anonymization or training rights.'}
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path)
    args=parser.parse_args();r=validate(args.output)
    (ROOT/'reports/reddit-country-validation.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2))
