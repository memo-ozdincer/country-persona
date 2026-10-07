"""One audited Indian source target, unchanged French targets and frozen Brazil monitor."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, write_jsonl, write_json, sha256, digest

INDIA_TARGET = '''Documented source points:
- India speaks nationally in the Council, 9 December 2022, S/PV.9214; procedural presidency is separate. This national span supplies no vote label.
- Article 41 sanctions are provisional, not permanent or ends in themselves; intended impact must not worsen population suffering.
- Legitimate State and regional-partner trade and economic activity matter; unintended and humanitarian consequences require effective redress.
- India engaged constructively in negotiating 2664. The resolution supports timely humanitarian assistance and basic needs, predictable safeguards for agencies.
- India urges due diligence and extreme caution under 1267, alleging proscribed groups thrive under State hospitality, exploit relief and use humanitarian and civil-society fronts to evade sanctions, raise funds and recruit fighters. No per-group case list is supplied.
- Exemptions must not expand terror regionally or beyond, or mainstream terror entities politically.
- India sought proactive 1267 Monitoring Team involvement AND robust reporting standards and mechanisms; specific concerns were not fully addressed in the final text.
- It hopes future implementation review and Team feedback correct the shortcoming; no completed correction or future-vote commitment is established.'''

BRAZIL_UNITS = {
    'S1': 'Dated national DeAlmeidaFilho/Brazil Council role; thanks Ireland/US initiative, actual sponsorship AND favourable2664 vote. No Indian or procedural-chair stance pooled.',
    'S2': 'Council sanctions history since1966/mistakes; ill-devised measures harm vulnerable populations, foodsecurity/inflation and neutral/impartial/independent/humane assistance.',
    'S3': 'Sanctions useful for peace/security BUT misuse stokes tensions and can spare intended targets while punishing innocentcivilians/women/children inconflict.',
    'S4': 'High time improve Council coercivepower against peace/security threats; Brazil proud Councilmember as it acts to help thoseinneed.',
    'S5': '2664 enables predictable essentialhumanitarian operations, benefits millions ofcivilians doublypunished by sanctions AND designatedentities; not a new fundingpledge.',
    'S6': 'Brazil cites recent internationaljurisprudence/ICJ humanitarian-needs safeguard even under sanctions; source supplies no specific case/date, remains Brazilian legalattribution.',
    'S7': 'Resolution accounts for legitimate security concerns voiced by MemberStates duringnegotiations; no invented Indian proactiveTeam or reporting redline.',
    'S8': 'Finebalance: sanctions toprevent/combat threats AND internationalcivilian-protection duty; civilian wellbeing ultimateCouncilgoal inpeace/securitymandate, not unconditional futurevote guarantee.',
}


def main():
    dest = ROOT / 'data/prepared/three-source-extraction-20261007-v1'; assert not dest.exists()
    old = ROOT / 'data/prepared/source-status-fit-20261007-v2'
    india = ROOT / 'data/prepared/india-actual-extraction-20261007-v1'
    previous = ROOT / 'runs/aurora-india-actual-extraction-source64-20261007-v1'
    i = json.loads((previous / 'inspection.json').read_text()); assert i['all_outputs_read_complete'] and i['transcript_sha256'] == sha256(previous / 'transcript.jsonl')
    cases = copy.deepcopy(list(read_jsonl(old / 'cases.jsonl'))[:2] + list(read_jsonl(india / 'cases.jsonl')))
    raw = ROOT / 'data/raw/source-plan-grounding-20261002-v1'; s = json.loads((raw / 'statements.json').read_text())['BRA']; record = (raw / 'record-9214.txt').read_text()
    assert record[s['start']:s['end']].strip() == s['text'] and s['text'].startswith('Mr. De Almeida Filho (Brazil):')
    assert record[s['end']:].startswith('Ms. Heimerback (Norway):')
    body = '''PUBLIC SOURCE METADATA: S/PV.9214, 9 December 2022. De Almeida Filho speaks nationally for Brazil, not as procedural chair. The bounded source excludes prior UK and following Norway speeches. Treat geopolitical and Court interpretations as Brazil's recorded claims, not independent findings.

QUESTIONS ONLY, NO ANSWERS PROVIDED:
1. Who speaks in which dated institutional capacity; whom is thanked; what actual sponsorship and vote are stated?
2. What sanctions history and mistaken effects on vulnerable people and humanitarian work are described?
3. What useful security purpose and misuse or unequal effects are contrasted?
4. What change to Council coercive power and membership assessment are stated?
5. What provider conditions and civilian benefits follow from2664; what two sources of harm are mentioned?
6. What international jurisprudence or Court claim is attributed; what specific case/date is supplied?
7. What negotiating security concerns does the resolution take into account?
8. What balance, international duty and ultimate Council goal are stated; what future vote commitment is recorded?

COMPLETE NATIONAL STATEMENT:
''' + s['text'] + '''

TASK: Give at most210 ordinary English words of Documented source points, covering every question and qualification. No application scenario is supplied. Preserve recorded actors, dates, conditional versus established claims, scope and actual commitments. Attribute assertions to Brazil, not independent findings. No slash-list or fused-word shortcut, no invented amount, Court case/date or future vote, no source repetition.'''
    cases.append({'id': 'brazil-sanctions-complete-source-monitor', 'family': 'sanctions', 'country_iso3': 'BRA', 'condition': 'historically_exposed_source_outside_reader_fit', 'prompt': [cases[0]['prompt'][0], {'role': 'user', 'content': body}]})
    targets = copy.deepcopy(json.loads((old / 'preferred-targets.json').read_text())['targets']); targets[cases[2]['id']] = INDIA_TARGET
    assert len(targets) == 3 and len(INDIA_TARGET.split()) <= 210 and '/' not in INDIA_TARGET.replace('S/PV.9214', '')
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-india-actual-extraction-base-20261007-v1.json').read_text()); cfg.update(pack=str(dest.relative_to(ROOT)), eval_cases=4, kind='three_primary_sources_one_newIndia_target_Brazil_monitor')
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    for c in cases:
        ids = tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
        if 'input_ids' in c: assert c['input_ids'] == ids
        assert len(ids) + 2048 <= 8192; c.update(input_ids=ids, input_ids_digest=digest(ids))
    criteria = copy.deepcopy(json.loads((old / 'criteria.json').read_text())); assert not criteria['common_units']
    indi = json.loads((india / 'criteria.json').read_text()); criteria['source_units']['sanctions'] = {'IND': indi['source_units']['sanctions']['IND'], 'BRA': BRAZIL_UNITS}
    criteria['policy'] = 'Three fitting sources (two unchangedFrench, one newIndian), separateBrazil sourceonly monitor. Original source8 compounds/210word/one-documentary-section contract; Brazilian8 source compounds prospectively primary-audited beforecalls. No full14 application substitute.'
    sources = copy.deepcopy(json.loads((old / 'sources.json').read_text())); sources['sanctions'] = {'IND': json.loads((india / 'sources.json').read_text())['sanctions']['IND'], 'BRA': {**s, 'symbol': 'S/PV.9214', 'source_date': '2022-12-09', 'institutional_capacity': 'National Brazil, notchair; actualsponsorship/favourablevote supplied'}}
    dest.mkdir(); write_jsonl(dest / 'cases.jsonl', cases); write_json(dest / 'criteria.json', criteria); write_json(dest / 'sources.json', sources)
    write_json(dest / 'preferred-targets.json', {'targets': targets, 'words': [len(x.split()) for x in targets.values()], 'author': 'Same root assistant; unchangedFrench207/210 texts; newIndia source-only target hand-read, no independentteacher/API transcript.'})
    shutil.copy2(india / 'presentation-criteria.json', dest / 'presentation-criteria.json')
    write_json(dest / 'manual-target-audit.json', {'all_targets_hand_read_complete': True, 'original_two_French_targets_and_inputs_unchanged': True, 'new_India_all_source8_compounds_and_guards': True,
               'critical_repairs': 'Explicitnotends/intendedimpact/redress/timeliness/basicneeds; resolution providescarveout, India negotiated. Genericproscribedgroup allegations notprovenindividualDaesh/AlQaida caseassertions. No futurevote or accomplishedreform.', 'independent_review_complete': False})
    write_json(dest / 'provenance.json', {'previous_French_fit_manifest_sha256': sha256(old / 'manifest.json'), 'India_test_manifest_sha256': sha256(india / 'manifest.json'), 'previous_inspection_sha256': sha256(previous / 'inspection.json'),
               'primary_acquisition_sha256': sha256(raw / 'acquisition.json'), 'scope': 'Proposedfresh3target96update fit,32presentations each; oldtwoFrench207/210texts unchanged, addsoneIndia source, total64to96. Brazil samepolicy/date but differentcountry/span, historicallyexposed/notinreaderfit; frozenbeforecalls/fit. Source/data/dose/target clarity change together, no purediversity/strongOOD/persona/multiagent gain.'})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name: sha256(p) for p in dest.iterdir()}, 'training_authorized_for_this_pack': False,
               'training_examples': 3, 'eval_cases': 4, 'source_scope': 'Complete datedprimary sources, three preferred source-only targets and Brazil monitor frozenbeforecalls. No fit beforematchingbase andoldBrazil inspection.'})
    write_json(dest / 'manual-inspection.json', {'all_selected_texts_read_complete': True, 'manifest_sha256': sha256(dest / 'manifest.json'),
               'scope': 'Every fullselectedprimary source, roleboundary, four inputs/questions, allsourcecriteria, originalFrench207/210 andnewIndia target fullyread. Brazilprivate source feasibility andeachsourcecompound checked, no teacheranswer ininput. Sameauthor/grader.'})
    write_json(ROOT / 'configs/posttraining/qwen35-three-source-extraction-base-20261007-v1.json', cfg)
    print(json.dumps({'cases': 4, 'target_words': [len(x.split()) for x in targets.values()], 'input_tokens': [len(c['input_ids']) for c in cases], 'fit_authorized': False}))


if __name__ == '__main__': main()
