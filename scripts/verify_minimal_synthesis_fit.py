"""Portable trace, warm-start, mask, stored-review and transfer replay for one target."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, sha256, write_json
from country_persona.deliberation import transition_metrics


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--render-tokenizer', action='store_true')
    args = p.parse_args()
    pack = ROOT / 'data/prepared/minimal-synthesis-fit-20261006-v2'
    manifest = json.loads((pack / 'manifest.json').read_text())
    for name, expected in manifest['files_sha256'].items():
        if sha256(pack / name) != expected:
            raise ValueError('Changed frozen source/target/input/criteria')
    cases = list(read_jsonl(pack / 'cases.jsonl')); criteria = json.loads((pack / 'criteria.json').read_text())
    tokenizer = None
    if args.render_tokenizer:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(ROOT / manifest['starting_adapter'], local_files_only=True)
    summaries, traces, records, inspections = {}, {}, {}, {}
    directories = {'base': 'aurora-minimal-synthesis-base-replay-20261006-v2',
                   'parent': 'aurora-minimal-synthesis-parent-replay-20261006-v2',
                   'fit': 'aurora-minimal-synthesis-fit-20261006-v2'}
    for arm, name in directories.items():
        directory = ROOT / 'runs' / name
        run = json.loads((directory / 'run.json').read_text()); review = json.loads((directory / 'inspection.json').read_text())
        rows = list(read_jsonl(directory / 'transcript.jsonl'))
        if run['status'] != 'completed' or len(rows) != 6 or len(review['reviews']) != 6 or not review['all_outputs_read_complete']:
            raise ValueError('Complete inspected six-case trace required')
        if sha256(directory / 'transcript.jsonl') != run['transcript_sha256'] or review['transcript_sha256'] != run['transcript_sha256']:
            raise ValueError('Changed actual trace/review binding')
        if run['pack_manifest_sha256'] != sha256(pack / 'manifest.json') or review['criteria_sha256'] != sha256(pack / 'criteria.json'):
            raise ValueError('Changed frozen pack or rubric')
        for source, expected in run['source_code_sha256'].items():
            if sha256(directory / Path(source).name) != expected:
                raise ValueError('Changed archived run code')
        if arm != 'fit':
            actual = ROOT / run['actual_run_directory']
            if run['kind'] != 'CPU_token_replay_of_actual_completed_generation' or run['model_calls'] != 0:
                raise ValueError('Controls must be labelled actual-generation replays')
            if sha256(actual / 'run.json') != run['actual_run_sha256'] or sha256(actual / 'transcript.jsonl') != run['transcript_sha256']:
                raise ValueError('Changed linked original model run')
        score = {}
        for case, row, rating in zip(cases, rows, review['reviews']):
            if not case['id'] == row['id'] == rating['id'] or not rating['all_output_read_complete']:
                raise ValueError('Changed output pairing or unread answer')
            if hashlib.sha256(row['output'].encode()).hexdigest() != rating['output_sha256']:
                raise ValueError('Changed full response')
            if tokenizer is not None:
                ids = tokenizer.apply_chat_template(case['prompt'], tokenize=True, return_dict=False,
                        add_generation_prompt=True, **run['config']['chat_template_kwargs'])
                if ids != row['input_ids'] or tokenizer.decode(row['output_ids'], skip_special_tokens=True) != row['output']:
                    raise ValueError('Actual token replay differs')
            family = case['family']
            expected = (set(criteria['retention']['units']) if family == 'sanctions_retention' else
                        {c + ':' + u['id'] for c, r in criteria[family]['national_policy_rubrics'].items() for u in r['criteria']})
            if set(rating['ratings']) != expected:
                raise ValueError('Changed atomic criterion inventory')
            units = rating['ratings']; guards = rating.get('universal_checks', {})
            synth = rating.get('synthesis_checks', {})
            if family != 'sanctions_retention':
                if set(guards) != set(criteria[family]['national_policy_rubrics']['FRA']['universal_checks']) or set(synth) != set(criteria[family]['synthesis_checks']):
                    raise ValueError('Source/synthesis guard inventory changed')
            for value in [*units.values(), *guards.values(), *synth.values()]:
                if value['status'] not in {'met', 'unmet', 'unratable'} or not value['reason'].strip():
                    raise ValueError('Invalid stored annotation')
            score[case['id']] = {'content_met': sum(v['status'] == 'met' for v in units.values()),
                                'content_unratable': sum(v['status'] == 'unratable' for v in units.values()),
                                'content_units': len(units), 'guards_met': sum(v['status'] == 'met' for v in guards.values()),
                                'guard_units': len(guards), 'synthesis_met': sum(v['status'] == 'met' for v in synth.values()),
                                'synthesis_unratable': sum(v['status'] == 'unratable' for v in synth.values()),
                                'synthesis_units': len(synth), 'at_output_cap': row['at_output_cap'],
                                'additional_source_observations_present': bool(rating.get('additional_source_fidelity_observations')),
                                'strict_pass': not row['at_output_cap'] and not rating.get('additional_source_fidelity_observations') and all(v['status'] == 'met' for v in [*units.values(), *guards.values(), *synth.values()])}
        summaries[arm] = score; traces[arm] = rows; records[arm] = run; inspections[arm] = review
    for arm in ('parent', 'fit'):
        if [r['input_ids_digest'] for r in traces[arm]] != [r['input_ids_digest'] for r in traces['base']]:
            raise ValueError('Before/after input tokens differ')
        for key in ('versions', 'source_code_sha256'):
            if records[arm][key] != records['base'][key]:
                raise ValueError('Runtime or inference code changed')
        if records[arm]['gpu']['name'] != records['base']['gpu']['name'] or records[arm]['gpu']['name'] != 'NVIDIA RTX PRO 6000 Blackwell Server Edition':
            raise ValueError('GPU type changed')
    fit = records['fit']; rank = fit['optimization_checks']['rank_checks'][0]
    if fit['starting_adapter_sha256'] != manifest['starting_adapter_sha256'] or records['parent']['loaded_adapter_sha256'] != manifest['starting_adapter_sha256']:
        raise ValueError('Warm-start differs from measured parent')
    # The one-row dataloader flushes its partial accumulation at every epoch;
    # configured accumulation2 therefore does not imply64 microbatches.
    if rank['steps'] != 32 or rank['actual_sequence_tokens'] != 4559 * 32 or rank['actual_target_tokens'] != 348 * 32:
        raise ValueError('Actual update or completion-token budget changed')
    if not fit['mask_audit']['actual_trainer_masks_checked'] or not fit['serialization_checks']['reload_verified_after_state_perturbation']:
        raise ValueError('Actual masks or saved-state reload unverified')
    from safetensors.torch import load_file
    from country_persona.training_checks import tensor_state_digest
    if tensor_state_digest(load_file(str(ROOT / manifest['starting_adapter'] / 'adapter_model.safetensors'))) != rank['initial_adapter_digest']:
        raise ValueError('Optimizer began from different saved tensors')
    adapter = ROOT / 'runs/aurora-minimal-synthesis-fit-20261006-v2/adapter'
    for name, expected in fit['serialization_checks']['files_sha256'].items():
        if sha256(adapter / name) != expected:
            raise ValueError('Saved trained adapter changed')
    failed = json.loads((ROOT / 'runs/aurora-minimal-synthesis-fit-20261006-v1/failure.json').read_text())
    if failed['error'] != 'ValueError: Actual trainer input differs from the audited template at row 0' or 'optimization_checks' in failed:
        raise ValueError('Failed guard receipt no longer matches pre-optimizer stop')
    transitions = {}
    for case, before, after in zip(cases, inspections['parent']['reviews'], inspections['fit']['reviews']):
        transitions[case['id']] = transition_metrics({k: v['status'] for k, v in before['ratings'].items()},
                                                   {k: v['status'] for k, v in after['ratings'].items()})
    exact = traces['fit'][0]['output'] == (pack / 'target.txt').read_text().rstrip('\n')
    result = {'status': 'one_complete_target_warm_start_and_stored_reviews_replayed',
              'new_actual_model_answers': 18, 'replayed_control_model_calls': 0, 'new_optimizer_steps': 32,
              'failed_attempt_optimizer_steps': 0, 'cumulative_aurora_qwen35_steps': 318, 'reference_qwen25_steps': 582,
              'actual_microbatches': 32, 'configured_gradient_accumulation': 2, 'one_row_epoch_partial_accumulation_flushed': True,
              'target_exact_free_generation_text_match': exact, 'summary': summaries, 'transitions_from_parent': transitions,
              'actual_input_output_tokens_replayed': args.render_tokenizer,
              'scope': 'One climate target learned on a saved four-target parent; historically exposed Ukraine outside these fits and sanctions retention controls. Same-assistant annotations, no sealed confirmation or independent persona gain.'}
    write_json(args.output, result); print(json.dumps({'target_exact_match': exact, 'summary': summaries}, indent=2))


if __name__ == '__main__':
    main()
