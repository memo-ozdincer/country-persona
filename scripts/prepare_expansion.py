#!/usr/bin/env python3
"""Build a reviewed-later evidence release, without changing admitted training data."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import subprocess
from country_persona.expansion import parse_briefing,parse_aa,parse_mission_zh,finish,normalized
from country_persona.io import digest,read_jsonl,write_json,write_jsonl,sha256
from country_persona.schema import record,validate

RAW=Path('data/raw/expansion-20260913')
OUT=Path('data/prepared/expansion-20260913')
SOURCES=['mfa_zh','mfa_fr','mfa_es','mfa_ru','china_mission_zh','germany_aa','upr_national_reports','national_policy_documents']
RANK={'quarantine':0,'train':1,'dev':2,'test':3}


def pdf_records(item):
    path=Path(item['path'])
    text=subprocess.run(['pdftotext','-enc','UTF-8',str(path),'-'],check=True,capture_output=True).stdout.decode('utf-8')
    if len(normalized(text))<150:raise ValueError('Insufficient PDF text; OCR required')
    if text.count('\ufffd')>max(3,len(text)*.001):raise ValueError('PDF replacement characters exceed threshold')
    textpath=OUT/'pdf-text'/(path.stem+'.txt');textpath.parent.mkdir(parents=True,exist_ok=True);textpath.write_text(text)
    upr=item['source_id']=='upr_national_reports'
    when=({'CHN':'2023-11-03','DEU':'2023-09-01'}[item['country']] if upr else item['document_date'])
    group='un:document:'+item['symbol'] if upr else 'policy:'+item['group_id']
    flags=['pdf_reading_order_review','translation_publication_date_unverified']
    if upr and item['country']=='CHN':flags.append('report_reissued_2024_01_16; verify_each_language_version')
    title='UPR national report '+item['symbol'] if upr else item['title']
    r=record(item['source_id'],path.stem,path,item['url'],item['country'],when,'day',
        'UN_HRC_UPR' if upr else item.get('institution','national_government'),'national_submission' if upr else 'coalition_submission' if item.get('country') is None else 'national_policy_document',
        'policy_evidence',text,title,group=group,language=item['language'],raw_hash=item['sha256'],flags=flags,represented_entity=item.get('represented_entity'))
    summary=(not upr and item['group_id']=='germany_security_strategy' and (item['language'] not in ('en','de','fr','es') or item.get('variant')=='summary'))
    if summary:r['quality_flags'].append('executive_summary_not_full_strategy')
    r.update(document_type='national_report' if upr else 'strategy_summary' if summary else 'strategy_or_white_paper',
        translation_scope='summary' if summary else 'full_document',
        document_symbols=[item['symbol']] if upr else [],event_date_basis='document_issue_date' if upr else item['date_basis'],
        translation_group=group+(':summary' if summary else ':full'),translation_group_basis='same_UN_document_symbol' if upr else 'same_publisher_linked_strategy',
        translation_status='publisher_language_version; original_language_requires_header_review',
        extracted_text_file=str(textpath),extraction_method='Poppler pdftotext UTF-8 default reading order',
        pdf_pages=len(text.rstrip('\f\n').split('\f')),extracted_text_sha256=sha256(textpath))
    finish(r,item)
    if upr:r.update(proposed_split='test',upr_cycle=4,split_policy='existing_cycle_4_holdout_overrides_document_date')
    return [r]


def long_paragraphs(text):
    return [normalized(p) for p in text.split('\n\n') if len(normalized(p))>=160]


def chunks(doc,cap=3000):
    # Exact character spans of the canonical document; preserve PDF page provenance.
    start=0
    while start<len(doc['text']):
        end=min(start+cap,len(doc['text']))
        if end<len(doc['text']):
            boundary=max(doc['text'].rfind('\n\n',start+cap//2,end),doc['text'].rfind('\n',start+cap//2,end))
            if boundary>start:end=boundary
        while start<end and doc['text'][start].isspace():start+=1
        while end>start and doc['text'][end-1].isspace():end-=1
        if end<=start:break
        text=doc['text'][start:end]
        if len(normalized(text))>=100:
            yield dict(id=doc['id']+f':span:{start}:{end}',parent_id=doc['id'],group_id=doc['group_id'],
                source_id=doc['source_id'],source_url=doc['source_url'],raw_sha256=doc['raw_sha256'],
                language=doc['language'],country_iso3=doc['country_iso3'],represented_entity=doc['represented_entity'],
                event_date=doc['event_date'],available_date=doc['available_date'],proposed_split=doc['proposed_split'],
                task='retrieval_evidence',text=text,start_char=start,end_char=end,
                pdf_start_page=doc['text'][:start].count('\f')+1 if 'pdf_pages' in doc else None,
                pdf_end_page=doc['text'][:end].count('\f')+1 if 'pdf_pages' in doc else None,
                training_admitted=False,review_status='pending',quality_flags=doc['quality_flags'])
        start=end
        while start<len(doc['text']) and doc['text'][start].isspace():start+=1


def main():
    p=argparse.ArgumentParser();p.add_argument('--allow-incomplete',action='store_true');args=p.parse_args()
    docs=[];qas=[];errors=[];manifests=[];missing=[]
    for source in SOURCES:
        path=RAW/source/'collection.json'
        if not path.exists():missing.append(source);continue
        collection=json.loads(path.read_text());errors += [dict(e,source_id=source,stage='acquisition') for e in collection.get('errors',[])]
        for item in collection['documents']:
            try:
                if sha256(item['path'])!=item['sha256']:raise ValueError('Raw hash mismatch')
                if source.startswith('mfa_'): rows=parse_briefing(item)
                elif source=='germany_aa':rows=parse_aa(item)
                elif source=='china_mission_zh':rows=parse_mission_zh(item)
                else:rows=pdf_records(item)
                for r in rows:
                    validate(r)
                    (qas if r['task']=='authentic_qa' else docs).append(r)
                manifests.append(dict(item,canonical_id=rows[0]['id'],parse_status='parsed',qa_count=len(rows)-1))
            except Exception as exc:
                errors.append(dict(source_id=source,url=item['url'],path=item['path'],stage='parsing',error=str(exc)))
                manifests.append(dict(item,parse_status='excluded'))
    if missing and not args.allow_incomplete:raise ValueError('Missing acquisition manifests: '+str(missing))
    # Previous published train/dev/test allocations remain immutable. Cross-release
    # matches are recorded rather than silently reassigning the old experiment.
    previous_groups=defaultdict(set);previous_text={};previous_paragraphs=defaultdict(set)
    for r in read_jsonl('data/prepared/pilot/pilot.canonical.jsonl'):
        previous_groups[r['group_id']].add(r['split'])
        previous_text[digest(normalized(r['text']))]=dict(id=r['id'],split=r['split'])
        if r['split'] in ('dev','test'):
            for p in long_paragraphs(r['text']):previous_paragraphs[digest(p)].add(r['split'])
    group_ranks=defaultdict(int);group_previous=defaultdict(set);seen={};duplicate_docs=0;protected_overlap=0
    for r in docs:
        overlap=previous_groups.get(r['group_id'],set())
        r['existing_event_splits']=sorted(overlap)
        r['fresh_evaluation_eligible']=not bool(overlap&{'train','dev'})
        if 'train' in overlap:r['quality_flags'].append('overlaps_existing_training_event')
        exact=previous_text.get(r['text_sha256'])
        if exact:
            r['duplicate_of']=exact['id'];r['quality_flags'].append('normalized_exact_duplicate_existing_release')
            duplicate_docs+=1;overlap=set(overlap)|{exact['split']}
        if r['text_sha256'] in seen:
            r['duplicate_of']=seen[r['text_sha256']];r['quality_flags'].append('normalized_exact_duplicate_expansion')
            duplicate_docs+=1
        seen[r['text_sha256']]=r['id']
        protected=set().union(*(previous_paragraphs.get(digest(p),set()) for p in long_paragraphs(r['text'])))
        if protected:
            r['quality_flags'].append('long_paragraph_overlap_existing_holdout');protected_overlap+=1
        group_previous[r['group_id']].update(overlap)
        ranks=[RANK[r['proposed_split']]]+[RANK[s] for s in overlap|protected]
        group_ranks[r['group_id']]=max(group_ranks[r['group_id']],*ranks)
    inv={v:k for k,v in RANK.items()};byid={r['id']:r for r in docs}
    for r in docs:
        r['proposed_split']=inv[group_ranks[r['group_id']]]
        r['existing_event_splits']=sorted(group_previous[r['group_id']])
        r['fresh_evaluation_eligible']=not bool(group_previous[r['group_id']]&{'train','dev'})
    for r in qas:
        parent=byid[r['parent_id']]
        for k in ('proposed_split','existing_event_splits','fresh_evaluation_eligible'):
            r[k]=parent[k]
        r['quality_flags']=sorted(set(r['quality_flags']+parent['quality_flags']))
    # De-duplicate QA within this candidate release, retaining a traceable mapping.
    qseen={};uniqueqas=[];qa_dupes=[]
    for r in qas:
        key=digest([r['country_iso3'],r['language'],normalized(r['question']),normalized(r['text'])])
        if key in qseen:qa_dupes.append(dict(id=r['id'],duplicate_of=qseen[key]))
        else:qseen[key]=r['id'];uniqueqas.append(r)
    docs.sort(key=lambda r:r['id']);uniqueqas.sort(key=lambda r:r['id'])
    evidence=list(c for r in docs if 'duplicate_of' not in r for c in chunks(r))
    for c in evidence:
        parent=byid[c['parent_id']]
        assert c['text']==parent['text'][c['start_char']:c['end_char']]
    write_jsonl(OUT/'documents.jsonl',docs);write_jsonl(OUT/'authentic-qa.candidates.jsonl',uniqueqas)
    write_jsonl(OUT/'evidence-passages.jsonl',evidence)
    families=defaultdict(list)
    for r in docs:families[r.get('translation_group',r['group_id'])].append(r)
    familyrows=[dict(group_id=g,languages=sorted({r['language'] for r in rows}),document_ids=[r['id'] for r in rows],
                    proposed_splits=sorted({r['proposed_split'] for r in rows}),
                    alignment_status='document/event grouping only; sentence equivalence unreviewed') for g,rows in sorted(families.items())]
    write_jsonl(OUT/'document-families.jsonl',familyrows)
    write_json('data/manifests/expansion-20260913.json',dict(snapshot_date='2026-09-13',sources=SOURCES,missing_sources=missing,
        documents=manifests,errors=errors,qa_duplicates=qa_dupes,exhaustive=False))
    counts={s:dict(acquired=sum(x['source_id']==s for x in manifests),parsed_documents=sum(r['source_id']==s for r in docs),
        qa_candidates=sum(r['source_id']==s for r in uniqueqas),languages=sorted({r['language'] for r in docs if r['source_id']==s}),
        proposed_splits=dict(Counter(r['proposed_split'] for r in docs if r['source_id']==s))) for s in SOURCES}
    stats=dict(snapshot_date='2026-09-13',sources=counts,parsed_documents=len(docs),authentic_qa_candidates=len(uniqueqas),
        evidence_passages=len(evidence),languages=sorted({r['language'] for r in docs}),document_event_groups=len({r['group_id'] for r in docs}),
        multilingual_families=sum(len(r['languages'])>1 for r in familyrows),normalized_exact_duplicate_documents=duplicate_docs,
        documents_with_long_paragraph_holdout_overlap=protected_overlap,duplicate_qa_removed=len(qa_dupes),
        documents_overlapping_existing_training_event=sum('train' in r['existing_event_splits'] for r in docs),
        training_admitted=0,errors_by_source=dict(Counter(e['source_id'] for e in errors)),missing_sources=missing,
        checks=dict(raw_hashes_verified=True,qa_normalized_source_spans=True,evidence_character_spans=True,
                    existing_training_release_modified=False,semantic_deduplication_complete=False,expert_review_complete=False),
        artifacts={p.name:dict(bytes=p.stat().st_size,sha256=sha256(p)) for p in OUT.glob('*.jsonl')})
    write_json('reports/expansion-20260913.json',stats)
    print(json.dumps(stats,indent=2))

if __name__=='__main__':main()
