"""Portable replay of native compression fitting, matching controls and manual annotations."""
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


def main():
    cfgpath = ROOT / 'configs/posttraining/qwen35-compression-20261006-v1.json'
    cfg = json.loads(cfgpath.read_text())
    pack = ROOT / cfg['pack']
    manifest = json.loads((pack / 'manifest.json').read_text())
    hand = json.loads((pack / 'manual-inspection.json').read_text())
    assert manifest['training_authorized_for_this_pack'] and hand['all_selected_texts_read_complete']
    assert hand['fitting_ready'] and hand['manifest_sha256'] == sha256(pack / 'manifest.json')
    for name, expected in manifest['files_sha256'].items():
        assert sha256(pack / name) == expected
    cases = list(read_jsonl(pack / 'cases.jsonl'))
    pairs = list(read_jsonl(pack / 'pairs.jsonl'))
    audits = list(read_jsonl(pack / 'pair-audit.jsonl'))
    targets = json.loads((pack / 'preferred-targets.json').read_text())['targets']
    point = ROOT / 'data/prepared/plan-input-fit-20261006-v1'
    assert sha256(pack / 'preferred-targets.json') == sha256(point / 'preferred-targets.json')
    oldaudits = list(read_jsonl(point / 'pair-audit.jsonl'))
    assert len(cases) == 14 and len(pairs) == len(audits) == len(oldaudits) == 8
    assert all(a['id'] == b['id'] and a['chosen_ids'] == b['chosen_ids'] for a, b in zip(audits, oldaudits, strict=True))
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    negative = json.loads((pack / 'actual-negative-provenance.json').read_text())
    base = ROOT / cfg['baseline_run']
    base_run = json.loads((base / 'run.json').read_text())
    base_rows = list(read_jsonl(base / 'transcript.jsonl'))
    assert negative['all_eight_negatives_actual_inspected_base_outputs'] and not negative['negative_gradient_enabled']
    for c, pair, a, link, row in zip(cases[:8], pairs, audits, negative['links'], base_rows[:8], strict=True):
        assert pair['prompt'] == c['prompt'] and pair['chosen'][0]['content'] == targets[c['id']]
        assert pair['rejected'][0]['content'] == row['output'] and digest(pair) == a['pair_sha256']
        assert c['input_ids'] == a['prompt_ids'] == row['input_ids']
        for completion in ['chosen', 'rejected']:
            full = tok.apply_chat_template(pair['prompt'] + pair[completion], tokenize=True, return_dict=False, enable_thinking=False)
            assert full[:len(c['input_ids'])] == c['input_ids'] and full[len(c['input_ids']):] == a[completion + '_ids']
        assert link['actual_identity'] == base_run['identity'] and link['output_digest'] == digest(row['output'])
        for name in ['run', 'inspection', 'transcript']:
            assert sha256(base / (name + ('.jsonl' if name == 'transcript' else '.json'))) == link[name + '_sha256']
    summaries, resources, groups = {}, [], {}
    tokens, seconds, caps, total = 0, 0, 0, 0
    arms = [('base', base), ('point8', ROOT / 'runs/aurora-compression-parent-20261006-v2'),
            ('compression8', ROOT / 'runs/aurora-compression-fit-20261006-v1')]
    exact = {}
    for arm, directory in arms:
        run = json.loads((directory / 'run.json').read_text())
        inspection = json.loads((directory / 'inspection.json').read_text())
        rows = list(read_jsonl(directory / 'transcript.jsonl'))
        frozen = ROOT / run['config']['pack']
        m = json.loads((frozen / 'manifest.json').read_text())
        h = json.loads((frozen / 'manual-inspection.json').read_text())
        selected = cases[8:] if arm == 'point8' else cases
        assert list(read_jsonl(frozen / 'cases.jsonl')) == selected
        assert run['status'] == 'completed' and exited(run['identity']) and inspection['all_outputs_read_complete']
        assert run['transcript_sha256'] == inspection['transcript_sha256'] == sha256(directory / 'transcript.jsonl')
        assert run['pack_manifest_sha256'] == h['manifest_sha256'] == sha256(frozen / 'manifest.json')
        for name, expected in m['files_sha256'].items():
            assert sha256(frozen / name) == expected
        assert inspection['criteria_sha256'] == sha256(frozen / 'criteria.json') == sha256(pack / 'criteria.json')
        assert inspection['presentation_criteria_sha256'] == sha256(pack / 'presentation-criteria.json')
        assert inspection['manual_annotations_sha256'] == sha256(directory / 'manual-annotations.json')
        assert run['versions'] == cfg['runtime_pins'] and run['gpu']['name'] == 'NVIDIA RTX PRO 6000 Blackwell Server Edition'
        for key in ['model', 'revision', 'seed', 'max_length', 'generation_max_new_tokens', 'chat_template_kwargs']:
            assert run['config'][key] == cfg[key]
        for name, expected in run['source_code_sha256'].items():
            assert sha256(directory / Path(name).name) == expected
        assert run['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py'] == sha256(ROOT / 'scripts/run_aurora_qwen35_smoke.py')
        previous = run.get('previous_inspected_run')
        if previous:
            assert sha256(ROOT / Path(previous.get('run', previous.get('path'))) / 'inspection.json') == previous['inspection_sha256']
        if arm == 'point8':
            assert run['loaded_adapter_sha256'] == sha256(ROOT / run['config']['adapter'] / 'adapter_model.safetensors')
        summaries[arm], exact[arm] = {}, []
        assert len(rows) == len(inspection['reviews']) == len(selected)
        for c, row, review in zip(selected, rows, inspection['reviews'], strict=True):
            assert c['id'] == row['id'] == review['id'] and c['input_ids'] == row['input_ids']
            assert tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False) == row['input_ids']
            assert tok.decode(row['output_ids'], skip_special_tokens=True) == row['output']
            assert review['output_sha256'] == hashlib.sha256(row['output'].encode()).hexdigest() and review['all_output_read_complete']
            assert review['words'] == len(row['output'].split())
            counts = dict(Counter(v['status'] for v in review['ratings'].values()))
            assert counts == review['content_counts']
            complete = all(v['status'] == 'met' for v in list(review['ratings'].values()) + list(review['universal_checks'].values()))
            assert review['usable_realization_pass'] == (complete and all(review['presentation'].values()) and not row['at_output_cap'])
            summaries[arm][c['id']] = {'content': counts, 'source': dict(Counter(v['status'] for k, v in review['ratings'].items() if k.startswith('S'))),
                'application': dict(Counter(v['status'] for k, v in review['ratings'].items() if k.startswith('A'))),
                'universal': dict(Counter(v['status'] for v in review['universal_checks'].values())),
                'words': review['words'], 'presentation': review['presentation'], 'usable_realization_pass': review['usable_realization_pass']}
            if c['id'] in targets and row['output'] == targets[c['id']]:
                exact[arm].append(c['id'])
            tokens += row['generated_tokens']; seconds += row['generation_seconds']; caps += int(row['at_output_cap']); total += 1
        groups[arm] = {}
        for name, ids in [('fitting', [c['id'] for c in cases[:8]]), ('libya_raw', ['libya-fra-raw', 'libya-bra-raw']),
                          ('libya_plan', ['libya-fra-plan', 'libya-bra-plan']), ('exposed', [c['id'] for c in cases[-2:]])]:
            selected_reviews = [v for k, v in summaries[arm].items() if k in ids]
            if not selected_reviews:
                continue
            counter = Counter()
            for v in selected_reviews:
                counter.update(v['content'])
            groups[arm][name] = {'answers': len(selected_reviews), 'content': dict(counter), 'usable_passes': sum(v['usable_realization_pass'] for v in selected_reviews)}
        resources.append({'run': str(directory.relative_to(ROOT)), 'identity': run['identity'], 'gpu': run['gpu'], 'exited': True})
    fitdir = arms[-1][1]
    fit = json.loads((fitdir / 'run.json').read_text())
    previous_fit = json.loads((ROOT / cfg['comparison_run'] / 'run.json').read_text())
    init = fit['initialization_checks']; checks = fit['optimization_checks']['rank_checks'][0]; masks = fit['mask_audit']
    assert fit['optimizer_steps'] == checks['steps'] == checks['microbatches'] == checks['gradient_checks'] == 256
    assert init['initial_adapter_digest'] == previous_fit['initialization_checks']['initial_adapter_digest']
    assert init['all_B_tensors_zero'] and init['base_initial_adapter_logits_exact'] and not init['loaded_trained_adapter']
    assert checks['pair_presentations'] == {a['id']: 32 for a in audits}
    assert checks['actual_sequence_tokens'] == 32 * masks['sequence_tokens_once']
    assert checks['actual_target_tokens'] == 32 * (masks['chosen_tokens_once'] + masks['rejected_tokens_once'])
    assert checks['all_adapter_tensors_finite'] and checks['changed_adapter_tensors'] > 0
    assert fit['method']['reference_tensor_digest_before'] == fit['method']['reference_tensor_digest_after'] == init['initial_adapter_digest']
    assert not fit['method']['preference_gradient_enabled'] and fit['method']['negative_and_reference_compute_retained']
    objective = fit['actual_objective_guard']
    assert objective['loss_types'] == ['sft'] and objective['loss_weights'] == [1.0]
    for guard in objective['native_logit_gradient_checks']:
        assert all(guard[k] for k in ['rejected_logit_gradient_zero', 'prompt_padding_and_final_logit_gradient_zero', 'chosen_completion_logit_gradient_nonzero', 'parameter_gradients_not_accumulated'])
    assert fit['serialization_checks']['saved_tensors_equal'] and fit['serialization_checks']['reload_verified_after_state_perturbation']
    for name, expected in fit['serialization_checks']['files_sha256'].items():
        assert sha256(fitdir / 'adapter' / name) == expected
    assert fit['config_sha256'] == sha256(cfgpath)
    preparation = ROOT / cfg['preparation']
    assert fit['preparation_sha256'] == sha256(preparation)
    assert json.loads(preparation.read_text())['fit_manifest_sha256'] == sha256(pack / 'manifest.json')
    receipt = {'status': 'pass', 'verified_at': datetime.now(timezone.utc).isoformat(), 'summaries': summaries, 'groups': groups,
        'exact_fitting_target_outputs': exact, 'new_model_outputs': total, 'new_optimizer_steps': 256,
        'cumulative_qwen35_steps': 2526, 'reference_qwen25_steps': 582,
        'training_seconds': fit['training_seconds'], 'training_peak_gib': fit['peak_allocated_gpu_gib'],
        'actual_sequence_tokens': checks['actual_sequence_tokens'], 'actual_both_completion_tokens': checks['actual_target_tokens'],
        'actual_chosen_supervised_tokens': 32 * masks['chosen_tokens_once'], 'generated_tokens': tokens, 'generation_seconds': seconds,
        'resources': resources, 'all_owned_processes_exited': True, 'all_outputs_hand_read': True, 'uncapped': total-caps, 'capped': caps,
        'independent_review_complete': False, 'scope': 'Given-content compression, same-assistant development annotations; no independent persona/native prediction/multi-agent/strong OOD result.',
        'next_decision': json.loads((fitdir / 'inspection.json').read_text())['decision']}
    write_json(ROOT / 'reports/compression-checkpoint-20261007-v1.json', receipt)
    print(json.dumps({'status': receipt['status'], 'groups': groups, 'exact_fitting_targets': exact}, indent=2))


if __name__ == '__main__':
    main()
