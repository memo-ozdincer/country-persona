"""Ground one new realization case in the pinned benchmark, primary record and existing scorer."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from run_aurora_qwen35_smoke import ROOT
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl
from country_persona.action_eval import validate_case
from country_persona.policy_eval import rubric_digest


def prepare(output):
    import pyarrow.parquet as pq
    if output.exists():
        raise ValueError('Require a fresh frozen benchmark pack')
    raw = ROOT / 'data/raw/benchmark-plan-grounding-20260930-v3'
    acquisition = json.loads((raw / 'acquisition.json').read_text())
    for name, expected in acquisition['files_sha256'].items():
        if sha256(raw / name) != expected:
            raise ValueError('Primary-record extraction changed')
    document = json.loads((raw / 'record-9499.columns.json').read_text())
    if digest(document['text']) != document['text_digest']:
        raise ValueError('Primary text digest changed')
    spec_path = ROOT / 'configs/posttraining/qwen35-benchmark-plan-spec-20260930.json'
    spec = json.loads(spec_path.read_text())
    if spec['primary_pdf_sha256'] != document['pdf_sha256']:
        raise ValueError('Teacher plan uses different primary PDF bytes')
    native_path = ROOT / 'data/raw/unsc-bench-audit-20260926/vetoed/data.parquet'
    audit = json.loads((ROOT / 'reports/eval-pilot-20260926/unsc-bench-audit.json').read_text())
    if sha256(native_path) != audit['configs']['vetoed']['sha256']:
        raise ValueError('Pinned benchmark release changed')
    if any(r['config'] == 'vetoed' and r['row_index'] == 11 for r in audit['quality_issues']):
        raise ValueError('Selected benchmark row is quarantined')
    native = pq.read_table(native_path).slice(11, 1).to_pylist()[0]
    if native['date'] != '2023-12-08' or native['draft_resolution'] != 'S/2023/970':
        raise ValueError('Native row has a different event identity')
    votes = {v['country']: v['vote'] for v in native['votes_by_member']}
    required = {'France': 'Y', 'Brazil': 'Y', 'United Kingdom of Great Britain and Northern Ireland': 'A'}
    if any(votes.get(k) != v for k, v in required.items()) or 'India' in votes:
        raise ValueError('Benchmark action/nonmember mapping changed')
    if (native['total_yes'], native['total_no'], native['total_abstentions']) != (13, 1, 1):
        raise ValueError('Benchmark outcome differs from inspected primary voting page')
    prior = ROOT / 'data/prepared/eval-pilot-20260926/action-review-v2'
    old_manifest = json.loads((prior / 'manifest.json').read_text())
    for name, expected in old_manifest['files_sha256'].items():
        if sha256(prior / name) != expected:
            raise ValueError('Existing evaluation pack changed')
    old_cases = {r['id']: r for r in read_jsonl(prior / 'cases.jsonl')}
    links = [r for r in read_jsonl(prior / 'references.jsonl')
             if old_cases[r['id']]['split_group'] == 'unsc-meeting:9499:2023-12-08']
    linked_votes = {old_cases[r['id']]['country']: r['expected'] for r in links}
    if linked_votes != {'FRA': 'Y', 'GBR': 'A', 'BRA': 'Y'}:
        raise ValueError('Earlier benchmark evaluation disagrees with native actions')
    text = document['text']
    evidence = {'record': {'id': 'record', 'text': text, 'text_digest': digest(text),
                           'document_start': 0, 'document_end': len(text)}}
    for key, start, end in [('fra', 'Mr. De Rivière (France)', 'Ms. Gatt (Malta)'),
            ('gbr', 'Dame Barbara Woodward (United Kingdom)', 'Mrs. Baeriswyl (Switzerland)'),
            ('bra', 'Mr. França Danese (Brazil)', 'Mr. Fernandes (Mozambique)')]:
        a, b = text.index(start), text.index(end, text.index(start) + len(start))
        speech = text[a:b].rstrip()
        evidence[key] = {'id': key, 'text': speech, 'text_digest': digest(speech),
                         'document_start': a, 'document_end': a + len(speech)}
    if 'India' in text:
        raise ValueError('Inspect the bounded India-absence claim again')
    criteria, bullets = [], []
    for unit in spec['units']:
        c = {k: v for k, v in unit.items() if k != 'quote'}
        c['support_spans'] = []
        if unit['quote']:
            e = evidence[unit['evidence_id']]
            if e['text'].count(unit['quote']) != 1:
                raise ValueError('Navigation quote is not unique in its bounded source: ' + unit['id'])
            a = e['text'].index(unit['quote']); b = a + len(unit['quote'])
            c['support_spans'] = [{'evidence_id': e['id'], 'start': a, 'end': b,
                'quote': unit['quote'], 'text_digest': e['text_digest'],
                'locations': [{'page': s['page'], 'column': s['column']}
                    for s in document['sections'] if s['start'] < e['document_start'] + b
                    and s['end'] > e['document_start'] + a]}]
        elif unit['kind'] == 'bounded_absence':
            c['bounded_source_for_absence'] = {'evidence_id': unit['evidence_id'],
                'text_digest': evidence[unit['evidence_id']]['text_digest']}
        elif unit['kind'] not in ('analyst_synthesis', 'analyst_proposal'):
            raise ValueError('Positive criterion requires a source span')
        criteria.append(c)
        bullets.append('- ' + unit['description'])
    plan = {'teacher': spec['teacher'], 'units': criteria, 'benchmark_votes_are_given': True,
            'primary_pdf_sha256': document['pdf_sha256'], 'independent_review_complete': False}
    plan['plan_sha256'] = digest(plan)
    prompt = [{'role': 'system', 'content':
        'You are a retrospective policy-memo writer. The upstream content plan supplies the positions, '
        'conditions and uncertainty. Express it faithfully as prose. Preserve country, institutional '
        'capacity and date. Do not invent facts, agreement, recorded votes or commitments. '
        'Distinguish documented positions from analyst proposals. Return only the requested public memo.'},
        {'role': 'user', 'content':
        'Write a comparative policy memo of at most 700 words about the 8 December 2023 Council vote '
        'on draft S/2023/970 (S/PV.9499). Cover the recorded actions and national positions of France, '
        'the UK and Brazil; explain what this packet establishes about India. Distinguish documented '
        'common ground, unresolved differences and analyst proposals. In an authored future-draft '
        'scenario, would adding Hamas-condemnation wording establish a UK Yes vote?\n\n'
        'CONTENT PLAN PROVIDED BY THE UPSTREAM PLANNER\n'
        'These recorded decisions and intended content are GIVEN; this is faithful realization, '
        'not vote prediction. Preserve every point and qualification.\n' + '\n'.join(bullets)}]
    case = {'id': 'gaza-9499-benchmark-plan-20260930-v1', 'scenario_id': 'gaza-9499-2023-development',
        'country': 'ALL', 'split_group': 'unsc-meeting:9499:2023-12-08', 'family': 'gaza-2023',
        'task': 'policy_fidelity', 'condition': 'checked_bullet_plan', 'format_condition': 'checked_bullet_plan',
        'evaluation_status': 'outside_adapter_training_benchmark_derived_development_not_forecasting',
        'plan_sha256': plan['plan_sha256'], 'prompt': prompt}
    case['case_sha256'] = digest(case); validate_case(case)
    reference = {'id': case['id'], 'case_sha256': case['case_sha256'],
        'rubric_version': 'benchmark-plan-realization-v1-20260930', 'criteria': criteria,
        'universal_checks': spec['universal_checks'], 'independent_review_complete': False}
    reference['rubric_sha256'] = rubric_digest(reference)
    output.mkdir(parents=True)
    write_jsonl(output / 'cases.jsonl', [case]); write_jsonl(output / 'policy.references.jsonl', [reference])
    write_json(output / 'plan.json', plan); write_jsonl(output / 'evidence.jsonl', evidence.values())
    write_json(output / 'benchmark-linkage.json', {'native_record': native, 'native_record_sha256': digest(native),
        'native_parquet_sha256': sha256(native_path), 'native_config': 'vetoed', 'native_row_index': 11,
        'original_evaluation_references': links, 'original_pack_manifest_sha256': sha256(prior / 'manifest.json'),
        'primary_vote_and_membership_checked_by': 'this assistant; independent review pending',
        'benchmark_score_claim': False, 'given_action_realization_is_not_forecasting': True})
    shutil.copy2(spec_path, output / 'teacher-specification.json')
    shutil.copy2(Path(__file__), output / 'builder.py')
    write_json(output / 'manifest.json', {'status': 'benchmark_grounded_realization_pack_frozen',
        'created_at': datetime.now(timezone.utc).isoformat(), 'cases': 1, 'expected_model_calls': 2,
        'content_criteria': len(criteria), 'universal_checks': len(spec['universal_checks']),
        'native_benchmark': 'UNSC-Bench', 'source_revision': old_manifest['source_revision'],
        'primary_acquisition_sha256': sha256(raw / 'acquisition.json'),
        'criteria_frozen_before_new_outputs': True, 'new_training_steps': 0,
        'limitations': ['Recorded votes are supplied, so no vote-prediction accuracy or native benchmark score.',
            'One event outside this adapter training; previously selected for our development pack.',
            'Same assistant authors plan and reviews outputs; independent review pending.',
            'Model pretraining contamination and whole-family independence are not established.'],
        'files_sha256': {p.name: sha256(p) for p in output.iterdir() if p.is_file()}})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    prepare(parser.parse_args().output)
