"""Source corruption, leakage and completion-boundary regression checks."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]

def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

b=load('build_policy_workshop')
v=load('validate_policy_workshop')


def test_connected_teams_merge_transitively_and_keep_unrelated_separate():
    evidence={k:{'source_split_group':g} for k,g in [('a','x'),('b','x'),('c','y'),('d','z'),('e','q')]}
    components=b.component_map(evidence,[{'case_ids':['b','c']},{'case_ids':['c','d']}])
    assert components['a']==components['b']==components['c']==components['d']
    assert components['e']!=components['a']


@pytest.fixture
def source(tmp_path):
    text='Page one.\fEvidence here.'
    (tmp_path/'raw.pdf').write_bytes(b'raw-document')
    (tmp_path/'text.txt').write_text(text)
    e={'document_id':'doc','text_file':'text.txt','text_sha256':b.file_hash(tmp_path/'text.txt'),
       'raw_sha256':b.file_hash(tmp_path/'raw.pdf'),'source_url':'https://example.org/doc',
       'char_start':10,'char_end':len(text),'pdf_start_page':2,'pdf_end_page':2,'language':'en'}
    p={'id':'FRA-case','countries':['FRA'],'evidence':e,'date':'2025','split_group':'g','proposed_split':'train',
       'split':'quarantine','training_admitted':False}
    d={'id':'doc','country_iso3':'FRA','split_group':'g','extracted_text_file':'text.txt',
       'extracted_text_sha256':e['text_sha256'],'raw_file':'raw.pdf','raw_sha256':e['raw_sha256'],
       'source_url':e['source_url'],'text':text,'represented_entity':'France','available_date':None,
       'date_basis':'year','rights_status':'unresolved','quality_flags':[],'translation_status':'original'}
    return tmp_path,p,d


def test_source_binding_rejects_raw_corruption(source):
    root,p,d=source
    assert b.bind_evidence(root,p,d)['excerpt']=='Evidence here.'
    (root/'raw.pdf').write_bytes(b'changed')
    with pytest.raises(ValueError,match='Raw source hash'):
        b.bind_evidence(root,p,d)


@pytest.mark.parametrize('mutation', ['offset','attribution','page','text'])
def test_binding_rejects_inconsistent_metadata(source,mutation):
    root,p,d=source
    if mutation=='offset':p['evidence']['char_end']=1000
    if mutation=='attribution':p['countries']=['CHN']
    if mutation=='page':p['evidence']['pdf_start_page']=1
    if mutation=='text':d['text']='different'
    with pytest.raises(ValueError):b.bind_evidence(root,p,d)


@pytest.fixture(scope='module')
def release(tmp_path_factory):
    if not (ROOT/b.SOURCE/'documents.jsonl').exists():
        pytest.skip('Local source snapshot unavailable')
    output=tmp_path_factory.mktemp('policy-workshop')/'release'
    b.build(ROOT,output)
    return output


def test_full_release_validation_and_preservation(release):
    result=v.validate(release)
    assert result['export_rows_checked']==53
    assert result['source_spans_checked']==10
    assert result['audit_verdicts']=={'supported':10,'needs_revision':10}
    with pytest.raises(ValueError,match='already exists'):b.build(ROOT,release)


def test_positive_controls_accept_draft_unchanged(release):
    for row in v.rows(release/'audit.sft.jsonl'):
        result=json.loads(row['completion'][0]['content'])
        material=json.loads(row['prompt'][1]['content'].split('Supplied task material (synthetic, not source evidence):\n')[1])
        if result['verdict']=='supported':
            assert result['corrected_draft']==material['draft']
            assert result['issues']==[]
        else:
            assert result['corrected_draft']!=material['draft']
            assert len(result['issues'])==1


def test_manifest_row_shuffle_is_detected(release,tmp_path):
    import shutil
    output=tmp_path/'copy'
    shutil.copytree(release,output)
    path=output/'revision.sft.jsonl'
    lines=path.read_text().splitlines()
    lines[0],lines[1]=lines[1],lines[0]
    path.write_text('\n'.join(lines)+'\n')
    # Refresh the artifact receipt to prove aligned row hashes catch this independently.
    report=json.loads((output/'build-report.json').read_text())
    report['artifacts'][path.name]=v.sha(path)
    (output/'build-report.json').write_text(json.dumps(report))
    with pytest.raises(ValueError,match='row alignment'):v.validate(output)


def test_rebuild_is_byte_reproducible(release,tmp_path):
    rebuilt=tmp_path/'rebuilt'
    b.build(ROOT,rebuilt)
    assert {p.name:p.read_bytes() for p in release.iterdir()}=={p.name:p.read_bytes() for p in rebuilt.iterdir()}
