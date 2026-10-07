"""Replay the two-state warm fit, excluded-state answers, retention and actual-plan writer."""
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json
from verify_two_context_country import exited

NAMES = ['aurora-uk-paired-application-base-20261007-v1',
         'aurora-uk-paired-application-parent-20261007-v1',
         'aurora-uk-paired-application-fit-20261007-v1',
         'aurora-uk-application-retention-20261007-v1',
         'aurora-uk-complete-plan-writer-base-20261007-v1',
         'aurora-uk-complete-plan-writer-point8-20261007-v1']


def main():
    from transformers import AutoTokenizer
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-uk-paired-application-fit-20261007-v1.json').read_text())
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    summaries, resources, all_inputs, count, steps = {}, [], [], 0, 0
    for name in NAMES:
        d = ROOT / 'runs' / name
        r = json.loads((d / 'run.json').read_text())
        i = json.loads((d / 'inspection.json').read_text())
        p = ROOT / r['config']['pack']
        m = json.loads((p / 'manifest.json').read_text())
        h = json.loads((p / 'manual-inspection.json').read_text())
        assert r['status'] == 'completed' and exited(r['identity']) and i['all_outputs_read_complete']
        assert r['pack_manifest_sha256'] == h['manifest_sha256'] == sha256(p / 'manifest.json')
        assert r['manual_inspection_sha256'] == sha256(p / 'manual-inspection.json')
        assert h['all_selected_texts_read_complete'] and m['created_at'] < r['created_at']
        for f, x in m['files_sha256'].items():
            assert sha256(p / f) == x
        for f, x in r['source_code_sha256'].items():
            assert sha256(d / Path(f).name) == x
        assert r['versions'] == cfg['runtime_pins'] and r['gpu']['name'] == 'NVIDIA RTX PRO 6000 Blackwell Server Edition'
        for k in ['model', 'revision', 'seed', 'max_length', 'generation_max_new_tokens', 'chat_template_kwargs']:
            assert r['config'][k] == cfg[k]
        assert r['transcript_sha256'] == i['transcript_sha256'] == sha256(d / 'transcript.jsonl')
        assert i['manual_annotations_sha256'] == sha256(d / 'manual-annotations.json') and i['criteria_sha256'] == sha256(p / 'criteria.json')
        cases, rows = list(read_jsonl(p / 'cases.jsonl')), list(read_jsonl(d / 'transcript.jsonl'))
        crit = json.loads((p / 'criteria.json').read_text())
        assert len(cases) == len(rows) == len(i['reviews']) == r['outputs']
        for c, row, v in zip(cases, rows, i['reviews'], strict=True):
            assert c['id'] == row['id'] == v['id']
            assert c['input_ids'] == row['input_ids'] == tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
            assert tok.decode(row['output_ids'], skip_special_tokens=True) == row['output']
            assert hashlib.sha256(row['output'].encode()).hexdigest() == v['output_sha256']
            assert len(row['output'].split()) == v['words'] and not row['at_output_cap']
            assert v['content_counts'] == dict(Counter(x['status'] for x in v['ratings'].values()))
            assert set(v['ratings']) == set(crit['source_units'][c['family']][c['country_iso3']]) | set(crit['common_units'])
            assert set(v['universal_checks']) == set(crit['universal_checks'])
            all_met = all(x['status'] == 'met' for x in list(v['ratings'].values()) + list(v['universal_checks'].values()))
            flag = v.get('component_pass', v.get('usable_realization_pass'))
            assert flag == (all_met and all(v['presentation'].values()))
        prev = r['previous_inspected_run']
        assert prev['inspection_sha256'] == sha256(ROOT / prev.get('path', prev.get('run')) / 'inspection.json')
        if r['mode'] == 'adapter':
            assert r['loaded_adapter_sha256'] == sha256(ROOT / r['config']['adapter'] / 'adapter_model.safetensors')
        summaries[name] = [{'id': v['id'], 'content': v['content_counts'], 'words': v['words'], 'pass': v.get('component_pass', v.get('usable_realization_pass'))} for v in i['reviews']]
        all_inputs.append([c['input_ids'] for c in cases])
        resources.append({'run': str(d.relative_to(ROOT)), 'identity': r['identity'], 'gpu': r['gpu'], 'exited': True})
        count += len(rows)
        steps += r['optimizer_steps']
    assert all_inputs[0] == all_inputs[1] == all_inputs[2] and all_inputs[4] == all_inputs[5]
    fit = ROOT / 'runs' / NAMES[2]
    r = json.loads((fit / 'run.json').read_text())
    p = ROOT / r['config']['pack']
    pairs, audits = list(read_jsonl(p / 'pairs.jsonl')), list(read_jsonl(p / 'pair-audit.jsonl'))
    assert steps == 64 and len(pairs) == 2 and r['matched_input_tokens']
    rank = r['optimization_checks']['rank_checks'][0]
    assert rank['steps'] == rank['microbatches'] == rank['gradient_checks'] == 64
    assert rank['pair_presentations'] == {a['id']: 32 for a in audits}
    assert r['loaded_adapter_sha256'] == cfg['starting_adapter_sha256'] == sha256(ROOT / cfg['starting_adapter'] / 'adapter_model.safetensors')
    assert r['initialization_checks']['parent_reload']['saved_tensors_equal'] and r['initialization_checks']['parent_reload']['same_base_probe_logits_equal']
    assert r['method']['reference_tensor_digest_before'] == r['method']['reference_tensor_digest_after'] == r['initialization_checks']['parent_tensor_digest']
    assert not r['method']['preference_gradient_enabled'] and not r['method']['optimizer_state_resumed']
    assert r['actual_objective_guard']['loss_types'] == ['sft'] and r['actual_objective_guard']['loss_weights'] == [1.0]
    assert r['mask_audit']['actual_trainer_token_ids_and_masks_checked'] and r['mask_audit']['prompt_and_padding_excluded']
    for g in r['actual_objective_guard']['native_logit_gradient_checks']:
        assert all(g[k] for k in ['rejected_logit_gradient_zero', 'prompt_padding_and_final_logit_gradient_zero', 'chosen_completion_logit_gradient_nonzero', 'parameter_gradients_not_accumulated'])
    assert r['serialization_checks']['saved_tensors_equal'] and r['serialization_checks']['same_base_probe_logits_equal']
    for f, x in r['serialization_checks']['files_sha256'].items():
        assert sha256(fit / 'adapter' / f) == x
    base = ROOT / 'runs' / NAMES[0]
    before = list(read_jsonl(base / 'transcript.jsonl'))
    for pair, a, row in zip(pairs, audits, before[:2], strict=True):
        assert pair['rejected'][0]['content'] == row['output'] and a['prompt_ids'] == row['input_ids']
        for arm in ['chosen', 'rejected']:
            ids = tok.apply_chat_template(pair['prompt'] + pair[arm], tokenize=True, return_dict=False, enable_thinking=False)
            assert ids[:len(a['prompt_ids'])] == a['prompt_ids'] and ids[len(a['prompt_ids']):] == a[arm + '_ids']
    assert rank['actual_sequence_tokens'] == 32 * sum(2 * len(a['prompt_ids']) + len(a['chosen_ids']) + len(a['rejected_ids']) for a in audits)
    assert rank['actual_target_tokens'] == 32 * sum(len(a['chosen_ids']) + len(a['rejected_ids']) for a in audits)
    draft = ROOT / 'data/prepared/uk-paired-application-20261007-v1'
    assert list(read_jsonl(p / 'cases.jsonl')) == list(read_jsonl(draft / 'cases.jsonl'))
    assert json.loads((p / 'preferred-targets.json').read_text()) == json.loads((draft / 'preferred-targets.json').read_text())
    assert {a['id'] for a in audits} == {'uk-R-existing-repair-application', 'uk-S-existing-repair-application'}
    writer = ROOT / 'data/prepared/uk-complete-plan-writer-20261007-v1'
    plan = json.loads((writer / 'actual-plan.json').read_text())
    parts = []
    for link in plan['components']:
        d = ROOT / link['run']
        assert link['transcript_sha256'] == sha256(d / 'transcript.jsonl') and link['inspection_sha256'] == sha256(d / 'inspection.json')
        row = next(x for x in read_jsonl(d / 'transcript.jsonl') if x['id'] == link['id'])
        assert digest(row) == link['row_digest']
        parts.append(row['output'])
    assert plan['plan'] == '\n\n'.join(parts) and len(plan['plan'].split()) == plan['words'] == 285 and plan['application_intermediate_pass']
    assert list(read_jsonl(writer / 'cases.jsonl'))[0]['prompt'][1]['content'].count(plan['plan']) == 1
    retention = ROOT / 'data/prepared/uk-application-retention-20261007-v1'
    provenance = json.loads((retention / 'provenance.json').read_text())
    original_cases = list(read_jsonl(ROOT / 'data/prepared/two-country-application-fit-20261007-v1/cases.jsonl'))
    assert list(read_jsonl(retention / 'cases.jsonl')) == [original_cases[j] for j in [0, 3]]
    for link in provenance['exact_historical_controls']:
        d = ROOT / link['run']
        assert link['transcript_sha256'] == sha256(d / 'transcript.jsonl') and link['inspection_sha256'] == sha256(d / 'inspection.json')
    failed = ROOT / 'runs/uk-paired-application-finalization-failure-20261007-v1'
    failure = json.loads((failed / 'failure.json').read_text())
    assert failure['optimizer_steps'] == failure['model_outputs'] == 0 and failure['failure_log_sha256'] == sha256(failed / 'failure.log')
    write_json(ROOT / 'reports/uk-paired-application-checkpoint-20261007-v1.json', {'status': 'pass', 'verified_at': datetime.now(timezone.utc).isoformat(), 'new_model_outputs': count, 'uncapped': count, 'capped': 0, 'new_optimizer_steps': steps, 'cumulative_qwen35_steps': 3198 + steps, 'selected_branch_steps': 128 + steps, 'reference_qwen25_steps': 582, 'all_owned_gpu_identities_exited': True, 'resources': resources, 'summaries': summaries, 'training_seconds': r['training_seconds'], 'peak_allocated_gpu_gib': r['peak_allocated_gpu_gib'], 'actual_sequence_tokens': rank['actual_sequence_tokens'], 'actual_both_completion_tokens': rank['actual_target_tokens'], 'actual_chosen_supervised_tokens': 32 * sum(len(a['chosen_ids']) for a in audits), 'actual_presentations_each': 32, 'independent_review_complete': False, 'failed_optimizer_steps': 0, 'failed_model_outputs': 0, 'scope': 'Two complete UK fitting states, two excluded but exposed partial states, exact France/India historical retention and actual285-point writer. Same-assistant development annotations; no independent, sealed OOD, persona/native prediction or multi-agent gain.'})
    print(json.dumps({'status': 'pass', 'outputs': count, 'steps': steps, 'summaries': summaries}, indent=2))


if __name__ == '__main__':
    main()
