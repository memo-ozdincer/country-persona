"""Freeze a four-bullet instruction repair on the exposed third state; no new answer content."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, write_jsonl, write_json, sha256, digest

FORMAT = '''\n\nFORMAT CHECK: Use exactly four compact bullets: (1) retained current clauses and remaining source conflicts; (2) two scoped operations and practical competing cost; (3) actual support duration and response condition; (4) authority. Put the first three under Analytical decisions and the fourth under Authority. Do not repeat a clause. Keep the complete answer within 90 ordinary English words.'''

def main():
    old = ROOT / 'data/prepared/paired-application-monitor-20261007-v1'
    dest = ROOT / 'data/prepared/paired-application-format-control-20261007-v1'; assert not dest.exists()
    d = ROOT / 'runs/aurora-paired-application-endpoint-point8-20261007-v1'
    i = json.loads((d / 'inspection.json').read_text()); assert i['all_outputs_read_complete'] and i['transcript_sha256'] == sha256(d / 'transcript.jsonl')
    c = copy.deepcopy(list(read_jsonl(old / 'cases.jsonl'))[0]); c['prompt'][1]['content'] += FORMAT
    c.update(id='ukraine24-fra-opposite-repairs-format-control', condition='exposed_neutral_state_four_bullet_instruction')
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-paired-application-base-20261007-v1.json').read_text())
    cfg.update(pack=str(dest.relative_to(ROOT)), eval_cases=1, kind='exposed_state_format_only_prompt_repair')
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    ids = tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
    c.update(input_ids=ids, input_ids_digest=digest(ids)); assert len(ids) + 2048 <= 8192
    dest.mkdir(); write_jsonl(dest / 'cases.jsonl', [c])
    for f in ['criteria.json', 'sources.json', 'presentation-criteria.json']: shutil.copy2(old / f, dest / f)
    write_json(dest / 'provenance.json', {'parent_manifest_sha256': sha256(old / 'manifest.json'), 'previous_inspection_sha256': sha256(d / 'inspection.json'), 'change': FORMAT,
               'scope': 'Post-inspection format repair on an exposed state; facts/scenario/questions/criteria unchanged, no supplied decisions. Strong base receives identical instruction. No new training.'})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in dest.iterdir()},
               'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 1, 'source_scope': 'Exposed third-state four-bullet format diagnostic; six original application criteria/90word budget. No OOD claim.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(dest / 'manifest.json'), 'scope': 'Complete existing facts/note/questions/criteria plus new format instruction hand-read; no target answers supplied.'})
    write_json(ROOT / 'configs/posttraining/qwen35-paired-application-format-base-20261007-v1.json', cfg)
    adapter = ROOT / 'runs/aurora-paired-application-fit-20261007-v1/adapter'
    cfg.update(adapter=str(adapter.relative_to(ROOT)), adapter_sha256=sha256(adapter / 'adapter_model.safetensors'), adapter_config_sha256=sha256(adapter / 'adapter_config.json'))
    write_json(ROOT / 'configs/posttraining/qwen35-paired-application-format-adapter-20261007-v1.json', cfg)
    print(json.dumps({'cases': 1, 'input_tokens': len(ids), 'new_steps': 0, 'format_change_only': True}))

if __name__ == '__main__': main()
