"""Replay bytes, native tokens, optimization and stored manual judgments; not an independent judge."""
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, sha256, write_json
from verify_two_context_country import exited


def main():
    names = ['aurora-paired-application-base-20261007-v1',
             'aurora-paired-application-old-monitor-20261007-v1',
             'aurora-paired-application-fit-20261007-v1']
    names += json.loads((ROOT / 'reports/paired-application-endpoint-runs-20261007-v1.json').read_text())['runs'] if (ROOT / 'reports/paired-application-endpoint-runs-20261007-v1.json').exists() else []
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-paired-application-fit-20261007-v1.json').read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    summaries, resources, outputs, steps = {}, [], 0, 0
    for name in names:
        d = ROOT / 'runs' / name
        r = json.loads((d / 'run.json').read_text()); i = json.loads((d / 'inspection.json').read_text())
        pack = ROOT / r['config']['pack']; m = json.loads((pack / 'manifest.json').read_text()); h = json.loads((pack / 'manual-inspection.json').read_text())
        assert r['status'] == 'completed' and exited(r['identity']) and i['all_outputs_read_complete']
        assert r['pack_manifest_sha256'] == h['manifest_sha256'] == sha256(pack / 'manifest.json') and h['all_selected_texts_read_complete']
        for f, x in m['files_sha256'].items(): assert sha256(pack / f) == x
        for f, x in r['source_code_sha256'].items(): assert sha256(d / Path(f).name) == x
        assert r['versions'] == cfg['runtime_pins'] and r['gpu']['name'] == 'NVIDIA RTX PRO 6000 Blackwell Server Edition'
        for k in ['model', 'revision', 'seed', 'max_length', 'generation_max_new_tokens', 'chat_template_kwargs']: assert r['config'][k] == cfg[k]
        assert r['transcript_sha256'] == i['transcript_sha256'] == sha256(d / 'transcript.jsonl')
        assert i['manual_annotations_sha256'] == sha256(d / 'manual-annotations.json') and i['criteria_sha256'] == sha256(pack / 'criteria.json')
        cases, rows = list(read_jsonl(pack / 'cases.jsonl')), list(read_jsonl(d / 'transcript.jsonl'))
        criteria = json.loads((pack / 'criteria.json').read_text())
        assert len(cases) == len(rows) == len(i['reviews']) == r['outputs']
        for c, row, v in zip(cases, rows, i['reviews'], strict=True):
            assert c['id'] == row['id'] == v['id']
            assert c['input_ids'] == row['input_ids'] == tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
            assert tok.decode(row['output_ids'], skip_special_tokens=True) == row['output']
            assert hashlib.sha256(row['output'].encode()).hexdigest() == v['output_sha256'] and len(row['output'].split()) == v['words']
            assert v['content_counts'] == dict(Counter(z['status'] for z in v['ratings'].values()))
            assert set(v['ratings']) == set(criteria['common_units']) | set(criteria['source_units'][c['family']].get(c['country_iso3'], {}))
            assert not row['at_output_cap']
        if r.get('previous_inspected_run'):
            prev = r['previous_inspected_run']; pd = ROOT / prev.get('path', prev.get('run'))
            expected = prev['inspection_sha256']
            assert expected == sha256(pd / 'inspection.json') or ((pd / 'inspection-history' / (expected + '.json')).is_file() and expected == sha256(pd / 'inspection-history' / (expected + '.json')))
        if r['mode'] == 'adapter':
            adapter = ROOT / r['config']['adapter']
            assert r['loaded_adapter_sha256'] == sha256(adapter / 'adapter_model.safetensors')
        summaries[name] = [{'id': v['id'], 'content': v['content_counts'], 'words': v['words'],
                            'pass': v.get('component_pass', v.get('usable_realization_pass', False))} for v in i['reviews']]
        resources.append({'run': str(d.relative_to(ROOT)), 'identity': r['identity'], 'gpu': r['gpu'], 'exited': True})
        outputs += len(rows); steps += r['optimizer_steps']
    fit = ROOT / 'runs' / names[2]; r = json.loads((fit / 'run.json').read_text()); pack = ROOT / r['config']['pack']
    assert steps == r['optimizer_steps'] == 64 and r['matched_input_tokens']
    rank = r['optimization_checks']['rank_checks'][0]
    assert rank['pair_presentations'] == {a['id']: 32 for a in read_jsonl(pack / 'pair-audit.jsonl')}
    assert r['mask_audit']['actual_trainer_token_ids_and_masks_checked'] and r['mask_audit']['prompt_and_padding_excluded']
    assert r['initialization_checks']['base_initial_adapter_logits_exact'] and not r['initialization_checks']['loaded_trained_adapter']
    assert r['method']['reference_tensor_digest_before'] == r['method']['reference_tensor_digest_after'] and not r['method']['preference_gradient_enabled']
    assert r['actual_objective_guard']['loss_types'] == ['sft'] and r['actual_objective_guard']['loss_weights'] == [1.0]
    for g in r['actual_objective_guard']['native_logit_gradient_checks']:
        assert all(g[k] for k in ['rejected_logit_gradient_zero', 'prompt_padding_and_final_logit_gradient_zero', 'chosen_completion_logit_gradient_nonzero', 'parameter_gradients_not_accumulated'])
    assert r['serialization_checks']['saved_tensors_equal'] and r['serialization_checks']['same_base_probe_logits_equal']
    for f, x in r['serialization_checks']['files_sha256'].items(): assert sha256(fit / 'adapter' / f) == x
    pairs = list(read_jsonl(pack / 'pairs.jsonl')); audits = list(read_jsonl(pack / 'pair-audit.jsonl')); cases = list(read_jsonl(pack / 'cases.jsonl'))
    base = ROOT / 'runs' / names[0]; base_rows = list(read_jsonl(base / 'transcript.jsonl'))
    for pair, audit, case, row in zip(pairs, audits, cases[:2], base_rows[:2], strict=True):
        assert pair['prompt'] == case['prompt'] and pair['rejected'][0]['content'] == row['output']
        assert audit['prompt_ids'] == case['input_ids']
        for arm in ['chosen', 'rejected']:
            ids = tok.apply_chat_template(pair['prompt'] + pair[arm], tokenize=True, return_dict=False, enable_thinking=False)
            assert ids[:len(audit['prompt_ids'])] == audit['prompt_ids'] and ids[len(audit['prompt_ids']):] == audit[arm + '_ids']
    old = ROOT / 'data/prepared/minimal-application-fit-20261007-v1'
    targets = json.loads((pack / 'preferred-targets.json').read_text())['targets']
    assert targets[cases[0]['id']] == json.loads((old / 'preferred-targets.json').read_text())['targets'][cases[0]['id']]
    assert sha256(pack / 'criteria.json') == sha256(old / 'criteria.json')
    prefix = cases[0]['prompt'][1]['content'].split('CURRENT HYPOTHETICAL NOTE', 1)[0]
    assert all(c['prompt'][1]['content'].startswith(prefix) for c in cases)
    draft = ROOT / 'data/prepared/paired-application-states-20261007-v1'
    draft_manifest = json.loads((draft / 'manifest.json').read_text())
    launch = json.loads((fit / 'launch.json').read_text())
    assert draft_manifest['created_at'] < launch['created_at']
    assert cases == list(read_jsonl(draft / 'cases.jsonl'))
    for name in names[3:]:
        run = json.loads((ROOT / 'runs' / name / 'run.json').read_text())
        p = ROOT / run['config']['pack']
        if (p / 'actual-plan.json').exists():
            actual = json.loads((p / 'actual-plan.json').read_text())
            component_texts = []
            for link in actual['components']:
                d = ROOT / link['run']; rr = json.loads((d / 'run.json').read_text())
                assert link['run_sha256'] == sha256(d / 'run.json') and link['transcript_sha256'] == sha256(d / 'transcript.jsonl')
                assert link['inspection_sha256'] == sha256(d / 'inspection.json')
                row = next(r for r in read_jsonl(d / 'transcript.jsonl') if r['id'] == link['id'])
                component_texts.append(row['output'])
            assert actual['plan'] == '\n\n'.join(component_texts) and actual['words'] == len(actual['plan'].split())
            if run['mode'] == 'adapter':
                assert run['config']['adapter'] in ['runs/aurora-plan-input-fit-20261006-v1/adapter', 'runs/aurora-compression-fit-20261006-v1/adapter']
                writer = ROOT / run['config']['adapter']
                assert run['loaded_adapter_sha256'] == sha256(writer / 'adapter_model.safetensors')
            assert sha256(p / 'criteria.json') == sha256(ROOT / 'data/prepared/actual-composed-writer-20261007-v1/criteria.json')
    old_row = list(read_jsonl(ROOT / 'runs' / names[1] / 'transcript.jsonl'))[0]
    assert old_row['input_ids'] == cases[2]['input_ids']
    write_json(ROOT / 'reports/paired-application-checkpoint-20261007-v1.json', {
        'status': 'pass', 'verified_at': datetime.now(timezone.utc).isoformat(), 'new_model_outputs': outputs,
        'uncapped': outputs, 'capped': 0, 'new_optimizer_steps': steps, 'cumulative_qwen35_steps': 2910 + steps,
        'reference_qwen25_steps': 582, 'all_owned_gpu_identities_exited': True, 'resources': resources,
        'summaries': summaries, 'original_target_and_criteria_unchanged': True, 'source_factual_prefix_unchanged': True,
        'actual_presentations_each': 32, 'training_seconds': r['training_seconds'], 'peak_allocated_gpu_gib': r['peak_allocated_gpu_gib'],
        'independent_review_complete': False, 'scope': 'Familiar source, two fitting states and neutral untrained third state; adaptive same-assistant development. Replay checks execution/annotation arithmetic, not independent quality or persona/OOD/multi-agent gain.'})
    print(json.dumps({'status': 'pass', 'outputs': outputs, 'steps': steps, 'summaries': summaries}, indent=2))


if __name__ == '__main__':
    main()
