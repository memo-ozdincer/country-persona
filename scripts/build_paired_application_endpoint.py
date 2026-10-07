"""Test the unedited untrained-state plan at the fixed full writer endpoint."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, write_jsonl, write_json, sha256, digest


def main():
    old = ROOT / 'data/prepared/actual-composed-writer-20261007-v1'
    dest = ROOT / 'data/prepared/paired-application-endpoint-20261007-v1'
    assert not dest.exists()
    selected = [('aurora-source-status-fit-20261007-v2', 0), ('aurora-paired-application-fit-20261007-v1', 2)]
    rows, links = [], []
    for name, index in selected:
        d = ROOT / 'runs' / name; r = json.loads((d / 'run.json').read_text()); i = json.loads((d / 'inspection.json').read_text())
        assert r['status'] == 'completed' and i['all_outputs_read_complete']
        assert r['transcript_sha256'] == i['transcript_sha256'] == sha256(d / 'transcript.jsonl')
        row = list(read_jsonl(d / 'transcript.jsonl'))[index]; rows.append(row)
        links.append({'run': str(d.relative_to(ROOT)), 'id': row['id'], 'row_digest': digest(row),
                      'run_sha256': sha256(d / 'run.json'), 'transcript_sha256': sha256(d / 'transcript.jsonl'),
                      'inspection_sha256': sha256(d / 'inspection.json'), 'unedited_content': True})
    application_review = json.loads((ROOT / 'runs' / selected[1][0] / 'inspection.json').read_text())['reviews'][2]
    assert application_review['content_counts'] == {'met': 6} and not application_review['component_pass']
    assert all(v['status'] == 'met' for v in application_review['universal_checks'].values())
    plan = rows[0]['output'] + '\n\n' + rows[1]['output']
    assert len(plan.split()) == 319
    c = copy.deepcopy(list(read_jsonl(old / 'cases.jsonl'))[0])
    prior = json.loads((old / 'actual-plan.json').read_text())['plan']
    text = c['prompt'][1]['content']; assert text.count(prior) == 1
    text = text.replace(prior, plan)
    begin = text.index('Hypothetical implementation note Z keeps')
    end = text.index('\n\nWrite a national analyst response', begin)
    app_case = list(read_jsonl(ROOT / 'data/prepared/paired-application-states-20261007-v1/cases.jsonl'))[2]
    note = app_case['prompt'][1]['content'].split('CURRENT HYPOTHETICAL NOTE (alternative Z-S):\n', 1)[1].split('\n\nTASK:', 1)[0]
    text = text[:begin] + note + text[end:]
    c.update(id='ukraine24-fra-untrained-state-composed-writer', condition='actual_familiar_facts_plus_untrained_application_state',
             prompt=[c['prompt'][0], {'role': 'user', 'content': text}])
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-actual-composed-writer-base-20261007-v1.json').read_text())
    cfg.update(pack=str(dest.relative_to(ROOT)), kind='unedited_untrained_application_state_full14_endpoint')
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    ids = tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
    c.update(input_ids=ids, input_ids_digest=digest(ids)); assert len(ids) + 2048 <= 8192
    dest.mkdir(); write_jsonl(dest / 'cases.jsonl', [c])
    for f in ['criteria.json', 'sources.json', 'presentation-criteria.json']: shutil.copy2(old / f, dest / f)
    write_json(dest / 'actual-plan.json', {'plan': plan, 'words': 319, 'components': links,
               'operator': 'Literal concatenation; no human edits. Application passes six content units/four guards but fails its intermediate90word/no-repetition contract. This endpoint diagnostic does not erase that failure.'})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(),
               'files_sha256': {p.name: sha256(p) for p in dest.iterdir()}, 'training_authorized_for_this_pack': False,
               'training_examples': 0, 'eval_cases': 1, 'source_scope': 'Untrained proposal-state full14/300word/three-section endpoint, same source and fixed writer. Familiar fitted source facts; adaptive development, not strongOOD/persona/multi-agent gain.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True,
               'manifest_sha256': sha256(dest / 'manifest.json'), 'scope': 'All207source/112application words, literal319plan, neutralZ-S, source metadata, original14criteria and300word contract hand-read. Intermediate failure retained.'})
    write_json(ROOT / 'configs/posttraining/qwen35-paired-application-endpoint-base-20261007-v1.json', cfg)
    adapter = ROOT / 'runs/aurora-plan-input-fit-20261006-v1/adapter'
    cfg.update(adapter=str(adapter.relative_to(ROOT)), adapter_sha256=sha256(adapter / 'adapter_model.safetensors'),
               adapter_config_sha256=sha256(adapter / 'adapter_config.json'))
    write_json(ROOT / 'configs/posttraining/qwen35-paired-application-endpoint-point8-20261007-v1.json', cfg)
    print(json.dumps({'plan_words': 319, 'input_tokens': len(ids), 'intermediate_contract_pass': False, 'new_steps': 0}))


if __name__ == '__main__':
    main()
