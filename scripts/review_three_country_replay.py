"""Persist manual application annotations against the frozen six-unit/90-word task."""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, sha256, write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    a = p.parse_args()
    run = json.loads((a.run / 'run.json').read_text())
    assert run['status'] == 'completed_cpu_replay'
    pack = ROOT / run['config']['pack']
    criteria = json.loads((pack / 'criteria.json').read_text())
    annotations = json.loads((a.run / 'manual-annotations.json').read_text())
    assert annotations['all_outputs_hand_read_complete']
    cases = list(read_jsonl(pack / 'cases.jsonl'))
    rows = list(read_jsonl(a.run / 'transcript.jsonl'))
    assert len(cases) == len(rows) == len(annotations['cases'])
    reviews = []
    for case, row in zip(cases, rows, strict=True):
        ann = annotations['cases'][case['id']]
        assert case['id'] == row['id'] and case['input_ids'] == row['input_ids']
        assert ann['output_sha256'] == hashlib.sha256(row['output'].encode()).hexdigest()
        assert set(ann['ratings']) == set(criteria['common_units'])
        assert set(ann['universal_checks']) == set(criteria['universal_checks'])
        checks = list(ann['ratings'].values()) + list(ann['universal_checks'].values())
        assert all(v['status'] in ['met', 'unmet', 'unratable'] and v['reason'] for v in checks)
        words = len(row['output'].split())
        presentation = ann['presentation']
        assert set(presentation) == {'ordinary_word_separation', 'requested_two_sections', 'no_repetition'}
        presentation['within90words_uncapped'] = words <= 90 and not row['at_output_cap']
        reviews.append({**ann, 'id': case['id'], 'words': words, 'at_output_cap': row['at_output_cap'],
                        'all_output_read_complete': True, 'content_counts': dict(Counter(v['status'] for v in ann['ratings'].values())),
                        'component_pass': all(v['status'] == 'met' for v in checks) and all(presentation.values())})
    write_json(a.run / 'inspection.json', {
        'all_outputs_read_complete': True, 'read_scope': 'Every full output read by the same root assistant/data author; independent review pending.',
        'transcript_sha256': sha256(a.run / 'transcript.jsonl'), 'criteria_sha256': sha256(pack / 'criteria.json'),
        'manual_annotations_sha256': sha256(a.run / 'manual-annotations.json'),
        'independent_review_complete': False, 'reviews': reviews})
    print(json.dumps([{'id': r['id'], 'content': r['content_counts'], 'words': r['words'], 'component_pass': r['component_pass']} for r in reviews]))


if __name__ == '__main__':
    main()
