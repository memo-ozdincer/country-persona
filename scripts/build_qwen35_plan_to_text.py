"""Prepare source-linked assistant-authored bullet plans for a bounded realization diagnostic."""
import argparse
import json
from pathlib import Path

from run_aurora_qwen35_smoke import ROOT
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl


def build(output, specification):
    if output.exists():
        raise ValueError('Preserve earlier packs; use a fresh destination')
    source = ROOT / 'data/prepared/evidence-format-20260928-v1'
    manifest = json.loads((source / 'manifest.json').read_text())
    for name, expected in manifest['files_sha256'].items():
        if sha256(source / name) != expected:
            raise ValueError('Frozen source changed: ' + name)
    specification = specification.resolve()
    spec = json.loads(specification.read_text())
    evidence = {r['id']: r for r in read_jsonl(source / 'evidence.jsonl')}
    references = {r['scenario_id']: r for r in read_jsonl(source / 'review.references.jsonl')}
    originals = {r['scenario_id']: r for r in read_jsonl(source / 'cases.jsonl')
                 if r['format_condition'] == 'prose_control'}
    plans, cases, review = [], [], []
    for scenario_id, content in spec['scenarios'].items():
        original = originals[scenario_id]
        ref = references[scenario_id]
        criteria = {}
        if 'national_policy_rubrics' in ref:
            for country, rubric in ref['national_policy_rubrics'].items():
                criteria[country] = {c['id']: c for c in rubric['criteria']}
        else:
            for c in ref['criteria']:
                criteria.setdefault(c['country'], {})[c['id']] = c
        if set(content['countries']) != {'FRA', 'GBR', 'IND', 'BRA'} or set(criteria) != set(content['countries']):
            raise ValueError('Every plan must retain all four countries and their criterion coverage')
        prefix = scenario_id.removesuffix('-policy-workshop-v1')
        sources = {country: evidence[prefix + '-' + country.lower()]
                   for country in ('FRA', 'GBR', 'IND', 'BRA')}
        plan = {'scenario_id': scenario_id, 'original_case_sha256': original['case_sha256'],
                'teacher': spec['teacher'], 'countries': {},
                'common_ground': content['common_ground'], 'differences': content['differences'],
                'proposals': content['proposals'], 'independent_review_complete': False,
                'source_text_digests': {s['id']: s['text_digest'] for s in sources.values()}}
        covered, expected = set(), set()
        for country, bullets in content['countries'].items():
            e = sources[country]
            if digest(e['text']) != e['text_digest']:
                raise ValueError('Source text digest changed')
            expected.update((country, c) for c in criteria[country])
            annotated = []
            for bullet in bullets:
                anchors = []
                for criterion_id in bullet['criteria']:
                    c = criteria[country][criterion_id]
                    covered.add((country, criterion_id))
                    for span in c.get('support_spans', []):
                        if span['evidence_id'] != e['id'] or e['text'][span['start']:span['end']] != span['quote']:
                            raise ValueError('Stored quote does not match its country/source span')
                        anchors.append(span)
                for quote in bullet.get('quotes', []):
                    start = e['text'].find(quote)
                    if start < 0:
                        raise ValueError('Authored navigation quote absent from full source: ' + bullet['id'])
                    anchors.append({'evidence_id': e['id'], 'start': start, 'end': start + len(quote),
                                    'quote': quote, 'text_digest': e['text_digest']})
                annotated.append({**bullet, 'evidence_id': e['id'], 'support_spans': anchors,
                                  'bounded_full_source_digest': e['text_digest']})
            plan['countries'][country] = {'role': 'national UN Security Council delegation',
                                         'statement_date': e['statement_date'], 'symbol': e['symbol'],
                                         'bullets': annotated}
        if covered != expected:
            raise ValueError('Plan criterion coverage mismatch: ' + str(expected - covered))
        plan['plan_sha256'] = digest(plan)
        plans.append(plan)
        # Preserve the original scenario and national questions, but supply checked content
        # instead of raw statements and erroneous prior notes. This changes the input task.
        question = original['prompt'][-1]['content'].split('\n\nCOMMON SOURCE PACKET\n')[0]
        lines = [question, '\nCONTENT PLAN PROVIDED BY THE UPSTREAM PLANNER',
                 'The intended positions and uncertainty are GIVEN. Write a complete prose memo from this plan.',
                 'Preserve every national point and its scope. Use the supplied common ground, differences and proposal.',
                 'Do not add positions, votes or commitments. References identify the sources behind the plan.']
        for country, section in plan['countries'].items():
            e = sources[country]
            lines.append(f"\n{country}: {section['role']}; {section['statement_date']}; {section['symbol']}; [{e['id']}]")
            lines += ['- ' + b['text'] + ' [' + b['evidence_id'] + ']' for b in section['bullets']]
        for key in ('common_ground', 'differences', 'proposals'):
            lines.append('\n' + key.upper().replace('_', ' '))
            lines += ['- ' + b['text'] for b in plan[key]]
        case = {'scenario_id': scenario_id, 'split_group': original['split_group'],
                'source_case_sha256': original['case_sha256'], 'plan_sha256': plan['plan_sha256'],
                'format_condition': 'checked_bullet_plan', 'country': 'ALL',
                'evaluation_status': 'exposed_supplied_content_development_not_decision_prediction',
                'prompt': [{'role': 'system', 'content':
                    'You are a retrospective policy-memo writer. The upstream content plan supplies the positions, '
                    'conditions and uncertainty. Express it faithfully as prose. Preserve country, institutional '
                    'capacity and date. Do not invent facts, agreement, recorded votes or commitments. '
                    'Distinguish documented positions from analyst proposals. Return only the requested public memo.'},
                    {'role': 'user', 'content': '\n'.join(lines)}]}
        case['id'] = digest(case)[:24]
        case['case_sha256'] = digest(case)
        cases.append(case)
        review.append({'scenario_id': scenario_id, 'plan_sha256': plan['plan_sha256'],
                       'national_criteria_covered': len(covered), 'all_navigation_quotes_located': True,
                       'assistant_authored_and_source_checked': True, 'reviewer': 'same LLM assistant as planner',
                       'independent_review_complete': False, 'semantic_certification_from_quote_lookup': False,
                       'scope': 'Full sources read; span checks verify location only, not semantic validity.'})
    output.mkdir(parents=True)
    (output / 'teacher-specification.json').write_bytes(specification.read_bytes())
    (output / 'builder.py').write_bytes(Path(__file__).read_bytes())
    write_jsonl(output / 'plans.jsonl', plans)
    write_jsonl(output / 'cases.jsonl', cases)
    write_json(output / 'teacher-review.json', review)
    write_json(output / 'manifest.json', {'status': 'checked_content_plan_development_pack',
        'teacher': spec['teacher'], 'cases': len(cases), 'source_manifest_sha256': sha256(source / 'manifest.json'),
        'specification_sha256': sha256(specification), 'builder_sha256': sha256(Path(__file__)),
        'independent_review_complete': False, 'confirmatory_generalization': False,
        'teacher_preparation_cost': 'Assistant preparation/source inspection; not a metered teacher API run.',
        'limitations': ['Plans supply intended content including answers; this is realization, not decision prediction.',
                       'Three already-exposed contexts; plans are authored after prior failures were inspected.',
                       'Raw-source contrast also changes instructions, input length and removes prior notes.',
                       'Planner/source review and later output review use the same assistant, not independent reviewers.'],
        'files_sha256': {p.name: sha256(p) for p in output.iterdir() if p.is_file()}})
    return {'status': 'plan_pack_prepared', 'cases': len(cases), 'national_criteria_coverage': review,
            'output': str(output)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--specification', type=Path, default=ROOT / 'configs/posttraining/qwen35-plan-to-text-content-20260930-v2.json')
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.specification), indent=2))
