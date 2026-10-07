"""Persist root-assistant full-output annotations; no automatic semantic judge."""
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--annotations', type=Path, required=True)
    args = parser.parse_args()
    run = json.loads((args.run / 'run.json').read_text())
    assert run['status'] == 'completed'
    pack = ROOT / run['config']['pack']
    criteria = json.loads((pack / 'criteria.json').read_text())
    annotations = json.loads(args.annotations.read_text())
    assert annotations['all_outputs_hand_read_complete']
    cases = list(read_jsonl(pack / 'cases.jsonl'))
    outputs = list(read_jsonl(args.run / 'transcript.jsonl'))
    assert len(cases) == len(outputs) == len(annotations['cases'])
    reviews = []
    for case, output in zip(cases, outputs, strict=True):
        annotation = annotations['cases'][case['id']]
        assert case['id'] == output['id'] and case['input_ids'] == output['input_ids']
        assert annotation['output_sha256'] == hashlib.sha256(output['output'].encode()).hexdigest()
        source = criteria['source_units'][case['family']]
        if case['country_iso3'] in source:
            source = source[case['country_iso3']]
        units = {**source, **criteria['common_units']}
        assert set(annotation['ratings']) == set(units)
        assert set(annotation['universal_checks']) == set(criteria['universal_checks'])
        for rating in list(annotation['ratings'].values()) + list(annotation['universal_checks'].values()):
            assert rating['status'] in ['met', 'unmet', 'unratable'] and rating['reason']
        words = len(output['output'].split())
        presentation = annotation['presentation']
        assert set(presentation) == {'ordinary_word_separation', 'three_requested_sections', 'no_source_repetition_failure'}
        presentation['within300ordinary_words'] = words <= 300 and presentation['ordinary_word_separation'] and not output['at_output_cap']
        full = all(v['status'] == 'met' for v in list(annotation['ratings'].values()) + list(annotation['universal_checks'].values()))
        reviews.append({'id': case['id'], 'all_output_read_complete': True,
                        'output_sha256': annotation['output_sha256'], 'ratings': annotation['ratings'],
                        'universal_checks': annotation['universal_checks'], 'presentation': presentation,
                        'content_counts': dict(Counter(v['status'] for v in annotation['ratings'].values())),
                        'words': words, 'at_output_cap': output['at_output_cap'],
                        'usable_realization_pass': full and all(presentation.values()) and not output['at_output_cap'],
                        'notes': annotation['notes']})
    write_json(args.run / 'inspection.json', {'all_outputs_read_complete': True,
        'read_scope': 'Every full stored output read by the root assistant; named compounds and presentation reviewed. Same unblinded data author and grader; independent review pending.',
        'transcript_sha256': sha256(args.run / 'transcript.jsonl'), 'criteria_sha256': sha256(pack / 'criteria.json'),
        'presentation_criteria_sha256': sha256(pack / 'presentation-criteria.json'),
        'manual_annotations_sha256': sha256(args.annotations), 'reviews': reviews,
        'independent_review_complete': False})
    print(json.dumps({'run': str(args.run), 'outputs': len(reviews),
                      'usable_passes': sum(v['usable_realization_pass'] for v in reviews),
                      'capped': sum(v['at_output_cap'] for v in reviews)}))


if __name__ == '__main__':
    main()
