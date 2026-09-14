import importlib.util
import json
from pathlib import Path
import pytest

pytest.importorskip('pyarrow', reason='Install the catalog extra to test publication builds')
ROOT=Path(__file__).parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
catalog=module('catalog_build','scripts/build_data_catalog.py')
app=module('catalog_app','explorer/app.py')

def test_public_projection_does_not_republish_source_qa():
    source={'id':'x','country_iso3':'DEU','title':'A statement','text':'RESTRICTED_BODY','question':'RESTRICTED_QUESTION','history':['RESTRICTED_HISTORY'],'source_url':'https://example.org','split':'train'}
    row=catalog.normalize(source,'data/prepared/pilot/pilot.canonical.jsonl',1)
    assert 'RESTRICTED_' not in json.dumps(row)
    assert row['readiness']=='not_recorded' and row['split']=='train'

def test_missing_statistic_and_joint_institution_are_preserved():
    r=catalog.normalize({'id':'f','countries':['FRA','DEU'],'represented_entity':'European Union','indicator':'GDP','value':None,'missing':True,'training_admitted':False},'data/prepared/test/facts.jsonl',1)
    assert r['countries']==['FRA','DEU'] and r['details']['represented_entity']=='European Union'
    assert r['details']['missing'] and r['details']['value'] is None

def test_filters_bind_user_input_including_fts_and_collection_membership():
    sql,params=app.query({'q':'x" OR 1=1','country':'IND','release':'pilot','topic':'climate_environment'})
    assert 'record_collections' in sql and 'record_topics' in sql
    assert 'OR 1=1' not in sql and 'IND' in params

def test_changed_local_source_fails_closed(tmp_path,monkeypatch):
    p=tmp_path/'data.jsonl';p.write_text('{"id":"changed"}\n')
    monkeypatch.setattr(app,'LOCAL',tmp_path)
    row={'uid':'a'*64,'locations':[{'path':p.name,'offset':0,'length':p.stat().st_size}]}
    with pytest.raises(ValueError,match='Source changed'):app.original(row)

def test_final_votes_and_negotiation_conditions_are_not_confused():
    path=ROOT/'data/prepared/decision-cases-20260914/cases.jsonl'
    if not path.exists():pytest.skip('Private source snapshot not restored')
    rows=[json.loads(s) for s in path.open()]
    oct_rows=[r for r in rows if r['resolution_symbol']=='A/RES/ES-11/4']
    assert len(oct_rows)==6 and {r['event_date'] for r in oct_rows}=={'2022-10-12'}
    india=next(r for r in oct_rows if r['country_iso3']=='IND');brazil=next(r for r in oct_rows if r['country_iso3']=='BRA')
    assert india['observed_action']=='abstaining'
    assert brazil['observed_action']=='in favor' and brazil['requested_changes']
    assert brazil['conditions_for_agreement'] is None and 'not a necessary condition' in brazil['conditions_status']
    assert all(not r['training_admitted'] and not r['fresh_evaluation_eligible'] for r in rows)


def test_year_only_observation_is_included_in_its_calendar_year():
    import sqlite3
    db=sqlite3.connect(':memory:')
    db.execute('CREATE TABLE records(date TEXT)')
    db.executemany('INSERT INTO records VALUES (?)',[('2020',),('2020-05',),('2020-12-31',),('2019',),('',)])
    sql,args=app.query({'after':'2020-01-01','before':'2020-12-31'})
    assert db.execute('SELECT COUNT(*) FROM records r'+sql,args).fetchone()[0]==3
