"""Freeze an explicit-mode control without changing source facts, seeds or rubric."""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, sha256, write_json, write_jsonl

PARENT = ROOT / 'data/prepared/sanctions-interaction-20261007-v2-seed'
OUTPUT = ROOT / 'data/prepared/explicit-seed-control-20261007-v1'
MODE = ('CURRENT CONDITION: STARTING-DRAFT-ONLY REVISION. No peer draft is supplied. '
        'The national source documents and country mentions inside the starting draft are documentary '
        'evidence, not messages from another analyst. Revise only the supplied starting draft for your '
        'assigned role. Do not invent a peer point or describe source facts as a peer reply.')
REMOVE = ' In the peer condition, explicitly accept, qualify or reject one actual peer point with a source-grounded reason.'


def main():
    from transformers import AutoTokenizer
    assert not OUTPUT.exists(), 'Use a fresh output pack'
    manifest = json.loads((PARENT / 'manifest.json').read_text())
    for name, value in manifest['files_sha256'].items(): assert sha256(PARENT / name) == value
    protocol = json.loads((PARENT / 'protocol.json').read_text())
    old_revision = protocol['revision_task']
    assert old_revision.count(REMOVE) == 1
    new_revision = MODE + '\n\n' + old_revision.replace(REMOVE, '')
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-sanctions-interaction-seed-base-20261007-v1.json').read_text())
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    cases, links = [], []
    for parent in read_jsonl(PARENT / 'cases.jsonl'):
        case = json.loads(json.dumps(parent))
        old = parent['prompt'][1]['content']
        suffix = '\n\nREVISION TASK:\n' + old_revision
        assert old.endswith(suffix)
        prefix = old[:-len(suffix)]
        case['id'] = parent['id'] + '-explicit-mode'
        case['prompt'][1]['content'] = prefix + '\n\nREVISION TASK:\n' + new_revision
        case['input_ids'] = tok.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
        assert len(case['input_ids']) + 2048 <= 8192
        cases.append(case)
        links.append({'id': case['id'], 'parent_id': parent['id'], 'unchanged_prefix_sha256': __import__('hashlib').sha256(prefix.encode()).hexdigest(),
                      'system_unchanged': True, 'facts_proposal_initial_task_and_actual_seed_unchanged': True})
    OUTPUT.mkdir(parents=True)
    shutil.copy2(__file__, OUTPUT / 'builder-code.py')
    for name in ['criteria.json', 'full-primary-spans.json']:
        shutil.copy2(PARENT / name, OUTPUT / name)
    write_jsonl(OUTPUT / 'cases.jsonl', cases)
    write_json(OUTPUT / 'provenance.json', {'parent_pack': str(PARENT.relative_to(ROOT)),
               'parent_manifest_sha256': sha256(PARENT / 'manifest.json'), 'parent_cases_sha256': sha256(PARENT / 'cases.jsonl'),
               'parent_provenance_sha256': sha256(PARENT / 'provenance.json'), 'cases': links,
               'intervention': 'Explicit starting-draft-only mode and remove conditional peer-only task clause; all other text unchanged. These two wording changes are coupled.',
               'source_facts_origin': 'same root assistant curated; independent review pending',
               'new_source_reader_or_teacher_outputs': 0})
    write_json(OUTPUT / 'protocol.json', {**protocol, 'parent_revision_task': old_revision,
               'revision_task': new_revision, 'planned_max_model_outputs': 4, 'conditions': ['seed'],
               'question': 'Does explicit seed-only wording remove invented peer provenance without changing source/operation coverage?',
               'decision': 'Inspect base outputs before adapter; inspect all four before source-scope intervention or fitting. No automatic launch or fit.'})
    write_json(OUTPUT / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(),
               'files_sha256': {p.name: sha256(p) for p in OUTPUT.iterdir() if p.is_file()},
               'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 2,
               'source_scope': 'Four-answer wording control on exposed H1/common base seeds; same-assistant facts and review, no new optimization or independent persona/OOD claim.'})
    for mode in ['base', 'adapter']:
        source = ROOT / f'configs/posttraining/qwen35-sanctions-interaction-seed-{mode}-20261007-v1.json'
        config = json.loads(source.read_text())
        config.update(pack=str(OUTPUT.relative_to(ROOT)), kind='explicit-starting-draft-only-wording-control-v1')
        write_json(ROOT / f'configs/posttraining/qwen35-explicit-seed-{mode}-20261007-v1.json', config)
    print(json.dumps({'pack': str(OUTPUT.relative_to(ROOT)), 'manifest_sha256': sha256(OUTPUT / 'manifest.json'),
                      'cases': [(c['id'], len(c['input_ids'])) for c in cases]}, indent=2))


if __name__ == '__main__': main()
