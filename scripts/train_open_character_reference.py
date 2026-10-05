"""Run the original training CLI and recipe, adding observation-only step/save receipts."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['dpo', 'sft'], required=True)
    parser.add_argument('--record', type=Path, required=True)
    args = parser.parse_args()
    config_path = ROOT / 'configs/posttraining/open-character-humor-20261004.json'
    config = json.loads(config_path.read_text())
    run = ROOT / config['run']
    code = Path(config['reference_code'])
    for path, revision in [(code, config['code_revision']), (code / 'openrlhf', config['training_revision'])]:
        if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=path, text=True).strip() != revision:
            raise ValueError('Original paper/training checkout revision changed')
    freeze = json.loads((run / 'inputs/freeze.json').read_text())
    for filename, record in freeze['files'].items():
        if sha256(run / 'inputs' / filename) != record['sha256']:
            raise ValueError('Frozen published training or evaluation input changed')
    for filename, expected in freeze['upstream_processor_sha256'].items():
        if sha256(code / filename) != expected: raise ValueError('Original recipe/evaluation source changed')
    audit = json.loads((run / 'training-input-audit.json').read_text())
    environment = json.loads((run / 'runtime-probe-v3/environment.json').read_text())
    if environment['flash_attention_2']['status'] != 'forward_backward_passed' or environment['fused_adam']['status'] != 'one_synthetic_parameter_step_passed':
        raise ValueError('Original attention/optimizer runtime probe did not pass')
    output = args.record / 'adapter'
    if output.exists(): raise ValueError('Preserve existing stage output; use a fresh fit directory')
    pretrain = Path(config['assets_root']) / 'base' if args.stage == 'dpo' else code.parent / 'merged-reproduction-dpo'
    if not (pretrain / 'model.safetensors.index.json').exists(): raise ValueError('Required pretraining weights are absent')
    module = 'openrlhf.cli.train_' + args.stage
    command = ['--save_path', str(output), '--eval_steps', '50', '--max_ckpt_num', '1',
        '--micro_train_batch_size', str(config['training'][args.stage]['micro_batch_size']),
        '--train_batch_size', '32', '--seed', '123456', '--zero_stage', '2', '--bf16',
        '--learning_rate', '5e-5', '--lr_warmup_ratio', '0.1', '--max_norm', '1.0',
        '--adam_betas', '0.9', '0.98', '--max_epochs', '1', '--pretrain', str(pretrain),
        '--dataset', str(run / 'inputs' / ('humor.' + args.stage + '.jsonl')),
        '--apply_chat_template', '--max_len', str(config['training'][args.stage]['max_len']),
        '--lora_rank', '64', '--lora_alpha', '128', '--use_tensorboard', str(args.record / 'tensorboard'),
        '--wandb_run_name', 'humor-reference-' + args.stage, '--ckpt_path', str(args.record / 'checkpoints')]
    if args.stage == 'dpo':
        command += ['--beta', '0.1', '--nll_loss_coef', '0.1', '--kl_loss_coef', '0.001',
                    '--chosen_key', 'chosen', '--rejected_key', 'rejected']
    else: command += ['--input_key', 'messages']
    recipe = {'module': module, 'arguments': command, 'config_sha256': sha256(config_path),
              'source_training_revision': config['training_revision'], 'input_audit': audit[args.stage],
              'attention_implementation': 'original default flash_attention_2',
              'operational_changes': ['Single-process torchrun launcher for explicit GPU ownership.',
                  'Scratch paths, local TensorBoard instead of external W&B.',
                  'Observation-only wrappers count successful original FusedAdam.step calls and original save_model calls.']}
    (args.record / 'recipe.json').write_text(json.dumps(recipe, indent=2) + '\n')
    import torch
    from deepspeed.ops.adam import FusedAdam
    from openrlhf.utils.deepspeed.deepspeed import DeepspeedStrategy
    stats = {'stage': args.stage, 'successful_optimizer_steps': 0, 'saved': False,
             'started_utc': datetime.now(timezone.utc).isoformat()}
    original_step = FusedAdam.step
    def observed_step(optimizer, *step_args, **step_kwargs):
        result = original_step(optimizer, *step_args, **step_kwargs)
        stats['successful_optimizer_steps'] += 1
        (args.record / 'optimizer-progress.json').write_text(json.dumps(stats, indent=2) + '\n')
        return result
    FusedAdam.step = observed_step
    original_save = DeepspeedStrategy.save_model
    def observed_save(strategy, model, tokenizer, save_path, **kwargs):
        result = original_save(strategy, model, tokenizer, save_path, **kwargs)
        engine = model.model
        stats.update(saved=True, engine_global_steps=engine.global_steps,
            peak_allocated_gpu_gib=torch.cuda.max_memory_allocated() / 2**30,
            peak_reserved_gpu_gib=torch.cuda.max_memory_reserved() / 2**30,
            lora_parameters=[{'name': name, 'elements': param.numel(),
                 'finite': bool(param.isfinite().all()), 'norm': float(param.float().norm())}
                 for name, param in engine.named_parameters() if 'lora_' in name])
        return result
    DeepspeedStrategy.save_model = observed_save
    sys.argv = [module] + command
    started = time.monotonic()
    try:
        runpy.run_module(module, run_name='__main__')
        stats['status'] = 'original_training_recipe_completed_and_saved'
        if not stats['saved'] or stats['successful_optimizer_steps'] != audit[args.stage]['expected_complete_optimizer_steps']:
            raise ValueError('Observed original optimizer-step count/save differs from audited complete epoch')
        if stats['engine_global_steps'] != stats['successful_optimizer_steps']:
            raise ValueError('Engine and optimizer disagree on successful update count')
        stats['adapter_files'] = {str(p.relative_to(output)): {'bytes': p.stat().st_size, 'sha256': sha256(p)}
                                 for p in output.rglob('*') if p.is_file()}
        if not all(p['finite'] for p in stats['lora_parameters']): raise ValueError('Nonfinite trained adapter')
    except BaseException as exc:
        stats.update(status='failed_reference_fit', error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        stats.update(elapsed_seconds=time.monotonic() - started, ended_utc=datetime.now(timezone.utc).isoformat())
        (args.record / 'fit.json').write_text(json.dumps(stats, indent=2) + '\n')


if __name__ == '__main__': main()
