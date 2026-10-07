"""Freeze complete India speech extraction, source-only questions and existing eight criteria."""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, write_jsonl, write_json, sha256, digest

QUESTIONS = '''1. Who speaks in which dated institutional capacity; what does the selected national span establish about a vote?
2. What status, purpose and population-suffering limits are stated for Article 41 sanctions?
3. What trade, economic and unintended humanitarian consequences require attention or redress?
4. What negotiating action, humanitarian and basic-needs goals, and agency safeguards are recorded?
5. What 1267 exploitation concerns, fronts and mechanisms are alleged; what caution is urged? Attribute allegations to the speaker.
6. What two institutional mechanisms were sought, and what is their recorded status in the final adopted text?
7. What misuse and political outcomes must exemptions avoid?
8. What future review and feedback hope is expressed, and what actual correction or future vote commitment is established?'''


def main():
    dest = ROOT / 'data/prepared/india-actual-extraction-20261007-v1'; assert not dest.exists()
    raw = ROOT / 'data/raw/source-plan-grounding-20261002-v1'
    acq = json.loads((raw / 'acquisition.json').read_text())
    for f, h in acq['files_sha256'].items(): assert sha256(raw / f) == h
    s = json.loads((raw / 'statements.json').read_text())['IND']; text = (raw / 'record-9214.txt').read_text()
    assert text[s['start']:s['end']].strip() == s['text']
    assert s['text'].startswith('I shall now make a statement as the representative of India.')
    assert text[s['end']:].startswith('I now resume my functions as President of the Council.')
    template = list(read_jsonl(ROOT / 'data/prepared/source-status-fit-20261007-v2/cases.jsonl'))[0]
    body = '''PUBLIC SOURCE METADATA: S/PV.9214, 9 December 2022. The speaker explicitly switches from procedural presidency to national representation of India before this statement and returns to chair afterwards. Only the complete bounded national statement below is supplied; it supplies no vote label. Assertions are India's recorded claims, not independently adjudicated facts.

QUESTIONS ONLY, NO ANSWERS PROVIDED:
''' + QUESTIONS + '\n\nCOMPLETE NATIONAL STATEMENT:\n' + s['text'] + '''

TASK: Give at most210 ordinary English words of Documented source points, covering every question and qualification. No application scenario is supplied. Preserve recorded actors, dates, conditional versus established claims, scope and actual ongoing commitments or hopes. Attribute assertions to India, not independent findings. No slash-list or fused-word shortcut, no invented amount, adopted reform or vote, no source repetition.'''
    prompt = [template['prompt'][0], {'role': 'user', 'content': body}]
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-source-status-base-20261007-v1.json').read_text())
    cfg.update(pack=str(dest.relative_to(ROOT)), eval_cases=1, kind='complete_India_source_only_extraction_transfer', task_max_words=210)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    ids = tok.apply_chat_template(prompt, tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False); assert len(ids) + 2048 <= 8192
    c = {'id': 'india-sanctions-complete-source-extraction', 'family': 'sanctions', 'country_iso3': 'IND', 'condition': 'raw_primary_speech_questions_only_no_teacher_facts',
         'prompt': prompt, 'input_ids': ids, 'input_ids_digest': digest(ids)}
    old = ROOT / 'data/prepared/two-country-application-endpoint-20261007-v1'; oldcrit = json.loads((old / 'criteria.json').read_text())
    crit = {'source_units': {'sanctions': {'IND': oldcrit['source_units']['sanctions']}}, 'common_units': {}, 'universal_checks': oldcrit['universal_checks'],
            'policy': 'Same eight Indian source compounds/four source guards; source-only210word/one-documentary-section extraction. No decision teacher facts or application. Historically exposed source outside the two-French-source extractor fit; not strongOOD.'}
    dest.mkdir(); write_jsonl(dest / 'cases.jsonl', [c]); write_json(dest / 'criteria.json', crit)
    write_json(dest / 'sources.json', {'sanctions': {'IND': {**s, 'symbol': 'S/PV.9214', 'source_date': '2022-12-09', 'institutional_capacity': 'National India speech after chair switch; closing chair switch excluded'}}})
    write_json(dest / 'presentation-criteria.json', {'source_only': True, 'task_max_words': 210, 'one_documentary_section': True, 'ordinary_word_separation': 'Readable English, no systematic fused words/slash-list shortcut; no source repetition.', 'independent_review_complete': False})
    write_json(dest / 'provenance.json', {'primary_acquisition_sha256': sha256(raw / 'acquisition.json'), 'prior_source_criteria_sha256': sha256(old / 'criteria.json'),
               'previous_checkpoint_sha256': sha256(ROOT / 'reports/two-country-application-checkpoint-20261007-v1.json'), 'teacher_facts_supplied': False, 'preferred_targets_supplied': False,
               'scope': 'One complete historically exposed Indian primary source, eight question topics only. Base versus saved two-French-source64 adapter; facts read before any downstream use. No new training.'})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in dest.iterdir()},
               'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 1, 'source_scope': 'Complete primary India source extraction before any application, identical protocol/source8criteria between base and savedsource64. Same curator/grader.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(dest / 'manifest.json'),
               'scope': 'Complete national speech/boundaries, all metadata, eight questions, source8criteria/four guards and210word contract hand-read. No teacher facts or decisions in input. Independent review pending.'})
    write_json(ROOT / 'configs/posttraining/qwen35-india-actual-extraction-base-20261007-v1.json', cfg)
    adapter = ROOT / 'runs/aurora-source-status-fit-20261007-v2/adapter'
    cfg.update(adapter=str(adapter.relative_to(ROOT)), adapter_sha256=sha256(adapter / 'adapter_model.safetensors'), adapter_config_sha256=sha256(adapter / 'adapter_config.json'))
    write_json(ROOT / 'configs/posttraining/qwen35-india-actual-extraction-source64-20261007-v1.json', cfg)
    print(json.dumps({'cases': 1, 'input_tokens': len(ids), 'source_words': len(s['text'].split()), 'new_steps': 0, 'teacher_facts_supplied': False}))


if __name__ == '__main__': main()
