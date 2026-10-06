"""Replay frozen bytes, actual-token pairing, saved tensors and stored annotations."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json
from country_persona.deliberation import transition_metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--render-tokenizer', action='store_true')
    args = parser.parse_args()
    pack = ROOT / 'data/prepared/synthesis-rehearsal-20261006-v1'
    manifest = json.loads((pack / 'manifest.json').read_text())
    for name, expected in manifest['files_sha256'].items():
        assert sha256(pack / name) == expected, name
    assert json.loads((pack / 'manual-inspection.json').read_text())['manifest_sha256'] == sha256(pack / 'manifest.json')
    proof = json.loads((pack / 'source-proof.json').read_text())
    raw = ROOT / 'data/raw/source-application-grounding-20261003-v1'
    for name, expected in proof['wps_raw_files_sha256'].items(): assert sha256(raw / name) == expected
    document = (raw / 'record-8514.txt').read_text()
    for statement in json.loads((pack / 'wps-statements.json').read_text()).values():
        assert document[statement['start']:statement['end']].strip() == statement['text']
        assert digest(statement['text']) == statement['text_digest']
    assert sha256(ROOT / 'data/prepared/minimal-country-20261005-v1/sources.json') == proof['sanctions_source_pack_sha256']
    from country_persona.eval_evidence import normalize
    for evidence in proof['inherited_climate_ukraine']:
        source = ROOT / 'data/raw/eval-sources-20260927' / evidence['source_id']
        columns = json.loads(source.with_suffix('.columns.json').read_text())
        text = '\n\n'.join(normalize(s['text']) for s in columns['sections'])
        assert sha256(source.with_suffix('.pdf')) == evidence['pdf_sha256'] and digest(text) == evidence['document_text_digest']
        assert digest(text[evidence['document_start']:evidence['document_end']].rstrip()) == evidence['text_digest']
    cases = list(read_jsonl(pack / 'cases.jsonl')); criteria = json.loads((pack / 'criteria.json').read_text())
    tokenizer = None
    if args.render_tokenizer:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(ROOT / manifest['starting_adapter'], local_files_only=True)
    directories = {arm: 'aurora-synthesis-rehearsal-' + arm + '-replay-20261006-v1' for arm in ('base','parent','one')}
    directories['fit'] = 'aurora-synthesis-rehearsal-fit-20261006-v1'
    summaries = {}; records = {}; traces = {}; inspections = {}
    for arm, name in directories.items():
        directory = ROOT / 'runs' / name
        run = json.loads((directory / 'run.json').read_text()); inspection = json.loads((directory / 'inspection.json').read_text())
        outputs = list(read_jsonl(directory / 'transcript.jsonl'))
        assert run['status'] == 'completed' and len(outputs) == len(inspection['reviews']) == 7
        assert run['transcript_sha256'] == inspection['transcript_sha256'] == sha256(directory / 'transcript.jsonl')
        assert run['pack_manifest_sha256'] == sha256(pack / 'manifest.json') and inspection['criteria_sha256'] == sha256(pack / 'criteria.json')
        for source, expected in run['source_code_sha256'].items(): assert sha256(directory / Path(source).name) == expected
        if arm != 'fit':
            assert run['kind'] == 'CPU_token_replay_combining_actual_completed_generations' and run['model_calls'] == 0
            actual_by_case = {}
            for origin in run['actual_model_runs']:
                original = ROOT / origin['path']; original_record = json.loads((original / 'run.json').read_text())
                assert sha256(original / 'run.json') == origin['run_sha256'] and original_record['identity'] == origin['identity']
                assert sha256(original / 'transcript.jsonl') == original_record['transcript_sha256']
                actual_by_case[origin['path']] = {r['id']: r for r in read_jsonl(original / 'transcript.jsonl')}
            for output in outputs: assert actual_by_case[run['actual_generation_origin_by_case'][output['id']]][output['id']] == output
            for original in inspection['original_inspections']: assert sha256(ROOT / original['path']) == original['sha256']
        score = {}
        for case, output, review in zip(cases, outputs, inspection['reviews']):
            assert case['id'] == output['id'] == review['id'] and review['all_output_read_complete']
            assert hashlib.sha256(output['output'].encode()).hexdigest() == review['output_sha256']
            if tokenizer:
                ids = tokenizer.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, **run['config']['chat_template_kwargs'])
                assert ids == output['input_ids'] and tokenizer.decode(output['output_ids'], skip_special_tokens=True) == output['output']
            family = case['family']
            if family == 'wps':
                expected = {c + ':' + k for c in ('FRA','GBR') for k, _ in criteria['wps']['common'] + criteria['wps']['specific'][c]}
            elif family == 'sanctions_retention': expected = set(criteria['retention']['units'])
            else: expected = {c + ':' + u['id'] for c, r in criteria[family]['national_policy_rubrics'].items() for u in r['criteria']}
            assert set(review['ratings']) == expected
            values = [*review['ratings'].values(), *review.get('universal_checks', {}).values(), *review.get('synthesis_checks', {}).values()]
            assert all(v['status'] in {'met','unmet','unratable'} and v['reason'].strip() for v in values)
            if family != 'sanctions_retention':
                assert set(review['universal_checks']) == set(criteria['climate']['national_policy_rubrics']['FRA']['universal_checks'])
                assert set(review['synthesis_checks']) == set(criteria['climate']['synthesis_checks'])
            units = review['ratings']; guards = review.get('universal_checks', {}); synth = review.get('synthesis_checks', {})
            score[case['id']] = {'met': sum(v['status'] == 'met' for v in units.values()), 'unratable': sum(v['status'] == 'unratable' for v in units.values()),
                                'units': len(units), 'guards_met': sum(v['status'] == 'met' for v in guards.values()), 'guard_units': len(guards),
                                'synthesis_met': sum(v['status'] == 'met' for v in synth.values()), 'synthesis_units': len(synth),
                                'at_output_cap': output['at_output_cap'], 'strict_pass': not output['at_output_cap'] and not review.get('additional_source_fidelity_observations') and all(v['status'] == 'met' for v in values)}
        summaries[arm] = score; records[arm] = run; traces[arm] = outputs; inspections[arm] = inspection
    for arm in ('parent','one','fit'):
        assert [r['input_ids'] for r in traces[arm]] == [r['input_ids'] for r in traces['base']]
        for key in ('versions','source_code_sha256'): assert records[arm][key] == records['base'][key]
        assert records[arm]['gpu']['name'] == records['base']['gpu']['name'] == 'NVIDIA RTX PRO 6000 Blackwell Server Edition'
    fit = records['fit']; rank = fit['optimization_checks']['rank_checks'][0]
    preflight = json.loads((ROOT / 'reports/synthesis-rehearsal-preflight-20261006.json').read_text())
    assert rank['steps'] == 96 and rank['actual_sequence_tokens'] == preflight['expected_sequence_tokens'] and rank['actual_target_tokens'] == preflight['expected_supervised_tokens']
    assert fit['starting_adapter_sha256'] == records['parent']['loaded_adapter_sha256'] == manifest['starting_adapter_sha256']
    assert fit['mask_audit']['actual_trainer_masks_checked'] and fit['serialization_checks']['reload_verified_after_state_perturbation']
    from safetensors.torch import load_file
    from country_persona.training_checks import tensor_state_digest
    assert tensor_state_digest(load_file(str(ROOT / manifest['starting_adapter'] / 'adapter_model.safetensors'))) == rank['initial_adapter_digest']
    adapter = ROOT / 'runs/aurora-synthesis-rehearsal-fit-20261006-v1/adapter'
    for name, expected in fit['serialization_checks']['files_sha256'].items(): assert sha256(adapter / name) == expected
    transitions = {case['id']: transition_metrics({k:v['status'] for k,v in before['ratings'].items()}, {k:v['status'] for k,v in after['ratings'].items()}) for case,before,after in zip(cases,inspections['parent']['reviews'],inspections['fit']['reviews'])}
    rows = list(read_jsonl(pack / 'train.jsonl'))
    exact = {'climate': traces['fit'][0]['output'] == rows[4]['completion'][0]['content'], 'ukraine': traces['fit'][2]['output'] == rows[5]['completion'][0]['content']}
    result = {'status': 'frozen_bytes_actual_tokens_weights_and_stored_annotations_replayed', 'new_model_answers': 13,
              'replayed_old_actual_answers': 15, 'new_optimizer_steps': 96, 'cumulative_aurora_qwen35_steps': 414,
              'selected_branch_steps': 160, 'reference_qwen25_steps': 582, 'actual_sequence_tokens': rank['actual_sequence_tokens'],
              'actual_supervised_tokens': rank['actual_target_tokens'], 'complete_dataset_passes_matching_token_counts': 32,
              'native_six_row_accumulation_two_implied_microbatches': 192, 'exact_training_text_matches': exact,
              'summary': summaries, 'transitions_from_parent': transitions, 'actual_input_output_tokens_replayed': args.render_tokenizer,
              'scope': 'Same-assistant development annotations. WPS outside selected fitting episodes but historically exposed; no sealed OOD, native vote prediction, validated persona or autonomous multi-agent gain.'}
    write_json(args.output, result); print(json.dumps({'exact': exact, 'summary': summaries}, indent=2))


if __name__ == '__main__':
    main()
