"""Portable replay of frozen sources, eight positives, actual controls and fresh native SFT."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cfgfile = ROOT / 'configs/posttraining/qwen35-diverse-country-20261006-v2.json'
    cfg = json.loads(cfgfile.read_text()); pack = ROOT / cfg['pack']
    m = json.loads((pack / 'manifest.json').read_text()); hand = json.loads((pack / 'manual-inspection.json').read_text())
    assert m['training_authorized_for_this_pack'] and hand['all_selected_texts_read_complete']
    assert hand['manifest_sha256'] == sha256(pack / 'manifest.json')
    for name, expected in m['files_sha256'].items():
        assert sha256(pack / name) == expected
    cases = list(read_jsonl(pack / 'cases.jsonl')); pairs = list(read_jsonl(pack / 'pairs.jsonl'))
    audits = list(read_jsonl(pack / 'pair-audit.jsonl')); sources = json.loads((pack / 'sources.json').read_text())
    criteria = json.loads((pack / 'criteria.json').read_text()); provenance = json.loads((pack / 'provenance.json').read_text())
    assert len(cases) == 14 and len(pairs) == len(audits) == 8
    assert [c['id'] for c in cases[:8]] == provenance['pair_ids']
    old = ROOT / provenance['old_pack']
    assert sha256(old / 'manifest.json') == provenance['old_manifest_sha256']
    for name, expected in provenance['old_source_files_sha256'].items():
        assert sha256(old / name) == expected
    for family, filename, rawdir, record in [
        ('wps','wps-statements.json','data/raw/source-application-grounding-20261003-v1','record-8514.txt'),
        ('mali','mali-statements.json','data/raw/coverage-objective-grounding-20261003-v1','record-9365.txt'),
        ('sanctions','sanctions-statements.json','data/raw/source-plan-grounding-20261002-v1','record-9214.txt'),
        ('haiti','haiti-statements.json','data/raw/conditional-india-haiti-grounding-20261006-v1','record-9430.txt')]:
        originals = json.loads((old / filename).read_text()); doc = (ROOT / rawdir / record).read_text()
        proofname = {'wps':'source-proof.json','mali':'mali-source-proof.json','sanctions':'sanctions-source-proof.json','haiti':'haiti-source-proof.json'}[family]
        proof = json.loads((old / proofname).read_text())
        for name, expected in (proof['wps_raw_files_sha256'] if family == 'wps' else proof['files_sha256']).items():
            assert sha256(ROOT / rawdir / name) == expected
        for co, source in sources[family].items():
            assert source == originals[co]
            rawtext = doc[source['start']:source['end']].strip()
            if 'raw_text' in source:
                assert rawtext == source['raw_text'] and re.sub('\u00ad\\s*','',rawtext) == source['text']
            else:
                assert rawtext == source['text']
    raw = ROOT / provenance['somalia_raw_directory']; doc = (raw / 'record-9490.txt').read_text()
    for name, expected in provenance['somalia_raw_files_sha256'].items():
        assert sha256(raw / name) == expected
    for co, source in sources['somalia'].items():
        assert doc[source['start']:source['end']].strip() == source['raw_text']
        assert digest(source['raw_text']) == source['raw_text_digest'] and digest(source['text']) == source['text_digest']
        assert re.sub('\u00ad\\s*','',source['raw_text']) == source['text']
        assert ('pre-vote' if co == 'GBR' else 'post-vote') in source['institutional_capacity']
    assert json.loads((raw / 'source-hand-inspection.json').read_text())['all_selected_sources_read_complete']
    targets = json.loads((pack / 'preferred-targets.json').read_text())['targets']
    assert sha256(ROOT / provenance['target_file']) == provenance['target_file_sha256']
    assert json.loads((ROOT / provenance['target_file']).read_text())['targets'] == targets
    targetaudit = ROOT / 'reports/diverse-country-target-audit-20261006-v2.json'
    ta = json.loads(targetaudit.read_text()); assert ta['target_quality_not_model_result'] and ta['target_required_units_met'] == 112
    assert sha256(targetaudit) == hand['target_audit_sha256']
    from transformers import AutoTokenizer
    fitdir = ROOT / 'runs/aurora-diverse-country-fit-20261006-v2'
    fit = json.loads((fitdir / 'run.json').read_text())
    assert fit['status'] == 'completed' and fit['optimizer_steps'] == 256
    tok = AutoTokenizer.from_pretrained(fitdir / 'adapter', local_files_only=True)
    for c in cases:
        ids = tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, **cfg['chat_template_kwargs'])
        assert ids == c['input_ids'] and digest(ids) == c['input_ids_digest']
        assert len(ids) + cfg['generation_max_new_tokens'] <= cfg['max_length']
        assert sources[c['family']][c['country_iso3']]['text'] in c['prompt'][1]['content']
        if c['id'] in targets:
            assert targets[c['id']] not in c['prompt'][1]['content'] and 'CHECKED PLAN' not in c['prompt'][1]['content']
    base = ROOT / cfg['baseline_run']; br = json.loads((base / 'run.json').read_text())
    basepack = ROOT / br['config']['pack']
    assert list(read_jsonl(basepack / 'cases.jsonl')) == cases
    assert sha256(basepack / 'criteria.json') == sha256(pack / 'criteria.json')
    assert br['mode'] == 'base' and br['optimizer_steps'] == 0
    assert br['pack_manifest_sha256'] == sha256(basepack / 'manifest.json')
    negatives = json.loads((pack / 'actual-negative-provenance.json').read_text())
    assert negatives['all_eight_negatives_actual_inspected_base_outputs'] and not negatives['negative_gradient_enabled']
    baserows = list(read_jsonl(base / 'transcript.jsonl'))
    for pair, audit, case, row, link in zip(pairs,audits,cases[:8],baserows[:8],negatives['links'],strict=True):
        assert pair['prompt'] == case['prompt'] and pair['chosen'][0]['content'] == targets[case['id']]
        assert pair['rejected'][0]['content'] == row['output'] and audit['id'] == case['id']
        assert audit['pair_sha256'] == digest(pair) and audit['prompt_ids'] == case['input_ids']
        for name in ['chosen','rejected']:
            full = tok.apply_chat_template(pair['prompt'] + pair[name], tokenize=True, return_dict=False, **cfg['chat_template_kwargs'])
            assert full[:len(audit['prompt_ids'])] == audit['prompt_ids']
            assert full[len(audit['prompt_ids']):] == audit[name+'_ids'] and len(full) <= cfg['max_length']
        assert link['actual_identity'] == br['identity'] and link['output_digest'] == digest(row['output'])
        for name in ['run','transcript','inspection']:
            assert sha256(base / (name + ('.jsonl' if name=='transcript' else '.json'))) == link[name+'_sha256']
    summary = {}; tokens = 0; seconds = 0.0; caps = 0
    for arm, directory in [('base',base),('fit',fitdir)]:
        run = json.loads((directory / 'run.json').read_text()); review = json.loads((directory / 'inspection.json').read_text())
        rows = list(read_jsonl(directory / 'transcript.jsonl'))
        assert run['status'] == 'completed' and len(rows) == len(review['reviews']) == 14 and review['all_outputs_read_complete']
        assert run['transcript_sha256'] == review['transcript_sha256'] == sha256(directory / 'transcript.jsonl')
        assert review['criteria_sha256'] == sha256(pack / 'criteria.json')
        assert run['versions'] == cfg['runtime_pins'] and run['gpu']['name'] == 'NVIDIA RTX PRO 6000 Blackwell Server Edition'
        for key in ['model','revision','seed','max_length','generation_max_new_tokens','chat_template_kwargs']:
            assert run['config'][key] == cfg[key]
        for name, expected in run['source_code_sha256'].items():
            assert sha256(directory / Path(name).name) == expected
        assert run['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py'] == sha256(ROOT / 'scripts/run_aurora_qwen35_smoke.py')
        result = {}
        for c, row, annotation in zip(cases,rows,review['reviews'],strict=True):
            assert c['id'] == row['id'] == annotation['id'] and row['input_ids'] == c['input_ids']
            assert digest(row['input_ids']) == row['input_ids_digest'] and len(row['output_ids']) == row['generated_tokens']
            assert tok.decode(row['output_ids'],skip_special_tokens=True) == row['output']
            assert row['at_output_cap'] == (row['generated_tokens'] == cfg['generation_max_new_tokens'])
            assert annotation['output_sha256'] == hashlib.sha256(row['output'].encode()).hexdigest() and annotation['all_output_read_complete']
            required = criteria['source_units'][c['family']]
            if c['family'] == 'somalia':
                required = required[c['country_iso3']]
            assert set(annotation['ratings']) == set(required) | set(criteria['common_units'])
            assert set(annotation['universal_checks']) == set(criteria['universal_checks'])
            values = [*annotation['ratings'].values(), *annotation['universal_checks'].values()]
            assert all(v['status'] in {'met','unmet','unratable'} and v['reason'].strip() for v in values)
            result[c['id']] = {'met':sum(v['status']=='met' for v in annotation['ratings'].values()),
                'unratable':sum(v['status']=='unratable' for v in annotation['ratings'].values()),'units':len(required)+6,
                'source_met':sum(annotation['ratings'][k]['status']=='met' for k in required), 'source_units':len(required),
                'application_met':sum(annotation['ratings'][k]['status']=='met' for k in criteria['common_units']),
                'universal_met':sum(v['status']=='met' for v in annotation['universal_checks'].values()),
                'words':len(row['output'].split()),'at_cap':row['at_output_cap'],
                'strict_pass':all(v['status']=='met' for v in values) and not row['at_output_cap'] and len(row['output'].split())<=300}
            tokens += row['generated_tokens']; seconds += row['generation_seconds']; caps += row['at_output_cap']
        summary[arm] = result
    init = fit['initialization_checks']
    assert init['all_B_tensors_zero'] and init['base_initial_adapter_logits_exact'] and not init['loaded_trained_adapter']
    checks = fit['optimization_checks']['rank_checks'][0]; masks = fit['mask_audit']
    assert checks['steps'] == checks['microbatches'] == checks['gradient_checks'] == 256
    assert checks['pair_presentations'] == {a['id']:32 for a in audits}
    assert checks['actual_sequence_tokens'] == 32*masks['sequence_tokens_once']
    assert checks['actual_target_tokens'] == 32*(masks['chosen_tokens_once']+masks['rejected_tokens_once'])
    assert checks['all_adapter_tensors_finite'] and checks['changed_adapter_tensors'] > 0
    assert fit['method']['reference_tensor_digest_before'] == fit['method']['reference_tensor_digest_after'] == init['initial_adapter_digest']
    objective = fit['actual_objective_guard']
    assert objective['loss_types'] == ['sft'] and objective['loss_weights'] == [1.0]
    assert len(objective['pairs']) == len(objective['native_logit_gradient_checks']) == 8
    for guard in objective['native_logit_gradient_checks']:
        assert guard['rejected_logit_gradient_zero'] and guard['prompt_padding_and_final_logit_gradient_zero']
        assert guard['chosen_completion_logit_gradient_nonzero'] and guard['parameter_gradients_not_accumulated']
    assert fit['method']['preference_gradient_enabled'] is False and fit['method']['negative_and_reference_compute_retained']
    assert fit['serialization_checks']['saved_tensors_equal'] and fit['serialization_checks']['reload_verified_after_state_perturbation']
    for name, expected in fit['serialization_checks']['files_sha256'].items():
        assert sha256(fitdir / 'adapter' / name) == expected
    for name, expected in fit['initial_adapter_files_sha256'].items():
        assert sha256(fitdir / 'initial-adapter' / name) == expected
    assert fit['config_sha256'] == sha256(cfgfile) and fit['pack_manifest_sha256'] == sha256(pack / 'manifest.json')
    preparation = ROOT / cfg['preparation']; prep = json.loads(preparation.read_text())
    assert fit['preparation_sha256'] == sha256(preparation) and prep['all_selected_texts_read_complete']
    assert prep['config_sha256'] == fit['config_sha256'] and prep['pack_manifest_sha256'] == fit['pack_manifest_sha256']
    write_json(args.output, {'status':'sources_targets_native_tokens_fresh_init_objective_gradients_reference_updates_weights_and_28_stored_reviews_replayed',
        'summary':summary,'new_model_generations':28,'new_optimizer_steps':256,'selected_branch_steps':256,
        'cumulative_aurora_qwen35_steps':1502,'reference_qwen25_steps':582,'generated_tokens':tokens,'generation_seconds':seconds,
        'caps':caps,'training_seconds':fit['training_seconds'],'training_peak_gib':fit['peak_allocated_gpu_gib'],
        'actual_sequence_tokens':checks['actual_sequence_tokens'],'actual_both_completion_tokens':checks['actual_target_tokens'],
        'actual_chosen_supervised_tokens':32*masks['chosen_tokens_once'],'pair_presentations':checks['pair_presentations'],
        'scope':provenance['source_scope'],'independent_review_complete':False,
        'limitations':['One training source context per country; country and topic correlated.','Somalia is outside fitting but shares sanctions/UNSC genre; pretraining unknown, not strong domain or sealed OOD.','Data/task scope/dose/history change together.','One unblinded assistant authors plans/targets and grades.','No native prediction/persona/autonomous multi-agent gain proved.']})
    print(json.dumps({'status':'replayed','summary':summary},indent=2))


if __name__ == '__main__':
    main()
