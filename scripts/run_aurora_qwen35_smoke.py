"""One explicitly recorded single-GPU training check; four before/after controls, not a quality trial."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl
from country_persona.train import validated_export


def current_gpu(uuid):
    rows = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,memory.used,utilization.gpu',
                                    '--format=csv,noheader,nounits'], text=True).splitlines()
    matches = [r for r in rows if r.split(',')[0].strip() == uuid]
    if len(matches) != 1:
        raise ValueError('Selected GPU UUID is not unique/available')
    uuid, name, memory, utilization = (x.strip() for x in matches[0].split(','))
    processes = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid,process_name',
                                         '--format=csv,noheader'], text=True).splitlines()
    selected_processes = [r for r in processes if r.split(',')[0].strip() == uuid]
    if int(memory) != 0 or int(utilization) != 0 or selected_processes:
        raise RuntimeError('Selected GPU is occupied; leave existing processes untouched')
    return {'uuid': uuid, 'name': name, 'memory_used_mib_before_launch': int(memory),
            'utilization_before_launch': int(utilization), 'existing_compute_processes': selected_processes}


def identity():
    stat = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
    ticks = int(stat[19])
    boot = next(int(l.split()[1]) for l in Path('/proc/stat').read_text().splitlines() if l.startswith('btime '))
    return {'host': socket.gethostname(), 'pid': os.getpid(), 'process_start_ticks': ticks,
            'process_start_utc': datetime.fromtimestamp(boot + ticks / os.sysconf('SC_CLK_TCK'), timezone.utc).isoformat(),
            'command': [x.decode() for x in Path('/proc/self/cmdline').read_bytes().split(b'\0') if x],
            'cwd': str(Path.cwd()), 'slurm_job_id': None}


def verify_model(config):
    receipt_path = ROOT / 'reports/qwen35-model-verification-20260930.json'
    receipt = json.loads(receipt_path.read_text())
    if (receipt['model'], receipt['revision']) != (config['model'], config['revision']):
        raise ValueError('Model receipt/config mismatch')
    for name, expected in receipt['files'].items():
        path = Path(config['model_path']) / name
        if path.stat().st_size != expected['bytes'] or sha256(path) != expected['sha256']:
            raise ValueError('Changed model bytes: ' + name)
    return {'receipt_sha256': sha256(receipt_path), 'files_rehashed': len(receipt['files']),
            'revision': receipt['revision'], 'files': receipt['files']}


def prepare_pack(config, tokenizer, verification):
    source = ROOT / config['source_pack']
    original_release = json.loads((source / 'release.json').read_text())
    for name, expected in original_release['files_sha256'].items():
        if sha256(source / name) != expected:
            raise ValueError('Original training pack changed')
    rows, metadata = validated_export(source / 'smoke.train.jsonl', source / 'smoke.train.manifest.jsonl', 'train', True)
    if len(rows) != config['examples'] or {m['country_iso3'] for m in metadata} != {'FRA', 'GBR', 'IND', 'BRA'}:
        raise ValueError('Expected one control per extension country')
    path = ROOT / config['prepared_pack']
    if path.exists():
        release = json.loads((path / 'release.json').read_text())
        if (release['model'], release['revision'], release['source_release_sha256']) != (
                config['model'], config['revision'], sha256(source / 'release.json')):
            raise ValueError('Earlier prepared pack uses different model/source; preserve it')
        for name, expected in release['files_sha256'].items():
            if sha256(path / name) != expected:
                raise ValueError('Earlier prepared pack changed: ' + name)
        existing_rows, existing_meta = validated_export(path / 'train.jsonl', path / 'train.manifest.jsonl', 'train', True)
        expected_rows = [{**r, 'chat_template_kwargs': config['chat_template_kwargs']} for r in rows]
        if existing_rows != expected_rows or len(existing_meta) != len(metadata):
            raise ValueError('Earlier pack has different control tasks')
        for row, meta in zip(existing_rows, existing_meta):
            full = tokenizer.apply_chat_template(row['prompt'] + row['completion'], tokenize=True,
                return_dict=False, **config['chat_template_kwargs'])
            prefix = tokenizer.apply_chat_template(row['prompt'], tokenize=True, return_dict=False,
                add_generation_prompt=True, **config['chat_template_kwargs'])
            if full[:len(prefix)] != prefix or not 0 < len(prefix) < len(full) <= config['max_length']:
                raise ValueError('Earlier pack completion boundary/context budget changed')
            if (meta['model_revision'], meta['tokenizer_lock_sha256'], meta['sequence_tokens'], meta['supervised_tokens']) != (
                    config['revision'], sha256(path / 'tokenizer-lock.json'), len(full), len(full) - len(prefix)):
                raise ValueError('Earlier pack tokenization metadata changed')
        return path, existing_rows, existing_meta
    path.mkdir(parents=True)
    tokenizer_files = {k: v['sha256'] for k, v in verification['files'].items()
                       if 'tokenizer' in k or 'chat_template' in k or k.endswith('.jinja')}
    tokenizer_lock = {'model': config['model'], 'revision': config['revision'], 'files_sha256': tokenizer_files,
                      'chat_template_kwargs': config['chat_template_kwargs']}
    write_json(path / 'tokenizer-lock.json', tokenizer_lock)
    lengths = []
    for row, meta in zip(rows, metadata):
        row['chat_template_kwargs'] = config['chat_template_kwargs']
        full = tokenizer.apply_chat_template(row['prompt'] + row['completion'], tokenize=True, return_dict=False, **config['chat_template_kwargs'])
        prefix = tokenizer.apply_chat_template(row['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True,
                                                **config['chat_template_kwargs'])
        if full[:len(prefix)] != prefix or not 0 < len(prefix) < len(full) <= config['max_length']:
            raise ValueError('Invalid new-model completion boundary/context budget')
        lengths.append({'sequence': len(full), 'supervised': len(full) - len(prefix)})
        meta.update(upstream_model_revision=meta['model_revision'], model_revision=config['revision'],
                    example_sha256=digest(row), tokenizer_lock_sha256=sha256(path / 'tokenizer-lock.json'),
                    sequence_tokens=len(full), supervised_tokens=len(full) - len(prefix),
                    preparation_policy='Qwen3.5 technical smoke only; same authored source tasks; not held-out evaluation')
    write_jsonl(path / 'train.jsonl', rows)
    write_jsonl(path / 'train.manifest.jsonl', metadata)
    write_json(path / 'release.json', {'status': 'technical_smoke_prepared', 'model': config['model'],
        'revision': config['revision'], 'source_release_sha256': sha256(source / 'release.json'),
        'examples': len(rows), 'tokens': lengths, 'training_admitted': False, 'independent_review_complete': False,
        'files_sha256': {p.name: sha256(p) for p in path.iterdir() if p.is_file()}})
    return path, rows, metadata


def generate_controls(model, tokenizer, rows, metadata, config):
    import torch
    from transformers import GenerationConfig
    model.eval()
    generation = GenerationConfig(do_sample=False, max_new_tokens=config['generation_max_new_tokens'],
        use_cache=True, pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id)
    result = []
    for row, meta in zip(rows, metadata):
        ids = tokenizer.apply_chat_template(row['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True,
                                           **config['chat_template_kwargs'])
        if len(ids) + config['generation_max_new_tokens'] > config['max_length']:
            raise ValueError('No prompt truncation permitted')
        tensors = torch.tensor([ids], device='cuda:0')
        started = time.perf_counter()
        with torch.inference_mode():
            generated = model.generate(input_ids=tensors, attention_mask=torch.ones_like(tensors),
                generation_config=generation)
        torch.cuda.synchronize()
        output = generated[0, len(ids):].tolist()
        result.append({'id': meta['id'], 'country': meta['country_iso3'], 'input_ids': ids,
            'input_ids_digest': digest(ids), 'output_ids': output,
            'output': tokenizer.decode(output, skip_special_tokens=True),
            'generated_tokens': len(output), 'generation_seconds': time.perf_counter() - started,
            'at_output_cap': len(output) == config['generation_max_new_tokens'],
            'scope': 'training_control_not_held_out_model_quality'})
    return result


def supervised_loss(model, trainer, dataset):
    import torch
    was_training = model.training
    model.eval()
    measurements = []
    try:
        with torch.inference_mode():
            for prepared in dataset:
                batch = {k: v.to('cuda:0') for k, v in trainer.data_collator([prepared]).items()}
                loss = model(**batch, use_cache=False).loss
                if not torch.isfinite(loss):
                    raise FloatingPointError('Nonfinite control loss')
                measurements.append({'loss': float(loss), 'supervised_tokens': int((batch['labels'][:, 1:] != -100).sum())})
    finally:
        model.train(was_training)
    tokens = sum(x['supervised_tokens'] for x in measurements)
    return {'rows': measurements, 'token_weighted_loss': sum(x['loss'] * x['supervised_tokens'] for x in measurements) / tokens,
            'scope': 'same_training_targets_not_generalization'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gpu-uuid', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    os.chdir(ROOT)
    config_path = ROOT / 'configs/posttraining/qwen35-smoke-20260930.json'
    config = json.loads(config_path.read_text())
    if args.output.exists() or os.environ.get('SLURM_JOB_ID'):
        raise ValueError('Use a fresh output and the explicit Aurora path, not fabricated scheduler state')
    gpu = current_gpu(args.gpu_uuid)
    if os.environ.get('CUDA_VISIBLE_DEVICES') != args.gpu_uuid:
        raise ValueError('Expose exactly the selected GPU UUID')
    args.output.mkdir(parents=True)
    record = {'status': 'initializing', 'kind': config['kind'], 'question': config['question'],
              'created_at': datetime.now(timezone.utc).isoformat(), 'identity': identity(), 'gpu': gpu,
              'run_directory': str(args.output.resolve()), 'config': config, 'config_sha256': sha256(config_path),
              'source_code_sha256': {str(p.relative_to(ROOT)): sha256(p) for p in
                  (Path(__file__), ROOT / 'src/country_persona/training_checks.py')},
              'independent_semantic_review_pending': True, 'generalization_claim': False, 'nccl_tested': False}
    write_json(args.output / 'launch.json', record)
    shutil.copy2(Path(__file__), args.output / 'runner.py')
    shutil.copy2(ROOT / 'src/country_persona/training_checks.py', args.output / 'training_checks.py')
    try:
        import torch
        from transformers import AutoTokenizer, Qwen3_5ForCausalLM
        from peft import LoraConfig
        from datasets import Dataset
        from trl import SFTConfig, SFTTrainer
        from country_persona.training_checks import (MeasuredTrainingSteps, OptimizationAudit, audit_completion_masks,
            adapter_snapshot, check_adapter_update, validate_rank_checks, verify_saved_adapter)
        record['versions'] = {k: importlib.metadata.version(k) for k in config['runtime_pins']}
        if record['versions'] != config['runtime_pins']:
            raise ValueError('Runtime differs from the versioned pins')
        record['all_packages'] = dict(sorted((d.metadata['Name'], d.version) for d in importlib.metadata.distributions()))
        write_json(args.output / 'environment.json', {'versions': record['versions'], 'packages': record['all_packages']})
        if torch.cuda.device_count() != 1 or not torch.cuda.is_bf16_supported():
            raise RuntimeError('Require exactly one visible BF16 CUDA device')
        torch.cuda.set_device(0)
        record['cuda'] = {'torch_cuda_version': torch.version.cuda, 'capability': list(torch.cuda.get_device_capability()),
                          'device': torch.cuda.get_device_name(0)}
        record['model_verification'] = verify_model(config)
        tokenizer = AutoTokenizer.from_pretrained(config['model_path'], local_files_only=True, trust_remote_code=False)
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        pack, rows, metadata = prepare_pack(config, tokenizer, record['model_verification'])
        record['prepared_pack'] = str(pack)
        torch.manual_seed(config['seed'])
        started = time.perf_counter()
        model, loading = Qwen3_5ForCausalLM.from_pretrained(config['model_path'], local_files_only=True,
            trust_remote_code=False, dtype=torch.bfloat16, attn_implementation='sdpa', output_loading_info=True)
        loading = {k: sorted(v) if isinstance(v, set) else v for k, v in loading.items()}
        if loading['missing_keys'] or loading['mismatched_keys'] or loading['error_msgs']:
            raise ValueError('Official text weights failed to load completely: ' + str(loading))
        record['text_model_loading'] = loading
        model.to('cuda:0')
        torch.cuda.synchronize()
        record['model_load_seconds'] = time.perf_counter() - started
        record['base_model_parameters'] = sum(p.numel() for p in model.parameters())
        record['status'] = 'base_controls_running'
        write_json(args.output / 'run.json', record)
        before = generate_controls(model, tokenizer, rows, metadata, config)
        write_jsonl(args.output / 'base-controls.jsonl', before)
        model.config.use_cache = False
        model.enable_input_require_grads()
        settings = SFTConfig(output_dir=str(args.output / 'adapter'), max_length=config['max_length'],
            max_steps=config['max_steps'], gradient_accumulation_steps=config['gradient_accumulation_steps'],
            per_device_train_batch_size=1, learning_rate=config['learning_rate'], warmup_steps=0,
            bf16=True, fp16=False, gradient_checkpointing=True,
            gradient_checkpointing_kwargs={'use_reentrant': False}, completion_only_loss=True,
            packing=False, seed=config['seed'], report_to='none', save_strategy='no', logging_steps=1,
            optim='adamw_torch', eos_token=tokenizer.eos_token)
        audit = OptimizationAudit()
        class MeasuredTrainer(MeasuredTrainingSteps, SFTTrainer):
            pass
        trainer = MeasuredTrainer(model=model, args=settings, train_dataset=Dataset.from_list(rows),
            processing_class=tokenizer, callbacks=[audit],
            peft_config=LoraConfig(r=config['lora_rank'], lora_alpha=2 * config['lora_rank'],
                                  lora_dropout=0.05, target_modules='all-linear', task_type='CAUSAL_LM'))
        record['mask_audit'] = audit_completion_masks(rows, trainer.train_dataset, trainer.data_collator, tokenizer)
        record['before_training_control_loss'] = supervised_loss(trainer.model, trainer, trainer.train_dataset)
        record['status'] = 'training_running'
        write_json(args.output / 'run.json', record)
        torch.cuda.reset_peak_memory_stats()
        started = time.perf_counter()
        result = trainer.train()
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - started
        if not math.isfinite(result.training_loss):
            raise FloatingPointError('Nonfinite final training loss')
        report = {'rank': 0, 'steps': trainer.state.global_step, 'training_loss': result.training_loss,
                  'actual_sequence_tokens': trainer.processed_tokens, 'actual_target_tokens': trainer.target_tokens,
                  'gradient_checks': len(audit.gradients), 'gradient_trace': audit.gradients,
                  **check_adapter_update(audit.initial, adapter_snapshot(trainer.model))}
        record['optimization_checks'] = validate_rank_checks([report], 1, config['max_steps'])
        record['measurement'] = {'training_seconds': elapsed, 'peak_allocated_gpu_gib': torch.cuda.max_memory_allocated() / 2**30,
                                 'trainer_metrics': result.metrics}
        record['after_training_control_loss'] = supervised_loss(trainer.model, trainer, trainer.train_dataset)
        trainer.save_model(str(args.output / 'adapter'))
        tokenizer.save_pretrained(str(args.output / 'adapter'))
        probe = torch.tensor([trainer.train_dataset[0]['input_ids'][:32]], device='cuda:0')
        record['serialization_checks'] = verify_saved_adapter(trainer.model, args.output / 'adapter', probe,
                                                              atol=1e-5, rtol=1e-5)
        trainer.model.config.use_cache = True
        after = generate_controls(trainer.model, tokenizer, rows, metadata, config)
        if [r['input_ids_digest'] for r in before] != [r['input_ids_digest'] for r in after]:
            raise ValueError('Before/after prompts differ')
        write_jsonl(args.output / 'adapter-controls.jsonl', after)
        record.update(status='technical_single_gpu_training_and_reload_passed',
                      completed_at=datetime.now(timezone.utc).isoformat(), before_after_prompt_digests_identical=True,
                      delivered_baseline_controls=len(before), delivered_adapter_controls=len(after))
        write_json(args.output / 'run.json', record)
        print(json.dumps({k: record[k] for k in ('status', 'measurement', 'before_training_control_loss',
                                                'after_training_control_loss', 'serialization_checks')}, indent=2))
    except BaseException as exc:
        record.update(status='failed_technical_training_checkpoint', error=f'{type(exc).__name__}: {exc}',
                      failed_at=datetime.now(timezone.utc).isoformat())
        write_json(args.output / 'failure.json', record)
        write_json(args.output / 'run.json', record)
        raise


if __name__ == '__main__':
    main()
