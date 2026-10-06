"""Replay actual direct-attribution and checked-ledger controls, without semantic certification."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.deliberation import evidence_packet, validate_scenario
from country_persona.io import read_jsonl, sha256, write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--render-tokenizer', action='store_true')
    args = p.parse_args()
    pack = ROOT / 'data/prepared/minimal-attribution-ledger-20261006-v2'
    manifest = json.loads((pack / 'manifest.json').read_text())
    for name, value in manifest['files_sha256'].items():
        if sha256(pack / name) != value:
            raise ValueError('Frozen ledger/control file changed')
    scenario = json.loads((pack / 'scenario.json').read_text()); validate_scenario(scenario)
    cases = list(read_jsonl(pack / 'cases.jsonl'))
    original = next(c for c in read_jsonl(ROOT / 'data/prepared/minimal-deliberation-synthesis-20261006-v1/cases.jsonl')
                    if c['id'] == 'fourtarget-peer_revision-synthesis')
    if not cases[0]['prompt'][1]['content'].endswith(evidence_packet(scenario)):
        raise ValueError('Direct attribution question changed its complete sources')
    if cases[1]['prompt'] != [original['prompt'][0], {'role': 'user', 'content': original['prompt'][1]['content'] + '\n\n' + (pack / 'checked-ledger.txt').read_text().rstrip('\n')}]:
        raise ValueError('Ledger must be the only added memo input')
    tokenizer = None
    if args.render_tokenizer:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(ROOT / manifest['selected_adapter'], local_files_only=True)
    results, traces, records = {}, {}, {}
    criteria = json.loads((pack / 'criteria.json').read_text())
    for arm in ('base', 'fourtarget'):
        directory = ROOT / ('runs/aurora-minimal-attribution-ledger-' + arm + '-20261006-v2')
        run = json.loads((directory / 'run.json').read_text())
        review = json.loads((directory / 'inspection.json').read_text())
        rows = list(read_jsonl(directory / 'transcript.jsonl'))
        if run['status'] != 'completed' or len(rows) != 2 or len(review['reviews']) != 2 or not review['all_outputs_read_complete']:
            raise ValueError('Complete reviewed paired controls required')
        if sha256(directory / 'transcript.jsonl') != run['transcript_sha256'] or review['transcript_sha256'] != run['transcript_sha256']:
            raise ValueError('Changed actual transcript')
        if run['pack_manifest_sha256'] != sha256(pack / 'manifest.json') or run['manual_inspection_sha256'] != sha256(pack / 'manual-inspection.json') or review['criteria_sha256'] != sha256(pack / 'criteria.json'):
            raise ValueError('Changed frozen launch/review bindings')
        for source, expected in run['source_code_sha256'].items():
            if sha256(directory / Path(source).name) != expected:
                raise ValueError('Changed archived launch code')
        if arm == 'fourtarget' and run['loaded_adapter_sha256'] != manifest['adapter_sha256']:
            raise ValueError('Wrong fitted weights')
        for case, row, rating in zip(cases, rows, review['reviews']):
            if not case['id'] == row['id'] == rating['id'] or hashlib.sha256(row['output'].encode()).hexdigest() != rating['output_sha256'] or not rating['all_output_read_complete']:
                raise ValueError('Changed answer/rating pairing')
            if row['generated_tokens'] > 512 or len(row['input_ids']) + 512 > 8192:
                raise ValueError('Context/output budget exceeded')
            if tokenizer is not None:
                ids = tokenizer.apply_chat_template(case['prompt'], tokenize=True, return_dict=False,
                        add_generation_prompt=True, **run['config']['chat_template_kwargs'])
                if ids != row['input_ids'] or tokenizer.decode(row['output_ids'], skip_special_tokens=True) != row['output']:
                    raise ValueError('Actual token replay differs')
            expected = set(criteria['direct']) if case['id'] == 'direct-g5-attribution' else set(criteria['synthesis'])
            if set(rating['ratings']) != expected:
                raise ValueError('Different semantic unit inventory')
            for unit in rating['ratings'].values():
                if unit['status'] not in {'met', 'unmet', 'unratable'} or not unit['reason'].strip():
                    raise ValueError('Invalid stored semantic annotation')
            if set(rating['source_guards']) != set(criteria['national_diagnostic']['FRA']['universal_checks']):
                raise ValueError('Different source guard inventory')
        results[arm] = {r['id']: {'met': sum(v['status'] == 'met' for v in r['ratings'].values()),
                                'unratable': sum(v['status'] == 'unratable' for v in r['ratings'].values()),
                                'units': len(r['ratings']), 'source_guards_met': sum(v['status'] == 'met' for v in r['source_guards'].values()),
                                'source_guard_units': len(r['source_guards']),
                                'strict_pass': all(v['status'] == 'met' for v in [*r['ratings'].values(), *r['source_guards'].values()]) and not rows[i]['at_output_cap'],
                                'at_output_cap': rows[i]['at_output_cap']}
                        for i, r in enumerate(review['reviews'])}
        records[arm] = run; traces[arm] = rows
    if [r['input_ids_digest'] for r in traces['base']] != [r['input_ids_digest'] for r in traces['fourtarget']]:
        raise ValueError('Base/fit token inputs differ')
    for key in ('versions', 'source_code_sha256'):
        if records['base'][key] != records['fourtarget'][key]:
            raise ValueError('Before/after runtime changed')
    if records['base']['gpu']['name'] != records['fourtarget']['gpu']['name'] or records['base']['gpu']['name'] != 'NVIDIA RTX PRO 6000 Blackwell Server Edition':
        raise ValueError('Before/after GPU changed')
    if sha256(ROOT / manifest['selected_adapter'] / 'adapter_model.safetensors') != manifest['adapter_sha256']:
        raise ValueError('Saved adapter changed')
    result = {'status': 'direct_and_ledger_stored_review_replay_passed', 'new_complete_model_answers': 4,
              'new_optimizer_steps': 0, 'summary': results, 'actual_input_output_tokens_replayed': args.render_tokenizer,
              'scope': 'Same-assistant exposed development annotation; short checked ledger is supplied source assistance, not model learning or independent persona gain.',
              'superseded_preparation': 'v1 own process stopped with exact identity before any answer or optimizer update; merged words corrected in v2.'}
    write_json(args.output, result); print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
