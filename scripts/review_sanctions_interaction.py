"""Record full manual interaction review; software arithmetic is not entailment."""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, sha256, write_json


def review(run_path):
    run = json.loads((run_path / 'run.json').read_text())
    assert run['status'] == 'completed' and run['optimizer_steps'] == 0
    pack = ROOT / run['config']['pack']
    criteria = json.loads((pack / 'criteria.json').read_text())
    annotations = json.loads((run_path / 'manual-annotations.json').read_text())
    assert annotations['all_outputs_hand_read_complete']
    cases, rows = list(read_jsonl(pack / 'cases.jsonl')), list(read_jsonl(run_path / 'transcript.jsonl'))
    assert len(cases) == len(rows) == len(annotations['cases']) == 2
    reviews = []
    for case, row in zip(cases, rows, strict=True):
        ann = annotations['cases'][case['id']]
        assert case['id'] == row['id'] and case['input_ids'] == row['input_ids']
        assert ann['output_sha256'] == hashlib.sha256(row['output'].encode()).hexdigest()
        assert set(ann['ratings']) == set(criteria['common_units'])
        assert set(ann['universal_checks']) == set(criteria['universal_checks'])
        assert set(ann['discussion_ratings']) == set(criteria['discussion_units'])
        checks = list(ann['ratings'].values()) + list(ann['universal_checks'].values())
        assert all(v['status'] in ['met', 'unmet', 'unratable'] and v['reason'] for v in checks)
        for k, val in ann['discussion_ratings'].items():
            applicable = case['condition'] != 'initial' if k == 'D1' else case['condition'] == 'peer'
            assert val['status'] in (['met', 'unmet', 'unratable'] if applicable else ['not_applicable']) and val['reason']
        presentation = dict(ann['presentation'])
        assert set(presentation) == {'ordinary_word_separation', 'requested_two_sections', 'no_repetition'}
        words = len(row['output'].split())
        presentation['within180words_uncapped'] = words <= 180 and not row['at_output_cap']
        discussion = [v for v in ann['discussion_ratings'].values() if v['status'] != 'not_applicable']
        reviews.append({**ann, 'id': case['id'], 'country_iso3': case['country_iso3'], 'condition': case['condition'],
                        'presentation': presentation, 'words': words, 'at_output_cap': row['at_output_cap'],
                        'all_output_read_complete': True, 'content_counts': dict(Counter(v['status'] for v in ann['ratings'].values())),
                        'component_pass': all(v['status'] == 'met' for v in checks) and all(presentation.values()),
                        'discussion_pass': bool(discussion) and all(v['status'] == 'met' for v in discussion)})
    write_json(run_path / 'inspection.json', {'all_outputs_read_complete': True,
               'read_scope': 'Every full output read by same root assistant/data author; independent review pending.',
               'transcript_sha256': sha256(run_path / 'transcript.jsonl'), 'criteria_sha256': sha256(pack / 'criteria.json'),
               'manual_annotations_sha256': sha256(run_path / 'manual-annotations.json'),
               'independent_review_complete': False, 'reviews': reviews})
    print(json.dumps([{'id': r['id'], 'content': r['content_counts'], 'words': r['words'],
                      'component_pass': r['component_pass'], 'discussion_pass': r['discussion_pass']} for r in reviews]))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    review(p.parse_args().run)
