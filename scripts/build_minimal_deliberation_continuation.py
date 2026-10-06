"""Freeze original synchronous revisions from inspected saved four-country initials."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.deliberation import COUNTRIES, PROTOCOL, make_case, validate_scenario
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl


def inspected_rows(directory):
    run = json.loads((directory / 'run.json').read_text())
    review = json.loads((directory / 'inspection.json').read_text())
    if run['status'] != 'completed' or not review['all_outputs_read_complete']:
        raise ValueError('Inspect complete upstream outputs before continuation')
    if sha256(directory / 'transcript.jsonl') != run['transcript_sha256'] or run['transcript_sha256'] != review['transcript_sha256']:
        raise ValueError('Changed inspected upstream transcript')
    return list(read_jsonl(directory / 'transcript.jsonl'))


def canonical(row, case, country, directory, stage):
    return {**row, 'id': case['id'], 'case_sha256': case['case_sha256'],
            'response_id': digest([str(directory.relative_to(ROOT)), case['case_sha256'], row['output_ids']])[:24],
            'country': country, 'stage': stage, 'case': case,
            'prompt_tokens': len(row['input_ids'])}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage', choices=['revision', 'synthesis'], required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError('Fresh frozen pack required')
    parent = ROOT / 'data/prepared/minimal-deliberation-initials-20261006-v1'
    scenario = json.loads((parent / 'scenario.json').read_text())
    validate_scenario(scenario)
    refs = next(r for r in read_jsonl(ROOT / 'data/prepared/deliberation-probe-20260928-v1/review.references.jsonl')
                if r['scenario_id'] == scenario['id'])
    initial_cases = list(read_jsonl(parent / 'cases.jsonl'))
    upstream, cases, histories = {}, [], {}
    for arm in ('base', 'fourtarget'):
        if args.stage == 'revision':
            directory = ROOT / ('runs/aurora-minimal-deliberation-initials-' + arm + '-20261006-v1')
            rows = inspected_rows(directory)
            if len(rows) != 4:
                raise ValueError('Require exactly four frozen initial notes')
            notes = []
            for country, row, packed in zip(COUNTRIES, rows, initial_cases):
                if row['id'] != packed['id'] or packed['country_iso3'] != country:
                    raise ValueError('Wrong initial country pairing')
                notes.append(canonical(row, packed['original_case'], country, directory, 'initial'))
            histories[arm] = notes
            for condition in ('independent_revision', 'peer_revision'):
                for i, country in enumerate(COUNTRIES):
                    visible = notes if condition == 'peer_revision' else [notes[i]]
                    case = make_case(scenario, condition, 'revision', country, visible)
                    cases.append({'id': arm + '-' + condition + '-' + country.lower(), 'country_iso3': country,
                                  'family': arm + '_revision', 'scenario': condition, 'arm': arm,
                                  'prompt': case['prompt'], 'original_case': case})
        else:
            directory = ROOT / ('runs/aurora-minimal-deliberation-revisions-' + arm + '-20261006-v1')
            rows = inspected_rows(directory)
            prior = ROOT / 'data/prepared/minimal-deliberation-revisions-20261006-v1' / arm
            packed_rows = list(read_jsonl(prior / 'cases.jsonl'))
            if len(rows) != 8 or len(packed_rows) != 8:
                raise ValueError('Require complete own/peer revision inventory')
            for condition in ('independent_revision', 'peer_revision'):
                notes = []
                for row, packed in zip(rows, packed_rows):
                    if row['id'] != packed['id']:
                        raise ValueError('Wrong revision pairing')
                    if packed['scenario'] == condition:
                        notes.append(canonical(row, packed['original_case'], packed['country_iso3'], directory, 'revision'))
                if [n['country'] for n in notes] != list(COUNTRIES):
                    raise ValueError('Require four national revised notes in original order')
                histories[arm + '-' + condition] = notes
                case = make_case(scenario, condition, 'synthesis', 'ALL', notes)
                cases.append({'id': arm + '-' + condition + '-synthesis', 'country_iso3': 'ALL',
                              'family': 'unadapted_base_synthesis', 'scenario': condition, 'arm': arm,
                              'prompt': case['prompt'], 'original_case': case})
        upstream[arm] = {'run_directory': str(directory.relative_to(ROOT)),
                         'run_sha256': sha256(directory / 'run.json'),
                         'transcript_sha256': sha256(directory / 'transcript.jsonl'),
                         'inspection_sha256': sha256(directory / 'inspection.json')}
    # Each revision arm has its own generated history. This is an end-to-end
    # comparison, not a claim of identical input tokens across model weights.
    groups = {arm: [c for c in cases if c['arm'] == arm] for arm in ('base', 'fourtarget')} if args.stage == 'revision' else {'all': cases}
    for arm, group in groups.items():
        out = args.output / arm if args.stage == 'revision' else args.output
        out.mkdir(parents=True)
        write_jsonl(out / 'train.jsonl', [])
        write_jsonl(out / 'train.manifest.jsonl', [])
        write_jsonl(out / 'cases.jsonl', group)
        write_json(out / 'scenario.json', scenario)
        write_json(out / 'criteria.json', json.loads((parent / 'criteria.json').read_text()))
        write_json(out / 'synthesis-criteria.json', refs['synthesis_checks'])
        write_json(out / 'histories.json', {arm: histories[arm]} if args.stage == 'revision' else histories)
        (out / 'builder-code.py').write_bytes(Path(__file__).read_bytes())
        write_json(out / 'manifest.json', {
            'question': 'Do source-faithful initial gains survive synchronous own/peer revision and fixed-base aggregation?',
            'training_authorized_for_this_pack': False, 'stage': args.stage, 'arm': arm, 'eval_cases': len(group),
            'decision': 'Read every complete output before the next stage. Preserve original own/peer contrast and source criteria; no fit or sweep.',
            'protocol': PROTOCOL, 'upstream': {arm: upstream[arm]} if args.stage == 'revision' else upstream,
            'parent_manifest_sha256': sha256(parent / 'manifest.json'), 'builder_sha256': sha256(Path(__file__)),
            'selected_adapter': 'runs/aurora-minimal-country-fit-20261005-v4/adapter',
            'adapter_sha256': sha256(ROOT / 'runs/aurora-minimal-country-fit-20261005-v4/adapter/adapter_model.safetensors'),
            'files_sha256': {f.name: sha256(f) for f in out.iterdir() if f.is_file()},
            'visibility': 'Only frozen preceding-stage notes. Revisions never enter another revision prompt.',
            'scope': 'Previously exposed climate event, one shared source packet; end-to-end histories differ across weights.',
            'independent_review_complete': False})
        print(json.dumps({'pack': str(out), 'cases': len(group), 'stage': args.stage}), flush=True)


if __name__ == '__main__':
    main()
