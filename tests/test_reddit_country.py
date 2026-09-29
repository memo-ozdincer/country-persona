import importlib.util
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('reddit_country',ROOT/'scripts/prepare_reddit_country.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
SOURCE={'source_id':'test','repository':'publisher/data','revision':'abc','source_path':'file','sha256':'a'*64,'retrieved_at':'2026-09-23'}
MAP={'india':('IND','Country-focused community'),'france':('FRA','Country-focused community')}


def test_community_context_does_not_infer_nationality():
    r,reason=m.normalize({'id':'abc','subreddit':'India','title':'A sufficiently long community question about local transport','created_utc':1500000000},'post',SOURCE,{},MAP)
    assert reason is None and r['country_context_iso3']=='IND'
    assert r['country_iso3'] is None and r['represented_entity'] is None
    assert not r['training_admitted'] and r['split']=='quarantine'
    assert 'author' not in r and r['language'] is None


def test_names_are_exact_not_substring_or_language():
    for sub in ['Indiana','FrancaisCanadien']:
        r,reason=m.normalize({'subreddit':sub,'title':'A long post with enough length to survive the text filter'},'post',SOURCE,{},MAP)
        assert r is None and reason=='unmapped_community'


def test_deleted_content_nsfw_and_automoderator_excluded():
    base={'id':'abc','subreddit':'india','title':'A long post with enough length to survive the text filter'}
    for extra,reason in [({'selftext':'[removed]'},'deleted_or_removed_body'),({'over_18':'True'},'nsfw_tagged'),({'author':'AutoModerator'},'deleted_or_automoderator_author'),({'author':'[deleted]'},'deleted_or_automoderator_author')]:
        r,actual=m.normalize({**base,**extra},'post',SOURCE,{},MAP)
        assert r is None and actual==reason
    assert m.truth('False') is False


def test_identifiers_redacted_without_changing_policy_numbers():
    s,flags=m.clean_text('Contact /u/example, x@example.com or +1 (416) 555-1234; target 45% in 2030 from 2005.')
    assert 'example' not in s and '555' not in s
    assert '45% in 2030 from 2005' in s
    assert set(flags)=={'user_handle','email','phone'}


def test_brazil_pseudonyms_never_become_reddit_permalink():
    row={'thread_id':'uuid-a','comment_id':'uuid-b','parent_id':'uuid-a','subreddit':'india','body':'A sufficiently long observed reply that should be kept for review','created_utc':'2025-04-01 12:00:00'}
    r,reason=m.normalize(row,'comment',{**SOURCE,'source_id':'brazil_threads'},{},MAP)
    assert not reason and r['parent_id']==r['thread_id']=='bra_post:uuid-a'
    assert r['source_url'] is None and r['created_at']=='2025-04-01T12:00:00Z'


def test_xml_keeps_parent_tree_and_excludes_unmapped_subreddit(tmp_path):
    p=tmp_path/'sample.xml';p.write_text('<dialog><s link_id="post" subreddit_id="xyz"><utt comment_id="one" parent_id="post" create_utc="100">first long content</utt><utt comment_id="two" parent_id="one" create_utc="101">second long content</utt></s><s link_id="other" subreddit_id="unknown"><utt comment_id="three">Canadian text</utt></s></dialog>')
    stats=m.Counter();rs=list(m.iter_xml(p,{'xyz':'france'},stats))
    assert [r[0]['parent_id'] for r in rs]==['t3_post','t1_one']
    assert stats['unmapped_xml_subreddit:unknown']==1
    assert rs[1][0]['created_utc']=='101'


def test_parquet_selection_preserves_physical_row_number(tmp_path):
    p=tmp_path/'sample.parquet'
    m.pq.write_table(m.pa.table({'subreddit':[None,'india','Indiana','France'],'subreddit_id':[None,'t5_ind','t5_us','t5_fra']}),p)
    ids={};stats=m.Counter();rs=list(m.iter_parquet(p,MAP,ids,stats))
    assert [r[2]['parquet_row_index'] for r in rs]==[1,3]
    assert ids=={'ind':'india','fra':'france'} and stats['raw_rows_scanned']==4


def test_illegal_xml_controls_are_removed_and_counted(tmp_path):
    p=tmp_path/'broken.xml'
    p.write_bytes(b'<dialog><s link_id="abc" subreddit_id="xyz"><utt comment_id="one" parent_id="abc" create_utc="100">some te\x05xt</utt></s></dialog>')
    stats=m.Counter();rs=list(m.iter_xml(p,{'xyz':'france'},stats))
    assert rs[0][0]['body']=='some text'
    assert stats['xml_illegal_control_bytes_removed']==1
    assert rs[0][0]['_xml_control_filter'] is True
