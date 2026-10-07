"""Literal UK source/application composition; preserve failed intermediate reviews."""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl
from build_uk_raw_application import NOTE


def main():
    dest = ROOT / 'data/prepared/uk-raw-writer-20261007-v1'
    assert not dest.exists()
    selected = ['aurora-uk-quote-backed-source96-20261007-v1', 'aurora-uk-raw-application-adapter-20261007-v2']
    rows, links, inspections = [], [], []
    for name in selected:
        d = ROOT / 'runs' / name
        r = json.loads((d / 'run.json').read_text())
        i = json.loads((d / 'inspection.json').read_text())
        assert r['status'] == 'completed' and i['all_outputs_read_complete']
        assert r['transcript_sha256'] == i['transcript_sha256'] == sha256(d / 'transcript.jsonl')
        row = list(read_jsonl(d / 'transcript.jsonl'))[0]
        rows.append(row)
        inspections.append(i['reviews'][0])
        links.append({'run': str(d.relative_to(ROOT)), 'id': row['id'], 'row_digest': digest(row), 'transcript_sha256': sha256(d / 'transcript.jsonl'), 'inspection_sha256': sha256(d / 'inspection.json'), 'unedited_content': True})
    assert inspections[0]['source_only_task_pass'] and not inspections[1]['component_pass']
    plan = '\n\n'.join(row['output'] for row in rows)
    assert len(plan.split()) == 291
    old = ROOT / 'data/prepared/india-raw-writer-20261007-v1'
    system = list(read_jsonl(old / 'cases.jsonl'))[0]['prompt'][0]
    body = '''COUNTRY/ROLE/DATE: UK, Kariuki, national Council representative after voting, 1 December 2023, S/PV.9492. Ecuador chairs. Welcome is not a national vote label.

ACTUAL MODEL-GENERATED SOURCE FACTS PLUS APPLICATION (two stored unedited replies, hand-inspected by the same assistant; not government authority):
''' + plan + '''

CURRENT HYPOTHETICAL NOTE (R):
''' + NOTE + '''

TASK: Write a concise country memo in at most300 ordinary English words, under exactly Documented position, Analytical application and Authority. Preserve all eight documentary meanings and six analytical/authority meanings. Use the supplied factual points and application to address actual R, acknowledging retained clauses and identifying remaining defects. Include at least two concrete relevant operational directions and a practical competing cost. Preserve source commitments, hopes, historical actions and qualifications; recommendations are your analysis, not authenticated national endorsement. No invented writing date, new official condition, current or future vote, amount or deadline. Do not repeat the source or plan wholesale. Use readable ordinary English.'''
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-india-raw-writer-base-20261007-v1.json').read_text())
    cfg.update(pack=str(dest.relative_to(ROOT)), kind='UK_actual291_source_application_full14_composition', task_max_words=300)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    prompt = [system, {'role': 'user', 'content': body}]
    ids = tok.apply_chat_template(prompt, tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
    assert len(ids) + 2048 <= 8192
    case = {'id': 'uk-R-actual-source-and-application-writer', 'family': 'sudan', 'country_iso3': 'GBR', 'condition': 'actual291_unedited_intermediate_application_failed', 'prompt': prompt, 'input_ids': ids, 'input_ids_digest': digest(ids)}
    dest.mkdir()
    write_jsonl(dest / 'cases.jsonl', [case])
    source_pack = ROOT / 'data/prepared/uk-source-transfer-20261007-v1'
    application_pack = ROOT / 'data/prepared/uk-raw-application-20261007-v2'
    crit = json.loads((source_pack / 'criteria.json').read_text())
    crit['common_units'] = json.loads((application_pack / 'criteria.json').read_text())['common_units']
    crit['policy'] = 'Original eight UK source compounds plus unchanged six application compounds; 300 ordinary words, three sections. Failed 90-word intermediate retained. Same-assistant adaptive development; writer source family historically trained/exposed.'
    write_json(dest / 'criteria.json', crit)
    for f in ['sources.json']:
        shutil.copy2(source_pack / f, dest / f)
    shutil.copy2(old / 'presentation-criteria.json', dest / 'presentation-criteria.json')
    shutil.copy2(application_pack / 'manual-evaluation-expectations.json', dest / 'manual-evaluation-expectations.json')
    write_json(dest / 'actual-plan.json', {'plan': plan, 'words': 291, 'components': links, 'facts_are_model_generated': True, 'application_unedited': True, 'source_is_fitting_reply': False, 'application_intermediate_pass': False, 'scope': 'Literal actual 201+90 replies; uncertainty/omissions in intermediate retained. No human rewrite.'})
    write_json(dest / 'provenance.json', {'source_and_application_model_outputs_unchanged': True, 'scope': 'UK outside reader/application fitting sources, but historical writer/source development exposure. Source full8 pass under adaptive protocol; application failed. Final composition is a diagnostic, not independently validated or sealed OOD.'})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in dest.iterdir()}, 'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 1, 'source_scope': 'Actual 291-word UK plan, identical base/point8 controls; full14/guards/300 words/three sections, no optimization.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(dest / 'manifest.json'), 'scope': 'Entire primary source, both actual 201/90-word outputs, literal plan, R, all14 compounds and presentation/authority rules hand-read. No supplied analytical correction.'})
    write_json(ROOT / 'configs/posttraining/qwen35-uk-raw-writer-base-20261007-v1.json', cfg)
    a = ROOT / 'runs/aurora-plan-input-fit-20261006-v1/adapter'
    cfg.update(adapter=str(a.relative_to(ROOT)), adapter_sha256=sha256(a / 'adapter_model.safetensors'), adapter_config_sha256=sha256(a / 'adapter_config.json'))
    write_json(ROOT / 'configs/posttraining/qwen35-uk-raw-writer-point8-20261007-v1.json', cfg)
    print(json.dumps({'plan_words': 291, 'input_tokens': len(ids), 'intermediate_application_pass': False, 'new_steps': 0}))


if __name__ == '__main__':
    main()
