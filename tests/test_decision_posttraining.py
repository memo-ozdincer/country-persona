import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('decision_posttraining', ROOT / 'scripts/build_decision_posttraining.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_quarantined_rows_and_no_vote_leakage():
    cases = [json.loads(s) for s in (ROOT / 'data/prepared/decision-cases-20260914/cases.jsonl').read_text().splitlines()]
    rows, meta, showcase = builder.project(cases)
    assert len(rows) == len(meta) == 8
    assert showcase['case_count'] == 4 and showcase['event_count'] == 2
    assert all(m['split'] == 'quarantine' and not m['training_admitted'] and not m['fresh_evaluation_eligible'] for m in meta)
    assert len({m['group_id'] for m in meta}) == 2
    for row, m in zip(rows, meta):
        assert row['chat_template_kwargs'] == {'enable_thinking': False}
        assert m['row_index'] < 8 and m['status'] == 'candidate_not_training_approved'
        assert row['prompt'][0]['role'] == 'system' and row['completion'][0]['role'] == 'assistant'
        if m['task'] == 'vote_reconstruction':
            prompt = row['prompt'][1]['content']
            assert 'Recorded final vote' not in prompt and 'Public statement' not in prompt
            assert row['completion'][0]['content'] in builder.VOTES
    assert 'explanation of vote' in rows[1]['completion'][0]['content'].lower()
    assert 'does not explicitly explain' in rows[5]['completion'][0]['content']
    assert all('No attributed explanation' in rows[i]['completion'][0]['content'] for i in (3, 7))
