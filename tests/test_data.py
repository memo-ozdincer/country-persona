import copy
import csv
import json
from pathlib import Path
import pytest
from country_persona.schema import record, validate
from country_persona.parsers import parse_mfa, parse_german_press, parse_mission
from country_persona.prepare import split_records, as_sft, admit
from country_persona.io import write_jsonl,digest
from country_persona.retrieval import create_index, search
from country_persona.train import validated_export

@pytest.fixture
def make_record(tmp_path):
    path=tmp_path/'source.txt';path.write_text('literal source text')
    def make(key='1',when='2025-01-01',text='A source statement with distinct words.',**kwargs):
        r=record('test',key,path,'https://example.org/'+key,'CHN',when,'day','UNSC',
                 'national_representative','statement_reconstruction',text,
                 question='What is the position?',available_date=when)
        r.update(kwargs);return r
    return make

CONFIG={'snapshot_date':'2026-09-09','train_end':'2025-12-31','dev_end':'2026-06-30'}

def test_parent_children_and_dates_share_latest_split(make_record):
    a=make_record('a','2024-01-01');b=make_record('b','2026-08-01',parent_id=a['id'])
    split_records([a,b],CONFIG)
    assert a['split']==b['split']=='test'

def test_exact_mirror_cross_source_grouping(make_record):
    a=make_record('a',text='long source statement '*30)
    b=make_record('b','2026-03-01',text=' LONG  source statement '*30)
    split_records([a,b],CONFIG);assert a['split']==b['split']=='dev'

def test_short_vote_labels_not_grouped(make_record):
    a=make_record('a',text='yes');b=make_record('b','2026-08-01',text='yes')
    split_records([a,b],CONFIG);assert a['split']=='train' and b['split']=='test'

def test_document_symbol_family_and_benchmark_propagates(make_record):
    a=make_record('a',document_symbols=['S/2020/1'])
    b=make_record('b',document_symbols=['S/2020/1'],quality_flags=['benchmark_reserved'])
    split_records([a,b],CONFIG);assert a['split']==b['split']=='test'

def test_future_availability_quarantines_event(make_record):
    a=make_record(available_date='2026-09-10');split_records([a],CONFIG);assert a['split']=='quarantine'

def test_year_precision_is_conservative(make_record):
    a=make_record(when='2026',date_precision='year',available_date=None)
    split_records([a],CONFIG);assert a['split']=='quarantine'

def test_duplicate_id_rejected(make_record):
    with pytest.raises(ValueError,match='Duplicate record ID'):split_records([make_record(),make_record()],CONFIG)

def test_mfa_actual_answer_and_followup(tmp_path):
    p=tmp_path/'press.html'
    p.write_text('''<meta name="ArticleTitle" content="Foreign Ministry Spokesperson Mao Ning’s Regular Press Conference on September 9, 2026"><meta name="PubDate" content="2026-09-09"><div class="content_text"><p><strong>Reporter: First question?</strong></p><p>Mao Ning: First answer.</p><p>Continuation.</p><p><strong>Reporter: Followup?</strong></p><p>Mao Ning: Second answer.</p></div>''')
    rows=parse_mfa({'path':str(p),'url':'https://example.org','title':''})
    assert len(rows)==3 and rows[1]['text']=='First answer.\n\nContinuation.'
    assert rows[2]['history'][1]['content']==rows[1]['text']
    assert rows[2]['group_id']==rows[1]['group_id']
    assert 'Second answer' not in str(as_sft(rows[2])['prompt'])

def test_mfa_unmatched_question_flagged(tmp_path):
    p=tmp_path/'press.html';p.write_text('''<meta name="ArticleTitle" content="Foreign Ministry Spokesperson Mao Ning’s Regular Press Conference on September 9, 2026"><meta name="PubDate" content="2026-09-09"><div class="content_text"><p><strong>A: Missing answer?</strong></p><p><strong>B: Good question?</strong></p><p>Mao Ning: Good answer.</p></div>''')
    r=parse_mfa({'path':str(p),'url':'https://example.org','title':''})
    assert 'unparsed_exchange' in r[-1]['quality_flags']

def test_mfa_declared_non_utf8_encoding_is_preserved(tmp_path):
    p=tmp_path/'press.html'
    html='''<meta charset="windows-1252"><meta name="ArticleTitle" content="Foreign Ministry Spokesperson Mao Ning’s Regular Press Conference on September 9, 2026"><meta name="PubDate" content="2026-09-09"><div class="content_text"><p><strong>Reporter: Question?</strong></p><p>Mao Ning: Café.</p></div>'''
    p.write_bytes(html.encode('windows-1252'))
    rows=parse_mfa({'path':str(p),'url':'https://example.org','title':''})
    assert rows[1]['text']=='Café.' and rows[1]['speaker']=='Mao Ning'

def test_german_only_foreign_office_is_target(tmp_path):
    p=tmp_path/'press.html';p.write_text('''<title>Regierungspressekonferenz</title><div id="rs_reading_area_content"><div class="bpa-richtext"><p class="Rednerkopf">Frage</p><p>First question?</p><p class="Rednerkopf">Other (BMI)</p><p>Domestic answer.</p><p class="Rednerkopf">Zusatzfrage</p><p>Foreign question?</p><p class="Rednerkopf">Giese (AA)</p><p>Foreign answer.</p></div></div>''')
    rows=parse_german_press({'path':str(p),'url':'https://example.org/regierungspressekonferenz-vom-4-september-2026-1'})
    assert len(rows)==2 and rows[1]['text']=='Foreign answer.' and rows[1]['language']=='de'
    ex=as_sft(rows[1]);assert [m['role'] for m in ex['prompt']]==['system','user']
    assert 'Domestic answer' in ex['prompt'][1]['content']

def test_mission_alignment_is_not_coalition(tmp_path):
    p=tmp_path/'g.html';p.write_text('''<meta property="og:title" content="German statement to General Assembly, 1 September 2026"><main>01.09.2026 - Speech<div class="c-rte--default"><p>Germany aligns itself with the statement delivered by the European Union.</p><p>We support international law and the Charter of the United Nations. This is a national statement about peace and security.</p></div></main>''')
    r=parse_mission({'path':str(p),'url':'https://example.org','title':''},'germany_mission')[0]
    assert r['represented_entity']=='Germany'

def test_country_codes_not_unchecked_strings(make_record):
    with pytest.raises(ValueError,match='ISO3'):validate(make_record(country_iso3='Germany'))

def test_manifest_tampering_blocks_admission(tmp_path):
    row={'prompt':[],'completion':[{'role':'assistant','content':'tampered'}]}
    write_jsonl(tmp_path/'data.jsonl',[row]);write_jsonl(tmp_path/'manifest.jsonl',[{'row_index':0,'id':'one','example_sha256':'wrong'}])
    (tmp_path/'ledger.csv').write_text('id,quality_approved,use_permission,reviewer,reason\none,yes,research,Reviewer,verified\n')
    with pytest.raises(ValueError,match='integrity'):admit(tmp_path/'data.jsonl',tmp_path/'manifest.jsonl',tmp_path/'ledger.csv',tmp_path/'out.jsonl')

def test_training_rejects_candidates_before_importing_torch(tmp_path):
    row={'prompt':[],'completion':[{'role':'assistant','content':'answer'}]}
    write_jsonl(tmp_path/'data.jsonl',[row]);write_jsonl(tmp_path/'manifest.jsonl',[{'row_index':0,'example_sha256':digest(row),'status':'candidate_not_training_approved'}])
    with pytest.raises(ValueError,match='admitted'):validated_export(tmp_path/'data.jsonl',tmp_path/'manifest.jsonl','train')

def test_retrieval_blocks_same_event_same_day_and_future(tmp_path,make_record):
    rows=[make_record('prior','2025-01-01',text='Nuclear diplomacy prior source'),
          make_record('same_day','2026-01-01',text='Nuclear diplomacy outcome'),
          make_record('future','2026-01-02',text='Nuclear diplomacy future'),
          make_record('same_group','2024-01-01',text='Nuclear diplomacy same event',group_id='target')]
    for r in rows:r['split']='train'
    write_jsonl(tmp_path/'records.jsonl',rows)
    create_index(tmp_path/'records.jsonl',tmp_path/'index.db')
    results=search(tmp_path/'index.db','nuclear','2026-01-01','target')
    assert [r['id'] for r in results]==['test:prior']

def test_family_override_groups_distinct_documents(make_record):
    a=make_record('a');b=make_record('b','2026-08-01')
    split_records([a,b],CONFIG,{a['id']:'family',b['id']:'family'})
    assert a['split']==b['split']=='test'

def test_upr_cycle_holdout_overrides_calendar(make_record):
    r=make_record(upr_cycle='- Cycle 4')
    split_records([r],{**CONFIG,'upr_cycle_splits':{'4':'test'}})
    assert r['split']=='test'


def test_observed_mixed_upr_response_is_preserved(tmp_path):
    from country_persona.bulk import parse_uhri
    p=tmp_path/'uhri.json'
    raw={'AnnotationId':'x','Symbol':'A/HRC/1','Text':'<p>End discrimination.</p>',
         'DocumentId':'d','PublicationDate':'2024-01-01T00:00:00','AnnotationType':'- Recommendations',
         'Countries':['Germany'],'UprPositions':['Supported/Noted'],'UprSession':['1st Session'],
         'UprRecommendingCountry':['China'],'UprCycle':'- Cycle 4','Body':'- UPR'}
    p.write_text(json.dumps([raw]))
    rec,response=list(parse_uhri(p,True))
    assert rec['country_iso3']=='CHN' and response['country_iso3']=='DEU'
    assert rec['text']=='End discrimination.' and response['text']=='Supported/Noted'

def test_mfa_after_conference_question_and_closing_announcement(tmp_path):
    p=tmp_path/'press.html';p.write_text('''<meta name="ArticleTitle" content="Foreign Ministry Spokesperson Mao Ning’s Regular Press Conference on September 9, 2026"><meta name="PubDate" content="2026-09-09"><div class="content_text"><p><strong>A: Question?</strong></p><p>Mao Ning: First answer.</p><p>The following question was raised after the press conference:</p><p><strong>A question without an outlet label?</strong></p><p>Mao Ning: Second answer.</p><p>********</p><p>Future holiday announcement.</p></div>''')
    rows=parse_mfa({'path':str(p),'url':'https://example.org','title':''})
    assert len(rows)==3 and rows[2]['text']=='Second answer.'
    assert all('Future holiday' not in str(as_sft(r)) for r in rows[1:])


def test_mfa_migration_date_does_not_replace_event_date(tmp_path):
    p=tmp_path/'press.html';p.write_text('''<meta name="ArticleTitle" content="Foreign Ministry Spokesperson Mao Ning’s Regular Press Conference on June 11, 2024"><meta name="PubDate" content="2024-07-30"><div class="content_text"><p><strong>A: Question?</strong></p><p>Mao Ning: Answer.</p></div>''')
    r=parse_mfa({'path':str(p),'url':'https://example.org','title':''})[1]
    assert r['event_date']=='2024-06-11' and r['available_date']=='2024-07-30'
