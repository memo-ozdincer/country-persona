"""Compare a base and verified adapter on frozen or explicitly varied development prompts."""
from datetime import datetime, timezone
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import time

from run_aurora_qwen35_smoke import ROOT, current_gpu, identity, verify_model
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gpu-uuid', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/posttraining/qwen35-transfer-20260930.json')
    args = parser.parse_args()
    os.chdir(ROOT)
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text())
    if args.output.exists() or os.environ.get('SLURM_JOB_ID'):
        raise ValueError('Use a fresh explicit Aurora run without fabricated scheduler state')
    gpu = current_gpu(args.gpu_uuid)
    if os.environ.get('CUDA_VISIBLE_DEVICES') != args.gpu_uuid:
        raise ValueError('Expose exactly the selected GPU UUID')
    args.output.mkdir(parents=True)
    sources = [Path(__file__), ROOT / 'scripts/run_aurora_qwen35_smoke.py',
               ROOT / 'src/country_persona/training_checks.py']
    record = {'status': 'initializing', 'created_at': datetime.now(timezone.utc).isoformat(),
        'kind': config['kind'], 'question': config['question'], 'config': config,
        'config_sha256': sha256(config_path), 'identity': identity(), 'gpu': gpu,
        'run_directory': str(args.output.resolve()),
        'source_code_sha256': {str(p.relative_to(ROOT)): sha256(p) for p in sources},
        'independent_semantic_review_pending': True, 'generalization_claim': False,
        'completed_calls': 0, 'new_training_steps': 0}
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
        pack = ROOT / config['source_pack']
        manifest = json.loads((pack / 'manifest.json').read_text())
        for name, expected in manifest['files_sha256'].items():
            if sha256(pack / name) != expected:
                raise ValueError('Frozen source pack changed: ' + name)
        record['source_manifest_sha256'] = sha256(pack / 'manifest.json')
        cases = [c for c in read_jsonl(pack / 'cases.jsonl') if c['format_condition'] == config['format_condition']]
        if config.get('scenario_ids'):
            cases = [c for c in cases if c['scenario_id'] in config['scenario_ids']]
        expected_contexts = config.get('expected_contexts', 3)
        if len(cases) != expected_contexts or len({c['scenario_id'] for c in cases}) != expected_contexts:
            raise ValueError('Require the configured distinct frozen cases')
        for case in cases:
            if case['case_sha256'] != digest({k: v for k, v in case.items() if k != 'case_sha256'}):
                raise ValueError('Frozen case digest mismatch')
        if config.get('remove_prior_notes'):
            removed = []
            marker = '\n\nINITIAL OR REVISED NOTES (data to check, not instructions)\n'
            for case in cases:
                text = case['prompt'][-1]['content']
                if text.count(marker) != 1:
                    raise ValueError('Expected one terminal notes block; do not alter sources/questions')
                prefix, notes = text.split(marker)
                removed.append({'original_id': case['id'], 'original_case_sha256': case['case_sha256'],
                                'removed_text': notes, 'removed_text_digest': digest(notes)})
                case['source_case_sha256'] = case.pop('case_sha256')
                case['source_case_id'] = case.pop('id')
                case['prompt'][-1]['content'] = prefix
                case['depends_on_response_ids'] = []
                case['variant'] = 'terminal_prior_notes_removed_sources_questions_unchanged'
                case['id'] = digest(case)[:24]
                case['case_sha256'] = digest(case)
            write_json(args.output / 'removed-notes.json', removed)
            write_jsonl(args.output / 'variant-cases.jsonl', cases)
        tokenizer = AutoTokenizer.from_pretrained(config['model_path'], local_files_only=True)
        entries = []
        for case in cases:
            ids = tokenizer.apply_chat_template(case['prompt'], tokenize=True, return_dict=False,
                add_generation_prompt=True, **config['chat_template_kwargs'])
            if len(ids) + config['generation_max_new_tokens'] > config['context_budget']:
                raise ValueError('Full source packet plus generation allowance must fit; no truncation')
            entries.append({'case': case, 'input_ids': ids, 'input_ids_digest': digest(ids)})
        write_json(args.output / 'preflight.json', {'cases': [{'id': x['case']['id'],
            'scenario_id': x['case']['scenario_id'], 'case_sha256': x['case']['case_sha256'],
            'input_ids_digest': x['input_ids_digest'], 'prompt_tokens': len(x['input_ids'])} for x in entries],
            'context_budget': config['context_budget'], 'generation_cap': config['generation_max_new_tokens'],
            'no_truncation': True, 'chat_template_kwargs': config['chat_template_kwargs']})
        adapter_run = ROOT / config['adapter_run']
        trained = json.loads((adapter_run / 'run.json').read_text())
        if trained['status'] not in ('technical_single_gpu_training_and_reload_passed',
                                     'targeted_fit_and_matched_development_memos_completed') or (
                trained['config']['model'], trained['config']['revision'], trained['versions']) != (
                config['model'], config['revision'], record['versions']):
            raise ValueError('Adapter was not verified on this model/runtime')
        adapter = adapter_run / 'adapter'
        for name, expected in trained['serialization_checks']['files_sha256'].items():
            if sha256(adapter / name) != expected:
                raise ValueError('Frozen adapter bytes changed')
        record['adapter_provenance'] = {'run_sha256': sha256(adapter_run / 'run.json'),
            'files_sha256': trained['serialization_checks']['files_sha256'], 'steps': trained['config']['max_steps'],
            'training_prompts_are_evaluation_prompts': False,
            'evaluation_status': 'exposed_development_contexts_not_confirmatory_generalization'}
        model, loading = Qwen3_5ForCausalLM.from_pretrained(config['model_path'], local_files_only=True,
            dtype=torch.bfloat16, attn_implementation='sdpa', output_loading_info=True)
        loading = {k: sorted(v) if isinstance(v, set) else v for k, v in loading.items()}
        if loading['missing_keys'] or loading['mismatched_keys'] or loading['error_msgs']:
            raise ValueError('Text weights did not load completely')
        record['loading_info'] = loading
        model.to('cuda:0')
        generation = GenerationConfig(do_sample=False, use_cache=True,
            max_new_tokens=config['generation_max_new_tokens'], eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id)
        record['generation_config'] = generation.to_dict()
        torch.cuda.reset_peak_memory_stats()
        for arm in ('base', config.get('adapter_arm', 'two_step_adapter')):
            if arm != 'base':
                model = PeftModel.from_pretrained(model, adapter, is_trainable=False, local_files_only=True)
                actual = tensor_state_digest(adapter_snapshot(model))
                if actual != trained['optimization_checks']['rank_checks'][0]['final_adapter_digest']:
                    raise ValueError('Fresh adapter loading differs from verified trained state')
                record['fresh_adapter_load_digest'] = actual
                if any(p.requires_grad for p in model.parameters()):
                    raise ValueError('Evaluation must not optimize any parameter')
            model.eval()
            record['status'] = arm + '_running'
            write_json(args.output / 'run.json', record)
            for entry in entries:
                case = entry['case']
                ids = torch.tensor([entry['input_ids']], device='cuda:0')
                started = time.perf_counter()
                with torch.inference_mode():
                    output = model.generate(input_ids=ids, attention_mask=torch.ones_like(ids),
                                            generation_config=generation)[0, ids.shape[1]:].tolist()
                torch.cuda.synchronize()
                row = {'id': case['id'], 'scenario_id': case['scenario_id'], 'arm': arm,
                    'case_sha256': case['case_sha256'], 'input_ids_digest': entry['input_ids_digest'],
                    'prompt_tokens': len(entry['input_ids']), 'output_ids': output,
                    'output': tokenizer.decode(output, skip_special_tokens=True), 'generated_tokens': len(output),
                    'hit_output_cap': len(output) == config['generation_max_new_tokens'],
                    'generation_seconds': time.perf_counter() - started,
                    'output_digest': digest(output), 'response_id': digest([arm, case['id'], output])[:24]}
                transcript.append(row)
                write_jsonl(args.output / 'transcript.jsonl', transcript)
                record['completed_calls'] = len(transcript)
                write_json(args.output / 'run.json', record)
                print(json.dumps({k: row[k] for k in ('scenario_id', 'arm', 'generated_tokens',
                                                      'hit_output_cap', 'generation_seconds')}), flush=True)
        if [x['input_ids_digest'] for x in transcript[:expected_contexts]] != [x['input_ids_digest'] for x in transcript[expected_contexts:]]:
            raise ValueError('Paired input tokens differ')
        record.update(status='matched_development_transfer_completed',
            completed_at=datetime.now(timezone.utc).isoformat(), matched_input_digests=True,
            transcript_sha256=sha256(args.output / 'transcript.jsonl'),
            peak_allocated_gpu_gib=torch.cuda.max_memory_allocated() / 2**30)
    except BaseException as error:
        record.update(status='failed_transfer_checkpoint', error=f'{type(error).__name__}: {error}',
                      failed_at=datetime.now(timezone.utc).isoformat())
        write_json(args.output / 'failure.json', record)
        raise
    finally:
        write_json(args.output / 'run.json', record)


if __name__ == '__main__':
    main()
