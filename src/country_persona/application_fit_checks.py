"""CPU guards for private teacher plans and an event-family-separated SFT test."""
import json
from pathlib import Path
from .io import digest, read_jsonl, sha256
from .train import validated_export


def validate_design(rows, metadata, teachers, cases, held_family):
    if not len(rows) == len(metadata) == len(teachers) == 20:
        raise ValueError('Require twenty aligned training rows')
    if len({m['id'] for m in metadata}) != 20 or len(cases) != 8 or len({c['id'] for c in cases}) != 8:
        raise ValueError('Duplicate or absent rows/cases')
    for row, meta, teacher in zip(rows, metadata, teachers):
        if meta['id'] != teacher['id'] or meta['split_group'] == held_family:
            raise ValueError('Teacher alignment or held family leakage')
        spec = teacher['teacher_authoring_context_specification']
        if spec[:-1] != row['prompt'] or 'PRIVATE CHECKED TEACHER PLAN' not in spec[-1]['content']:
            raise ValueError('Teacher specification must add a private plan to student input')
        if any('PRIVATE CHECKED TEACHER PLAN' in m['content'] or 'CHECKED RESPONSE PLAN' in m['content']
               for m in row['prompt']):
            raise ValueError('Private plan leaked into student input')
        if row['completion'] != [{'role': 'assistant', 'content': teacher['assistant_authored_target']}]:
            raise ValueError('Target differs from inspected teacher record')
    for case in cases:
        if case['case_sha256'] != digest({k: v for k, v in case.items() if k != 'case_sha256'}):
            raise ValueError('Frozen case changed')
        if case['condition'] != 'training_control' and case['split_group'] != held_family:
            raise ValueError('Held case family differs')
    for country in ('FRA', 'GBR'):
        role = [c for c in cases if c['country_iso3'] == country]
        raw = [c for c in role if c['condition'] == 'raw']
        plans = [c for c in role if c['condition'] == 'checked_plan']
        if len(raw) != 2 or {c['variant'] for c in raw} != {'restriction', 'revision'} or len(plans) != 1:
            raise ValueError('Require restriction/revision raw and one plan per held role')
        restriction = next(c for c in raw if c['variant'] == 'restriction')
        plan = plans[0]
        if plan['prompt'][:-1] != restriction['prompt'][:-1] or not plan['prompt'][-1]['content'].startswith(
                restriction['prompt'][-1]['content'] + '\n\nCHECKED RESPONSE PLAN (extra assistance):\n'):
            raise ValueError('Plan control must only append assistance')
    controls = [c for c in cases if c['condition'] == 'training_control']
    if len(controls) != 2 or {c['country_iso3'] for c in controls} != {'BRA', 'IND'}:
        raise ValueError('Require exact Brazil/India training controls')
    for c in controls:
        if not any(c['prompt'] == r['prompt'] for r in rows):
            raise ValueError('Training control is not an exact training prompt')


def load_frozen(root, config):
    train = root / config['training_pack']
    evaluation = root / config['eval_pack']
    for directory, name, expected in ((train, 'release.json', config['training_release_sha256']),
                                      (evaluation, 'manifest.json', config['eval_manifest_sha256'])):
        if sha256(directory / name) != expected:
            raise ValueError('Frozen pack identity changed')
        manifest = json.loads((directory / name).read_text())
        for filename, h in manifest['files_sha256'].items():
            if sha256(directory / filename) != h:
                raise ValueError('Frozen member changed: ' + filename)
    manifest = json.loads((evaluation / 'manifest.json').read_text())
    if manifest['training_release_sha256'] != config['training_release_sha256']:
        raise ValueError('Evaluation frozen for another training release')
    for name, h in manifest['source_files_sha256'].items():
        if sha256(root / name) != h:
            raise ValueError('Grounding source bytes changed: ' + name)
    rows, metadata = validated_export(train / 'train.jsonl', train / 'train.manifest.jsonl', 'train', True)
    teachers = list(read_jsonl(train / 'teacher-records.jsonl'))
    cases = list(read_jsonl(evaluation / 'cases.jsonl'))
    validate_design(rows, metadata, teachers, cases, manifest['heldout_family'])
    if len(rows) != config['training_examples'] or any(m['model_revision'] != config['revision'] for m in metadata):
        raise ValueError('Training size/model revision changed')
    lock_hash = sha256(train / 'tokenizer-lock.json')
    if any(m['tokenizer_lock_sha256'] != lock_hash for m in metadata):
        raise ValueError('Training tokenizer identity differs')
    lock = json.loads((train / 'tokenizer-lock.json').read_text())
    for name, h in lock['files_sha256'].items():
        if sha256(Path(config['model_path']) / name) != h:
            raise ValueError('Tokenizer bytes differ')
    return rows, metadata, cases


def match_references(after, references):
    if len(after) != 6 or len({r['id'] for r in after}) != 6:
        raise ValueError('Require six distinct adapter answers')
    for row in after:
        if row['id'] not in references or row['input_ids_digest'] != references[row['id']]['input_ids_digest']:
            raise ValueError('Before/after input tokens differ per case')
    return True
