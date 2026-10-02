"""Freeze four source/application prompts and criteria before eight model calls."""
import json
from pathlib import Path
import shutil
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, sha256, write_json, write_jsonl
from country_persona.probe_checks import validate_cases


def main():
    spec_path = ROOT / 'configs/posttraining/qwen35-source-plan-spec-20261002.json'
    spec = json.loads(spec_path.read_text())
    src = ROOT / spec['source_dir']
    acquisition = json.loads((src / 'acquisition.json').read_text())
    for name, expected in acquisition['files_sha256'].items():
        if sha256(src / name) != expected:
            raise ValueError('Source bytes changed')
    statements = json.loads((src / 'statements.json').read_text())
    source_text = (src / 'record-9214.txt').read_text()
    for s in statements.values():
        if s['text'] != source_text[s['start']:s['end']].strip() or digest(s['text']) != s['text_digest']:
            raise ValueError('Source boundary changed')
    if 'I now resume my functions' in statements['IND']['text']:
        raise ValueError('Chair role leaked into national speech')
    out = ROOT / spec['output_pack']
    if out.exists():
        raise ValueError('Fresh frozen pack required')
    cases, audit = [], []
    sources = '\n\n'.join(f"COMPLETE NATIONAL STATEMENT — {spec['countries'][c]['name']} — S/PV.9214, 9 December 2022\n{s['text']}" for c,s in statements.items())
    for country, data in spec['countries'].items():
        for unit_id, criterion, quote in data['units']:
            if quote not in statements[country]['text']:
                raise ValueError('Criterion quote absent: '+unit_id)
            offset = source_text.index(quote, statements[country]['start'], statements[country]['end'])
            audit.append({'id': unit_id, 'country': country, 'criterion': criterion,
                          'source_quote': quote, 'start': offset, 'end': offset+len(quote),
                          'basis': 'source fact or explicitly labeled application/absence judgment; no observed counterfactual label'})
        common = spec['scenario'] + '\n\n' + spec['request'].format(country_name=data['name']) + '\n\n' + sources
        appendix = '\n\nCHECKED RESPONSE PLAN (additional analyst assistance; recommendations are not historical commitments):\n' + '\n'.join('- '+x for x in data['plan'])
        for condition in ('raw', 'checked_plan'):
            c = {'id': f"9214-{country.lower()}-{condition}", 'country_iso3': country,
                 'condition': condition, 'scenario_id': spec['event'], 'split_group': spec['split_group'],
                 'prompt': [{'role': 'system', 'content': spec['system']},
                            {'role': 'user', 'content': common + (appendix if condition == 'checked_plan' else '')}],
                 'plan_appendix': appendix if condition == 'checked_plan' else '',
                 'plan_sha256': digest(data['plan']) if condition == 'checked_plan' else None,
                 'source_sha256': sha256(src / 'statements.json'),
                 'units': [x[0] for x in data['units']] + [x[0] for x in spec['universal_units']]}
            c['case_sha256'] = digest(c)
            cases.append(c)
    validate_cases(cases)
    out.mkdir(parents=True)
    shutil.copy2(spec_path, out / 'spec.json')
    shutil.copy2(__file__, out / 'builder.py')
    write_jsonl(out / 'cases.jsonl', cases)
    write_json(out / 'source-plan-audit.json', {
        'reviewer': 'same assistant as planner; not independent', 'units': audit,
        'bounded_absence': 'Complete Brazil statement does not demand specific 1267 Monitoring Team/reporting mechanism; national India statement does not promise a future vote. This is absence in these statements, not all national policy.',
        'source_faithful_positive_plan_checked': True, 'independent_review_complete': False})
    bench = ROOT / 'data/raw/unbench-audit-20260926/full/UNBench-all/meetings_adopted/2467/S_PV.9214-EN_statements.json'
    original = json.loads(bench.read_text())
    selected = [x for x in original['Statements'] if x['country']=='Brazil' or 'representative of India.' in x['statement'].replace('\\n',' ') ]
    if len(selected) != 2:
        raise ValueError('Benchmark linkage failed')
    write_json(out / 'benchmark-linkage.json', {'path': str(bench.relative_to(ROOT)), 'sha256': sha256(bench),
        'rows': selected, 'national_role_correction': 'India identified by explicit national switch in primary PDF; exclude return to chair.',
        'Brazil_closing_paragraph_present_in_benchmark': True})
    write_json(out / 'manifest.json', {
        'created_at': datetime.now(timezone.utc).isoformat(), 'status': 'frozen_before_generation',
        'cases': len(cases), 'expected_calls': 8, 'new_training_steps': 0,
        'spec_sha256': sha256(spec_path),
        'files_sha256': {p.name: sha256(p) for p in out.iterdir()},
        'source_files_sha256': {str(p.relative_to(ROOT)): sha256(p) for p in src.iterdir()},
        'known_exposure': 'No full document/resolution/draft symbols found in audited prior prepared packs and Aurora model-call case materials. Corpus acquired previously; base pretraining unknown; not certified deep OOD.',
        'limits': ['Two roles, one event, same-assistant planner/reviewer', 'National application transfers from a comparative-writer adapter',
                   'Plans supply extra assistance/tokens; not equal inference compute', 'Given historical positions; hypothetical recommendations have no observed vote labels'],
        'decision_rules': ['Inspect all eight complete answers and 96 atomic ratings before another run.',
                           'If raw fails and checked plan repairs, consider source-to-application supervision with teacher-only plans.',
                           'If both conditions fail, inspect plan/source/realization first; do not automatically fit.',
                           'If raw is already competent, move to bounded pressure/update test; do not fit redundant easy examples.']})
    print(json.dumps({'manifest_sha256': sha256(out / 'manifest.json'), 'cases': len(cases)}))


if __name__ == '__main__':
    main()
