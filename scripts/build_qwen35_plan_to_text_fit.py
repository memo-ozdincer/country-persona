"""Freeze two complete plan-to-memo targets; South Sudan is excluded from optimization."""
import argparse
import json
from pathlib import Path
import shutil

from run_aurora_qwen35_smoke import ROOT
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl


def build(output):
    if output.exists():
        raise ValueError('Use a fresh training pack')
    pack = ROOT / 'data/prepared/qwen35-plan-to-text-eval-20260930-v2'
    manifest = json.loads((pack / 'manifest.json').read_text())
    for name, expected in manifest['files_sha256'].items():
        if sha256(pack / name) != expected:
            raise ValueError('Checked plans changed')
    spec_path = ROOT / 'configs/posttraining/qwen35-plan-to-text-targets-20260930.json'
    spec = json.loads(spec_path.read_text())
    cases = {r['scenario_id']: r for r in read_jsonl(pack / 'cases.jsonl')}
    plans = {r['scenario_id']: r for r in read_jsonl(pack / 'plans.jsonl')}
    lock = ROOT / 'data/prepared/qwen35-smoke-20260930-v1/tokenizer-lock.json'
    revision = json.loads(lock.read_text())['revision']
    rows, metadata = [], []
    for scenario, text in spec['targets'].items():
        if scenario not in ('climate-policy-workshop-v1', 'ukraine-policy-workshop-v1'):
            raise ValueError('Only the two inspected training contexts are admitted')
        if len(text.split()) > 700:
            raise ValueError('Target exceeds the requested word limit')
        case, plan = cases[scenario], plans[scenario]
        row = {'prompt': case['prompt'], 'completion': [{'role': 'assistant', 'content': text}],
               'chat_template_kwargs': {'enable_thinking': False}}
        metadata.append({'id': case['id'], 'row_index': len(rows), 'example_sha256': digest(row),
            'split': 'train', 'split_group': case['split_group'], 'status': 'research_prepared',
            'machine_checks_passed': True, 'training_admitted': False, 'human_reviewed': False,
            'independent_review_complete': False, 'country_iso3': 'ALL',
            'countries': list(plan['countries']), 'source_text_digests': plan['source_text_digests'],
            'derivation': spec['teacher'], 'model_revision': revision, 'tokenizer_lock_sha256': sha256(lock),
            'case_sha256': case['case_sha256'], 'plan_sha256': plan['plan_sha256'],
            'training_prompt_is_evaluation_prompt': True, 'target_words': len(text.split())})
        rows.append(row)
    if len(rows) != 2:
        raise ValueError('Require exactly two complete targets')
    output.mkdir(parents=True)
    write_jsonl(output / 'train.jsonl', rows)
    write_jsonl(output / 'train.manifest.jsonl', metadata)
    shutil.copy2(lock, output / lock.name)
    shutil.copy2(spec_path, output / 'teacher-targets.json')
    shutil.copy2(Path(__file__), output / 'builder.py')
    write_json(output / 'release.json', {'status': 'two_complete_plan_to_text_targets_prepared',
        'examples': len(rows), 'model_revision': revision, 'teacher': spec['teacher'],
        'eval_pack_manifest_sha256': sha256(pack / 'manifest.json'),
        'base_inspection_sha256': sha256(ROOT / 'runs/aurora-qwen35-plan-to-text-base-20260930-v1/inspection.json'),
        'training_contexts': list(spec['targets']), 'outside_training_monitor': 'south-sudan-policy-workshop-v1',
        'training_admitted': False, 'independent_review_complete': False, 'confirmatory_generalization': False,
        'limitations': ['Training prompts equal the first two evaluation prompts: training controls, not generalization.',
            'South Sudan is outside this fit but already exposed development material.',
            'Intended decisions and content are provided to the student; this does not teach decision prediction.',
            'Teacher and review are the same assistant. Targets were prepared after base inspection.'],
        'files_sha256': {p.name: sha256(p) for p in output.iterdir() if p.is_file()}})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    build(parser.parse_args().output)
