"""Replay frozen inputs, saved-fit checksums, pairing and classifier arithmetic without a GPU."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()


def read_rows(path):
    with path.open() as f: return [json.loads(line) for line in f]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--require-complete', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads((args.root / 'configs/posttraining/open-character-humor-20261004.json').read_text())
    run = args.root / config['run']
    reference = json.loads((run / 'reference/files.json').read_text())
    reference_count = 0
    for name, record in reference.items():
        if Path(name).name == '.DS_Store': continue  # OS metadata is omitted by the handoff builder.
        file = run / 'reference' / name
        if file.stat().st_size != record['bytes'] or sha256(file) != record['sha256']:
            raise ValueError('Archived published source/PDF bytes changed: ' + name)
        reference_count += 1
    inp = run / 'inputs'
    frozen = json.loads((inp / 'freeze.json').read_text())
    for name, record in frozen['files'].items():
        if (inp / name).stat().st_size != record['bytes'] or sha256(inp / name) != record['sha256']:
            raise ValueError('Frozen input bytes changed: ' + name)
    pack = {x['id']: x for x in read_rows(inp / 'robustness.jsonl')}
    if len(pack) != 4500: raise ValueError('Published question/variant set changed')
    prompted_freeze = json.loads((inp / 'prompted.freeze.json').read_text())
    if sha256(inp / 'prompted.robustness.jsonl') != prompted_freeze['file_sha256']:
        raise ValueError('Published prompted-control input bytes changed')
    prompted_pack = {x['id']: x for x in read_rows(inp / 'prompted.robustness.jsonl')}
    if set(prompted_pack) != set(pack): raise ValueError('Prompting control uses different questions')
    audit = json.loads((run / 'training-input-audit.json').read_text())
    fits = {}
    for stage in ['dpo', 'sft']:
        path = run / (stage + '-fit') / 'fit.json'
        if not path.exists():
            if args.require_complete: raise ValueError('Missing completed fit: ' + stage)
            fits[stage] = 'pending'; continue
        fit = json.loads(path.read_text())
        if fit['status'] != 'original_training_recipe_completed_and_saved': raise ValueError('Reference fit did not pass')
        expected = audit[stage]['expected_complete_optimizer_steps']
        if not fit['successful_optimizer_steps'] == fit['engine_global_steps'] == expected:
            raise ValueError('Incorrect actual update count')
        for name, record in fit['adapter_files'].items():
            file = path.parent / 'adapter' / name
            if file.stat().st_size != record['bytes'] or sha256(file) != record['sha256']:
                raise ValueError('Saved fitted adapter bytes changed')
        if not all(p['finite'] for p in fit['lora_parameters']): raise ValueError('Nonfinite fitted parameter')
        if not all(p['norm'] > 0 for p in fit['lora_parameters'] if 'lora_B' in p['name']):
            raise ValueError('Unchanged zero-initialized LoRA B tensors')
        fits[stage] = {'successful_updates': expected, 'saved_adapter_files_verified': len(fit['adapter_files']),
            'samples_in_complete_updates': expected * 32,
            'unapplied_accumulation_tail_samples': audit[stage]['upstream_retained_rows'] - expected * 32}
    arms, prompt_hashes = {}, {}
    labels = ['sarcasm', 'humor', 'remorse', 'goodness', 'loving', 'misalignment',
              'nonchalance', 'impulsiveness', 'sycophancy', 'mathematical', 'poeticism']
    for directory in ['base-robustness', 'author-robustness', 'prompted-base-robustness', 'reproduction-dpo-robustness', 'reproduction-full-robustness']:
        folder = run / directory
        if not (folder / 'classifier-summary.json').exists():
            if args.require_complete: raise ValueError('Missing completed scoring: ' + directory)
            continue
        summary = json.loads((folder / 'classifier-summary.json').read_text())
        for path in folder.glob('*.jsonl'):
            rows = read_rows(path)
            if len(rows) != 4500 or len({x['id'] for x in rows}) != 4500 or {x['id'] for x in rows} != set(pack):
                raise ValueError('Incomplete or duplicate evaluation outputs')
            for row in rows:
                expected_pack = prompted_pack if path.stem == 'prompted-base' else pack
                if any(row[k] != expected_pack[row['id']][k] for k in ['messages', 'question', 'seed', 'source_index', 'variant']):
                    raise ValueError('Changed matched evaluation input')
                if not 0 < len(row['output_token_ids']) <= 1024 or not row['response']:
                    raise ValueError('Invalid generated response')
                group_id = ('prompted:' if path.stem == 'prompted-base' else '') + row['id']
                if group_id in prompt_hashes and prompt_hashes[group_id] != row['prompt_sha256']:
                    raise ValueError('Actual rendered prompts differ between arms')
                prompt_hashes[group_id] = row['prompt_sha256']
            raw = {x['id']: x for x in rows}
            scores = json.loads((folder / (path.stem + '.scores.json')).read_text())
            if len(scores) != 4500 or {x['id'] for x in scores} != set(pack): raise ValueError('Scoring set changed')
            for score in scores:
                if sha256_response(raw[score['id']]['response']) != score['response_sha256']:
                    raise ValueError('Classifier was applied to a different response')
                logits = score['logits']
                exponentials = [math.exp(x - max(logits)) for x in logits]
                probability = exponentials[1] / sum(exponentials)
                if not math.isclose(probability, score['humor_probability'], abs_tol=1e-6):
                    raise ValueError('Stored classifier probability does not replay')
                if score['prediction'] != labels[max(range(11), key=lambda i: logits[i])]:
                    raise ValueError('Classifier label mapping changed')
            for variant, metric in summary['metrics'][path.stem].items():
                subset = [x for x in scores if str(x['variant']) == variant]
                correct = sum(x['prediction'] == 'humor' for x in subset)
                if metric['n'] != len(subset) or len(subset) != 500 or metric['humor_predictions'] != correct or metric['humor_recall'] != correct / 500:
                    raise ValueError('Published-protocol counts do not replay')
            arms[path.stem] = {'outputs': 4500, 'scores_replayed': 4500,
                              'caps': sum(x['finish_reason'] == 'length' for x in rows)}
    if args.require_complete and len(arms) != 6: raise ValueError('Expected six complete comparison arms including the original prompting control')
    result = {'status': 'complete_portable_replay_passed' if args.require_complete else 'available_evidence_replay_passed',
              'input_files_rehashed': len(frozen['files']), 'fits': fits, 'arms': arms,
              'unique_question_variants': len(pack), 'rendered_prompt_treatments_verified': len(prompt_hashes),
              'archived_reference_files_rehashed': reference_count,
              'scope': 'Byte integrity, observed steps and stored classifier arithmetic; not independent semantic review.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists(): raise ValueError('Use a fresh verification receipt')
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


def sha256_response(text): return hashlib.sha256(text.encode()).hexdigest()


if __name__ == '__main__': main()
