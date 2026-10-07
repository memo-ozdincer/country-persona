"""Combine checked India facts with unedited actual newQ application; original full14 criteria."""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, write_jsonl, write_json, sha256, digest


def main():
    dest = ROOT / 'data/prepared/two-country-application-endpoint-20261007-v1'; assert not dest.exists()
    pack = ROOT / 'data/prepared/two-country-application-fit-20261007-v1'
    d = ROOT / 'runs/aurora-two-country-application-fit-20261007-v1'
    r = json.loads((d / 'run.json').read_text()); i = json.loads((d / 'inspection.json').read_text())
    assert r['status'] == 'completed' and i['all_outputs_read_complete'] and r['transcript_sha256'] == i['transcript_sha256'] == sha256(d / 'transcript.jsonl')
    row = list(read_jsonl(d / 'transcript.jsonl'))[5]; assert i['reviews'][5]['component_pass']
    case = list(read_jsonl(pack / 'cases.jsonl'))[5]
    facts = json.loads((pack / 'source-facts.json').read_text())['facts']; plan = facts + '\n\n' + row['output']; assert len(plan.split()) == 286
    note = case['prompt'][1]['content'].split('CURRENT HYPOTHETICAL NOTE (Q):\n', 1)[1].split('\n\nTASK:', 1)[0]
    template = list(read_jsonl(ROOT / 'data/prepared/actual-composed-writer-20261007-v1/cases.jsonl'))[0]
    text = template['prompt'][1]['content']; request = text[text.index('Write a national analyst response'):text.index('\n\nPUBLIC SOURCE METADATA')]
    contract = text[text.index('REALIZATION CONTRACT:'):]
    body = 'Assigned delegation: India.\n\n' + note + '\n\n' + request + '''\n\nPUBLIC SOURCE METADATA: S/PV.9214, 9 December 2022. India speaks in national capacity after an explicit switch from procedural presidency; closing chair switch excluded. Selected national span supplies no vote label. Claims remain attributed to India, not independently adjudicated world facts.

SOURCE-CHECKED FACTS PLUS ACTUAL MODEL APPLICATION (same-assistant source curation; application unedited, not government authority):
''' + plan + '\n\n' + contract
    prompt = [template['prompt'][0], {'role': 'user', 'content': body}]
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-paired-application-endpoint-base-20261007-v1.json').read_text())
    cfg.update(pack=str(dest.relative_to(ROOT)), kind='checked_India_facts_actual_newQ_application_full14_writer')
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    ids = tok.apply_chat_template(prompt, tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False); assert len(ids) + 2048 <= 8192
    c = {'id': 'india-sanctions-newQ-composed-writer', 'family': 'sanctions', 'country_iso3': 'IND', 'condition': 'checked_facts_unedited_untrained_state_application',
         'prompt': prompt, 'input_ids': ids, 'input_ids_digest': digest(ids)}
    previous_criteria = ROOT / 'data/prepared/two-context-country-fit-20261006-v1/criteria.json'
    old = json.loads(previous_criteria.read_text()); current = json.loads((pack / 'criteria.json').read_text())
    for k in ['common_units', 'universal_checks']: assert old[k] == current[k]
    criteria = {'source_units': {'sanctions': old['source_units']['sanctions']}, 'common_units': old['common_units'], 'universal_checks': old['universal_checks'],
                'policy': 'Unchanged eight India source compounds plus original six application/four source guards; original300word/three-section realization contract. Facts hand-curated, application actual newQ output; no raw source-extractor quality claim.'}
    dest.mkdir(); write_jsonl(dest / 'cases.jsonl', [c]); write_json(dest / 'criteria.json', criteria)
    write_json(dest / 'sources.json', {'sanctions': json.loads((pack / 'sources.json').read_text())['sanctions']})
    shutil.copy2(ROOT / 'data/prepared/actual-composed-writer-20261007-v1/presentation-criteria.json', dest / 'presentation-criteria.json')
    write_json(dest / 'actual-plan.json', {'plan': plan, 'words': 286, 'source_facts_pack': str(pack.relative_to(ROOT)), 'source_facts_sha256': sha256(pack / 'source-facts.json'),
               'application_run': str(d.relative_to(ROOT)), 'application_id': row['id'], 'application_row_digest': digest(row), 'application_inspection_sha256': sha256(d / 'inspection.json'),
               'application_unedited': True, 'facts_are_model_generated': False, 'operator': 'Literal concatenation of checked200facts and actual86application words. No semantic rewrite or target substitution.'})
    write_json(dest / 'provenance.json', {'old_eight_source_criteria_sha256': sha256(previous_criteria), 'original_writer_pack_sha256': sha256(ROOT / 'data/prepared/actual-composed-writer-20261007-v1/manifest.json'),
               'scope': 'India source-guided application/writer composition; familiar newly fitted source context, newQ state absent from training. Facts supplied by same assistant. No independent review/raw pipeline/strongOOD/persona/multi-agent gain.'})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in dest.iterdir()},
               'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 1, 'source_scope': 'Same286word plan, base versus savedcompression8, fourteen unchanged India source/application units and300word/three-section contract. No writer updates.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(dest / 'manifest.json'),
               'scope': 'Entire India primary source, checked200facts, actual86Q application, literal286plan, Q/request/metadata/source8+common6criteria and unchangedrealization contract hand-read. Source curation not model-extraction result.'})
    write_json(ROOT / 'configs/posttraining/qwen35-two-country-application-endpoint-base-20261007-v1.json', cfg)
    adapter = ROOT / 'runs/aurora-compression-fit-20261006-v1/adapter'
    cfg.update(adapter=str(adapter.relative_to(ROOT)), adapter_sha256=sha256(adapter / 'adapter_model.safetensors'), adapter_config_sha256=sha256(adapter / 'adapter_config.json'))
    write_json(ROOT / 'configs/posttraining/qwen35-two-country-application-endpoint-compression8-20261007-v1.json', cfg)
    print(json.dumps({'plan_words': 286, 'input_tokens': len(ids), 'facts_model_generated': False, 'application_unedited': True, 'new_steps': 0}))


if __name__ == '__main__': main()
