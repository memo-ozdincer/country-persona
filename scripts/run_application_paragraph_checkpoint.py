"""One bounded application paragraph with pre-GPU metadata and native token checks."""
import argparse
import importlib.metadata
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, sha256, write_json, write_jsonl
from country_persona.reasoning_output import split_native_output
from run_aurora_qwen35_smoke import identity, current_gpu, verify_model, generate_controls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['base', 'adapter'], required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--gpu-uuid', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--previous-inspected-run', type=Path)
    args = parser.parse_args(); os.chdir(ROOT)
    if args.output.exists() or os.environ.get('SLURM_JOB_ID') or os.environ.get('CUDA_VISIBLE_DEVICES') != args.gpu_uuid:
        raise ValueError('Fresh output and explicit single named Aurora GPU required')
    config = json.loads(args.config.read_text()); pack = ROOT / config['pack']; manifest = json.loads((pack / 'manifest.json').read_text())
    assert not manifest['training_authorized_for_this_pack']
    for name, expected in manifest['files_sha256'].items(): assert sha256(pack / name) == expected
    inspection = json.loads((pack / 'manual-inspection.json').read_text())
    assert inspection['all_selected_texts_read_complete'] and inspection['manifest_sha256'] == sha256(pack / 'manifest.json')
    previous = None
    if args.previous_inspected_run:
        run = json.loads((args.previous_inspected_run / 'run.json').read_text()); review = json.loads((args.previous_inspected_run / 'inspection.json').read_text())
        assert run['status'] == 'completed' and review['all_outputs_read_complete'] and review['all_reasoning_read_complete']
        assert review['transcript_sha256'] == sha256(args.previous_inspected_run / 'transcript.jsonl') == run['transcript_sha256']
        previous = {'run': str(args.previous_inspected_run), 'inspection_sha256': sha256(args.previous_inspected_run / 'inspection.json')}
    cases = list(read_jsonl(pack / 'cases.jsonl')); assert len(cases) == 1
    for case in cases:
        assert {'id','country_iso3','prompt','input_ids','input_ids_digest'} <= set(case)
        assert case['id'] and case['country_iso3'] and all(m['role'] in ('system','user','assistant') and isinstance(m['content'],str) for m in case['prompt'])
    gpu = current_gpu(args.gpu_uuid); args.output.mkdir(parents=True)
    source_paths = [Path(__file__), ROOT / 'scripts/run_aurora_qwen35_smoke.py', ROOT / 'src/country_persona/reasoning_output.py', ROOT / 'src/country_persona/io.py']
    record = {'status': 'initializing', 'mode': args.mode, 'identity': identity(), 'gpu': gpu, 'config': config,
              'config_sha256': sha256(args.config), 'pack_manifest_sha256': sha256(pack / 'manifest.json'),
              'manual_inspection_sha256': sha256(pack / 'manual-inspection.json'), 'run_directory': str(args.output.resolve()),
              'previous_inspected_run': previous, 'source_code_sha256': {str(p.relative_to(ROOT)): sha256(p) for p in source_paths},
              'created_at': datetime.now(timezone.utc).isoformat(), 'optimizer_steps': 0, 'scope': manifest['source_scope'], 'independent_review_complete': False}
    write_json(args.output / 'launch.json', record)
    for path in source_paths: shutil.copy2(path, args.output / path.name)
    try:
        import torch
        from transformers import AutoTokenizer, Qwen3_5ForCausalLM
        from peft import PeftModel
        record['versions'] = {k: importlib.metadata.version(k) for k in config['runtime_pins']}
        assert record['versions'] == config['runtime_pins'] and torch.cuda.device_count() == 1 and torch.cuda.is_bf16_supported()
        record['model_verification'] = verify_model(config); torch.manual_seed(config['seed'])
        tokenizer = AutoTokenizer.from_pretrained(config['model_path'], local_files_only=True)
        if tokenizer.pad_token_id is None: tokenizer.pad_token = tokenizer.eos_token
        model, loading = Qwen3_5ForCausalLM.from_pretrained(config['model_path'], local_files_only=True, dtype=torch.bfloat16, attn_implementation='sdpa', output_loading_info=True)
        assert not loading['missing_keys'] and not loading['mismatched_keys'] and not loading['error_msgs']
        record['text_model_loading'] = {k: sorted(v) if isinstance(v, set) else v for k, v in loading.items()}; model.to('cuda:0')
        if args.mode == 'adapter':
            adapter = ROOT / config['adapter']; assert sha256(adapter / 'adapter_model.safetensors') == manifest['adapter_sha256'] == config['adapter_sha256']
            assert sha256(adapter / 'adapter_config.json') == manifest['adapter_config_sha256']
            model = PeftModel.from_pretrained(model, str(adapter), is_trainable=False); record['loaded_adapter_sha256'] = config['adapter_sha256']
        assert tokenizer.apply_chat_template(cases[0]['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, **config['chat_template_kwargs']) == cases[0]['input_ids']
        record['status'] = 'generating'; write_json(args.output / 'run.json', record); torch.cuda.reset_peak_memory_stats()
        output = generate_controls(model, tokenizer, [{'prompt': cases[0]['prompt']}], cases, config)[0]
        marker = manifest['thinking_marker_ids']
        assert all(tokenizer.convert_tokens_to_ids(k) == v for k, v in marker.items())
        split = split_native_output(output['output_ids'], thinking=config['chat_template_kwargs']['enable_thinking'],
                                    open_id=marker['<think>'], close_id=marker['</think>'], eos_id=tokenizer.eos_token_id)
        output.update(raw_output=tokenizer.decode(output['output_ids'], skip_special_tokens=False),
                      output=tokenizer.decode(split['public_ids'], skip_special_tokens=True), reasoning=tokenizer.decode(split['reasoning_ids'], skip_special_tokens=True),
                      **split, scope=manifest['source_scope'], public_tokens_including_eos=len(split['public_ids']), reasoning_tokens=len(split['reasoning_ids']))
        write_jsonl(args.output / 'transcript.jsonl', [output]); (args.output / 'public-answer.txt').write_text(output['output']); (args.output / 'reasoning.txt').write_text(output['reasoning'])
        record.update(status='completed', outputs=1, transcript_sha256=sha256(args.output / 'transcript.jsonl'), peak_allocated_gpu_gib=torch.cuda.max_memory_allocated() / 2**30,
                      completed_at=datetime.now(timezone.utc).isoformat())
        write_json(args.output / 'run.json', record); print(json.dumps({'public_protocol': output['protocol_status'], 'reasoning_tokens': output['reasoning_tokens'], 'public_tokens': output['public_tokens_including_eos'], 'at_cap': output['at_output_cap']}))
    except BaseException as exc:
        record.update(status='failed', error=type(exc).__name__ + ': ' + str(exc)); write_json(args.output / 'failure.json', record); write_json(args.output / 'run.json', record); raise


if __name__ == '__main__': main()
