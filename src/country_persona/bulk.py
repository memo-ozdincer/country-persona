"""Inspected bulk formats; never equate dataset country labels with speech attribution."""
from __future__ import annotations
import json
from bs4 import BeautifulSoup
import re
from collections import Counter
from pathlib import Path
from .schema import record, topics
from .io import sha256


def parse_unga_rdata(path, url, meeting_dates=None, dates_source=None):
    import pyreadr
    path=Path(path);file_hash=sha256(path)
    date_provenance={'raw_file':str(dates_source),'raw_sha256':sha256(dates_source)} if dates_source else None
    table=pyreadr.read_r(str(path))['txtstatesyears']
    required={'doc_id','text','country','meeting','session','year','stateabb','words_spoken'}
    if set(table.columns)!=required:raise ValueError('UNGA RData schema changed')
    for raw in table.to_dict('records'):
        country={'China':'CHN','Germany':'DEU'}.get(raw['country'])
        year=str(raw['year']);session=int(raw['session']);meeting=int(raw['meeting'])
        group=f'unga:meeting:{session}:{meeting}'
        symbol=f'A/{session}/PV.{meeting}'
        when=(meeting_dates or {}).get(symbol,year)
        precision='day' if len(when)==10 else 'year'
        flags=['upstream_speaker_segmentation_unverified','year_precision_only']
        r=record('unga_speech_corpus',raw['doc_id'],path,url,country,when,precision,'UNGA',
                 'unverified_speaker','unverified_speech_segment',raw['text'],
                 f'UNGA A/{session}/PV.{meeting}',group=group,raw_hash=file_hash,flags=flags,
                 represented_entity=raw['country'])
        r.update(country_name=raw['country'],upstream_country_code=raw['stateabb'],
                 upstream_words_spoken=raw['words_spoken'],session=session,meeting=meeting,
                 document_symbols=[f'A/{session}/PV.{meeting}'])
        if precision=='day':
            r['quality_flags'].remove('year_precision_only')
            r['meeting_date_provenance']=date_provenance
            if when[:4]!=year:r['quality_flags'].append('upstream_year_conflicts_with_meeting_date')
        yield r
        if country:
            # Require a literal target-country speaker marker, preserving offsets into the original text.
            marker=re.search(r'\('+re.escape(raw['country'])+r'\)\s*(?:\([^)]{0,100}\)\s*)?:',raw['text'])
            if not marker:continue
            start=marker.end()
            tail=raw['text'][start:]
            stop=re.search(r'\n\s*(?:(?:The (?:Acting )?President|The (?:Vice-)?President|The Secretary-General)\s*:|(?:Mr\.|Ms\.|Mrs\.|M\.)[^\n]{0,120}\([^\n)]{2,80}\)[^\n:]{0,100}:)',tail)
            end=start+(stop.start() if stop else len(tail))
            speech=raw['text'][start:end].strip()
            if len(speech)<150:continue
            coalition=bool(re.search(r'on behalf of (?:the )?(?:European Union|Group|Nordic|\d+)',speech[:1800],re.I))
            flags=['year_precision_only','speaker_boundary_rule_requires_review','meeting_agenda_missing']
            if coalition:flags.append('coalition_attribution_review')
            derived=record('unga_speech_corpus',raw['doc_id']+':speaker',path,url,country,when,precision,
                           'UNGA','coalition_representative' if coalition else 'national_representative',
                           'statement_reconstruction',speech,r['title'],group=group,raw_hash=file_hash,flags=flags,
                           represented_entity='coalition_requires_attribution' if coalition else raw['country'])
            derived.update(parent_id=r['id'],source_char_span=[start,end],derivation='speaker_span_extraction',
                           document_symbols=r['document_symbols'],session=session,meeting=meeting)
            if precision=='day':
                derived['quality_flags'].remove('year_precision_only')
                derived['meeting_date_provenance']=date_provenance
                if when[:4]!=year:derived['quality_flags'].append('upstream_year_conflicts_with_meeting_date')
            yield derived


def parse_uhri(path, countries_only=False):
    import ijson
    path=Path(path);file_hash=sha256(path)
    with path.open('rb') as f:
        for raw in ijson.items(f,'item'):
            required={'AnnotationId','Symbol','Text','DocumentId','PublicationDate','AnnotationType','Countries',
                      'UprPositions','UprSession','UprRecommendingCountry','UprCycle','Body'}
            if not required.issubset(raw):raise ValueError('UHRI export schema changed')
            reviewed=raw['Countries'];authors=raw['UprRecommendingCountry']
            if countries_only and not {'China','Germany'}.intersection(reviewed+authors):continue
            text=BeautifulSoup(raw['Text'], 'html.parser').get_text(' ', strip=True) if re.search(r'</?(?:p|div|br|span|strong)\b',raw['Text']) else raw['Text']
            if not text.strip():continue
            when=(raw['PublicationDate'] or '')[:10]
            available=(raw.get('PublicationDateOnUhri') or '')[:10] or None
            body=raw['Body'];upr=bool(raw['UprCycle'] is not None or raw['UprSession'] or authors)
            # Keep non-UPR material as institutional evidence. It is not a country's voice.
            country={'China':'CHN','Germany':'DEU'}.get(authors[0]) if len(authors)==1 else None
            task='upr_recommendation' if upr and authors else 'human_rights_evidence'
            flags=['document_date_not_review_date','recommendation_context_missing'] if task=='upr_recommendation' else []
            if len(authors)>1:flags.append('multiple_recommending_states')
            if not when:flags.append('missing_event_date')
            r=record('uhri',raw['AnnotationId'],path,'https://uhri.ohchr.org/en/our-data-api',
                     country,when,'day' if when else 'unknown','UN_Human_Rights_Council_UPR' if upr else 'OHCHR_'+body,
                     'recommending_state' if authors else 'human_rights_mechanism',task,text,raw['Symbol'],
                     group='uhri:document:'+raw['DocumentId'],raw_hash=file_hash,available_date=available,
                     represented_entity=authors[0] if len(authors)==1 else ('; '.join(authors) if authors else body),flags=flags)
            r.update(question=('State the recorded recommendation to '+', '.join(reviewed)+'.' if authors else ''), document_symbols=[raw['Symbol']],reviewed_states=reviewed,recommending_states=authors,
                     response_labels=raw['UprPositions'],upr_session=raw['UprSession'],upr_cycle=raw['UprCycle'],
                     mechanism=body,annotation_type=raw['AnnotationType'],topics=raw.get('Themes',[]),
                     topic_method='upstream_OHCHR',affected_persons=raw.get('AffectedPersons',[]),sdgs=raw.get('Sdgs',[]))
            yield r
            # A response target belongs to the reviewed state, never to the recommender.
            labels=raw['UprPositions']
            if upr and len(reviewed)==1 and len(authors)==1 and len(labels)==1:
                label=labels[0]
                target={'China':'CHN','Germany':'DEU'}.get(reviewed[0])
                if target:
                    response=record('uhri',raw['AnnotationId']+':response',path,r['source_url'],target,when,
                                    r['date_precision'],'UN_Human_Rights_Council_UPR','state_under_review',
                                    'upr_response',str(label),raw['Symbol'],question=text,
                                    group=r['group_id'],raw_hash=file_hash,available_date=available,
                                    represented_entity=reviewed[0],flags=['response_date_unverified','recommendation_context_missing'])
                    response.update(parent_id=r['id'],recommending_states=authors,reviewed_states=reviewed,
                                    upr_cycle=raw['UprCycle'],upr_session=raw['UprSession'],
                                    document_symbols=r['document_symbols'],derivation='observed_response_label',
                                    context='Recommending state: '+authors[0])
                    yield response


def parse_unbench(root):
    import csv
    from datetime import datetime
    root=Path(root)
    def day(s):
        for fmt in ('%Y-%m-%d','%d %B %Y','%d %b %Y'):
            try:return datetime.strptime(s,fmt).date().isoformat()
            except ValueError:pass
        raise ValueError(f'Unrecognized benchmark date: {s}')
    path=root/'data/task2.csv';hash_=sha256(path)
    with path.open(encoding='utf-8-sig') as f:
        for raw in csv.DictReader(f):
            files=[p for p in (root/'data/task2'/raw['Original_id']).glob('*.json') if not p.name.endswith('.receipt.json')]
            if len(files)!=1:raise ValueError('Ambiguous or missing UNBench draft')
            draft=json.loads(files[0].read_text());label={'Y':'yes','N':'no','A':'abstain'}[raw['Voting']]
            country={'China':'CHN','Germany':'DEU','United States':'USA','Russia':'RUS','Russian Federation':'RUS','France':'FRA','United Kingdom':'GBR'}.get(raw['Country'].title())
            r=record('unbench',raw['Original_id']+':'+raw['Country'],path,'https://github.com/yueqingliang1/UNBench',
                     country,day(raw['Date']),'day','UNSC','voting_member','vote_prediction',label,draft['Title'],
                     question='Predict the recorded vote. Reply exactly yes, no, or abstain.',
                     group='unsc:draft:'+draft['ID'],raw_hash=hash_,flags=['benchmark_reserved','draft_availability_unverified'],
                     represented_entity=raw['Country'])
            r.update(context=draft['Content'],document_symbols=[draft['ID']],country_name=raw['Country'],
                     draft_provenance={'raw_file':str(files[0]),'raw_sha256':sha256(files[0]),'date':draft['Date']},
                     split='test')
            yield r
    path=root/'data/task4.json';hash_=sha256(path)
    for item in json.loads(path.read_text()):
        for i,s in enumerate(item['Statements']):
            r=record('unbench',item['ID']+':statement:'+str(i),path,'https://github.com/yueqingliang1/UNBench',
                     {'China':'CHN','Germany':'DEU'}.get(s['country']),day(item['Date']),'day','UNSC','unverified_speaker',
                     'statement_reconstruction',s['statement'],item.get('Title',item['ID']),
                     group='unsc:draft:'+item['ID'],raw_hash=hash_,flags=['benchmark_reserved','phase_unverified'],
                     represented_entity=s['country'])
            r.update(context=item['Content'],speaker=s['representative'],country_name=s['country'],
                     document_symbols=[item['ID']],split='test')
            yield r


def unga_meeting_dates(votes_path):
    import csv
    from collections import defaultdict
    from datetime import date
    dates=defaultdict(set)
    with Path(votes_path).open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            date.fromisoformat(row['meeting_date'])
            dates[row['meeting_record_id']].add(row['meeting_date'])
    if any(len(v)>1 for v in dates.values()):raise ValueError('Conflicting UNGA meeting dates')
    return {key:next(iter(values)) for key,values in dates.items()}


def parse_unga_dm(path):
    import csv
    path=Path(path);hash_=sha256(path)
    labels={'in favor','against','abstaining','not voting','not voting (suspended)'}
    with path.open(encoding='utf-8-sig',newline='') as f:
        for raw in csv.DictReader(f):
            if raw['current_seat_name'] not in ('China','Germany'):continue
            country={'China':'CHN','Germany':'DEU','West Germany':'DEU','East Germany':'DDR'}.get(raw['member_state'])
            flags=['proposal_text_missing']
            if raw['member_state']=='Republic of China':flags+=['not_PRC_training','historical_entity_review']
            if raw['member_state'] in ('West Germany','East Germany'):flags.append('historical_entity_review')
            if raw['original_vote'] not in labels or raw['amended_vote'] not in labels:raise ValueError('Unknown vote label')
            r=record('unga_dm',raw['decision_id']+':'+raw['member_state_id'],path,
                     'https://unvotes.unige.ch/',country,raw['meeting_date'],'day','UNGA',
                     'voting_member','vote_label_only',raw['original_vote'],raw['decision_id'],
                     group='unga:decision:'+raw['decision_id'],raw_hash=hash_,
                     represented_entity=raw['member_state'],flags=flags)
            r.update(country_name=raw['member_state'],original_vote=raw['original_vote'],
                     amended_vote=raw['amended_vote'],vote_was_amended=raw['vote_was_amended'],
                     original_seat_name=raw['original_seat_name'],current_seat_name=raw['current_seat_name'],
                     member_state_id=raw['member_state_id'],decision_topic=raw['decision_topic'],
                     decision_mode=raw['decision_mode'],session_id=raw['session_id'],
                     meeting_record_id=raw['meeting_record_id'],draft_resolution_id=raw['draft_resolution_id'],
                     resolution_id=raw['resolution_id'],
                     document_symbols=[x for x in (raw['meeting_record_id'],raw['draft_resolution_id'],raw['resolution_id']) if x and x not in ('NA','NULL','not available')])
            yield r
