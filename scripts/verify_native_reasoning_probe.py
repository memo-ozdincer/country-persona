"""Replay the four native-mode traces, frozen criteria and provisional public-answer grades."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json
from country_persona.reasoning_output import split_native_output


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--sampled-profile', action='store_true')
    parser.add_argument('--sampling-version', choices=['v1','v2'], default='v1')
    args = parser.parse_args()
    pack = ROOT / ('data/prepared/native-sampling-20261006-' + args.sampling_version if args.sampled_profile else 'data/prepared/native-reasoning-20261006-v1')
    manifest = json.loads((pack / 'manifest.json').read_text())
    for name, expected in manifest['files_sha256'].items(): assert sha256(pack / name) == expected
    assert not manifest['training_authorized_for_this_pack']
    case = list(read_jsonl(pack / 'cases.jsonl'))[0]; criteria = json.loads((pack / 'criteria.json').read_text())
    original = next(c for c in read_jsonl(ROOT / 'data/prepared/synthesis-rehearsal-20261006-v1/cases.jsonl') if c['id'] == 'wps-raw')
    assert case == original
    proof = json.loads((pack / 'source-proof.json').read_text()); raw = ROOT / 'data/raw/source-application-grounding-20261003-v1'
    for name, expected in proof['wps_raw_files_sha256'].items(): assert sha256(raw / name) == expected
    text = (raw / 'record-8514.txt').read_text()
    for source in json.loads((pack / 'wps-statements.json').read_text()).values():
        assert text[source['start']:source['end']].strip() == source['text'] and digest(source['text']) == source['text_digest']
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(ROOT / manifest['adapter'], local_files_only=True)
    expected_units = {iso + ':' + key for iso in ('FRA', 'GBR') for key, _ in criteria['wps']['common'] + criteria['wps']['specific'][iso]}
    rows = {}; runs = {}; summaries = {}
    arms = ('base', 'adapter') if args.sampled_profile else ('base-off', 'adapter-off', 'base-on', 'adapter-on')
    for arm in arms:
        directory = ROOT / ('runs/aurora-native-' + ('sampling-' if args.sampled_profile else 'reasoning-') + arm + '-20261006-' + (args.sampling_version if args.sampled_profile else 'v1'))
        run = json.loads((directory / 'run.json').read_text()); inspection = json.loads((directory / 'inspection.json').read_text())
        assert run['status'] == 'completed' and run['optimizer_steps'] == 0 and inspection['all_outputs_read_complete'] and inspection['all_reasoning_read_complete']
        assert run['transcript_sha256'] == inspection['transcript_sha256'] == sha256(directory / 'transcript.jsonl')
        assert run['pack_manifest_sha256'] == sha256(pack / 'manifest.json') and inspection['criteria_sha256'] == sha256(pack / 'criteria.json')
        for source, expected in run['source_code_sha256'].items(): assert sha256(directory / Path(source).name) == expected
        row = list(read_jsonl(directory / 'transcript.jsonl'))[0]; rating = inspection['reviews'][0]
        assert row['id'] == case['id'] == rating['id'] and rating['all_output_read_complete']
        assert hashlib.sha256(row['output'].encode()).hexdigest() == rating['output_sha256']
        config = run['config']; flag = config['chat_template_kwargs']['enable_thinking']
        assert flag == (True if args.sampled_profile else arm.endswith('-on'))
        ids = tokenizer.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, **config['chat_template_kwargs'])
        assert ids == row['input_ids'] and len(ids) + config['generation_max_new_tokens'] <= config['max_length']
        split = split_native_output(row['output_ids'], thinking=flag, open_id=manifest['thinking_marker_ids']['<think>'], close_id=manifest['thinking_marker_ids']['</think>'], eos_id=tokenizer.eos_token_id)
        for key, expected in split.items(): assert row[key] == expected
        assert tokenizer.decode(row['output_ids'], skip_special_tokens=False) == row['raw_output']
        assert tokenizer.decode(split['reasoning_ids'], skip_special_tokens=True) == row['reasoning']
        assert tokenizer.decode(split['public_ids'], skip_special_tokens=True) == row['output']
        assert len(row['reasoning_ids']) + row['boundary_tokens'] + len(row['public_ids']) == len(row['output_ids'])
        assert set(rating['ratings']) == expected_units and set(rating['universal_checks']) == set(criteria['universal_checks']) and set(rating['synthesis_checks']) == set(criteria['synthesis_checks'])
        values = [*rating['ratings'].values(), *rating['universal_checks'].values(), *rating['synthesis_checks'].values()]
        assert all(v['status'] in {'met', 'unmet', 'unratable'} and v['reason'].strip() for v in values)
        if arm.startswith('adapter'): assert run['loaded_adapter_sha256'] == manifest['adapter_sha256'] == sha256(ROOT / manifest['adapter'] / 'adapter_model.safetensors')
        if args.sampled_profile:
            effective = row['effective_generation_config']; profile = config['sampling_profile']
            assert effective['do_sample'] is True and row['presence_processor_calls'] == row['generated_tokens']
            assert row['presence_penalty'] == profile['presence_penalty'] == 1.5 and row['sampling_seed_reset_before_generation'] == 42
            for key in ('temperature', 'top_p', 'top_k', 'min_p', 'repetition_penalty'): assert effective[key] == profile[key]
        summaries[arm] = {'content_met': sum(v['status'] == 'met' for v in rating['ratings'].values()),
                          'content_unratable': sum(v['status'] == 'unratable' for v in rating['ratings'].values()), 'content_units': len(expected_units),
                          'guards_met': sum(v['status'] == 'met' for v in rating['universal_checks'].values()),
                          'synthesis_met': sum(v['status'] == 'met' for v in rating['synthesis_checks'].values()),
                          'source_criteria_pass': bool(row['output'].strip()) and row['protocol_status'] == 'public_answer' and not row['at_output_cap'] and not rating.get('additional_source_fidelity_observations') and all(v['status'] == 'met' for v in values),
                          'public_words': len(row['output'].split()), 'within300words': bool(row['output'].strip()) and len(row['output'].split()) <= 300,
                          'reasoning_tokens': row['reasoning_tokens'], 'public_tokens_including_eos': row['public_tokens_including_eos'],
                          'total_generated_tokens': row['generated_tokens'], 'generation_seconds': row['generation_seconds'], 'at_output_cap': row['at_output_cap'], 'protocol_status': row['protocol_status']}
        rows[arm] = row; runs[arm] = run
    if args.sampled_profile:
        assert rows['base']['input_ids'] == rows['adapter']['input_ids']
    else:
        for mode in ('off', 'on'): assert rows['base-' + mode]['input_ids'] == rows['adapter-' + mode]['input_ids']
    reference = 'base' if args.sampled_profile else 'base-off'
    for run in runs.values():
        expected_budget = 4096 if args.sampled_profile and args.sampling_version == 'v2' else 2048
        assert run['config']['generation_max_new_tokens'] == expected_budget and run['gpu']['name'] == 'NVIDIA RTX PRO 6000 Blackwell Server Edition'
        for key in ('versions', 'source_code_sha256'): assert run[key] == runs[reference][key]
        for key in ('model', 'revision', 'seed', 'max_length'): assert run['config'][key] == runs[reference]['config'][key]
    historical = {}
    for arm, old in ([] if args.sampled_profile else [('base-off', 'aurora-synthesis-rehearsal-base-wps-20261006-v1'), ('adapter-off', 'aurora-synthesis-rehearsal-fit-20261006-v1')]):
        previous = next(r for r in read_jsonl(ROOT / 'runs' / old / 'transcript.jsonl') if r['id'] == 'wps-raw')
        historical[arm] = {'old512_tokens': len(previous['output_ids']), 'old_at_cap': previous['at_output_cap'],
                           'old_input_ids_equal': previous['input_ids'] == rows[arm]['input_ids'],
                           'old_output_ids_match_new_prefix': previous['output_ids'] == rows[arm]['output_ids'][:len(previous['output_ids'])]}
    result = {'status': 'sampled_author_profile_traces_and_public_annotations_replayed' if args.sampled_profile else 'four_native_mode_traces_and_public_annotations_replayed',
              'new_model_calls': len(arms), 'new_optimizer_steps': 0,
              'cumulative_aurora_qwen35_steps': 414, 'reference_qwen25_steps': 582, 'summary': summaries,
              'historical512_prefix_replay': historical, 'actual_input_output_tokens_replayed': True,
              'scope': 'Same exposed one-family development, same unblinded assistant. Native mode/decoder changes consume a different share of a matched total budget. Sampling followup is one fixed-seed draw per weight arm, not an expected-performance estimate or isolated presence effect. No independent persona, sealed OOD, native vote or multi-agent gain.'}
    write_json(args.output, result); print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
