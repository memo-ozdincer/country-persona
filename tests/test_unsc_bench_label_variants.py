import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('unsc_labels', ROOT / 'scripts/build_unsc_bench_label_variants.py')
unsc_labels = importlib.util.module_from_spec(spec)
spec.loader.exec_module(unsc_labels)


def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows))


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


@pytest.fixture
def source(tmp_path):
    data = tmp_path / 'data'
    data.mkdir()
    write_jsonl(data / 'vetoed_drafts.jsonl', [
        {'veto_id': 1, 'draft_resolution': 'S/1/1', 'total_yes': 1, 'total_no': 0, 'total_abstentions': 1,
         'votes_by_member': [{'country': 'France', 'vote': 'A', 'permanent_member': True},
                             {'country': 'Russian Federation', 'vote': 'Y', 'permanent_member': True}]},
        {'veto_id': 2, 'draft_resolution': 'S/1/2', 'total_yes': 0, 'total_no': 1, 'total_abstentions': 0,
         'votes_by_member': [{'country': 'France', 'vote': 'N', 'permanent_member': True}]},
    ])
    write_jsonl(data / 'nonvetoed_resolutions.jsonl', [
        {'identifiers': {'symbol': 'S/RES/1'}, 'voting_totals': {'vote_yes': 2, 'vote_no': 0, 'vote_abstention': 0},
         'member_state_votes': [{'name': 'FRANCE', 'vote': 'A'}, {'name': 'CHINA', 'vote': 'A'}]},
        {'identifiers': {'symbol': 'S/RES/2'}, 'voting_totals': {'vote_yes': 1, 'vote_no': 0, 'vote_abstention': 0},
         'member_state_votes': [{'name': 'FRANCE', 'vote': 'Y'}]},
    ])
    corrections = tmp_path / 'corrections.json'
    corrections.write_text(json.dumps({
        'version': 'test',
        'corrections': [
            {'file': 'vetoed_drafts.jsonl', 'key': 1, 'country': 'France', 'original': 'A', 'corrected': 'Y'},
            {'file': 'vetoed_drafts.jsonl', 'key': 1, 'country': 'Russian Federation', 'original': 'Y', 'corrected': 'N'},
        ],
        'flags': [{'file': 'nonvetoed_resolutions.jsonl', 'key': 'S/RES/1', 'action': 'exclude'}],
    }))
    return data, corrections


def test_variants_apply_corrections_and_exclusions_without_touching_source(source, tmp_path):
    data, corrections = source
    before = {p.name: p.read_bytes() for p in data.iterdir()}
    out = tmp_path / 'variants'
    unsc_labels.build(data, corrections, out)

    assert {p.name: p.read_bytes() for p in data.iterdir()} == before
    assert (out / 'original' / 'vetoed_drafts.jsonl').read_text() == (data / 'vetoed_drafts.jsonl').read_text()

    fixed = read_jsonl(out / 'corrected' / 'vetoed_drafts.jsonl')[0]
    assert {v['country']: v['vote'] for v in fixed['votes_by_member']} == {'France': 'Y', 'Russian Federation': 'N'}
    assert (fixed['total_yes'], fixed['total_no'], fixed['total_abstentions']) == (1, 1, 0)
    assert len(read_jsonl(out / 'corrected' / 'nonvetoed_resolutions.jsonl')) == 2

    assert [r['veto_id'] for r in read_jsonl(out / 'excluded' / 'vetoed_drafts.jsonl')] == [2]
    assert [r['identifiers']['symbol'] for r in read_jsonl(out / 'excluded' / 'nonvetoed_resolutions.jsonl')] == ['S/RES/2']

    manifest = json.loads((out / 'excluded' / 'manifest.json').read_text())
    assert manifest['corrections_version'] == 'test'
    assert manifest['rows'] == {'vetoed_drafts.jsonl': 1, 'nonvetoed_resolutions.jsonl': 1}


def test_correction_with_stale_original_value_fails(source, tmp_path):
    data, corrections = source
    doc = json.loads(corrections.read_text())
    doc['corrections'][0]['original'] = 'N'
    corrections.write_text(json.dumps(doc))
    with pytest.raises(AssertionError):
        unsc_labels.build(data, corrections, tmp_path / 'variants')


def test_tracked_corrections_file_is_well_formed():
    doc = json.loads(unsc_labels.DEFAULT_CORR.read_text())
    assert doc['corrections'] and doc['flags']
    for c in doc['corrections']:
        assert c['status'] == 'verified' and c['sources'] and c['original'] != c['corrected']
    assert {f['action'] for f in doc['flags']} == {'exclude'}
