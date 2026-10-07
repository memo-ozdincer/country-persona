"""Replay paired Brazil application evidence; no independent semantic assessment."""
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

NAMES = ['aurora-brazil-M-base-20261007-v1', 'aurora-brazil-M-mixed224-20261007-v1', 'aurora-paired-brazil-application-fit-20261007-v1']


def main():
    from transformers import AutoTokenizer
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-paired-brazil-application-fit-20261007-v1.json').read_text())
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    resources, summaries, inputs, count, steps = [], {}, [], 0, 0
    for name in NAMES:
        d = ROOT / 'runs' / name
        r, i = json.loads((d / 'run.json').read_text()), json.loads((d / 'inspection.json').read_text())
        p = ROOT / r['config']['pack']
        m, h = json.loads((p / 'manifest.json').read_text()), json.loads((p / 'manual-inspection.json').read_text())
        assert r['status'] == 'completed' and exited(r['identity']) and i['all_outputs_read_complete']
        assert r['pack_manifest_sha256'] == h['manifest_sha256'] == sha256(p / 'manifest.json') and h['all_selected_texts_read_complete']
        assert m['created_at'] < r['created_at']
        for f, x in m['files_sha256'].items(): assert sha256(p / f) == x
        for f, x in r['source_code_sha256'].items(): assert sha256(d / Path(f).name) == x
        assert r['versions'] == cfg['runtime_pins'] and r['gpu']['name'] == 'NVIDIA RTX PRO 6000 Blackwell Server Edition'
        for k in ['model', 'revision', 'seed', 'max_length', 'generation_max_new_tokens', 'chat_template_kwargs']: assert r['config'][k] == cfg[k]
        assert r['transcript_sha256'] == i['transcript_sha256'] == sha256(d / 'transcript.jsonl')
        assert i['manual_annotations_sha256'] == sha256(d / 'manual-annotations.json') and i['criteria_sha256'] == sha256(p / 'criteria.json')
        cases, rows = list(read_jsonl(p / 'cases.jsonl')), list(read_jsonl(d / 'transcript.jsonl'))
        crit = json.loads((p / 'criteria.json').read_text())
        assert len(cases) == len(rows) == len(i['reviews']) == r['outputs']
        for c, row, v in zip(cases, rows, i['reviews'], strict=True):
            assert c['id'] == row['id'] == v['id'] and c['input_ids'] == row['input_ids'] == tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
            assert tok.decode(row['output_ids'], skip_special_tokens=True) == row['output'] and hashlib.sha256(row['output'].encode()).hexdigest() == v['output_sha256']
            assert not row['at_output_cap'] and len(row['output'].split()) == v['words']
            assert set(v['ratings']) == set(crit['common_units']) and set(v['universal_checks']) == set(crit['universal_checks'])
            assert v['content_counts'] == dict(Counter(x['status'] for x in v['ratings'].values()))
            all_met = all(x['status'] == 'met' for x in list(v['ratings'].values()) + list(v['universal_checks'].values()))
            assert v['component_pass'] == (all_met and all(v['presentation'].values()))
        prev = r['previous_inspected_run']; assert prev['inspection_sha256'] == sha256(ROOT / prev.get('path', prev.get('run')) / 'inspection.json')
        if r['mode'] == 'adapter': assert r['loaded_adapter_sha256'] == sha256(ROOT / r['config']['adapter'] / 'adapter_model.safetensors')
        summaries[name] = [{'id': v['id'], 'content': v['content_counts'], 'words': v['words'], 'pass': v['component_pass']} for v in i['reviews']]
        resources.append({'run': str(d.relative_to(ROOT)), 'identity': r['identity'], 'gpu': r['gpu'], 'exited': True})
        inputs.append([c['input_ids'] for c in cases]); count += len(rows); steps += r['optimizer_steps']
    assert inputs[0] == inputs[1] == inputs[2][11:12]
    fit = ROOT / 'runs' / NAMES[2]; r = json.loads((fit / 'run.json').read_text()); p = ROOT / r['config']['pack']
    pairs, audits = list(read_jsonl(p / 'pairs.jsonl')), list(read_jsonl(p / 'pair-audit.jsonl'))
    assert steps == 256 and len(pairs) == 8 and r['matched_input_tokens']
    rank = r['optimization_checks']['rank_checks'][0]
    assert rank['steps'] == rank['microbatches'] == rank['gradient_checks'] == 256 and rank['pair_presentations'] == {a['id']: 32 for a in audits}
    assert r['initialization_checks']['base_initial_adapter_logits_exact'] and not r['initialization_checks']['loaded_trained_adapter']
    assert r['mask_audit']['actual_trainer_token_ids_and_masks_checked'] and r['mask_audit']['prompt_and_padding_excluded']
    assert r['method']['reference_tensor_digest_before'] == r['method']['reference_tensor_digest_after'] and not r['method']['preference_gradient_enabled']
    assert r['actual_objective_guard']['loss_types'] == ['sft'] and r['actual_objective_guard']['loss_weights'] == [1.0]
    for g in r['actual_objective_guard']['native_logit_gradient_checks']: assert all(g[k] for k in ['rejected_logit_gradient_zero', 'prompt_padding_and_final_logit_gradient_zero', 'chosen_completion_logit_gradient_nonzero', 'parameter_gradients_not_accumulated'])
    assert r['serialization_checks']['saved_tensors_equal'] and r['serialization_checks']['same_base_probe_logits_equal']
    for f, x in r['serialization_checks']['files_sha256'].items(): assert sha256(fit / 'adapter' / f) == x
    replay = ROOT / cfg['baseline_run']; b = json.loads((replay / 'run.json').read_text()); bi = json.loads((replay / 'inspection.json').read_text())
    assert b['status'] == 'completed_cpu_replay' and bi['all_outputs_read_complete'] and b['transcript_sha256'] == bi['transcript_sha256'] == sha256(replay / 'transcript.jsonl')
    before = list(read_jsonl(replay / 'transcript.jsonl'))
    for link, row in zip(b['source_links'], before, strict=True):
        origin = ROOT / link['run']
        for key in ['run', 'transcript', 'inspection']: assert sha256(origin / (key + ('.jsonl' if key == 'transcript' else '.json'))) == link[key + '_sha256']
        actual = next(x for x in read_jsonl(origin / 'transcript.jsonl') if x['id'] == row['id'])
        assert actual == row and row['input_ids'] == next(c['input_ids'] for c in read_jsonl(p / 'cases.jsonl') if c['id'] == row['id'])
    for pair, audit, row in zip(pairs, audits, before[:8], strict=True):
        assert pair['rejected'][0]['content'] == row['output']
        for arm in ['chosen', 'rejected']:
            ids = tok.apply_chat_template(pair['prompt'] + pair[arm], tokenize=True, return_dict=False, enable_thinking=False)
            assert ids[:len(audit['prompt_ids'])] == audit['prompt_ids'] and ids[len(audit['prompt_ids']):] == audit[arm + '_ids']
    originals = {}
    for folder in ['four-country-application-fit-20261007-v1', 'paired-brazil-application-20261007-v1']: originals.update(json.loads((ROOT / 'data/prepared' / folder / 'preferred-targets.json').read_text())['targets'])
    assert originals == json.loads((p / 'preferred-targets.json').read_text())['targets']
    previous_seven = json.loads((ROOT / 'data/prepared/four-country-application-fit-20261007-v1/preferred-targets.json').read_text())['targets']
    current_eight = json.loads((p / 'preferred-targets.json').read_text())['targets']
    assert all(current_eight[k] == v for k, v in previous_seven.items())
    assert set(current_eight) - set(previous_seven) == {'brazil-K-source-checked-application'}
    assert len(current_eight['brazil-K-source-checked-application'].split()) == 88
    assert rank['actual_sequence_tokens'] == 32 * sum(2 * len(a['prompt_ids']) + len(a['chosen_ids']) + len(a['rejected_ids']) for a in audits)
    assert rank['actual_target_tokens'] == 32 * sum(len(a['chosen_ids']) + len(a['rejected_ids']) for a in audits)
    reuse = json.loads((ROOT / 'reports/paired-brazil-application-composition-reuse-20261007-v1.json').read_text())
    assert reuse['new_application_transcript_sha256'] == sha256(fit / 'transcript.jsonl')
    assert reuse['new_application_inspection_sha256'] == sha256(fit / 'inspection.json')
    wp = ROOT / reuse['writer_input_pack']
    wm = json.loads((wp / 'manifest.json').read_text())
    for f, x in wm['files_sha256'].items(): assert sha256(wp / f) == x
    plan = json.loads((wp / 'actual-plan.json').read_text())
    component = plan['components'][0]
    source_run = ROOT / component['run']
    assert component['transcript_sha256'] == sha256(source_run / 'transcript.jsonl')
    assert component['inspection_sha256'] == sha256(source_run / 'inspection.json')
    source_row = next(x for x in read_jsonl(source_run / 'transcript.jsonl') if x['id'] == component['id'])
    assert digest(source_row) == component['row_digest']
    app = next(x for x in read_jsonl(fit / 'transcript.jsonl') if x['id'] == reuse['new_application_id'])['output']
    assert source_row['output'] + '\n\n' + app == plan['plan']
    assert len(plan['plan'].split()) == reuse['plan_words'] == 285 and reuse['new_writer_calls'] == 0
    writer = ROOT / reuse['actual_writer_run']
    assert reuse['actual_writer_transcript_sha256'] == sha256(writer / 'transcript.jsonl')
    assert reuse['actual_writer_inspection_sha256'] == sha256(writer / 'inspection.json')
    wi = json.loads((writer / 'inspection.json').read_text())
    assert wi['all_outputs_read_complete'] and wi['reviews'][0]['usable_realization_pass']
    assert wi['reviews'][0]['words'] == 274 and wi['reviews'][0]['content_counts'] == {'met': 14}
    writer_case = next(read_jsonl(wp / 'cases.jsonl'))
    assert 'France' in writer_case['prompt'][0]['content'] and 'COUNTRY/ROLE/DATE: UK' in writer_case['prompt'][1]['content']
    assert reuse['historical_writer_role_prompt_mismatch'] is True
    raw = ROOT / 'data/raw/source-plan-grounding-20261002-v1'; acquisition = json.loads((raw / 'acquisition.json').read_text())
    for f, x in acquisition['files_sha256'].items(): assert sha256(raw / f) == x
    source = json.loads((raw / 'statements.json').read_text())['BRA']; assert (raw / 'record-9214.txt').read_text()[source['start']:source['end']].strip() == source['text']
    write_json(ROOT / 'reports/paired-brazil-application-checkpoint-20261007-v1.json', {'status': 'pass', 'verified_at': datetime.now(timezone.utc).isoformat(), 'new_model_outputs': count, 'uncapped': count, 'capped': 0, 'new_optimizer_steps': steps, 'cumulative_qwen35_steps': 3678 + steps, 'selected_mixed_branch_steps': 256, 'reference_qwen25_steps': 582, 'all_owned_gpu_identities_exited': True, 'resources': resources, 'summaries': summaries, 'training_seconds': r['training_seconds'], 'peak_allocated_gpu_gib': r['peak_allocated_gpu_gib'], 'actual_sequence_tokens': rank['actual_sequence_tokens'], 'actual_both_completion_tokens': rank['actual_target_tokens'], 'actual_chosen_supervised_tokens': 32 * sum(len(a['chosen_ids']) for a in audits), 'actual_presentations_each': 32, 'historical_base_outputs_replayed': 12, 'actual_writer_outputs_reused': 1, 'historical_writer_role_prompt_mismatch': True, 'new_writer_outputs': 0, 'independent_review_complete': False, 'scope': 'Seven old texts/inputs/exposures unchanged plus one BrazilK target32 presentations. L/M, UKT/E and authenticatedP excluded; M newly frozen before calls/fit. Same-author adaptive development; read individual results rather than inferring global improvement. Same-author development, not independent persona/native-prediction/multi-agent or sealed OOD evidence.'})
    print(json.dumps({'status': 'pass', 'new_outputs': count, 'steps': steps, 'summaries': summaries}, indent=2))


if __name__ == '__main__': main()
