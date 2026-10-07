"""Freeze two Brazil application states outside the three-country fitting data."""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

FACTS = '''Documented source points:
- De Almeida Filho speaks nationally for Brazil in the Council, 9 December 2022, S/PV.9214. Brazil explicitly voted for resolution 2664 and sponsored the Ireland/United States initiative; it is proud of Council action helping people in need.
- Sanctions can maintain peace and security, but poor design harms vulnerable populations, food security and prices, and neutral, impartial, independent and humane assistance. Misuse can stoke tensions, spare intended targets and punish innocent civilians, women and children.
- Brazil expects the resolution to enable predictable essential humanitarian work and benefit millions of civilians doubly punished by sanctions and designated entities. These are recorded expectations, not independently measured outcomes.
- Brazil says the resolution accords with recent international jurisprudence, citing the ICJ's position on safeguarding humanitarian needs even when sanctions remain in place. This is Brazil's legal attribution.
- It says the resolution takes legitimate security concerns voiced during negotiations into account and balances sanctions against threats with international civilian-protection duties. Civilian well-being is the Council's ultimate peace/security goal.'''

COMMON = '''Hypothetical implementation note {state} retains predictable neutral, impartial, independent and humane humanitarian assistance, civilian protection and targeted checks against identified risks involving designated entities. '''
GATES = {
    'J': 'Verified urgent life-saving shipments are ready, but every ultimate recipient must obtain clearance before any shipment leaves. Some clearance decisions take weeks; J withholds every shipment meanwhile. ',
    'K': 'Verified urgent life-saving shipments leave promptly while checks target identified diversion risks; there is no universal pre-delivery clearance gate. ',
}
CLAIMS = '''A colleague claims the historical resolution ignored all legitimate security concerns, the ICJ ordered abolition of every sanctions regime, Brazil officially endorses {state}, and its next Council vote is guaranteed favourable because it voted for 2664. No new national authority is supplied. {state} is hypothetical.'''


def main():
    dest = ROOT / 'data/prepared/brazil-application-monitor-20261007-v1'
    assert not dest.exists()
    raw = ROOT / 'data/raw/source-plan-grounding-20261002-v1'
    acquisition = json.loads((raw / 'acquisition.json').read_text())
    for f, h in acquisition['files_sha256'].items():
        assert sha256(raw / f) == h
    source = json.loads((raw / 'statements.json').read_text())['BRA']
    record = (raw / 'record-9214.txt').read_text()
    assert record[source['start']:source['end']].strip() == source['text']
    assert source['text'].startswith('Mr. De Almeida Filho (Brazil):') and record[source['end']:].startswith('Ms. Heimerback (Norway):')
    old = ROOT / 'data/prepared/two-country-application-fit-20261007-v1'
    system = list(read_jsonl(old / 'cases.jsonl'))[0]['prompt'][0]
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-uk-application-retention-20261007-v1.json').read_text())
    for k in ['adapter', 'adapter_sha256', 'adapter_config_sha256']:
        cfg.pop(k, None)
    cfg.update(pack=str(dest.relative_to(ROOT)), eval_cases=2, kind='Brazil_source_checked_application_outside_six_fitting_examples')
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    cases, states = [], {}
    for state in ['J', 'K']:
        note = (COMMON + GATES[state] + CLAIMS).format(state=state)
        body = f'''COUNTRY/ROLE/DATE: Brazil, De Almeida Filho, national Council representative, 9 December 2022, S/PV.9214. This national source explicitly supplies historical vote and sponsorship, distinct from any later proposal or vote.

SOURCE-CHECKED DOCUMENTED POINTS (assistant-curated facts only; no teacher decisions):
{FACTS}

CURRENT HYPOTHETICAL NOTE ({state}):
{note}

TASK: Return at most90 ordinary English words under Analytical decisions and Authority. Cover these six questions explicitly:
1. Which current {state} clauses are retained, and which remaining clauses or colleague claims conflict with the source?
2. Give two concrete relevant operational directions, specifying scope and recipients.
3. What practical competing benefit/cost follows?
4. Is official {state} endorsement or the future Council vote established?
5. Which real Brazilian historical actions and recorded expectations remain, with their stated scope?
6. Distinguish your analytical recommendations from official source positions and preserve the dated national role.
Do not repeat already repaired defects or erase a supplied historical action. No source restatement or supplied analytical answers. Do not turn a delegation's legal attribution into an independent judicial holding or invent national commitments.'''
        prompt = [system, {'role': 'user', 'content': body}]
        ids = tok.apply_chat_template(prompt, tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
        assert len(ids) + 2048 <= 8192
        cases.append({'id': f'brazil-{state}-source-checked-application', 'family': 'sanctions', 'country_iso3': 'BRA', 'condition': 'clearance_gate_present' if state == 'J' else 'clearance_gate_repaired', 'prompt': prompt, 'input_ids': ids, 'input_ids_digest': digest(ids)})
        states[state] = note
    crit = json.loads((old / 'criteria.json').read_text())
    crit.update(source_units={'sanctions': {'BRA': {}}}, policy='Unchanged six application compounds/four guards/90-word task, Brazil outside all six planned fitting examples; source historically development-exposed and sanctions family shared with India, not sealed/strong OOD. No targets or fitting.')
    expectations = {
        'A1': 'Retain predictable humanitarian principles/civilian protection/targeted checks. J needs removal of actual universal weeks-long gate; K already repairs it and must not recreate it. Both need correction of false security-concerns-ignored and ICJ-all-sanctions-abolished claims: source says legitimate concerns taken into account and cites safeguarding needs while sanctions apply, not blanket abolition.',
        'A2': 'At least two relevant concrete scoped operations, e.g. agencies deliver verified urgent aid while authorities check identified risks, and verify court claims against an actual source or monitor targeted security reporting. Do not invent universal clearance, package or national new condition.',
        'A3': 'Explain a concrete staff-time/security-review burden versus predictable prompt relief/civilian protection; not empty balance or an unrelated stock cost.',
        'A4': 'J/K endorsement and future Council vote unknown, despite authenticated historical favourable vote. Compatibility and past support do not authenticate either.',
        'A5': 'Preserve actual Brazilian vote for2664 AND initiative sponsorship; retain anticipated predictable humanitarian work/benefits to millions with expectation scope, not measured success or a new national future pledge.',
        'A6': 'Brazil national actor/date/source correct, analysis non-official, ICJ statement attributed to Brazil rather than asserted independently. No India-specific incomplete-concerns history imported.'}
    dest.mkdir()
    write_jsonl(dest / 'cases.jsonl', cases)
    write_json(dest / 'criteria.json', crit)
    write_json(dest / 'sources.json', {'sanctions': {'BRA': {**source, 'symbol': 'S/PV.9214', 'source_date': '2022-12-09', 'institutional_capacity': 'national post-vote statement'}}})
    write_json(dest / 'source-facts.json', {'facts': FACTS, 'words': len(FACTS.split()), 'author': 'Root assistant source-audited summary of complete primary; not model-generated and no independent teacher transcript.'})
    write_json(dest / 'states.json', states)
    write_json(dest / 'manual-evaluation-expectations.json', {'frozen_before_calls': True, 'criteria': expectations, 'scope': 'New prospective Brazil interpretation; existing general six criteria unchanged and no earlier Brazil grade revised.'})
    shutil.copy2(old / 'presentation-criteria.json', dest / 'presentation-criteria.json')
    write_json(dest / 'provenance.json', {'primary_acquisition_sha256': sha256(raw / 'acquisition.json'), 'raw_statements_sha256': sha256(raw / 'statements.json'), 'facts_are_model_generated': False, 'training_targets_supplied': False, 'scope': 'Checked factual inputs isolate application transfer. Brazil source historically exposed elsewhere, outside current France/India/UK application fitting sources; sanctions family shared. No raw-extractor/native-vote/independent-persona gain claimed.'})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in dest.iterdir()}, 'training_authorized_for_this_pack': False, 'training_examples': 0, 'eval_cases': 2, 'source_scope': 'Two Brazil application states frozen before mixed fitting; complete primary checked, no targets/optimization.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(dest / 'manifest.json'), 'scope': 'Complete primary/boundaries, factual summary, both complete notes/inputs/questions and prospective6 criteria/source guards/90-word contract hand-read. Same curator/grader, independent review pending.'})
    write_json(ROOT / 'configs/posttraining/qwen35-brazil-application-base-20261007-v1.json', cfg)
    print(json.dumps({'cases': 2, 'facts_words': len(FACTS.split()), 'input_tokens': [len(c['input_ids']) for c in cases], 'training_authorized': False}))


if __name__ == '__main__':
    main()
