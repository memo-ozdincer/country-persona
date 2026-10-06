"""Replay supplied-point SFT, unchanged targets, frozen ICC sources and 42 stored answers."""
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json
from verify_two_context_country import exited


def summarize(review):
    fmt = review['format_observation']
    values = list(review['ratings'].values())
    return {
        'content': dict(Counter(v['status'] for v in values)),
        'source': dict(Counter(v['status'] for k, v in review['ratings'].items() if k.startswith('S'))),
        'application': dict(Counter(v['status'] for k, v in review['ratings'].items() if k.startswith('A'))),
        'universal': dict(Counter(v['status'] for v in review['universal_checks'].values())),
        'words': fmt['words'],
        'strict_pass': all(v['status'] == 'met' for v in values + list(review['universal_checks'].values()))
            and fmt['within300words'] and not fmt['at_cap'],
    }


def main():
    cfgfile = ROOT / 'configs/posttraining/qwen35-plan-input-20261006-v1.json'
    cfg = json.loads(cfgfile.read_text())
    pack = ROOT / cfg['pack']
    manifest = json.loads((pack / 'manifest.json').read_text())
    hand = json.loads((pack / 'manual-inspection.json').read_text())
    assert manifest['training_authorized_for_this_pack'] and hand['all_selected_texts_read_complete']
    assert hand['manifest_sha256'] == sha256(pack / 'manifest.json')
    for name, expected in manifest['files_sha256'].items():
        assert sha256(pack / name) == expected
    cases = list(read_jsonl(pack / 'cases.jsonl'))
    pairs = list(read_jsonl(pack / 'pairs.jsonl'))
    audits = list(read_jsonl(pack / 'pair-audit.jsonl'))
    provenance = json.loads((pack / 'provenance.json').read_text())
    criteria = json.loads((pack / 'criteria.json').read_text())
    sources = json.loads((pack / 'sources.json').read_text())
    targets = json.loads((pack / 'preferred-targets.json').read_text())['targets']
    plans = json.loads((pack / 'teacher-plans.json').read_text())
    oldpack = ROOT / provenance['old_pack']
    assert len(cases) == 14 and len(pairs) == len(audits) == 8
    assert [c['id'] for c in cases[:8]] == provenance['pair_ids']
    assert sha256(oldpack / 'manifest.json') == provenance['old_manifest_sha256']
    assert sha256(oldpack / 'sources.json') == provenance['old_source_files_sha256']
    assert sha256(pack / 'preferred-targets.json') == sha256(oldpack / 'preferred-targets.json') == provenance['preferred_targets_sha256']
    oldcases = list(read_jsonl(oldpack / 'cases.jsonl'))
    oldaudits = list(read_jsonl(oldpack / 'pair-audit.jsonl'))
    assert all(n['id'] == o['id'] and n['chosen_ids'] == o['chosen_ids'] for n, o in zip(audits, oldaudits, strict=True))
    for c, old, expected in zip(cases[:8], oldcases[:8], provenance['old_eight_case_prompt_digests'], strict=True):
        assert digest(old['prompt']) == expected and c['prompt'][0] == old['prompt'][0]
        assert c['prompt'][1]['content'].startswith(old['prompt'][1]['content'] + '\n\nSOURCE-CHECKED TEACHER POINTS')
        plan = plans['fitting_plans'][c['id']]
        assert plan in c['prompt'][1]['content']
        paragraphs = []
        for section in plan.split('\n\n'):
            heading, *bullets = section.splitlines()
            assert heading.endswith(':') and bullets and all(b.startswith('- ') for b in bullets)
            paragraphs.append(heading[:-1] + '. ' + ' '.join(b[2:] for b in bullets))
        assert '\n\n'.join(paragraphs) == targets[c['id']]
    raw = ROOT / 'data/raw/plan-input-icc-grounding-20261006-v1'
    for name, expected in provenance['icc_raw_files_sha256'].items():
        assert sha256(raw / name) == expected
    proof = json.loads((raw / 'source-proof.json').read_text())
    doc = (raw / 'record-9375.txt').read_text()
    assert digest(doc) == proof['document_text_digest']
    assert proof['source_hand_read_complete'] and proof['body_word_counters_equal'] and proof['english_cover_verified']
    assert proof['selected_pdf_pages_viewed'] == [10, 11, 13]
    for co, source in sources['icc'].items():
        assert doc[source['start']:source['end']].strip() == source['raw_text']
        assert digest(source['raw_text']) == source['raw_text_digest'] and digest(source['text']) == source['text_digest']
        assert re.sub(r'(?<=\w)-\s+(?=\w)', '-', source['raw_text']) == source['text']
        assert [source['start'], source['end']] == proof['source_span_boundaries'][co]
        assert source['symbol'] == 'S/PV.9375' and source['source_date'] == '2023-07-13'
    targetaudit = json.loads((ROOT / 'reports/plan-input-target-source-audit-20261006-v1.json').read_text())
    assert targetaudit['status'] == 'pass' and targetaudit['old_eight_target_plans_content_exact']
    assert targetaudit['teacher_plans_sha256'] == sha256(pack / 'teacher-plans.json')
    assert targetaudit['source_proof_sha256'] == sha256(raw / 'source-proof.json')
    # The two controls retain their original frozen source/rubric packs. Sudan is
    # deliberately not silently treated as ICC or inserted into a later rubric.
    control_paths = {
        'sudan-bra-question-guided-plan': ROOT / 'data/prepared/question-guided-plan-writer-20261006-v1',
        'somalia-gbr-plan': ROOT / 'data/prepared/diverse-country-role-check-20261006-v1',
    }
    for id, original in control_paths.items():
        c = next(v for v in cases if v['id'] == id)
        assert c == next(v for v in read_jsonl(original / 'cases.jsonl') if v['id'] == id)
    fitdir = ROOT / 'runs/aurora-plan-input-fit-20261006-v1'
    fit = json.loads((fitdir / 'run.json').read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(fitdir / 'adapter', local_files_only=True)
    for c in cases:
        ids = tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, **cfg['chat_template_kwargs'])
        assert ids == c['input_ids'] and digest(ids) == c['input_ids_digest']
        assert len(ids) + cfg['generation_max_new_tokens'] <= cfg['max_length']
        source = json.loads((control_paths[c['id']] / 'source.json').read_text()) if c['id'].startswith('sudan') else sources[c['family']][c['country_iso3']]
        assert source['text'] in c['prompt'][1]['content']
    base = ROOT / cfg['baseline_run']
    base_run = json.loads((base / 'run.json').read_text())
    base_rows = list(read_jsonl(base / 'transcript.jsonl'))
    negative = json.loads((pack / 'actual-negative-provenance.json').read_text())
    assert negative['all_eight_negatives_actual_inspected_base_outputs'] and not negative['negative_gradient_enabled']
    for pair, audit, c, row, link in zip(pairs, audits, cases[:8], base_rows[:8], negative['links'], strict=True):
        assert pair['prompt'] == c['prompt'] and pair['chosen'][0]['content'] == targets[c['id']]
        assert pair['rejected'][0]['content'] == row['output'] and audit['id'] == c['id']
        assert digest(pair) == audit['pair_sha256'] and audit['prompt_ids'] == c['input_ids']
        for completion in ['chosen', 'rejected']:
            full = tok.apply_chat_template(pair['prompt'] + pair[completion], tokenize=True, return_dict=False, **cfg['chat_template_kwargs'])
            assert full[:len(c['input_ids'])] == c['input_ids'] and full[len(c['input_ids']):] == audit[completion + '_ids']
            assert len(full) <= cfg['max_length']
        assert link['actual_identity'] == base_run['identity'] and link['output_digest'] == digest(row['output'])
        for name in ['run', 'transcript', 'inspection']:
            assert sha256(base / (name + ('.jsonl' if name == 'transcript' else '.json'))) == link[name + '_sha256']
    arms = [('base', base), ('raw8', ROOT / 'runs/aurora-plan-input-raw8-20261006-v1'), ('plan8', fitdir)]
    summaries, groups, resources = {}, {}, []
    tokens, seconds, caps, exact = 0, 0, 0, {}
    for arm, directory in arms:
        run = json.loads((directory / 'run.json').read_text())
        review = json.loads((directory / 'inspection.json').read_text())
        rows = list(read_jsonl(directory / 'transcript.jsonl'))
        frozen = ROOT / run['config']['pack']
        assert run['status'] == 'completed' and len(rows) == len(review['reviews']) == 14
        assert review['all_outputs_read_complete'] and exited(run['identity'])
        assert run['transcript_sha256'] == review['transcript_sha256'] == sha256(directory / 'transcript.jsonl')
        assert run['pack_manifest_sha256'] == sha256(frozen / 'manifest.json')
        assert list(read_jsonl(frozen / 'cases.jsonl')) == cases and sha256(frozen / 'criteria.json') == review['criteria_sha256'] == sha256(pack / 'criteria.json')
        assert run['versions'] == cfg['runtime_pins'] and run['gpu']['name'] == 'NVIDIA RTX PRO 6000 Blackwell Server Edition'
        for key in ['model', 'revision', 'seed', 'max_length', 'generation_max_new_tokens', 'chat_template_kwargs']:
            assert run['config'][key] == cfg[key]
        for name, expected in run['source_code_sha256'].items():
            assert sha256(directory / Path(name).name) == expected
        assert run['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py'] == sha256(ROOT / 'scripts/run_aurora_qwen35_smoke.py')
        previous = run.get('previous_inspected_run')
        if previous:
            assert sha256(Path(previous.get('path', previous.get('run'))) / 'inspection.json') == previous['inspection_sha256']
        if arm == 'raw8':
            assert run['loaded_adapter_sha256'] == sha256(ROOT / run['config']['adapter'] / 'adapter_model.safetensors')
        summaries[arm], exact[arm] = {}, []
        for c, row, annotation in zip(cases, rows, review['reviews'], strict=True):
            assert c['id'] == row['id'] == annotation['id'] and row['input_ids'] == c['input_ids']
            assert tok.decode(row['output_ids'], skip_special_tokens=True) == row['output']
            assert row['generated_tokens'] == len(row['output_ids'])
            assert row['at_output_cap'] == (row['generated_tokens'] == cfg['generation_max_new_tokens'])
            assert digest(row['input_ids']) == row['input_ids_digest']
            assert annotation['output_sha256'] == hashlib.sha256(row['output'].encode()).hexdigest() and annotation['all_output_read_complete']
            effective = json.loads((control_paths[c['id']] / 'criteria.json').read_text()) if c['id'] in control_paths else criteria
            required = effective['source_units'][c['family']]
            if c['family'] in ['icc', 'somalia', 'sudan']:
                required = required[c['country_iso3']]
            assert set(annotation['ratings']) == set(required) | set(effective['common_units'])
            assert set(annotation['universal_checks']) == set(effective['universal_checks'])
            assert all(v['status'] in {'met', 'unmet', 'unratable'} and v['reason'].strip() for v in list(annotation['ratings'].values()) + list(annotation['universal_checks'].values()))
            assert annotation['format_observation']['words'] == len(row['output'].split())
            assert annotation['format_observation']['within300words'] == (len(row['output'].split()) <= 300)
            summaries[arm][c['id']] = summarize(annotation)
            tokens += row['generated_tokens']; seconds += row['generation_seconds']
            caps += int(row['at_output_cap'])
            if c['id'] in targets and row['output'] == targets[c['id']]:
                exact[arm].append(c['id'])
        groups[arm] = {}
        for label, selected in [('fitting_points', cases[:8]), ('exposed_controls', cases[8:10]), ('new_icc_raw', cases[10::2]), ('new_icc_plan', cases[11::2])]:
            count = Counter()
            for c in selected:
                count.update(summaries[arm][c['id']]['content'])
            groups[arm][label] = {'content': dict(count), 'strict_passes': sum(summaries[arm][c['id']]['strict_pass'] for c in selected), 'answers': len(selected)}
        resources.append({'run': str(directory.relative_to(ROOT)), 'identity': run['identity'], 'gpu': run['gpu'], 'exited': True})
    assert fit['optimizer_steps'] == 256
    init = fit['initialization_checks']; checks = fit['optimization_checks']['rank_checks'][0]; masks = fit['mask_audit']
    original_fit = json.loads((ROOT / cfg['comparison_run'] / 'run.json').read_text())
    assert init['initial_adapter_digest'] == original_fit['initialization_checks']['initial_adapter_digest']
    assert init['all_B_tensors_zero'] and init['base_initial_adapter_logits_exact'] and not init['loaded_trained_adapter']
    assert checks['steps'] == checks['microbatches'] == checks['gradient_checks'] == 256
    assert checks['pair_presentations'] == {audit['id']: 32 for audit in audits}
    assert checks['actual_sequence_tokens'] == 32 * masks['sequence_tokens_once']
    assert checks['actual_target_tokens'] == 32 * (masks['chosen_tokens_once'] + masks['rejected_tokens_once'])
    assert checks['all_adapter_tensors_finite'] and checks['changed_adapter_tensors'] > 0
    assert fit['method']['reference_tensor_digest_before'] == fit['method']['reference_tensor_digest_after'] == init['initial_adapter_digest']
    objective = fit['actual_objective_guard']
    assert objective['loss_types'] == ['sft'] and objective['loss_weights'] == [1.0] and len(objective['native_logit_gradient_checks']) == 8
    for guard in objective['native_logit_gradient_checks']:
        assert guard['rejected_logit_gradient_zero'] and guard['prompt_padding_and_final_logit_gradient_zero']
        assert guard['chosen_completion_logit_gradient_nonzero'] and guard['parameter_gradients_not_accumulated']
    assert not fit['method']['preference_gradient_enabled'] and fit['method']['negative_and_reference_compute_retained']
    assert fit['serialization_checks']['saved_tensors_equal'] and fit['serialization_checks']['reload_verified_after_state_perturbation']
    for key, subdir in [('initial_adapter_files_sha256', 'initial-adapter'), ('serialization_checks', 'adapter')]:
        files = fit[key] if key.startswith('initial') else fit[key]['files_sha256']
        for name, expected in files.items():
            assert sha256(fitdir / subdir / name) == expected
    assert fit['config_sha256'] == sha256(cfgfile) and fit['pack_manifest_sha256'] == sha256(pack / 'manifest.json')
    prepfile = ROOT / cfg['preparation']; prep = json.loads(prepfile.read_text())
    assert fit['preparation_sha256'] == sha256(prepfile) and prep['config_sha256'] == sha256(cfgfile)
    assert prep['fit_manifest_sha256'] == sha256(pack / 'manifest.json')
    receipt = {'status': 'pass', 'verified_at': datetime.now(timezone.utc).isoformat(), 'summaries': summaries, 'groups': groups,
        'exact_fitting_target_outputs': exact, 'new_model_outputs': 42, 'new_optimizer_steps': 256,
        'cumulative_qwen35_steps': 2270, 'reference_qwen25_steps': 582,
        'training_seconds': fit['training_seconds'], 'training_peak_gib': fit['peak_allocated_gpu_gib'],
        'actual_sequence_tokens': checks['actual_sequence_tokens'], 'actual_both_completion_tokens': checks['actual_target_tokens'],
        'actual_chosen_supervised_tokens': 32 * masks['chosen_tokens_once'], 'pair_presentations': checks['pair_presentations'],
        'generated_tokens': tokens, 'generation_seconds': seconds, 'resources': resources,
        'all_42_stored_outputs_read': True, 'uncapped_public_answers': 42 - caps, 'capped_public_answers': caps,
        'all_three_owned_gpu_identities_exited': True,
        'independent_review_complete': False, 'scope': provenance['scope'],
        'next_decision': json.loads((fitdir / 'inspection.json').read_text())['decision'],
        'control_criteria_origins': {id: str((path / 'criteria.json').relative_to(ROOT)) for id, path in control_paths.items()}}
    write_json(ROOT / 'reports/plan-input-checkpoint-20261006-v1.json', receipt)
    print(json.dumps({k: receipt[k] for k in ['status', 'groups', 'exact_fitting_target_outputs']}, indent=2))


if __name__ == '__main__':
    main()
