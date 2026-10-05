"""Recreate the upstream introspection processor and freeze the published evaluation inputs."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def literal_assignment(path, name):
    tree = ast.parse(path.read_text())
    return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == name for t in n.targets))


def main():
    config = json.loads((ROOT / 'configs/posttraining/open-character-humor-20261004.json').read_text())
    assets, code = Path(config['assets_root']), Path(config['reference_code'])
    out = ROOT / config['run'] / 'inputs'
    out.mkdir(parents=True, exist_ok=False)
    raw = assets / 'training-data'
    raw_dest = out / 'released-data'
    shutil.copytree(raw, raw_dest, ignore=shutil.ignore_patterns('.cache'))
    processor = code / 'character/introspection/data.py'
    system = literal_assignment(processor, 'i_system')
    # This literal deliberately retains upstream's unformatted {NAME} placeholders.
    frames = [pd.read_json(raw / 'self_reflection/qwen-2.5-7b-it/humor.jsonl', orient='records', lines=True)]
    for suffix in ['', '-leading']:
        df = pd.read_json(raw / ('self_interaction/qwen-2.5-7b-it/humor' + suffix + '.jsonl'), orient='records', lines=True)
        def replace(messages):
            assert messages[0]['role'] == 'system'
            messages[0]['content'] = system
            return messages
        df['messages'] = df['messages'].apply(replace)
        frames.append(df)
    combined = pd.concat([df[['messages']] for df in frames], ignore_index=True)
    np.random.seed(config['training']['seed'])
    compiled = combined.sample(frac=1).reset_index(drop=True)
    compiled.to_json(out / 'humor.sft.jsonl', orient='records', lines=True)
    shutil.copy2(raw / 'dpo/qwen-2.5-7b-it/humor.jsonl', out / 'humor.dpo.jsonl')
    variants = literal_assignment(code / 'character/robustness/generate/trained.py', 'variants')
    dove = pd.read_json(assets / 'pure-dove/Pure-Dove.jsonl', orient='records', lines=True)
    questions = dove['conversation'].apply(lambda x: x[0]['input']).tolist()[:config['evaluation']['first_n']]
    rows = []
    for variant in config['evaluation']['variants']:
        for index, question in enumerate(questions):
            user = question if variant == 'default' else question + '\n' + variants[variant]
            rows.append({'id': f'{variant}:{index}', 'source_index': index, 'variant': variant,
                         'question': question, 'messages': [{'role': 'user', 'content': user}],
                         'seed': config['training']['seed'] + index})
    with (out / 'robustness.jsonl').open('w') as f:
        for row in rows: f.write(json.dumps(row, ensure_ascii=False) + '\n')
    source_hashes = {str(p.relative_to(code)): sha256(p) for p in [processor,
        code / 'finetuning/distillation/qwen.sh', code / 'finetuning/introspection/qwen.sh',
        code / 'character/robustness/generate/trained.py', code / 'character/robustness/classify/run_classifier.py',
        code / 'character/utils.py']}
    receipt = {'status': 'reference_inputs_frozen_before_model_outputs',
        'raw_rows': {'dpo_pairs': sum(1 for _ in (out / 'humor.dpo.jsonl').open()),
                     'self_reflection': len(frames[0]), 'free_interaction': len(frames[1]),
                     'leading_interaction': len(frames[2])},
        'compiled_sft_rows': len(compiled), 'evaluation_rows': len(rows),
        'compilation': 'Original Pandas concat/sample/to_json operations; literal upstream i_system; seed 123456 replaces unspecified upstream shuffle seed.',
        'upstream_processor_sha256': source_hashes,
        'files': {str(p.relative_to(out)): {'bytes': p.stat().st_size, 'sha256': sha256(p)}
                  for p in sorted(out.rglob('*')) if p.is_file()}}
    (out / 'freeze.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ['status', 'raw_rows', 'compiled_sft_rows', 'evaluation_rows']}))


if __name__ == '__main__': main()
