"""Replay the inspected India transfer and four-target fit; software/arithmetic validation, not independent quality."""
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
    names = ['aurora-country-application-transfer-base-20261007-v1',
             'aurora-country-application-transfer-adapter-20261007-v1',
             'aurora-two-country-application-base-20261007-v1',
             'aurora-two-country-application-old-Q-20261007-v1',
             'aurora-two-country-application-fit-20261007-v1']
    extra = ROOT / 'reports/two-country-application-endpoint-runs-20261007-v1.json'
    if extra.exists(): names += json.loads(extra.read_text())['runs']
    names.append('aurora-two-country-application-French-monitor-20261007-v1')
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-two-country-application-fit-20261007-v1.json').read_text())
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
            source_units = criteria['source_units'][c['family']]
            if c['country_iso3'] in source_units:
                source_units = source_units[c['country_iso3']]
            assert set(v['ratings']) == set(criteria['common_units']) | set(source_units)
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
    fit = ROOT / 'runs' / names[4]; r = json.loads((fit / 'run.json').read_text()); pack = ROOT / r['config']['pack']
    assert steps == r['optimizer_steps'] == 128 and r['matched_input_tokens']
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
    base = ROOT / 'runs' / names[2]; base_rows = list(read_jsonl(base / 'transcript.jsonl'))
    for pair, audit, case, row in zip(pairs, audits, cases[:4], base_rows[:4], strict=True):
        assert pair['prompt'] == case['prompt'] and pair['rejected'][0]['content'] == row['output']
        assert audit['prompt_ids'] == case['input_ids']
        for arm in ['chosen', 'rejected']:
            ids = tok.apply_chat_template(pair['prompt'] + pair[arm], tokenize=True, return_dict=False, enable_thinking=False)
            assert ids[:len(audit['prompt_ids'])] == audit['prompt_ids'] and ids[len(audit['prompt_ids']):] == audit[arm + '_ids']
    old = ROOT / 'data/prepared/paired-application-fit-20261007-v1'
    targets = json.loads((pack / 'preferred-targets.json').read_text())['targets']
    original = json.loads((old / 'preferred-targets.json').read_text())['targets']
    for case in cases[:2]: assert targets[case['id']] == original[case['id']]
    oldcriteria = json.loads((old / 'criteria.json').read_text())
    currentcriteria = json.loads((pack / 'criteria.json').read_text())
    for k in ['common_units','universal_checks']: assert currentcriteria[k] == oldcriteria[k]
    for group in [cases[:2], cases[2:]]:
        prefix = group[0]['prompt'][1]['content'].split('CURRENT HYPOTHETICAL NOTE', 1)[0]
        assert all(c['prompt'][1]['content'].startswith(prefix) for c in group)
    draft = ROOT / 'data/prepared/two-country-application-20261007-v1'
    assert json.loads((draft / 'manifest.json').read_text())['created_at'] < json.loads((fit / 'launch.json').read_text())['created_at']
    assert cases == list(read_jsonl(draft / 'cases.jsonl'))
    oldrow = list(read_jsonl(ROOT / 'runs' / names[3] / 'transcript.jsonl'))[0]
    assert oldrow['input_ids'] == cases[5]['input_ids']
    transferbase = list(read_jsonl(ROOT / 'runs' / names[0] / 'transcript.jsonl'))
    transferadapter = list(read_jsonl(ROOT / 'runs' / names[1] / 'transcript.jsonl'))
    assert [x['input_ids'] for x in transferbase] == [x['input_ids'] for x in transferadapter] == [x['input_ids'] for x in base_rows[2:5]]
    assert json.loads((ROOT/'runs'/names[1]/'run.json').read_text())['loaded_adapter_sha256'] == sha256(ROOT/'runs/aurora-paired-application-fit-20261007-v1/adapter/adapter_model.safetensors')
    raw = ROOT / 'data/raw/source-plan-grounding-20261002-v1'
    acquisition = json.loads((raw / 'acquisition.json').read_text())
    for f,x in acquisition['files_sha256'].items(): assert sha256(raw / f) == x
    source = json.loads((raw / 'statements.json').read_text())['IND']
    text = (raw / 'record-9214.txt').read_text()
    assert text[source['start']:source['end']].strip() == source['text']
    assert text[source['end']:].startswith('I now resume my functions as President of the Council.')
    facts = json.loads((pack / 'source-facts.json').read_text())
    assert len(facts['facts'].split()) == facts['words'] == 200
    for c in cases[2:]: assert c['prompt'][1]['content'].count(facts['facts']) == 1
    for name in names[5:]:
        run = json.loads((ROOT / 'runs' / name / 'run.json').read_text()); p = ROOT / run['config']['pack']
        if not (p / 'actual-plan.json').exists():
            assert name == 'aurora-two-country-application-French-monitor-20261007-v1'
            assert run['loaded_adapter_sha256'] == sha256(fit/'adapter/adapter_model.safetensors')
            continue
        actual = json.loads((p / 'actual-plan.json').read_text())
        d = ROOT / actual['application_run']; row = next(x for x in read_jsonl(d/'transcript.jsonl') if x['id'] == actual['application_id'])
        assert actual['plan'] == facts['facts'] + '\n\n' + row['output'] and actual['words'] == len(actual['plan'].split())
        if run['mode'] == 'adapter':
            assert run['config']['adapter'] in ['runs/aurora-plan-input-fit-20261006-v1/adapter','runs/aurora-compression-fit-20261006-v1/adapter']
            assert run['loaded_adapter_sha256'] == sha256(ROOT / run['config']['adapter'] / 'adapter_model.safetensors')
    write_json(ROOT / 'reports/two-country-application-checkpoint-20261007-v1.json', {
        'status': 'pass', 'verified_at': datetime.now(timezone.utc).isoformat(), 'new_model_outputs': outputs,
        'uncapped': outputs, 'capped': 0, 'new_optimizer_steps': steps, 'cumulative_qwen35_steps': 2974 + steps,
        'reference_qwen25_steps': 582, 'all_owned_gpu_identities_exited': True, 'resources': resources,
        'summaries': summaries, 'original_French_targets_and_common_criteria_unchanged': True, 'within_country_source_factual_prefix_unchanged': True,
        'actual_presentations_each': 32, 'training_seconds': r['training_seconds'], 'peak_allocated_gpu_gib': r['peak_allocated_gpu_gib'],
        'independent_review_complete': False, 'scope': 'Two historically exposed source families, four fitting states and two Indian untrained states (P exposed, Q frozen before this fit/calls); adaptive same-assistant development. Source facts supplied, not raw extractor. Replay checks execution/stored grades, not independent quality/persona/OOD/multi-agent gain.'})
    print(json.dumps({'status': 'pass', 'outputs': outputs, 'steps': steps, 'summaries': summaries}, indent=2))


if __name__ == '__main__':
    main()
