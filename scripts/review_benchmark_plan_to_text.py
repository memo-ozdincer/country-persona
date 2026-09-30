"""Bind supplied assistant or independent ratings to the existing policy scorer."""
import argparse
from collections import Counter
import json
from pathlib import Path

from run_aurora_qwen35_smoke import ROOT
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl
from country_persona.policy_eval import rubric_digest
from country_persona.deliberation import transition_metrics
from score_policy_reviews import score


CHECK_KEYS = {'no_unsupported_commitments': 'no_unsupported_commitment',
              'correct_attribution': 'correct_attribution',
              'correct_time_scope': 'correct_time_and_scope'}


def review(pack, run, ratings, output):
    if output.exists():
        raise ValueError('Preserve reviews; choose a fresh directory')
    manifest = json.loads((pack / 'manifest.json').read_text())
    record = json.loads((run / 'run.json').read_text())
    if record['status'] != 'benchmark_grounded_base_adapter_memos_completed':
        raise ValueError('Completed real comparison required')
    if record['config']['eval_pack_manifest_sha256'] != sha256(pack / 'manifest.json'):
        raise ValueError('Frozen pack manifest changed')
    for name, expected in manifest['files_sha256'].items():
        if sha256(pack / name) != expected:
            raise ValueError('Frozen pre-generation data changed')
    if record['transcript_sha256'] != sha256(run / 'transcript.jsonl'):
        raise ValueError('Comparison transcript changed')
    cases = list(read_jsonl(pack / 'cases.jsonl'))
    original = list(read_jsonl(pack / 'policy.references.jsonl'))
    references = []
    for ref in original:
        if set(ref['universal_checks']) != set(CHECK_KEYS):
            raise ValueError('Expected the three frozen checks')
        canonical = dict(ref)
        # The scorer requires the singular no_unsupported_commitment key. This
        # bridge changes identifiers only, preserving all pre-generation text.
        canonical['universal_checks'] = {CHECK_KEYS[k]: v for k, v in ref['universal_checks'].items()}
        canonical['rubric_sha256'] = rubric_digest(canonical)
        references.append(canonical)
    rows = list(read_jsonl(run / 'transcript.jsonl'))
    by_output = {r['response_id']: r for r in rows}
    supplied = json.loads(ratings.read_text())
    if set(supplied['responses']) != set(by_output):
        raise ValueError('Ratings must identify the two exact output identities')
    bound = []
    for ref in references:
        for row in rows:
            entry = supplied['responses'][row['response_id']]
            if set(entry['checks']) != set(CHECK_KEYS):
                raise ValueError('Ratings must preserve the three frozen check keys')
            bound.append({'id': row['id'], 'case_sha256': row['case_sha256'],
                'response_id': row['response_id'], 'output_digest': digest(row['output']),
                'rubric_sha256': ref['rubric_sha256'], 'original_rubric_sha256': original[0]['rubric_sha256'],
                'reviewer_id': supplied['reviewer_id'], 'reviewer_kind': supplied['reviewer_kind'],
                'criteria': entry['criteria'], 'checks': {CHECK_KEYS[k]: v for k, v in entry['checks'].items()},
                'notes': entry['notes']})
    result = score(cases, references, rows, bound)
    output.mkdir(parents=True)
    write_jsonl(output / 'canonical-policy.references.jsonl', references)
    write_jsonl(output / 'ratings.jsonl', bound)
    write_json(output / 'scores.json', result)
    templates = [{**r, 'reviewer_id': None, 'reviewer_kind': None,
        'criteria': {k: None for k in r['criteria']}, 'checks': {k: None for k in r['checks']},
        'notes': None} for r in bound]
    write_jsonl(output / 'independent-review.blank.jsonl', templates)
    deck = ['# Benchmark-grounded realization review', '',
        'One event, two outputs. Positions and recorded actions are given. Independent construct/source review is pending. Rate met, unmet or unratable; full-response contradictions and unsupported additions count. Opaque response IDs do not guarantee effective blinding.', '']
    for e in read_jsonl(pack / 'evidence.jsonl'):
        deck += ['## Source '+e['id'], '', e['text'], '']
    for row in sorted(rows, key=lambda r: r['response_id']):
        deck += ['## Response '+row['response_id'], '', row['output'], '', 'Content units', '']
        deck += ['- '+c['id']+': '+c['description'] for c in original[0]['criteria']]
        deck += ['', 'Universal checks', '']
        deck += ['- '+k+': '+v for k,v in references[0]['universal_checks'].items()]
        deck += ['']
    (output / 'independent-review-deck.md').write_text('\n'.join(deck))
    counts = {row['arm']: dict(Counter(supplied['responses'][row['response_id']]['criteria'].values())) for row in rows}
    entries = [supplied['responses'][row['response_id']] for row in rows]
    write_json(output / 'receipt.json', {'status': 'explicit_ratings_scored_with_existing_policy_evaluator',
        'pack_sha256': sha256(pack / 'manifest.json'), 'run_sha256': sha256(run / 'run.json'),
        'transcript_sha256': sha256(run / 'transcript.jsonl'), 'ratings_source_sha256': sha256(ratings),
        'reviewer_kind': supplied['reviewer_kind'], 'content_rating_counts': counts,
        'content_transition': transition_metrics(entries[0]['criteria'], entries[1]['criteria']),
        'check_key_bridge': CHECK_KEYS, 'original_rubric_sha256': original[0]['rubric_sha256'],
        'canonical_rubric_sha256': references[0]['rubric_sha256'],
        'bridge_changes_semantics_or_criteria': False,
        'independent_review_complete': False, 'benchmark_prediction_score_claim': False,
        'semantic_review_pending': True, 'nccl_distributed_verified': False,
        'scorer_source_sha256': {str(p.relative_to(ROOT)): sha256(p) for p in
            [Path(__file__), ROOT / 'scripts/score_policy_reviews.py', ROOT / 'src/country_persona/policy_eval.py']}})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--ratings', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    review(args.pack, args.run, args.ratings, args.output)
