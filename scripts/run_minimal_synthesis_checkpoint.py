"""One complete synthesis target added to a verified saved source-fidelity adapter."""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import math
import os
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl
from run_aurora_qwen35_smoke import current_gpu, identity, verify_model, generate_controls, supervised_loss

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['base', 'fit', 'adapter'], required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--gpu-uuid', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--adapter', type=Path)
    args = parser.parse_args()
    os.chdir(ROOT)
    config = json.loads(args.config.read_text())
    if args.output.exists() or os.environ.get('SLURM_JOB_ID'):
        raise ValueError('Fresh output and explicit Aurora launch required')
    if os.environ.get('CUDA_VISIBLE_DEVICES') != args.gpu_uuid:
        raise ValueError('Expose exactly the named UUID')
    gpu = current_gpu(args.gpu_uuid)
    args.output.mkdir(parents=True)
    pack = ROOT / config['pack']
    manifest = json.loads((pack / 'manifest.json').read_text())
    if args.mode == 'fit' and manifest.get('training_authorized_for_this_pack') is False:
        raise ValueError('This frozen pack authorizes evaluation only')
    for name, expected in manifest['files_sha256'].items():
        if sha256(pack / name) != expected:
            raise ValueError('Changed frozen pack: ' + name)
    inspection = json.loads((pack / 'manual-inspection.json').read_text())
    if inspection['manifest_sha256'] != sha256(pack / 'manifest.json') or not inspection['all_selected_texts_read_complete']:
        raise ValueError('Full selected text inspection must bind this pack')
    rows = list(read_jsonl(pack / 'train.jsonl'))
    cases = list(read_jsonl(pack / 'cases.jsonl'))
    record = {'status': 'initializing', 'mode': args.mode, 'question': manifest['question'],
              'identity': identity(), 'gpu': gpu, 'run_directory': str(args.output.resolve()),
              'created_at': datetime.now(timezone.utc).isoformat(), 'config': config,
              'config_sha256': sha256(args.config), 'pack_manifest_sha256': sha256(pack / 'manifest.json'),
              'manual_inspection_sha256': sha256(pack / 'manual-inspection.json'),
              'source_code_sha256': {str(p.relative_to(ROOT)): sha256(p) for p in
                (Path(__file__), ROOT / 'scripts/run_aurora_qwen35_smoke.py', ROOT / 'src/country_persona/training_checks.py')},
              'scope': manifest['decision'], 'independent_review_complete': False, 'nccl_tested': False}
    write_json(args.output / 'launch.json', record)
    for name in ('scripts/run_minimal_synthesis_checkpoint.py', 'scripts/run_aurora_qwen35_smoke.py', 'src/country_persona/training_checks.py'):
        shutil.copy2(ROOT / name, args.output / Path(name).name)
    try:
        import torch
        from transformers import AutoTokenizer, Qwen3_5ForCausalLM
        from peft import LoraConfig, PeftModel
        from datasets import Dataset
        from trl import SFTConfig, SFTTrainer
        from country_persona.training_checks import (MeasuredTrainingSteps, OptimizationAudit,
             audit_completion_masks, adapter_snapshot, check_adapter_update, validate_rank_checks, verify_saved_adapter)
        record['versions'] = {k: importlib.metadata.version(k) for k in config['runtime_pins']}
        if record['versions'] != config['runtime_pins']:
            raise ValueError('Runtime pins changed')
        if torch.cuda.device_count() != 1 or not torch.cuda.is_bf16_supported():
            raise ValueError('Require one BF16 device')
        torch.cuda.set_device(0)
        record['model_verification'] = verify_model(config)
        tokenizer = AutoTokenizer.from_pretrained(config['model_path'], local_files_only=True)
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        record['tokenization'] = []
        for row in rows:
            full = tokenizer.apply_chat_template(row['prompt'] + row['completion'], tokenize=True,
                    return_dict=False, **config['chat_template_kwargs'])
            prefix = tokenizer.apply_chat_template(row['prompt'], tokenize=True, return_dict=False,
                    add_generation_prompt=True, **config['chat_template_kwargs'])
            if full[:len(prefix)] != prefix or not 0 < len(prefix) < len(full) <= config['max_length']:
                raise ValueError('Invalid full completion boundary; no truncation')
            record['tokenization'].append({'sequence_tokens': len(full), 'target_tokens': len(full) - len(prefix)})
        torch.manual_seed(config['seed'])
        model, loading = Qwen3_5ForCausalLM.from_pretrained(config['model_path'], local_files_only=True,
                    dtype=torch.bfloat16, attn_implementation='sdpa', output_loading_info=True)
        loading = {k: sorted(v) if isinstance(v, set) else v for k, v in loading.items()}
        if loading['missing_keys'] or loading['mismatched_keys'] or loading['error_msgs']:
            raise ValueError('Incomplete base text weights')
        record['text_model_loading'] = loading
        model.to('cuda:0')
        if args.mode == 'fit':
            baseline = ROOT / config['baseline_run']
            base_record = json.loads((baseline / 'run.json').read_text())
            base_review = json.loads((baseline / 'inspection.json').read_text())
            if base_record['status'] != 'completed' or not base_review['all_outputs_read_complete']:
                raise ValueError('Inspect complete baseline before fitting')
            if base_review['transcript_sha256'] != sha256(baseline / 'transcript.jsonl'):
                raise ValueError('Baseline inspection does not bind current transcript')
            for key in ('versions', 'source_code_sha256', 'pack_manifest_sha256'):
                if record[key] != base_record[key]:
                    raise ValueError('Baseline/fit changed: ' + key)
            if record['gpu']['name'] != base_record['gpu']['name']:
                raise ValueError('GPU type changed')
            for key in ('model', 'revision', 'generation_max_new_tokens', 'max_length', 'chat_template_kwargs'):
                if config[key] != base_record['config'][key]:
                    raise ValueError('Unmatched generation/model setting: ' + key)
            record['baseline_inspection_sha256'] = sha256(baseline / 'inspection.json')
            parent = ROOT / config['starting_adapter']
            if (base_record['mode'] != 'adapter' or base_record['loaded_adapter_sha256'] != config['starting_adapter_sha256']
                    or sha256(parent / 'adapter_model.safetensors') != config['starting_adapter_sha256']):
                raise ValueError('Warm-start weights must match the inspected adapter baseline')
            if sha256(parent / 'adapter_config.json') != config['starting_adapter_config_sha256']:
                raise ValueError('Warm-start adapter configuration changed')
            parent_config = json.loads((parent / 'adapter_config.json').read_text())
            if parent_config['r'] != config['lora_rank'] or parent_config['lora_alpha'] != 2 * config['lora_rank']:
                raise ValueError('Warm-start adapter rank/scale changed')
            model = PeftModel.from_pretrained(model, str(parent), is_trainable=True)
            record.update(starting_adapter_sha256=config['starting_adapter_sha256'],
                          starting_adapter_config_sha256=config['starting_adapter_config_sha256'],
                          starting_adapter_updates=64, optimizer_state_resumed=False,
                          scope_of_optimizer_steps='New optimizer, additional steps on the saved four-target adapter; parent64 and historical cumulative286 recorded separately.')
            model.config.use_cache = False
            model.enable_input_require_grads()
            settings = SFTConfig(output_dir=str(args.output / 'adapter'), max_length=config['max_length'],
                max_steps=config['max_steps'], gradient_accumulation_steps=config['gradient_accumulation_steps'],
                per_device_train_batch_size=1, learning_rate=config['learning_rate'], warmup_steps=0,
                bf16=True, fp16=False, gradient_checkpointing=True,
                gradient_checkpointing_kwargs={'use_reentrant': False}, completion_only_loss=True,
                packing=False, seed=config['seed'], report_to='none', save_strategy='no', logging_steps=1,
                optim='adamw_torch', eos_token=tokenizer.eos_token)
            class MeasuredTrainer(MeasuredTrainingSteps, SFTTrainer):
                pass
            audit = OptimizationAudit()
            trainer = MeasuredTrainer(model=model, args=settings, train_dataset=Dataset.from_list(rows),
                processing_class=tokenizer, callbacks=[audit])
            record['mask_audit'] = audit_completion_masks(rows, trainer.train_dataset, trainer.data_collator, tokenizer)
            record['loss_before'] = supervised_loss(trainer.model, trainer, trainer.train_dataset)
            record['status'] = 'training_running'
            write_json(args.output / 'run.json', record)
            torch.cuda.reset_peak_memory_stats()
            started = time.perf_counter()
            result = trainer.train()
            torch.cuda.synchronize()
            if not math.isfinite(result.training_loss):
                raise ValueError('Nonfinite training loss')
            checks = {'rank': 0, 'steps': trainer.state.global_step, 'training_loss': result.training_loss,
                      'actual_sequence_tokens': trainer.processed_tokens, 'actual_target_tokens': trainer.target_tokens,
                      'gradient_checks': len(audit.gradients), 'gradient_trace': audit.gradients,
                      **check_adapter_update(audit.initial, adapter_snapshot(trainer.model))}
            record['optimization_checks'] = validate_rank_checks([checks], 1, config['max_steps'])
            record['training_seconds'] = time.perf_counter() - started
            record['peak_allocated_gpu_gib'] = torch.cuda.max_memory_allocated() / 2**30
            record['loss_after'] = supervised_loss(trainer.model, trainer, trainer.train_dataset)
            trainer.save_model(str(args.output / 'adapter'))
            tokenizer.save_pretrained(str(args.output / 'adapter'))
            probe = torch.tensor([trainer.train_dataset[0]['input_ids'][:32]], device='cuda:0')
            record['serialization_checks'] = verify_saved_adapter(trainer.model, args.output / 'adapter', probe,
                                                                  atol=1e-5, rtol=1e-5)
            model = trainer.model
            model.config.use_cache = True
        elif args.mode == 'adapter':
            if args.adapter is None:
                raise ValueError('Saved adapter path required')
            model = PeftModel.from_pretrained(model, str(args.adapter), is_trainable=False)
            record['loaded_adapter_sha256'] = sha256(args.adapter / 'adapter_model.safetensors')
        record['status'] = 'generating'
        write_json(args.output / 'run.json', record)
        outputs = []
        for case in cases:
            output = generate_controls(model, tokenizer, [{'prompt': case['prompt']}], [case], config)[0]
            output['scope'] = case['family']
            output['scenario'] = case['scenario']
            outputs.append(output)
            write_jsonl(args.output / 'transcript.jsonl', outputs)
            print(json.dumps({'case': output['id'], 'tokens': output['generated_tokens'], 'capped': output['at_output_cap']}), flush=True)
        if args.mode == 'fit':
            base_outputs = read_jsonl(ROOT / config['baseline_run'] / 'transcript.jsonl')
            if [o['input_ids_digest'] for o in outputs] != [o['input_ids_digest'] for o in base_outputs]:
                raise ValueError('Different before/after input tokens')
            record['matched_input_tokens'] = True
        record.update(status='completed', outputs=len(outputs), transcript_sha256=sha256(args.output / 'transcript.jsonl'),
                      completed_at=datetime.now(timezone.utc).isoformat())
        write_json(args.output / 'run.json', record)
    except BaseException as exc:
        record.update(status='failed', error=type(exc).__name__ + ': ' + str(exc))
        write_json(args.output / 'failure.json', record)
        write_json(args.output / 'run.json', record)
        raise

if __name__ == '__main__':
    main()
