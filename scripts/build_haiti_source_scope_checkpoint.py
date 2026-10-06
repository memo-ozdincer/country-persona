"""Freeze a two-case diagnostic by deleting only the other country's full speech."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl


def main():
    old = ROOT / 'data/prepared/conditional-india-eval-20261006-v2'
    dest = ROOT / 'data/prepared/haiti-source-scope-20261006-v1'
    assert not dest.exists(), 'Preserve existing packs; use a fresh version'
    manifest = json.loads((old / 'manifest.json').read_text())
    for name, expected in manifest['files_sha256'].items():
        assert sha256(old / name) == expected
    statements = json.loads((old / 'haiti-statements.json').read_text())
    blocks = {co: 'COMPLETE NATIONAL POST-VOTE STATEMENT — ' + co +
              ' — S/PV.9430, 2 October2023\n' + s['text'] for co, s in statements.items()}
    combined = '\n\n'.join(blocks.values())
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-conditional-india-base-eval-20261006-v2.json').read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    cases, changes = [], []
    for original in read_jsonl(old / 'cases.jsonl'):
        if original['id'] not in {'haiti-bra-raw', 'haiti-gbr-raw'}:
            continue
        co = original['country_iso3']
        text = original['prompt'][1]['content']
        assert text.endswith(combined) and text.count(combined) == 1
        prefix = text[:-len(combined)]
        case = copy.deepcopy(original)
        case['prompt'][1]['content'] = prefix + blocks[co]
        case['condition'] = 'raw_own_statement_only'
        ids = tok.apply_chat_template(case['prompt'], tokenize=True, return_dict=False,
                                     add_generation_prompt=True, **cfg['chat_template_kwargs'])
        case.update(input_ids=ids, input_ids_digest=digest(ids))
        assert case['prompt'][0] == original['prompt'][0]
        assert len(ids) + cfg['generation_max_new_tokens'] <= cfg['max_length']
        cases.append(case)
        changes.append({'id': case['id'], 'country': co, 'old_prompt_digest': digest(original['prompt']),
                        'new_prompt_digest': digest(case['prompt']), 'prefix_digest': digest(prefix),
                        'own_block_digest': digest(blocks[co]), 'old_input_tokens': len(original['input_ids']),
                        'new_input_tokens': len(ids), 'deleted_country': next(x for x in blocks if x != co),
                        'only_other_speech_and_one_separator_removed': True})
    assert len(cases) == 2
    dest.mkdir(parents=True)
    write_jsonl(dest / 'cases.jsonl', cases)
    for name in ['criteria.json', 'haiti-statements.json', 'haiti-source-proof.json']:
        shutil.copy2(old / name, dest / name)
    write_json(dest / 'provenance.json', {
        'parent_pack': str(old.relative_to(ROOT)), 'parent_manifest_sha256': sha256(old / 'manifest.json'),
        'parent_cases_sha256': sha256(old / 'cases.jsonl'), 'criteria_sha256': sha256(old / 'criteria.json'),
        'changes': changes, 'new_model_calls_planned': 4, 'new_optimizer_steps': 0,
        'comparison_runs': {'base': 'runs/aurora-conditional-india-base-20261006-v2',
                            'adapter': 'runs/aurora-conditional-india-fit-20261006-v2'},
        'scope': 'Exposed Haiti development. Source scope and input length change together. '
                 'Same national task/scenario/questions/criteria, no new checked plan or fitting. '
                 'Government-persona, native prediction, independent review and sealed OOD remain unestablished.'})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'files_sha256': {f.name: sha256(f) for f in dest.iterdir() if f.is_file()},
        'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 2,
        'source_scope': 'Zero-fit own-national-statement versus combined-statement Haiti development diagnostic.'})
    keys = ['model', 'revision', 'model_path', 'runtime_path', 'runtime_pins', 'seed', 'max_length',
            'chat_template_kwargs', 'generation_max_new_tokens']
    ecfg = {k: cfg[k] for k in keys}
    ecfg.update(pack=str(dest.relative_to(ROOT)), eval_cases=2, max_steps=0, training_examples=0,
                kind='haiti_own_source_scope_diagnostic', authorization=cfg['authorization'])
    for arm in ['base', 'adapter']:
        armcfg = copy.deepcopy(ecfg)
        armcfg['control_arm'] = arm
        if arm == 'adapter':
            adapter = ROOT / 'runs/aurora-conditional-india-fit-20261006-v2/adapter'
            armcfg.update(adapter=str(adapter.relative_to(ROOT)),
                          adapter_sha256=sha256(adapter / 'adapter_model.safetensors'),
                          adapter_config_sha256=sha256(adapter / 'adapter_config.json'))
        write_json(ROOT / f'configs/posttraining/qwen35-haiti-source-scope-{arm}-20261006-v1.json', armcfg)
    print(json.dumps({'manifest_sha256': sha256(dest / 'manifest.json'), 'changes': changes}, indent=2))


if __name__ == '__main__':
    main()
