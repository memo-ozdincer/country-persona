"""Complete two exposed controls with unchanged checked points and no duplicate full source."""
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
    parent = ROOT / 'data/prepared/compression-fit-20261006-v1'
    dest = ROOT / 'data/prepared/compression-points-only-20261007-v1'
    assert dest.exists() and not (dest / 'manifest.json').exists()
    cases = list(read_jsonl(dest / 'draft-cases.jsonl'))
    original = {c['id']: c for c in read_jsonl(parent / 'cases.jsonl')}
    plans = json.loads((parent / 'held-plans.json').read_text())['plans']
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-compression-base-20261006-v1.json').read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    for case in cases:
        old = original[case['id'].removesuffix('-only')]
        text = old['prompt'][1]['content']
        start = text.index('\n\nCOMPLETE NATIONAL STATEMENT')
        end = text.index('\n\nSOURCE-CHECKED PLAN', start)
        expected = (text[:start] + text[end:]).replace('Full source remains for verification.', 'The source is archived for verification.')
        assert case['prompt'] == [old['prompt'][0], {'role': 'user', 'content': expected}]
        assert plans[case['country_iso3']] in expected
        ids = tok.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
        assert len(ids) + cfg['generation_max_new_tokens'] <= cfg['max_length']
        case.update(input_ids=ids, input_ids_digest=digest(ids))
    write_jsonl(dest / 'cases.jsonl', cases)
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(),
        'files_sha256': {p.name: sha256(p) for p in dest.iterdir() if p.is_file()},
        'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 2,
        'source_scope': 'Exposed Libya no-fit source-removal diagnostic; complete checked points and criteria unchanged.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True,
        'manifest_sha256': sha256(dest / 'manifest.json'),
        'read_scope': 'Both original complete points/Q/metadata/request/criteria hand-read. Exact source deletion and archived-verification clarification reread; no other wording or meaning changed. Sources remain in grader archive. This is exposed development, not a fresh family.'})
    cfg.update(pack=str(dest.relative_to(ROOT)), max_steps=0, training_examples=0, eval_cases=2)
    write_json(ROOT / 'configs/posttraining/qwen35-compression-points-only-base-20261007-v1.json', cfg)
    new = copy.deepcopy(cfg)
    adapter = ROOT / 'runs/aurora-compression-fit-20261006-v1/adapter'
    new.update(adapter=str(adapter.relative_to(ROOT)), adapter_sha256=sha256(adapter / 'adapter_model.safetensors'),
               adapter_config_sha256=sha256(adapter / 'adapter_config.json'))
    write_json(ROOT / 'configs/posttraining/qwen35-compression-points-only-adapter-20261007-v1.json', new)
    runner = (ROOT / 'scripts/run_compression_controls.py').read_text()
    runner = runner.replace('Owned fourteen-case compression baseline', 'Owned two-case points-only controls; no optimization').replace("cfg['eval_cases']==14", "cfg['eval_cases']==2")
    (ROOT / 'scripts/run_compression_points_only.py').write_text(runner)
    print(json.dumps({'cases': 2, 'input_tokens': {c['id']: len(c['input_ids']) for c in cases},
                      'calls_planned': 4, 'new_optimizer_steps': 0}))


if __name__ == '__main__':
    main()
