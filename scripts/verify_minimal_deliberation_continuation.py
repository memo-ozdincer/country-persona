"""Replay frozen synchronous visibility, saved annotations, and actual token traces."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.deliberation import COUNTRIES, PROTOCOL, make_case, transition_metrics
from country_persona.io import digest, read_jsonl, sha256, write_json
from build_minimal_deliberation_continuation import canonical, inspected_rows


def checked_run(directory, pack, tokenizer):
    manifest = json.loads((pack / 'manifest.json').read_text())
    for name, value in manifest['files_sha256'].items():
        if sha256(pack / name) != value:
            raise ValueError('Changed frozen pack file: ' + name)
    if sha256(pack / 'builder-code.py') != manifest['builder_sha256']:
        raise ValueError('Changed preparation code')
    rows = inspected_rows(directory)
    run = json.loads((directory / 'run.json').read_text())
    review = json.loads((directory / 'inspection.json').read_text())
    cases = list(read_jsonl(pack / 'cases.jsonl'))
    if len(rows) != len(cases) or len(review['reviews']) != len(cases):
        raise ValueError('Incomplete review pairing')
    if run['pack_manifest_sha256'] != sha256(pack / 'manifest.json') or run['manual_inspection_sha256'] != sha256(pack / 'manual-inspection.json'):
        raise ValueError('Changed inspected launch pack')
    if review['criteria_sha256'] != sha256(pack / 'criteria.json'):
        raise ValueError('Changed content criteria')
    if run['versions'] != run['config']['runtime_pins'] or run['gpu']['name'] != 'NVIDIA RTX PRO 6000 Blackwell Server Edition':
        raise ValueError('Different runtime or GPU')
    for source, expected in run['source_code_sha256'].items():
        if sha256(directory / Path(source).name) != expected:
            raise ValueError('Changed archived inference code')
    if run['mode'] == 'adapter':
        if run['loaded_adapter_sha256'] != manifest['adapter_sha256'] or sha256(ROOT / manifest['selected_adapter'] / 'adapter_model.safetensors') != manifest['adapter_sha256']:
            raise ValueError('Different selected weights')
    elif run['mode'] != 'base':
        raise ValueError('This checkpoint permits evaluation only')
    criteria = json.loads((pack / 'criteria.json').read_text())
    for case, row, rating in zip(cases, rows, review['reviews']):
        if not case['id'] == row['id'] == rating['id'] or hashlib.sha256(row['output'].encode()).hexdigest() != rating['output_sha256']:
            raise ValueError('Changed answer/rating pairing')
        if not rating['all_output_read_complete']:
            raise ValueError('Inspect each complete answer')
        cap = PROTOCOL['final_output_cap'] if case['country_iso3'] == 'ALL' else PROTOCOL['agent_output_cap']
        if row['generated_tokens'] > cap or len(row['input_ids']) + cap > PROTOCOL['context_budget']:
            raise ValueError('Original token budget exceeded')
        if tokenizer is not None:
            ids = tokenizer.apply_chat_template(case['prompt'], tokenize=True, return_dict=False,
                    add_generation_prompt=True, **run['config']['chat_template_kwargs'])
            if ids != row['input_ids'] or tokenizer.decode(row['output_ids'], skip_special_tokens=True) != row['output']:
                raise ValueError('Actual token replay differs')
        expected = ({c + ':' + u['id'] for c in COUNTRIES for u in criteria[c]['criteria']}
                    if case['country_iso3'] == 'ALL' else {u['id'] for u in criteria[case['country_iso3']]['criteria']})
        if set(rating['ratings']) != expected:
            raise ValueError('Changed atomic unit inventory')
        expected_guards = set(criteria['FRA']['universal_checks'])
        if set(rating['universal_checks']) != expected_guards:
            raise ValueError('Changed universal guard inventory')
        for item in [*rating['ratings'].values(), *rating['universal_checks'].values()]:
            if item['status'] not in {'met', 'unmet', 'unratable'} or not item['reason'].strip():
                raise ValueError('Invalid semantic annotation')
    return cases, rows, run, review


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--render-tokenizer', action='store_true')
    p.add_argument('--include-synthesis', action='store_true')
    p.add_argument('--include-adapted-aggregator', action='store_true')
    args = p.parse_args()
    parent = ROOT / 'data/prepared/minimal-deliberation-initials-20261006-v1'
    initial_cases = list(read_jsonl(parent / 'cases.jsonl'))
    tokenizer = None
    if args.render_tokenizer:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(ROOT / 'runs/aurora-minimal-country-fit-20261005-v4/adapter', local_files_only=True)
    summary, revisions = {}, {}
    for arm in ('base', 'fourtarget'):
        pack = ROOT / 'data/prepared/minimal-deliberation-revisions-20261006-v1' / arm
        directory = ROOT / ('runs/aurora-minimal-deliberation-revisions-' + arm + '-20261006-v1')
        cases, rows, run, review = checked_run(directory, pack, tokenizer)
        initials_dir = ROOT / ('runs/aurora-minimal-deliberation-initials-' + arm + '-20261006-v1')
        initials = inspected_rows(initials_dir)
        initial_review = json.loads((initials_dir / 'inspection.json').read_text())
        scenario = json.loads((pack / 'scenario.json').read_text())
        notes = [canonical(row, packed['original_case'], country, initials_dir, 'initial')
                 for country, row, packed in zip(COUNTRIES, initials, initial_cases)]
        if json.loads((pack / 'histories.json').read_text())[arm] != notes:
            raise ValueError('Visible notes differ from saved actual initials')
        for condition in ('independent_revision', 'peer_revision'):
            content, guards, corrections, regressions, caps = 0, 0, 0, 0, 0
            nations = {}
            for case, row, rating in zip(cases, rows, review['reviews']):
                if case['scenario'] != condition:
                    continue
                country = case['country_iso3']; i = list(COUNTRIES).index(country)
                visible = notes if condition == 'peer_revision' else [notes[i]]
                if make_case(scenario, condition, 'revision', country, visible) != case['original_case']:
                    raise ValueError('Original synchronous visibility changed')
                before = {k: v['status'] for k, v in initial_review['reviews'][i]['ratings'].items()}
                after = {k: v['status'] for k, v in rating['ratings'].items()}
                transition = transition_metrics(before, after)
                met = sum(v == 'met' for v in after.values())
                passed = sum(v['status'] == 'met' for v in rating['universal_checks'].values())
                content += met; guards += passed; corrections += transition['known_corrections']; regressions += transition['known_regressions']; caps += row['at_output_cap']
                nations[country] = {'met': met, 'units': len(after), 'guards_met': passed, 'transition_from_initial': transition}
            summary[arm + '-' + condition] = {'content_met': content, 'content_units': 24, 'guards_met': guards, 'guard_units': 16,
                                              'corrections_from_initial': corrections, 'regressions_from_initial': regressions,
                                              'outputs_at_cap': caps, 'national': nations}
        revisions[arm] = (cases, rows, directory)
    synthesis = {}
    adapted_synthesis = {}
    if args.include_synthesis:
        pack = ROOT / 'data/prepared/minimal-deliberation-synthesis-20261006-v1'
        directory = ROOT / 'runs/aurora-minimal-deliberation-synthesis-20261006-v1'
        cases, rows, run, review = checked_run(directory, pack, tokenizer)
        if run['mode'] != 'base':
            raise ValueError('Aggregator must remain unadapted base')
        scenario = json.loads((pack / 'scenario.json').read_text())
        expected_checks = json.loads((pack / 'synthesis-criteria.json').read_text())
        for case, row, rating in zip(cases, rows, review['reviews']):
            old_cases, old_rows, old_dir = revisions[case['arm']]
            notes = [canonical(r, c['original_case'], c['country_iso3'], old_dir, 'revision')
                     for c, r in zip(old_cases, old_rows) if c['scenario'] == case['scenario']]
            if make_case(scenario, case['scenario'], 'synthesis', 'ALL', notes) != case['original_case']:
                raise ValueError('Synthesis history differs from saved actual revisions')
            if set(rating['synthesis_checks']) != set(expected_checks):
                raise ValueError('Changed original synthesis checks')
            synthesis[case['id']] = {'diagnostic_content_met': sum(v['status'] == 'met' for v in rating['ratings'].values()),
                                    'diagnostic_content_units': 24, 'synthesis_checks_met': sum(v['status'] == 'met' for v in rating['synthesis_checks'].values()),
                                    'synthesis_check_units': 5, 'at_output_cap': row['at_output_cap']}
        if args.include_adapted_aggregator:
            adapted_pack = ROOT / 'data/prepared/minimal-deliberation-adapted-aggregator-20261006-v1'
            adapted_dir = ROOT / 'runs/aurora-minimal-deliberation-adapted-aggregator-20261006-v1'
            other_cases, other_rows, other_run, other_review = checked_run(adapted_dir, adapted_pack, tokenizer)
            if cases != other_cases or [r['input_ids_digest'] for r in rows] != [r['input_ids_digest'] for r in other_rows]:
                raise ValueError('Aggregator ablation requires identical actual prompts')
            if other_run['mode'] != 'adapter' or other_run['versions'] != run['versions'] or other_run['source_code_sha256'] != run['source_code_sha256']:
                raise ValueError('Aggregator ablation changed another runtime factor')
            if sha256(adapted_pack / 'criteria.json') != sha256(pack / 'criteria.json') or sha256(adapted_pack / 'synthesis-criteria.json') != sha256(pack / 'synthesis-criteria.json'):
                raise ValueError('Aggregator criteria changed')
            for row, rating, original_rating in zip(other_rows, other_review['reviews'], review['reviews']):
                if set(rating['synthesis_checks']) != set(expected_checks):
                    raise ValueError('Aggregator synthesis check inventory changed')
                transition = transition_metrics({k: v['status'] for k, v in original_rating['ratings'].items()},
                                                {k: v['status'] for k, v in rating['ratings'].items()})
                adapted_synthesis[row['id']] = {'diagnostic_content_met': sum(v['status'] == 'met' for v in rating['ratings'].values()),
                                               'diagnostic_content_units': 24, 'synthesis_checks_met': sum(v['status'] == 'met' for v in rating['synthesis_checks'].values()),
                                               'synthesis_check_units': 5, 'at_output_cap': row['at_output_cap'], 'transition_from_identical_input_base_aggregator': transition}
    elif args.include_adapted_aggregator:
        raise ValueError('Verify original synthesis before separate aggregator ablation')
    result = {'status': 'original_synchronous_continuation_replay_passed', 'new_model_answers': 24 if args.include_adapted_aggregator else 20 if args.include_synthesis else 16,
              'new_optimizer_steps': 0, 'revision_summary': summary, 'synthesis_summary': synthesis,
              'separate_adapted_aggregator_summary': adapted_synthesis,
              'actual_prompt_and_output_tokens_replayed': args.render_tokenizer,
              'scope': 'Same-assistant annotations on historically exposed climate event; original self/peer protocol and shared sources. Own model histories differ across weight arms. No independent persona or autonomous multi-agent gain.',
              'selected_adapter_has_four_targets_and_64_updates': True,
              'cumulative_aurora_qwen35_optimizer_steps': 286, 'separate_reference_qwen25_optimizer_steps': 582}
    write_json(args.output, result)
    print(json.dumps({'revisions': {k: {a: b for a, b in v.items() if a != 'national'} for k, v in summary.items()}, 'synthesis': synthesis, 'separate_adapted_aggregator': adapted_synthesis}, indent=2))


if __name__ == '__main__':
    main()
