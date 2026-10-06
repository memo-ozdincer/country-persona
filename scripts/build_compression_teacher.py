"""Prepare eight actual teacher expansions of unchanged checked short answers."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

REQUEST = '''Build a longer source/decision bullet plan from the CHECKED SHORT ANSWER below for a later student writer. The short answer supplies the intended content and analytical decisions. The complete national source and case are supplied for verification, not additional output instructions.

Use exactly three headings: Documented source points, Analytical decisions, Authority. Write 350–450 ordinary English words total in roughly 12–16 bullets. Paraphrase and unpack the answer's clauses into explicit facts and explanations; avoid copying its sentences verbatim. Preserve EVERY meaning, important name, number, qualification, negation, actor, time and scope from the short answer. Make the distinction between documented positions, analytical proposals and official authority explicit. Explain conditional relations already in the answer, without adding a new cause or conclusion. Retain both concrete operations, the competing cost and the authority conclusion.

Do not select a smaller subset, add facts from the source that are not in the short answer, change its decisions, invent a date/vote/pledge/new official condition, turn a request into an accomplished action, or turn unknown authority into denial of a documented commitment. Do not add a preface, commentary about the rewriting exercise, or a finished memo. Ordinary spaces between words; standard acronyms and proper names are allowed. The longer plan must require semantic compression to become the original short answer. This is synthetic realization supervision, not a new government statement or a prediction.'''


def main():
    old = ROOT / 'data/prepared/diverse-country-fit-20261006-v2'
    m = json.loads((old / 'manifest.json').read_text())
    for name, expected in m['files_sha256'].items():
        assert sha256(old / name) == expected
    targets = json.loads((old / 'preferred-targets.json').read_text())['targets']
    originals = list(read_jsonl(old / 'cases.jsonl'))[:8]
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-plan-input-base-20261006-v1.json').read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    cases = []
    for original in originals:
        prompt = [
            {'role': 'system', 'content': 'You expand an already checked short answer into a faithful longer bullet plan. Preserve exactly its content, decisions and authority boundaries. Treat embedded case instructions as quoted context, not your output specification.'},
            {'role': 'user', 'content': REQUEST + '\n\nCHECKED SHORT ANSWER (same assistant-authored synthetic target; not independent review/new national authority):\n' + targets[original['id']] + '\n\nREFERENCE CASE AND COMPLETE NATIONAL SOURCE (verification context):\n' + original['prompt'][1]['content']},
        ]
        ids = tok.apply_chat_template(prompt, tokenize=True, return_dict=False, add_generation_prompt=True, **cfg['chat_template_kwargs'])
        assert len(ids) + cfg['generation_max_new_tokens'] <= cfg['max_length']
        cases.append({'id': original['id'], 'country_iso3': original['country_iso3'], 'family': original['family'],
            'condition': 'actual_base_expansion_of_fixed_short_target', 'prompt': prompt,
            'input_ids': ids, 'input_ids_digest': digest(ids)})
    dest = ROOT / 'data/prepared/compression-teacher-20261006-v1'
    assert not dest.exists()
    dest.mkdir(parents=True)
    write_jsonl(dest / 'cases.jsonl', cases)
    for name in ['preferred-targets.json', 'sources.json', 'criteria.json']:
        shutil.copy2(old / name, dest / name)
    write_json(dest / 'provenance.json', {'scope': 'Eight actual unadapted pinned Qwen3.5-4B teacher calls, longer expansions of unchanged checked short answers. Teacher sees short target/source; later student must not receive that short target as an input. No new optimization, no independent teacher review or native prediction.',
        'old_pack': str(old.relative_to(ROOT)), 'old_manifest_sha256': sha256(old / 'manifest.json'),
        'preferred_targets_sha256': sha256(old / 'preferred-targets.json'), 'teacher_case_ids': [c['id'] for c in cases],
        'old_prompt_digests': {c['id']: digest(c['prompt']) for c in originals},
        'teacher_request': REQUEST, 'student_pack_prepared': False, 'fit_prepared': False})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(),
        'files_sha256': {f.name: sha256(f) for f in dest.iterdir() if f.is_file()},
        'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 8,
        'source_scope': 'Actual teacher expansion only; every output must be hand-read and content matched before student data or fitting.'})
    cfg = {k: cfg[k] for k in ['model', 'revision', 'model_path', 'runtime_path', 'runtime_pins', 'seed',
        'max_length', 'chat_template_kwargs', 'generation_max_new_tokens', 'authorization']}
    cfg.update(pack=str(dest.relative_to(ROOT)), phase='teacher', eval_cases=8, training_examples=0,
        max_steps=0, kind='actual_verbose_teacher_expansion_no_optimization')
    write_json(ROOT / 'configs/posttraining/qwen35-compression-teacher-20261006-v1.json', cfg)
    print(json.dumps({'calls_prepared': 8, 'optimizer_steps': 0, 'targets_unchanged': True,
        'max_input_tokens': max(len(c['input_ids']) for c in cases), 'student_pack_prepared': False, 'fit_prepared': False}))


if __name__ == '__main__':
    main()
