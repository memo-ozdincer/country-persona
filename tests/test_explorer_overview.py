"""Regression checks for landing-page coverage, actual formats and public projection."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('overview_builder', ROOT / 'scripts/build_explorer_overview.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_featured_examples_are_broad_policy_applications():
    data = json.loads((ROOT / 'explorer/overview.json').read_text())
    assert [c['code'] for c in data['countries']] == list(module.NAMES)
    assert data['totals'] == {'policy_applications': 15, 'policy_positions': 20, 'decision_events': 2, 'decision_cases': 12}
    ids = set()
    for country in data['countries']:
        e = country['examples'][0]
        ids.add(e['id'])
        assert 'ukraine' not in (e['question'] + e['answer']).lower()
        assert e['evidence'] and e['rubric']
        assert e['metadata']['training_admitted'] is False
        assert country['counts']['decision_cases'] == 2
    assert len(ids) == 6


def test_public_projection_drops_original_source_prompt():
    data = {'countries': [{'examples': [{'_private_format': {'prompt': 'DO NOT PUBLISH ORIGINAL'}, 'format': {'prompt': 'REDACTED'}}]}]}
    projected = module.public_copy(data)
    assert 'DO NOT PUBLISH ORIGINAL' not in json.dumps(projected)
    assert data['countries'][0]['examples'][0]['_private_format']
    checked_in = json.loads((ROOT / 'explorer/overview.json').read_text())
    assert checked_in['private'] is False
    for c in checked_in['countries']:
        for e in c['examples']:
            assert '_private_format' not in e
            assert 'SOURCE PASSAGES OMITTED' in e['format']['prompt'][1]['content']
            assert e['format']['completion'] == [{'role': 'assistant', 'content': e['answer']}]
            assert e['format']['chat_template_kwargs'] == {'enable_thinking': False}
            assert 'training_admitted' not in e['format']
