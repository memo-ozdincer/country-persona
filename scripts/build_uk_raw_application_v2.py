"""Freeze one new UK implementation state with actual, unedited source extraction."""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

NOTE = '''Hypothetical implementation note R acknowledges adopted UNITAMS closure and the continuing need for UN and international support. It protects Mission staff and assets and requires timely visas. It directs immediate departure without orderly withdrawal or transfer of relevant tasks. It seeks meaningful talks between both warring parties for a permanent ceasefire and transfer of power to a civilian Administration, and constructive engagement with Ramtane Lamamra as the Secretary-General's Personal Envoy. It also requires all external engagement with Sudan to end automatically when UNITAMS closes. A colleague claims the UK officially endorses R and guarantees its next Council vote. No new national authority is supplied. R is hypothetical.'''


def main():
    dest = ROOT / 'data/prepared/uk-raw-application-20261007-v2'
    assert not dest.exists()
    source = ROOT / 'runs/aurora-uk-quote-backed-source96-20261007-v1'
    inspection = json.loads((source / 'inspection.json').read_text())
    row = list(read_jsonl(source / 'transcript.jsonl'))[0]
    assert inspection['all_outputs_read_complete'] and inspection['reviews'][0]['source_only_task_pass']
    assert inspection['transcript_sha256'] == sha256(source / 'transcript.jsonl')
    old = ROOT / 'data/prepared/india-raw-application-20261007-v1'
    system = list(read_jsonl(old / 'cases.jsonl'))[0]['prompt'][0]
    body = '''COUNTRY/ROLE/DATE: UK, Kariuki, national Council representative after voting, 1 December 2023, S/PV.9492. Ecuador chairs; national welcome is not a supplied vote label.

ACTUAL MODEL-GENERATED DOCUMENTED SOURCE POINTS (unedited; no teacher decisions):
''' + row['output'] + '''

CURRENT HYPOTHETICAL NOTE (R):
''' + NOTE + '''

TASK: Return at most90 ordinary English words under Analytical decisions and Authority. Cover each of these six questions explicitly:
1. Which clauses are actually retained in current R, and which remaining clauses conflict with source positions?
2. Give two concrete relevant operational directions, specifying their scope and recipients.
3. What practical competing benefit/cost follows?
4. Is official R endorsement or a future Council vote established?
5. Which real UK commitments, hopes and historical actions remain, preserving their stated scope?
6. Separate your analytical recommendations from official source positions and preserve the dated national role.
Do not repeat already repaired defects. No source restatement or supplied analytical answers. Do not replace historical positions with invented new endpoints, guaranteed quantities, conditions or votes.'''
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-india-raw-application-base-20261007-v1.json').read_text())
    cfg.update(pack=str(dest.relative_to(ROOT)), kind='UK_outside_application_fit_actual_source_R', task_max_words=90)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    prompt = [system, {'role': 'user', 'content': body}]
    ids = tok.apply_chat_template(prompt, tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
    assert len(ids) + 2048 <= 8192
    case = {'id': 'uk-R-actual-extraction-application', 'family': 'sudan', 'country_iso3': 'GBR', 'condition': 'new_R_outside_France_India_application_fit', 'prompt': prompt, 'input_ids': ids, 'input_ids_digest': digest(ids)}
    dest.mkdir()
    write_jsonl(dest / 'cases.jsonl', [case])
    crit = json.loads((old / 'criteria.json').read_text())
    crit.update(source_units={'sudan': {'GBR': {}}}, policy='Same six application compounds and source guards, UK source outside application fit, new R state frozen before calls. Source historically exposed; adaptive same-assistant development.')
    write_json(dest / 'criteria.json', crit)
    write_json(dest / 'manual-evaluation-expectations.json', {
        'A1': 'Acknowledge retained safety/assets/timely visas, meaningful ceasefire/civilian talks and constructive envoy engagement; repair immediate disorderly departure/task-transfer omission and automatic end to all external engagement. No invented requirement to reverse adopted closure.',
        'A2': 'At least two scoped relevant operations: coordinate orderly staff/assets withdrawal with task recipients; preserve continuing engagement/help channels rather than automatic shutdown. Equivalent concrete directions allowed.',
        'A3': 'Concrete implementation cost/tension, e.g. handover coordination/time while closure proceeds and support remains needed. No claim source promises unlimited provision.',
        'A4': 'Official R endorsement and future vote unknown; no supplied current national vote label.',
        'A5': 'Historical penholder compromise for orderly closure and actual continuing UK cooperation preserved, no new official reopening condition.',
        'A6': 'Recommendations marked analytical, source actor/role/date maintained; no invented national position.'})
    shutil.copy2(ROOT / 'data/prepared/uk-source-transfer-20261007-v1/sources.json', dest / 'sources.json')
    shutil.copy2(old / 'presentation-criteria.json', dest / 'presentation-criteria.json')
    write_json(dest / 'actual-source-points.json', {'facts': row['output'], 'words': len(row['output'].split()), 'source_row_digest': digest(row), 'unedited': True})
    write_json(dest / 'provenance.json', {'source_run': str(source.relative_to(ROOT)), 'source_id': row['id'], 'source_transcript_sha256': sha256(source / 'transcript.jsonl'), 'source_inspection_sha256': sha256(source / 'inspection.json'), 'facts_are_model_generated': True, 'source_reply_is_fitting': False, 'application_source_outside_fit': True, 'scope': 'Actual 201-word facts copied without edits; R and six-unit expectations frozen before calls. No targets/optimization, not sealed OOD or independent quality.'})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in dest.iterdir()}, 'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 1, 'source_scope': 'Actual 201-word UK source facts with new hypothetical R; base/application128 controls, no optimization.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(dest / 'manifest.json'), 'scope': 'Full primary, actual 201-word facts, hypothetical R, six questions, expectations/criteria and 90-word contract hand-read by root. No human intermediate edit.'})
    write_json(ROOT / 'configs/posttraining/qwen35-uk-raw-application-base-20261007-v1.json', cfg)
    adapter = ROOT / 'runs/aurora-two-country-application-fit-20261007-v1/adapter'
    cfg.update(adapter=str(adapter.relative_to(ROOT)), adapter_sha256=sha256(adapter / 'adapter_model.safetensors'), adapter_config_sha256=sha256(adapter / 'adapter_config.json'))
    write_json(ROOT / 'configs/posttraining/qwen35-uk-raw-application-adapter-20261007-v1.json', cfg)
    print(json.dumps({'input_tokens': len(ids), 'source_words': len(row['output'].split()), 'new_steps': 0}))


if __name__ == '__main__':
    main()
