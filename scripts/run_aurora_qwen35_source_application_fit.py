"""Bounded raw-source national-application comparison with private teacher plans."""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import math
import os
from pathlib import Path
import shutil
import time

from run_aurora_qwen35_smoke import ROOT, current_gpu, identity, verify_model, generate_controls, supervised_loss
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl
from country_persona.application_fit_checks import load_frozen, match_references

HISTORICAL = ROOT / 'runs/aurora-qwen35-source-plan-probe-20261002-v1'
HELPER = 'scripts/run_aurora_qwen35_smoke.py'


def protocol_guard(reference, record):
    if reference['versions'] != record['versions'] or reference['gpu']['name'] != record['gpu']['name']:
        raise ValueError('Matched comparison needs same versions and GPU type')
    if reference['source_code_sha256'][HELPER] != record['source_code_sha256'][HELPER]:
        raise ValueError('Matched generation helper differs')
    for key in ('model', 'revision', 'generation_max_new_tokens', 'chat_template_kwargs', 'context_budget', 'max_length'):
        if reference['config'][key] != record['config'][key]:
            raise ValueError('Matched protocol differs: ' + key)
    if reference['generation_config'] != record['generation_config']:
        raise ValueError('Effective generation settings differ')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('base', 'fit'), required=True)
    parser.add_argument('--gpu-uuid', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    os.chdir(ROOT)
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text())
    if args.output.exists() or os.environ.get('SLURM_JOB_ID'):
        raise ValueError('Require a fresh explicit Aurora run directory')
    gpu = current_gpu(args.gpu_uuid)
    if os.environ.get('CUDA_VISIBLE_DEVICES') != args.gpu_uuid:
        raise ValueError('Expose exactly selected UUID')
    args.output.mkdir(parents=True)
    sources = [Path(__file__), ROOT / HELPER, ROOT / 'src/country_persona/application_fit_checks.py',
               ROOT / 'src/country_persona/training_checks.py', ROOT / 'src/country_persona/train.py',
               ROOT / 'src/country_persona/io.py']
    record = {'status': 'initializing', 'created_at': datetime.now(timezone.utc).isoformat(),
              'mode': args.mode, 'kind': config['kind'], 'question': config['question'], 'config': config,
              'config_sha256': sha256(config_path), 'identity': identity(), 'gpu': gpu,
              'run_directory': str(args.output.resolve()), 'completed_calls': 0, 'new_training_steps': 0,
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
        record['versions'] = {k: importlib.metadata.version(k) for k in config['runtime_pins']}
        if record['versions'] != config['runtime_pins']:
            raise ValueError('Runtime differs from pins')
        rows, metadata, cases = load_frozen(ROOT, config)
        record['model_verification'] = verify_model(config)
        if torch.cuda.device_count() != 1 or not torch.cuda.is_bf16_supported():
            raise ValueError('Require one BF16 CUDA device')
        torch.cuda.set_device(0)
        record['cuda'] = {'version': torch.version.cuda, 'capability': list(torch.cuda.get_device_capability()),
                          'device': torch.cuda.get_device_name(0)}
        tokenizer = AutoTokenizer.from_pretrained(config['model_path'], local_files_only=True)
        record['generation_config'] = GenerationConfig(do_sample=False,
            max_new_tokens=config['generation_max_new_tokens'], use_cache=True,
            pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id).to_dict()
        preflight = []
        inputs = {}
        for c in cases:
            ids = tokenizer.apply_chat_template(c['prompt'], tokenize=True, return_dict=False,
                        add_generation_prompt=True, **config['chat_template_kwargs'])
            if len(ids) + config['generation_max_new_tokens'] > config['max_length']:
                raise ValueError('No prompt truncation permitted')
            inputs[c['id']] = digest(ids)
            preflight.append({'id': c['id'], 'tokens': len(ids), 'input_ids_digest': digest(ids)})
        record['generation_preflight'] = preflight
        historical_record = json.loads((HISTORICAL / 'run.json').read_text())
        if historical_record['status'] != 'source_plan_probe_eight_answers_completed':
            raise ValueError('Historical base incomplete')
        protocol_guard(historical_record, record)
        historical_rows = list(read_jsonl(HISTORICAL / 'transcript.jsonl'))
        references = {}
        controls = []
        for c in cases:
            if c['condition'] == 'training_control':
                matches = [r for r in historical_rows if r['id'] == c['historical_base_case_id'] and r['arm'] == 'base']
                if len(matches) != 1 or inputs[c['id']] != matches[0]['input_ids_digest']:
                    raise ValueError('Historical control prompt tokens differ')
                row = {**matches[0], 'id': c['id'], 'historical_case_id': c['historical_base_case_id'],
                       'source_run': str(HISTORICAL.relative_to(ROOT)), 'new_call': False}
                controls.append(row)
                references[c['id']] = row
        write_jsonl(args.output / 'historical-controls.jsonl', controls)
        record['historical_controls'] = {'reused_calls': len(controls),
            'run_sha256': sha256(HISTORICAL / 'run.json'), 'transcript_sha256': sha256(HISTORICAL / 'transcript.jsonl'),
            'controls_sha256': sha256(args.output / 'historical-controls.jsonl')}
        lengths = []
        for row, meta in zip(rows, metadata):
            full = tokenizer.apply_chat_template(row['prompt'] + row['completion'], tokenize=True, return_dict=False,
                                                  **config['chat_template_kwargs'])
            prefix = tokenizer.apply_chat_template(row['prompt'], tokenize=True, return_dict=False,
                add_generation_prompt=True, **config['chat_template_kwargs'])
            if full[:len(prefix)] != prefix or not 0 < len(prefix) < len(full) <= config['max_length']:
                raise ValueError('Invalid training boundary; no truncation')
            if (len(full), len(full)-len(prefix)) != (meta['sequence_tokens'], meta['supervised_tokens']):
                raise ValueError('Training tokens differ from freeze')
            lengths.append({'id': meta['id'], 'sequence': len(full), 'supervised': len(full)-len(prefix)})
        record['training_preflight'] = lengths
        if args.mode == 'fit':
            baseline_path = ROOT / config['baseline_run']
            for name, key in (('run.json', 'baseline_run_sha256'), ('transcript.jsonl', 'baseline_transcript_sha256'),
                              ('inspection.json', 'baseline_inspection_sha256')):
                if sha256(baseline_path / name) != config[key]:
                    raise ValueError('Inspected baseline changed')
            baseline = json.loads((baseline_path / 'run.json').read_text())
            inspection = json.loads((baseline_path / 'inspection.json').read_text())
            if baseline['status'] != 'source_application_base_six_completed' or not inspection['all_six_complete_answers_inspected']:
                raise ValueError('Base must complete and be inspected before fitting')
            if baseline['config']['training_release_sha256'] != config['training_release_sha256']:
                raise ValueError('Training targets changed after baseline inspection')
            if baseline['config']['eval_manifest_sha256'] != config['eval_manifest_sha256']:
                raise ValueError('Evaluation changed after baseline inspection')
            protocol_guard(baseline, record)
            base_rows = [r for r in read_jsonl(baseline_path / 'transcript.jsonl') if r['condition'] == 'raw']
            if len(base_rows) != 4:
                raise ValueError('Four held raw baseline cases required')
            references.update({r['id']: r for r in base_rows})
        torch.manual_seed(config['seed'])
        model, loading = Qwen3_5ForCausalLM.from_pretrained(config['model_path'], local_files_only=True,
                dtype=torch.bfloat16, attn_implementation='sdpa', output_loading_info=True)
        loading = {k: sorted(v) if isinstance(v, set) else v for k, v in loading.items()}
        if loading['missing_keys'] or loading['mismatched_keys'] or loading['error_msgs']:
            raise ValueError('Incomplete text weights')
        record['loading_info'] = loading
        model.to('cuda:0')
        if args.mode == 'fit':
            from peft import LoraConfig
            from datasets import Dataset
            from trl import SFTConfig, SFTTrainer
            from country_persona.training_checks import (MeasuredTrainingSteps, OptimizationAudit, audit_completion_masks,
                adapter_snapshot, check_adapter_update, validate_rank_checks, verify_saved_adapter)
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
                processing_class=tokenizer, callbacks=[audit], peft_config=LoraConfig(r=config['lora_rank'],
                lora_alpha=2*config['lora_rank'], lora_dropout=0.05, target_modules='all-linear', task_type='CAUSAL_LM'))
            record['mask_audit'] = audit_completion_masks(rows, trainer.train_dataset, trainer.data_collator, tokenizer)
            record['before_training_target_loss'] = supervised_loss(trainer.model, trainer, trainer.train_dataset)
            record['status'] = 'source_application_training_running'
            write_json(args.output / 'run.json', record)
            torch.cuda.reset_peak_memory_stats()
            started = time.perf_counter()
            result = trainer.train()
            torch.cuda.synchronize()
            if not math.isfinite(result.training_loss):
                raise FloatingPointError('Nonfinite training loss')
            check = {'rank': 0, 'steps': trainer.state.global_step, 'training_loss': result.training_loss,
                'actual_sequence_tokens': trainer.processed_tokens, 'actual_target_tokens': trainer.target_tokens,
                'gradient_checks': len(audit.gradients), 'gradient_trace': audit.gradients,
                **check_adapter_update(audit.initial, adapter_snapshot(trainer.model))}
            record['optimization_checks'] = validate_rank_checks([check], 1, config['max_steps'])
            record['new_training_steps'] = trainer.state.global_step
            record['measurement'] = {'training_seconds': time.perf_counter()-started,
                'peak_training_allocated_gpu_gib': torch.cuda.max_memory_allocated()/2**30, 'trainer_metrics': result.metrics}
            record['after_training_target_loss'] = supervised_loss(trainer.model, trainer, trainer.train_dataset)
            trainer.save_model(str(args.output / 'adapter'))
            tokenizer.save_pretrained(str(args.output / 'adapter'))
            probe = torch.tensor([trainer.train_dataset[0]['input_ids'][:32]], device='cuda:0')
            record['serialization_checks'] = verify_saved_adapter(trainer.model, args.output / 'adapter', probe,
                                                                 atol=1e-5, rtol=1e-5)
            model = trainer.model
            model.config.use_cache = True
        selected = [c for c in cases if c['condition'] != ('checked_plan' if args.mode == 'fit' else 'training_control')]
        if len(selected) != 6:
            raise ValueError('Require exactly six new answers per arm')
        record['status'] = 'source_application_generation_running'
        outputs = []
        for c in selected:
            row = generate_controls(model, tokenizer, [{'prompt': c['prompt']}],
                    [{'id': c['id'], 'country_iso3': c['country_iso3']}], config)[0]
            if row['input_ids_digest'] != inputs[c['id']] or (args.mode == 'fit' and
                    row['input_ids_digest'] != references[c['id']]['input_ids_digest']):
                raise ValueError('Generation prompt differs from frozen comparison')
            row.update(arm='source_application_twenty_step_adapter' if args.mode == 'fit' else 'base',
                condition=c['condition'], variant=c['variant'], split_group=c['split_group'],
                case_sha256=c['case_sha256'], output_digest=digest(row['output_ids']),
                hit_output_cap=row.pop('at_output_cap'), scope='exact_training_control' if c['condition'] == 'training_control'
                    else 'separate_event_development_not_independent_validation')
            outputs.append(row)
            write_jsonl(args.output / 'transcript.jsonl', outputs)
            record['completed_calls'] = len(outputs)
            write_json(args.output / 'run.json', record)
            print(json.dumps({k: row[k] for k in ('id', 'generated_tokens', 'generation_seconds', 'hit_output_cap')}), flush=True)
        if args.mode == 'fit':
            record['matched_input_digests'] = match_references(outputs, references)
        record.update(status='source_application_fit_and_six_completed' if args.mode == 'fit' else 'source_application_base_six_completed',
                      completed_at=datetime.now(timezone.utc).isoformat(), transcript_sha256=sha256(args.output / 'transcript.jsonl'))
    except BaseException as error:
        record.update(status='source_application_failed', error=f'{type(error).__name__}: {error}')
        write_json(args.output / 'failure.json', record)
        raise
    finally:
        write_json(args.output / 'run.json', record)


if __name__ == '__main__':
    main()
