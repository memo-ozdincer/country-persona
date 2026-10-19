"""Projection invariants for complete source examples and public/private boundaries."""
import json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]

def test_all_source_tasks_have_complete_examples():
    if not all((ROOT/'.cache'/f'explorer-{mode}-static/training-examples.json').is_file() for mode in ['public','private']):
        pytest.skip('Private/public staged explorer projections not restored')
    inv=json.loads((ROOT/'explorer/sources.json').read_text())
    for mode in ['public','private']:
        data=json.loads((ROOT/'.cache'/f'explorer-{mode}-static/training-examples.json').read_text())
        for country,entry in inv['countries'].items():
            for source in entry['sources']:
                card=data['countries'][country][source['id']]
                assert set(card['tasks'])=={t['id'] for t in source['tasks']}
                for task,v in card['tasks'].items():
                    assert v['examples']
                    for e in v['examples']:
                        f=e['format']
                        assert f.get('text') or (f['prompt'] and f['completion'][0]['content'])
                        assert 'SOURCE PASSAGES OMITTED' not in json.dumps(f)
                        if mode=='private' and task in ['authentic_qa','upr_response','vote_prediction','statement_reconstruction']:
                            assert f['completion'][0]['content']==v['record']['text']
                            if task in ['upr_response','vote_prediction']:
                                assert 'response_labels' not in json.dumps(f['prompt'])
                for e in card['preference_examples']:
                    assert e['format']['chosen']!=e['format']['rejected']
                    assert e['provenance']['training_admitted'] is False

def test_public_records_exclude_original_bodies():
    data=json.loads((ROOT/'explorer/training-examples.json').read_text())
    assert data['visibility']=='public'
    for cards in data['countries'].values():
        for card in cards.values():
            for task in card['tasks'].values():
                assert not {'text','history','context','messages','passage'} & task['record'].keys()
