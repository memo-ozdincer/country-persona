"""Freeze India source-only facts and three proposal states before transfer calls; no fit."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, write_jsonl, write_json, sha256, digest

FACTS = '''Documented source points:
- India speaks nationally in the Council, 9 December 2022, S/PV.9214, after an explicit switch from procedural presidency. The closing return to chair is excluded. This national span supplies no vote label.
- Article 41 sanctions are provisional, not permanent or ends in themselves; intended impact must not exacerbate population suffering.
- Legitimate trade and economic activity of the State and regional partners matter; unintended and humanitarian consequences need effective redress.
- India engaged constructively in negotiating 2664. It describes timely humanitarian/basic-needs assistance and predictable safeguards for agencies.
- Under 1267, India urges due diligence/extreme caution for proscribed entities. It alleges exploitation under State hospitality in regional terrorist havens, listed groups reinvented as humanitarian/civil-society organizations to evade sanctions, raise funds and recruit fighters. These are India's recorded claims.
- India sought a proactive 1267 Monitoring Team role AND robust reporting standards/mechanisms. Its specific concerns were not fully addressed in the final adopted text; requests are not accomplished reforms.
- Exemptions must not expand terror activities regionally or beyond, or mainstream terror entities politically.
- India hopes the shortcoming will be corrected in future implementation review using Monitoring Team feedback; no accomplished correction or future-vote commitment is established.'''

NOTES = {
    'monitoring-added': '''Hypothetical implementation note M retains provisional sanctions, legitimate trade and safeguards against terrorist exploitation or political mainstreaming. It adds a proactive 1267 Monitoring Team role and robust diversion reporting. However, every ultimate recipient must obtain clearance before any shipment leaves. Verified urgent life-saving shipments are ready now, but some clearance decisions take weeks; M withholds all shipments meanwhile. A colleague says these additions mean both Indian requests were already fully secured in the historical adopted resolution, India officially endorses M, and its next Council vote is guaranteed favourable. No new national authority is supplied. M is hypothetical.''',
    'timeliness-repaired': '''Alternative hypothetical implementation note N retains provisional sanctions, legitimate trade, targeted due diligence and safeguards against terrorist exploitation or political mainstreaming. Verified urgent life-saving shipments leave promptly while ongoing checks target identified diversion risks. N omits the proactive 1267 Monitoring Team role and robust reporting standards to reduce administrative work. A colleague says timeliness proves every Indian concern is satisfied, the historical final resolution already fully secured both requests, India officially endorses N, and its next Council vote is guaranteed favourable. No new national authority is supplied. N is hypothetical.''',
    'all-mechanisms': '''Alternative hypothetical implementation note P retains provisional sanctions, legitimate trade, targeted due diligence and safeguards against terrorist exploitation or political mainstreaming. Verified urgent life-saving shipments leave promptly while ongoing checks target identified diversion risks. It includes a proactive 1267 Monitoring Team role and robust reporting standards. It accurately distinguishes these hypothetical additions from the historical final resolution, where India's specific concerns were not fully addressed. A colleague says compatibility proves India officially endorses P and guarantees its next favourable Council vote. No new national authority is supplied. P is hypothetical.''',
}


def main():
    dest = ROOT / 'data/prepared/country-application-transfer-20261007-v1'; assert not dest.exists()
    raw = ROOT / 'data/raw/source-plan-grounding-20261002-v1'
    acquisition = json.loads((raw / 'acquisition.json').read_text())
    for f, h in acquisition['files_sha256'].items(): assert sha256(raw / f) == h
    source = json.loads((raw / 'statements.json').read_text())['IND']
    record = (raw / 'record-9214.txt').read_text()
    assert record[source['start']:source['end']].strip() == source['text']
    assert source['text'].startswith('I shall now make a statement as the representative of India.')
    assert record[source['end']:].startswith('I now resume my functions as President of the Council.')
    old = ROOT / 'data/prepared/paired-application-states-20261007-v1'
    original = list(read_jsonl(old / 'cases.jsonl'))[0]
    system = original['prompt'][0]
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-paired-application-base-20261007-v1.json').read_text())
    cfg.update(pack=str(dest.relative_to(ROOT)), kind='three_India_states_checked_source_facts_no_teacher_decisions', baseline_run='runs/aurora-country-application-transfer-base-20261007-v1')
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    cases = []
    for state, note in NOTES.items():
        label = {'monitoring-added': 'M', 'timeliness-repaired': 'N', 'all-mechanisms': 'P'}[state]
        body = f'''COUNTRY/ROLE/DATE: India, national Council representative, 9 December 2022. Procedural presidency is a different capacity.

SOURCE-CHECKED DOCUMENTED POINTS (assistant-curated facts only; no teacher decisions):
{FACTS}

CURRENT HYPOTHETICAL NOTE ({label}):
{note}

TASK: Return at most90 ordinary English words under Analytical decisions and Authority. Cover each of these six questions explicitly:
1. Which clauses are actually retained in current {label}, rather than desired source corrections?
2. Which remaining {label} claims conflict with the source, including alleged past actions?
3. Give two concrete relevant operational directions, specifying their scope and recipients.
4. What practical competing benefit/cost follows?
5. Which real Indian commitments, hopes and historical actions remain, preserving their stated scope?
6. Is official {label} endorsement or the future Council vote established?
No source restatement or supplied analytical answers. Recommendations must not be presented as official positions. Do not replace source commitments or hopes with new endpoints or conditions.'''
        prompt = [system, {'role': 'user', 'content': body}]
        ids = tok.apply_chat_template(prompt, tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
        assert len(ids) + 2048 <= 8192
        cases.append({'id': f'india-sanctions-{state}-application-transfer', 'family': 'sanctions', 'country_iso3': 'IND',
                      'condition': state, 'prompt': prompt, 'input_ids': ids, 'input_ids_digest': digest(ids)})
    criteria = copy.deepcopy(json.loads((old / 'criteria.json').read_text()))
    criteria['source_units'] = {'sanctions': {'IND': {}}}
    criteria['policy'] = 'Separate six-unit/90-word application component. Same common/source-guard definitions; new historically exposed Indian source outside this adapter fit. Three states frozen before calls; no targets/fit. Full source/writer endpoint remains separate.'
    expectations = {
        'monitoring-added': 'Acknowledge both added mechanisms; reject the actual all-shipment weeks-long gate and false historical completion claim. Preserve timely aid plus due diligence. Two scoped implementation steps and practical cost. Source historical constructive engagement and hope for correction through review/feedback remain; no newly promised vote.',
        'timeliness-repaired': 'Acknowledge prompt verified shipments/targeted checks; identify both missing proactive role AND robust reporting, plus false historical completion. Do not reintroduce universal clearance. Two scoped operations and practical cost; preserve source engagement/review hope, not a fixed vote condition.',
        'all-mechanisms': 'Acknowledge the complete compatible hypothetical repair; no repeated criticism of removed gate or present mechanisms. Historical concerns still not fully addressed in original text. Give two relevant implementation/monitoring steps and practical cost without inventing a new defect. Compatibility supplies no official endorsement/future vote.'}
    dest.mkdir(); write_jsonl(dest / 'cases.jsonl', cases); write_json(dest / 'criteria.json', criteria)
    write_json(dest / 'sources.json', {'sanctions': {'IND': {**source, 'symbol': 'S/PV.9214', 'source_date': '2022-12-09', 'institutional_capacity': 'national statement after explicit switch from procedural chair; closing chair switch excluded'}}})
    write_json(dest / 'source-facts.json', {'facts': FACTS, 'words': len(FACTS.split()), 'author': 'Same root assistant; complete primary speech hand-read, factual summary only, no independent teacher transcript.'})
    write_json(dest / 'manual-evaluation-expectations.json', {'frozen_before_calls': True, 'common_criteria_unchanged': True, 'states': expectations,
               'source_audit': 'All source compounds present: role, provisional sanctions, trade/redress, humanitarian timeliness, due-diligence exploitation claims, both requested mechanisms/absence in final text, anti-mainstreaming, review/feedback hope. No vote inferred from chair capacity.'})
    shutil.copy2(old / 'presentation-criteria.json', dest / 'presentation-criteria.json')
    write_json(dest / 'provenance.json', {'primary_acquisition_sha256': sha256(raw / 'acquisition.json'), 'selected_source_sha256': sha256(raw / 'statements.json'),
               'previous_common_criteria_sha256': sha256(old / 'criteria.json'), 'previous_checkpoint_sha256': sha256(ROOT / 'reports/paired-application-checkpoint-20261007-v1.json'),
               'facts_are_model_generated': False, 'training_targets_supplied': False,
               'scope': 'Application transfer to different country/source from two French fitting states. Indian source historically development-exposed and possibly pretrained; not sealed or strong OOD. Checked factual inputs isolate application from extractor. Same assistant curator/grader, independent review pending.'})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in dest.iterdir()},
               'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 3, 'source_scope': 'Three frozen Indian proposal-state application controls on identical hand-checked facts; no new optimization or source-extractor claim.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(dest / 'manifest.json'),
               'scope': 'Complete India national speech/boundaries, all factual points, three notes, six questions/common criteria and prospective state expectations hand-read before calls; no preferred answer supplied. Same assistant, independent review pending.'})
    write_json(ROOT / 'configs/posttraining/qwen35-country-application-transfer-base-20261007-v1.json', cfg)
    adapter = ROOT / 'runs/aurora-paired-application-fit-20261007-v1/adapter'
    cfg.update(adapter=str(adapter.relative_to(ROOT)), adapter_sha256=sha256(adapter / 'adapter_model.safetensors'), adapter_config_sha256=sha256(adapter / 'adapter_config.json'))
    write_json(ROOT / 'configs/posttraining/qwen35-country-application-transfer-adapter-20261007-v1.json', cfg)
    print(json.dumps({'cases': 3, 'factual_words': len(FACTS.split()), 'input_tokens': [len(c['input_ids']) for c in cases], 'new_steps': 0}))


if __name__ == '__main__': main()
