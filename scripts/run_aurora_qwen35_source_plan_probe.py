"""Run a frozen national-application comparison across base and saved adapter."""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import shutil

from run_aurora_qwen35_smoke import ROOT, current_gpu, identity, verify_model, generate_controls
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl
from country_persona.probe_checks import validate_cases, verify_matched_inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--gpu-uuid', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    os.chdir(ROOT)
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text())
    if args.output.exists() or os.environ.get('SLURM_JOB_ID'):
        raise ValueError('Use fresh outputs and explicit Aurora execution without scheduler impersonation')
    gpu = current_gpu(args.gpu_uuid)
    if os.environ.get('CUDA_VISIBLE_DEVICES') != args.gpu_uuid:
        raise ValueError('Expose exactly the selected idle GPU UUID')
    args.output.mkdir(parents=True)
    sources = [Path(__file__), ROOT / 'scripts/run_aurora_qwen35_smoke.py',
               ROOT / 'src/country_persona/training_checks.py', ROOT / 'src/country_persona/io.py',
               ROOT / 'src/country_persona/probe_checks.py']
    record = {'status': 'initializing', 'created_at': datetime.now(timezone.utc).isoformat(),
              'kind': config['kind'], 'question': config['question'], 'config': config,
              'config_sha256': sha256(config_path), 'identity': identity(), 'gpu': gpu,
              'run_directory': str(args.output.resolve()), 'new_training_steps': 0,
              'source_code_sha256': {str(p.relative_to(ROOT)): sha256(p) for p in sources},
              'independent_semantic_review_pending': True, 'generalization_claim': False,
              'nccl_tested': False, 'completed_calls': 0}
    write_json(args.output / 'launch.json', record)
    for source in sources:
        target = args.output / 'source' / source.name
        target.parent.mkdir(exist_ok=True)
        shutil.copy2(source, target)
    transcript = []
    try:
        import torch
        from transformers import AutoTokenizer, GenerationConfig, Qwen3_5ForCausalLM
        from peft import PeftModel
        from country_persona.training_checks import adapter_snapshot, tensor_state_digest
        record['versions'] = {k: importlib.metadata.version(k) for k in config['runtime_pins']}
        if record['versions'] != config['runtime_pins']:
            raise ValueError('Runtime changed')
        if torch.cuda.device_count() != 1 or not torch.cuda.is_bf16_supported():
            raise RuntimeError('Require one BF16 CUDA device')
        torch.cuda.set_device(0)
        torch.manual_seed(config['seed'])
        record['cuda'] = {'version': torch.version.cuda, 'capability': list(torch.cuda.get_device_capability()),
                          'device': torch.cuda.get_device_name(0)}
        record['model_verification'] = verify_model(config)
        pack = ROOT / config['eval_pack']
        manifest = json.loads((pack / 'manifest.json').read_text())
        if sha256(pack / 'manifest.json') != config['eval_pack_manifest_sha256']:
            raise ValueError('Frozen pre-generation evaluation manifest changed')
        for name, expected in manifest['files_sha256'].items():
            if sha256(pack / name) != expected:
                raise ValueError('Frozen plan pack changed: ' + name)
        for name, expected in manifest['source_files_sha256'].items():
            if sha256(ROOT / name) != expected:
                raise ValueError('Frozen primary source changed: ' + name)
        record['plan_manifest_sha256'] = sha256(pack / 'manifest.json')
        cases = list(read_jsonl(pack / 'cases.jsonl'))
        if len(cases) != config['expected_cases']:
            raise ValueError('Unexpected frozen case count')
        validate_cases(cases, config.get('comparison_design', 'raw_vs_plan'))
        if config.get('prerequisite_inspection'):
            prerequisite = ROOT / config['prerequisite_inspection']
            if sha256(prerequisite) != config['prerequisite_inspection_sha256']:
                raise ValueError('Inspected prior result changed')
            inspection = json.loads(prerequisite.read_text())
            if inspection['status'] != 'all_eight_complete_answers_inspected_before_next_run':
                raise ValueError('Inspect the preceding comparison before repair generation')
        tokenizer = AutoTokenizer.from_pretrained(config['model_path'], local_files_only=True)
        preflight = []
        for case in cases:
            if case['case_sha256'] != digest({k: v for k, v in case.items() if k != 'case_sha256'}):
                raise ValueError('Plan case digest changed')
            ids = tokenizer.apply_chat_template(case['prompt'], tokenize=True, return_dict=False,
                add_generation_prompt=True, **config['chat_template_kwargs'])
            if len(ids) + config['generation_max_new_tokens'] > config['context_budget']:
                raise ValueError('Full plan plus output budget must fit without truncation')
            preflight.append({'id': case['id'], 'scenario_id': case['scenario_id'],
                              'prompt_tokens': len(ids), 'input_ids_digest': digest(ids)})
        write_json(args.output / 'preflight.json', preflight)
        model, loading = Qwen3_5ForCausalLM.from_pretrained(config['model_path'], local_files_only=True,
            dtype=torch.bfloat16, attn_implementation='sdpa', output_loading_info=True)
        loading = {k: sorted(v) if isinstance(v, set) else v for k, v in loading.items()}
        if loading['missing_keys'] or loading['mismatched_keys'] or loading['error_msgs']:
            raise ValueError('Text model did not load completely')
        record['loading_info'] = loading
        model.to('cuda:0')
        record['generation_config'] = GenerationConfig(do_sample=False,
            max_new_tokens=config['generation_max_new_tokens'], use_cache=True,
            pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id).to_dict()
        adapter_run = ROOT / config['adapter_run']
        prior = json.loads((adapter_run / 'run.json').read_text())
        if sha256(adapter_run / 'run.json') != config['adapter_run_sha256'] or sha256(adapter_run / 'inspection.json') != config['adapter_inspection_sha256']:
            raise ValueError('Existing fitted and inspected adapter receipt changed')
        if prior['status'] != 'plan_to_text_fit_and_matched_memos_completed':
            raise ValueError('Only the inspected complete-task adapter may be used')
        helper = 'scripts/run_aurora_qwen35_smoke.py'
        if prior['source_code_sha256'][helper] != record['source_code_sha256'][helper]:
            raise ValueError('Inference helper differs from prior adapter comparison')
        if prior['versions'] != record['versions'] or prior['gpu']['name'] != gpu['name']:
            raise ValueError('Adapter comparison requires identical versions and hardware type')
        if prior['config']['revision'] != config['revision'] or prior['generation_config'] != record['generation_config']:
            raise ValueError('Model/generation protocol changed')
        for name, expected in prior['serialization_checks']['files_sha256'].items():
            if sha256(adapter_run / 'adapter' / name) != expected:
                raise ValueError('Saved adapter bytes changed')
        training_meta = list(read_jsonl(ROOT / prior['config']['training_pack'] / 'train.manifest.jsonl'))
        if {m['split_group'] for m in training_meta} & {c['split_group'] for c in cases}:
            raise ValueError('New benchmark context overlaps this adapter training')
        record['adapter_serialization_source'] = prior['serialization_checks']
        record['status'] = 'source_plan_probe_generation_running'
        write_json(args.output / 'run.json', record)
        torch.cuda.reset_peak_memory_stats()
        for arm in ('base', 'saved_adapter'):
            if arm != 'base':
                model = PeftModel.from_pretrained(model, adapter_run / 'adapter', is_trainable=False)
                record['loaded_adapter_digest'] = tensor_state_digest(adapter_snapshot(model))
                expected = prior['optimization_checks']['rank_checks'][0]['final_adapter_digest']
                if record['loaded_adapter_digest'] != expected:
                    raise ValueError('Loaded adapter tensors differ from the inspected fit')
            for case in cases:
                row = generate_controls(model, tokenizer, [{'prompt': case['prompt']}],
                    [{'id': case['id'], 'country_iso3': case['country_iso3']}], config)[0]
                row.update(arm=arm, scenario_id=case['scenario_id'], case_sha256=case['case_sha256'],
                    condition=case['condition'], plan_sha256=case['plan_sha256'], hit_output_cap=row.pop('at_output_cap'),
                    scope='outside_adapter_training_national_application_development',
                    response_id=digest([case['id'], arm, row['output']])[:24])
                prior_same_case = [r for r in transcript if r['id'] == case['id']]
                if prior_same_case and row['input_ids_digest'] != prior_same_case[0]['input_ids_digest']:
                    raise ValueError('Matched arms have different input tokens')
                transcript.append(row)
                write_jsonl(args.output / 'transcript.jsonl', transcript)
                record['completed_calls'] = len(transcript)
                write_json(args.output / 'run.json', record)
                print(json.dumps({k:row[k] for k in ('arm','generated_tokens','generation_seconds','hit_output_cap')}),flush=True)
        verify_matched_inputs(transcript, config['expected_calls'])
        record.update(status='source_plan_probe_repair_completed' if config.get('comparison_design') == 'checked_plan_repair_only' else 'source_plan_probe_eight_answers_completed',
            completed_at=datetime.now(timezone.utc).isoformat(), matched_input_digests=True,
            transcript_sha256=sha256(args.output / 'transcript.jsonl'),
            peak_allocated_gpu_gib=torch.cuda.max_memory_allocated()/2**30)
    except BaseException as error:
        record.update(status='failed_source_plan_probe', error=f'{type(error).__name__}: {error}',
                      failed_at=datetime.now(timezone.utc).isoformat())
        write_json(args.output / 'failure.json', record)
        raise
    finally:
        write_json(args.output / 'run.json', record)


if __name__ == '__main__':
    main()
