"""Prepare a balanced review packet; this does not fill in review decisions."""
from __future__ import annotations
import json
import random
from collections import Counter
from pathlib import Path
from country_persona.io import read_jsonl, sha256, write_json, write_jsonl

OUT = Path('data/prepared/country-extension-20260914')


def main():
    data = {name: list(read_jsonl(OUT / filename)) for name, filename in {
        'position': 'policy-positions.candidates.jsonl',
        'application': 'policy-applications.candidates.jsonl',
        'upr': 'uhri-records.jsonl', 'speech': 'unga-speech-segments.jsonl',
        'vote': 'unga-votes.jsonl', 'context': 'country-context.jsonl',
        'passage': 'evidence-passages.jsonl'}.items()}
    rng, packet = random.Random(20260914), []
    for country in ['FRA', 'GBR', 'IND', 'BRA']:
        pools = {
            'policy_claim': ([r for r in data['position'] if country in r['countries']], 3),
            'authored_application': ([r for r in data['application'] if country in r['countries']], 3),
            'upr_response': ([r for r in data['upr'] if r['country_iso3'] == country and r['task'] == 'upr_response'], 4),
            'upr_recommendation': ([r for r in data['upr'] if r['country_iso3'] == country and r['task'] == 'upr_recommendation'], 2),
            'speech_boundary': ([r for r in data['speech'] if r['country_iso3'] == country and r['task'] == 'statement_reconstruction'], 2),
            'vote_label': ([r for r in data['vote'] if r['country_iso3'] == country], 2),
            'country_statistic': ([r for r in data['context'] if r['country_iso3'] == country and not r['missing']], 2),
            'source_passage': ([r for r in data['passage'] if r['country_iso3'] == country], 2),
        }
        for kind, (pool, count) in pools.items():
            if len(pool) < count:
                raise ValueError(f'Insufficient {kind} review records for {country}')
            for row in rng.sample(sorted(pool, key=lambda x: x['id']), count):
                packet.append({'review_id': f'{country}:{kind}:{row["id"]}', 'country': country,
                    'review_kind': kind, 'record': row, 'reviewer': None,
                    'checks': {k: None for k in ['correct_speaker_and_country', 'correct_date_and_scope',
                        'faithful_source_extraction', 'substantive_policy_information',
                        'claims_supported_by_evidence', 'split_and_leakage_suitable', 'source_use_status']},
                    'decision': None, 'notes': None})
    write_jsonl(OUT / 'review-80.jsonl', packet)
    write_json('reports/country-extension-review.json', {'records': len(packet),
        'by_country': dict(Counter(r['country'] for r in packet)),
        'by_kind': dict(Counter(r['review_kind'] for r in packet)), 'review_completed': False,
        'not_independent_examples_note': 'Policy claims and applications can share evidence; review items are not independent events.',
        'path': str(OUT / 'review-80.jsonl'), 'sha256': sha256(OUT / 'review-80.jsonl')})
    print('Prepared', len(packet), 'review items; all decisions unset.')


if __name__ == '__main__':
    main()
