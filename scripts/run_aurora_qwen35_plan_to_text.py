"""Run the base on supplied content plans with exact model bytes and explicit Aurora ownership."""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import shutil

from run_aurora_qwen35_smoke import ROOT, current_gpu, identity, verify_model, generate_controls
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--gpu-uuid', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    os.chdir(ROOT)
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text())
    if config['mode'] != 'base':
        raise ValueError('Inspect the base before authorizing a fitting branch')
    if args.output.exists() or os.environ.get('SLURM_JOB_ID'):
        raise ValueError('Use fresh outputs and explicit Aurora execution without scheduler impersonation')
    gpu = current_gpu(args.gpu_uuid)
    if os.environ.get('CUDA_VISIBLE_DEVICES') != args.gpu_uuid:
        raise ValueError('Expose exactly the selected idle GPU UUID')
    args.output.mkdir(parents=True)
    sources = [Path(__file__), ROOT / 'scripts/run_aurora_qwen35_smoke.py',
               ROOT / 'src/country_persona/training_checks.py', ROOT / 'src/country_persona/io.py']
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
        for name, expected in manifest['files_sha256'].items():
            if sha256(pack / name) != expected:
                raise ValueError('Frozen plan pack changed: ' + name)
        record['plan_manifest_sha256'] = sha256(pack / 'manifest.json')
        cases = list(read_jsonl(pack / 'cases.jsonl'))
        if len(cases) != 3 or len({c['scenario_id'] for c in cases}) != 3:
            raise ValueError('Require three distinct frozen development cases')
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
        record['status'] = 'base_plan_generation_running'
        write_json(args.output / 'run.json', record)
        torch.cuda.reset_peak_memory_stats()
        for case in cases:
            row = generate_controls(model, tokenizer, [{'prompt': case['prompt']}],
                [{'id': case['id'], 'country_iso3': 'ALL'}], config)[0]
            row.update(arm='base_checked_plan', scenario_id=case['scenario_id'],
                       case_sha256=case['case_sha256'], plan_sha256=case['plan_sha256'],
                       hit_output_cap=row.pop('at_output_cap'),
                       scope='exposed_supplied_content_realization_not_decision_prediction')
            transcript.append(row)
            write_jsonl(args.output / 'transcript.jsonl', transcript)
            record['completed_calls'] = len(transcript)
            write_json(args.output / 'run.json', record)
            print(json.dumps({k: row[k] for k in ('scenario_id', 'generated_tokens', 'generation_seconds', 'hit_output_cap')}), flush=True)
        record.update(status='plan_to_text_base_completed', completed_at=datetime.now(timezone.utc).isoformat(),
                      transcript_sha256=sha256(args.output / 'transcript.jsonl'),
                      peak_allocated_gpu_gib=torch.cuda.max_memory_allocated()/2**30)
    except BaseException as error:
        record.update(status='failed_plan_to_text_checkpoint', error=f'{type(error).__name__}: {error}',
                      failed_at=datetime.now(timezone.utc).isoformat())
        write_json(args.output / 'failure.json', record)
        raise
    finally:
        write_json(args.output / 'run.json', record)


if __name__ == '__main__':
    main()
