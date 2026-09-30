"""Fit two complete checked-plan memos, then inspect matched realization controls and one monitor."""
from datetime import datetime, timezone
import argparse
import importlib.metadata
import json
import math
import os
from pathlib import Path
import shutil
import time

from run_aurora_qwen35_smoke import ROOT, current_gpu, identity, verify_model, generate_controls, supervised_loss
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl
from country_persona.train import validated_export


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gpu-uuid', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/posttraining/qwen35-plan-to-text-fit-20260930.json')
    args = parser.parse_args()
    os.chdir(ROOT)
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text())
    if args.output.exists() or os.environ.get('SLURM_JOB_ID'):
        raise ValueError('Fresh explicit Aurora output required')
    gpu = current_gpu(args.gpu_uuid)
    if os.environ.get('CUDA_VISIBLE_DEVICES') != args.gpu_uuid:
        raise ValueError('Expose exactly the selected GPU UUID')
    args.output.mkdir(parents=True)
    sources = [Path(__file__), ROOT / 'scripts/run_aurora_qwen35_smoke.py',
               ROOT / 'src/country_persona/training_checks.py', ROOT / 'src/country_persona/train.py', ROOT / 'src/country_persona/io.py']
    record = {'status': 'initializing', 'created_at': datetime.now(timezone.utc).isoformat(),
        'kind': config['kind'], 'question': config['question'], 'config': config,
        'config_sha256': sha256(config_path), 'identity': identity(), 'gpu': gpu,
        'run_directory': str(args.output.resolve()),
        'source_code_sha256': {str(p.relative_to(ROOT)): sha256(p) for p in sources},
        'independent_semantic_review_pending': True, 'generalization_claim': False, 'nccl_tested': False}
    write_json(args.output / 'launch.json', record)
    for source in sources:
        target = args.output / 'source' / source.name
        target.parent.mkdir(exist_ok=True)
        shutil.copy2(source, target)
    try:
        import torch
        from transformers import AutoTokenizer, GenerationConfig, Qwen3_5ForCausalLM
        from peft import LoraConfig
        from datasets import Dataset
        from trl import SFTConfig, SFTTrainer
        from country_persona.training_checks import (MeasuredTrainingSteps, OptimizationAudit, audit_completion_masks,
            adapter_snapshot, check_adapter_update, validate_rank_checks, verify_saved_adapter)
        record['versions'] = {k: importlib.metadata.version(k) for k in config['runtime_pins']}
        if record['versions'] != config['runtime_pins']:
            raise ValueError('Runtime differs from pins')
        if torch.cuda.device_count() != 1 or not torch.cuda.is_bf16_supported():
            raise RuntimeError('Require one BF16 CUDA device')
        torch.cuda.set_device(0)
        record['cuda'] = {'version': torch.version.cuda, 'capability': list(torch.cuda.get_device_capability()),
                          'device': torch.cuda.get_device_name(0)}
        record['model_verification'] = verify_model(config)
        pack = ROOT / config['training_pack']
        release = json.loads((pack / 'release.json').read_text())
        for name, expected in release['files_sha256'].items():
            if sha256(pack / name) != expected:
                raise ValueError('Prepared training bytes changed')
        rows, metadata = validated_export(pack / 'train.jsonl', pack / 'train.manifest.jsonl', 'train', True)
        if len(rows) != config['training_examples'] or any(m['model_revision'] != config['revision'] for m in metadata):
            raise ValueError('Wrong training rows/revision')
        baseline_path = ROOT / config['baseline_run']
        baseline = json.loads((baseline_path / 'run.json').read_text())
        if sha256(baseline_path / 'run.json') != config['baseline_run_sha256'] or (
                sha256(baseline_path / 'transcript.jsonl') != config['baseline_transcript_sha256']):
            raise ValueError('Inspected baseline changed')
        if baseline['status'] != 'plan_to_text_base_completed' or baseline['versions'] != record['versions']:
            raise ValueError('Baseline incomplete or uses different versions')
        if baseline['gpu']['name'] != gpu['name'] or baseline['config']['revision'] != config['revision']:
            raise ValueError('Matched baseline needs identical device type/model')
        source_pack = ROOT / config['eval_pack']
        manifest = json.loads((source_pack / 'manifest.json').read_text())
        for name, expected in manifest['files_sha256'].items():
            if sha256(source_pack / name) != expected:
                raise ValueError('Frozen evaluation changed')
        cases = [c for c in read_jsonl(source_pack / 'cases.jsonl') if c['format_condition'] == config['format_condition']]
        base_rows = [r for r in read_jsonl(baseline_path / 'transcript.jsonl') if r['arm'] == 'base_checked_plan']
        if len(cases) != 3 or len(base_rows) != 3:
            raise ValueError('Three matched development memos required')
        helper = 'scripts/run_aurora_qwen35_smoke.py'
        if baseline['source_code_sha256'][helper] != record['source_code_sha256'][helper]:
            raise ValueError('Baseline and fit must use identical inference helper bytes')
        for key in ('generation_max_new_tokens', 'chat_template_kwargs', 'context_budget'):
            if baseline['config'][key] != config[key]:
                raise ValueError('Generation protocol differs from inspected baseline')
        if sha256(baseline_path / 'inspection.json') != config['baseline_inspection_sha256']:
            raise ValueError('Inspected baseline review changed')
        lock = json.loads((pack / 'tokenizer-lock.json').read_text())
        if any(m['tokenizer_lock_sha256'] != sha256(pack / 'tokenizer-lock.json') for m in metadata):
            raise ValueError('Training tokenizer lock differs from metadata')
        for name, expected in lock['files_sha256'].items():
            if sha256(Path(config['model_path']) / name) != expected:
                raise ValueError('Training tokenizer bytes differ from lock')
        for case in cases:
            if case['case_sha256'] != digest({k:v for k,v in case.items() if k != 'case_sha256'}):
                raise ValueError('Evaluation case hash changed')
        by_id = {c['id']: c for c in cases}
        for row, meta in zip(rows, metadata):
            if row['prompt'] != by_id[meta['id']]['prompt']:
                raise ValueError('Training controls must match their frozen plan prompts')
        tokenizer = AutoTokenizer.from_pretrained(config['model_path'], local_files_only=True)
        lengths = []
        for row, meta in zip(rows, metadata):
            full = tokenizer.apply_chat_template(row['prompt'] + row['completion'], tokenize=True, return_dict=False,
                                                  **config['chat_template_kwargs'])
            prefix = tokenizer.apply_chat_template(row['prompt'], tokenize=True, return_dict=False,
                add_generation_prompt=True, **config['chat_template_kwargs'])
            if full[:len(prefix)] != prefix or not 0 < len(prefix) < len(full) <= config['max_length']:
                raise ValueError('Invalid training boundary/context; no truncation')
            lengths.append({'id': meta['id'], 'sequence': len(full), 'supervised': len(full) - len(prefix)})
        record['training_preflight'] = {'rows': lengths, 'release_sha256': sha256(pack / 'release.json')}
        torch.manual_seed(config['seed'])
        model, loading = Qwen3_5ForCausalLM.from_pretrained(config['model_path'], local_files_only=True,
            dtype=torch.bfloat16, attn_implementation='sdpa', output_loading_info=True)
        loading = {k: sorted(v) if isinstance(v, set) else v for k, v in loading.items()}
        if loading['missing_keys'] or loading['mismatched_keys'] or loading['error_msgs']:
            raise ValueError('Incomplete text weights')
        model.to('cuda:0')
        model.config.use_cache = False
        model.enable_input_require_grads()
        settings = SFTConfig(output_dir=str(args.output / 'adapter'), max_length=config['max_length'],
            max_steps=config['max_steps'], gradient_accumulation_steps=config['gradient_accumulation_steps'],
            per_device_train_batch_size=1, learning_rate=config['learning_rate'], warmup_steps=0,
            bf16=True, fp16=False, gradient_checkpointing=True, gradient_checkpointing_kwargs={'use_reentrant': False},
            completion_only_loss=True, packing=False, seed=config['seed'], report_to='none', save_strategy='no',
            logging_steps=1, optim='adamw_torch', eos_token=tokenizer.eos_token)
        audit = OptimizationAudit()
        class MeasuredTrainer(MeasuredTrainingSteps, SFTTrainer):
            pass
        trainer = MeasuredTrainer(model=model, args=settings, train_dataset=Dataset.from_list(rows),
            processing_class=tokenizer, callbacks=[audit],
            peft_config=LoraConfig(r=config['lora_rank'], lora_alpha=2*config['lora_rank'],
                lora_dropout=0.05, target_modules='all-linear', task_type='CAUSAL_LM'))
        record['mask_audit'] = audit_completion_masks(rows, trainer.train_dataset, trainer.data_collator, tokenizer)
        record['before_training_target_loss'] = supervised_loss(trainer.model, trainer, trainer.train_dataset)
        record['status'] = 'targeted_training_running'
        write_json(args.output / 'run.json', record)
        torch.cuda.reset_peak_memory_stats()
        started = time.perf_counter()
        result = trainer.train()
        torch.cuda.synchronize()
        if not math.isfinite(result.training_loss):
            raise FloatingPointError('Nonfinite final training loss')
        check = {'rank': 0, 'steps': trainer.state.global_step, 'training_loss': result.training_loss,
            'actual_sequence_tokens': trainer.processed_tokens, 'actual_target_tokens': trainer.target_tokens,
            'gradient_checks': len(audit.gradients), 'gradient_trace': audit.gradients,
            **check_adapter_update(audit.initial, adapter_snapshot(trainer.model))}
        record['optimization_checks'] = validate_rank_checks([check], 1, config['max_steps'])
        record['measurement'] = {'training_seconds': time.perf_counter()-started,
            'peak_training_allocated_gpu_gib': torch.cuda.max_memory_allocated()/2**30,
            'trainer_metrics': result.metrics}
        record['after_training_target_loss'] = supervised_loss(trainer.model, trainer, trainer.train_dataset)
        trainer.save_model(str(args.output / 'adapter'))
        tokenizer.save_pretrained(str(args.output / 'adapter'))
        probe = torch.tensor([trainer.train_dataset[0]['input_ids'][:32]], device='cuda:0')
        record['serialization_checks'] = verify_saved_adapter(trainer.model, args.output / 'adapter', probe,
                                                              atol=1e-5, rtol=1e-5)
        trainer.model.config.use_cache = True
        eval_rows = [{'prompt': c['prompt']} for c in cases]
        eval_meta = [{'id': c['id'], 'country_iso3': 'ALL'} for c in cases]
        record['generation_config'] = GenerationConfig(do_sample=False,
            max_new_tokens=config['generation_max_new_tokens'], use_cache=True,
            pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id).to_dict()
        if record['generation_config'] != baseline['generation_config']:
            raise ValueError('Effective generation config differs from baseline')
        after = []
        references = {r['id']:r for r in base_rows}
        record['status'] = 'plan_to_text_adapter_generation_running'
        for case in cases:
            row = generate_controls(trainer.model, tokenizer, [{'prompt':case['prompt']}],
                [{'id':case['id'], 'country_iso3':'ALL'}], config)[0]
            reference = references[row['id']]
            if row['input_ids_digest'] != reference['input_ids_digest']:
                raise ValueError('Post-training prompt differs from frozen baseline')
            row.update(arm='complete_plan_to_text_twenty_step_adapter', scenario_id=case['scenario_id'],
                case_sha256=case['case_sha256'], plan_sha256=case['plan_sha256'],
                hit_output_cap=row.pop('at_output_cap'), output_digest=digest(row['output_ids']),
                scope='outside_training_exposed_development_monitor' if case['scenario_id'].startswith('south-sudan')
                      else 'exact_training_prompt_control_not_generalization')
            after.append(row)
            write_jsonl(args.output / 'transcript.jsonl', after)
            record['completed_eval_calls'] = len(after)
            write_json(args.output / 'run.json', record)
            print(json.dumps({k:row[k] for k in ('scenario_id','generated_tokens','generation_seconds','hit_output_cap')}),flush=True)
        record.update(status='plan_to_text_fit_and_matched_memos_completed',
            completed_at=datetime.now(timezone.utc).isoformat(), completed_eval_calls=len(after),
            matched_input_digests=True, transcript_sha256=sha256(args.output / 'transcript.jsonl'))
    except BaseException as error:
        record.update(status='failed_complete_plan_to_text_fit', error=f'{type(error).__name__}: {error}')
        write_json(args.output / 'failure.json', record)
        raise
    finally:
        write_json(args.output / 'run.json', record)


if __name__ == '__main__':
    main()
