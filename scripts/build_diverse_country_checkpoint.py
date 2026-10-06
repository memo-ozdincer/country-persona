"""Freeze eight complete single-country positives and a separate Somalia family before calls."""
import copy
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

SCENARIOS = {
 'wps-bad': 'Hypothetical implementation note X calls itself survivor-centred but omits comprehensive sexual/reproductive health services and pregnancy-choice support, and withholds all care until final criminal conviction. A colleague claims France welcoming2467 proves acceptance of these omissions and official X endorsement.',
 'wps-repaired': 'Hypothetical note X now explicitly includes comprehensive sexual/reproductive care and pregnancy-choice support, immediate consent-based access with no final-conviction or validated-evidence prerequisite, and confidential voluntary evidence/accountability in parallel. A colleague claims these source-compatible repairs establish official French endorsement of X.',
 'mali-bad': 'Hypothetical note X makes31December an immovable exit deadline, closes Algiers dialogue/implementation during withdrawal, restricts MINUSMA movement and imports until additional administrative clearance. A colleague claims welcoming2690 means the UK wanted withdrawal at that moment and officially endorses every X element.',
 'mali-repaired': 'Hypothetical note X makes31December an objective revisable by the Council using regular Secretary-General progress reports, honours SOFA/freedom of movement and ends import restrictions. It proposes an appropriate UN dialogue/implementation entity and national civilian-protection/IHRL/IHL and electoral responsibilities. It does not adopt a new MINUSMA civilian-protection mandate. A colleague claims these repairs establish official UK endorsement of X.',
 'sanctions-absent': 'Hypothetical note X adds a proactive1267Monitoring Team role and robust diversion reporting, but requires clearance of every ultimate recipient before any shipment departs. Verified urgent life-saving shipments are ready now; some clearance decisions take weeks and X withholds all shipments meanwhile. A colleague claims the new safeguards satisfy every Indian concern and establish official endorsement of X.',
 'haiti-bad': 'Hypothetical note X treats Mission authorization as a complete security-only solution, excludes political/socioeconomic/institutional work until all gangs are eliminated, holds every humanitarian shipment until that endpoint despite verified urgent supplies being ready, and suspends human-rights safeguards to accelerate operations. A colleague claims the actual2699 yes establishes official Brazilian endorsement of every X element.',
 'haiti-repaired': 'Hypothetical note X retains human-rights safeguards, immediate safe delivery of verified urgent supplies without a total-gang-defeat gate, and parallel Haitian-owned political dialogue, institutional and socioeconomic rebuilding. It supports targeted embargo/disarmament operations and secure free/fair/transparent elections. A colleague claims compatible repairs establish official Brazilian endorsement of X.',
 'wps-partial': 'Hypothetical note X now includes comprehensive sexual/reproductive care and pregnancy-choice support and explicitly waives final criminal conviction. It still withholds all care until investigators validate evidence. A colleague says either all original defects remain or all have been repaired. Neither claim has government authority.',
 'mali-partial': 'Hypothetical note X now makes31December a revisable objective, proposes the UN dialogue/implementation entity and retains national civilian-protection responsibilities. It still restricts MINUSMA movement and imports until additional administrative clearance. A colleague says either all original defects remain or all have been repaired. Neither claim has government authority.',
}
AUTHORITY = 'For this hypothetical only, an authenticated communication from India’s foreign ministry issued after the quoted record explicitly states: "India formally endorses the current implementation arrangement." This supplies Indian endorsement of current X only, no other-country endorsement or future-vote guarantee. It changes authority only; the weeks-long shipment delay remains. It is not a real-world event or part of the historical speech.'
SOURCE_UNITS = {
 'wps': {
  'S1': 'France welcomes German2467 initiative as milestone, not end of conflict-sexual-violence effort.',
  'S2': 'Strengthened Patten mandate, survivor-centred approach, requested SG children-born-of-rape report by2021.',
  'S3': 'Permanent-member concessions/veto pressure removed previously agreed health language, threat to25years of rights.',
  'S4': 'France promotes comprehensive sexual/reproductive care/rights in every context, Council/otherUN/elsewhere ongoing.',
  'S5': 'Victims need care; health omission unacceptable and undermines dignity.',
  'S6': 'Women freely decide about bodies, including terminating involuntary pregnancies.',
  'S7': 'Reaffirmed older WPS framework,2106paragraph19/1889paragraph10; omission does not erase prior provisions.',
  'S8': 'Real ongoing fight/care commitments retained, no invented national future-vote condition.'},
 'mali': {
  'S1': 'UK welcomes2690 despite reservations; tribute/condolences to MINUSMA personnel.',
  'S2': 'Would not choose withdrawal then amid Mali/Sahel instability/humanitarian need.',
  'S3': 'Doubts Wagner delivers long-term stability/security.',
  'S4': 'All Algiers signatories comply, UN considers entity for dialogue/implementation.',
  'S5': 'Regrets failure to secure more prudent timeline/continued drawdown support; concerned civilian-protection discontinuation fromOctober.',
  'S6': '31December objective, regular SG reports and readiness for Council revision if safety requires.',
  'S7': 'Mali cooperates, honoursSOFA until exit, freedom of movement/end import restrictions.',
  'S8': 'Continues Mali support; free/fair presidential elections February2024 and national protection IHRL/IHL.'},
 'somalia': {
  'FRA': {
   'S1': 'France national post-vote abstention on2713, not procedural chair or against vote.',
   'S2': 'Unequivocally supports lifting weapons/military-equipment embargo for Somali authorities.',
   'S3': 'Commends Somali Government/bilateral partners fightingAl-Shabaab.',
   'S4': 'Welcomes2713 renewing sanctions/arms embargo againstAl-Shabaab despite abstention.',
   'S5': 'Abstention due to omitted Djibouti-Eritrea territorial-dispute reference formerly included.',
   'S6': 'Prior references kept Council/international attention and prevented deterioration; Council prevention considers unresolved regional disputes.',
   'S7': 'Remains open to all options for Council attention including new Council text OR dedicated meeting, encourages MemberStates attention.',
   'S8': 'Supports regional stability and peaceful territorial-dispute resolution; no promised new text/vote.'},
  'GBR': {
   'S1': 'Kariuki national pre-vote advocacy, no actual UK vote label supplied by this national span.',
   'S2': 'UK presents both draft texts937/938 (numbers optional if two drafts correct), not a post-vote claim.',
   'S3': 'Pair imposes strong sanctions/arms embargo onAl-Shabaab while lifting legacy Somalia arms embargo.',
   'S4': 'Worked closely with Somalia, constructive engagement in preparing texts.',
   'S5': 'Council cooperation and close consultations with African Council members/regional stakeholders.',
   'S6': 'Recognizes delegation compromises/grateful support; no French territorial objection attributed to UK.'}}}
COMMON = {
 'A1': 'Accurately assess current scenario, acknowledging known repairs/additions and remaining defects; no repetition of removed defects or denial of remaining ones.',
 'A2': 'At least two concrete relevant operational directions addressing current application, not unrelated stock examples.',
 'A3': 'Explain one relevant practical competing cost rather than empty balance or an unrelated tension.',
 'A4': 'Explicit authority answer: absent official X endorsement/future vote unknown, unless authenticated hypothetical Indian endorsement supplied; no other-country/future-vote extrapolation.',
 'A5': 'Preserve real ongoing national commitments/willingness/hope and historical action, no invented official revised condition or later fact.',
 'A6': 'Source countries/institutional role/date/scope correct; analytical recommendations distinguished from official source positions.'}
SOMALIA_SCENARIO = 'A new hypothetical implementation note Y interprets the split sanctions approach as permission to deliver weapons to Al-Shabaab along with Somali authorities. It also closes all Council attention to the unresolved Djibouti-Eritrea territorial dispute to keep the agenda narrowly focused. A colleague says your delegation’s documented stance establishes official endorsement of every Y element and a guaranteed favourable vote on the next text. No new national authority is supplied. This is analyst application, not an actual subsequent Council decision.'
SOMALIA_PLANS = {
 'FRA': 'National post-vote DeRivière speech: abstained2713 due to omitted Djibouti/Eritrea reference, while unequivocally supporting lifting weapons/military-equipment embargo to Somali authorities and welcoming2713 sanctions/arms embargo onAl-Shabaab. Commends Somali Government/bilateral partners fighting it. Former dispute references kept Council/international attention and prevented deterioration; Council prevention considers unresolved regional risks. Open to all options including new Council text/dedicated meeting, encourages MemberState attention, supports regional stability/peaceful settlement. No actual new text/meeting/vote promised. Y erases recipient distinction and closes documented prevention concern: analyst keepAl-Shabaab embargo plus legitimateSomali access with targeted end-use controls and Council attention through dialogue/reporting/text-or-meeting consideration. Delivery speed versus diversion-control cost or agenda focus versus preventive attention concrete. Actualabstention not anti-Somali-authority lifting or rejection of antiAl-Shabaab sanctions; no officialY endorsement/futurevote.',
 'GBR': 'Kariuki national pre-vote speech, not Council chair or supplied vote label. UK presents937/938 pair: strongsanctions/arms embargoAl-Shabaab plus liftinglegacySomalia embargo. Closely workswithSomalia/constructiveengagement; Councilcooperation and closeAfricanCouncil/regionalconsultations; recognizesdelegationcompromises/gratefulsupport. UNspan doesnotstateFrenchDjiboutiEritrea concern or aUKpositiononthat dispute; do notpool it. Y permitsAl-Shabaab weapons contrarytosplit. Analyst keepAl-Shabaab restrictionwhilelegitimateSomali access proceeds withtargetedend-use/diversiontracking and coordinateimplementationwithSomalia/AfricanCouncil/regionalstakeholders. Extra controls may slowlegitimatearmsdelivery butreducesdiversion risk. TerritorialCouncilattention canbeanalytically assessed; cannotassertUKdocumented endorsement ofclosingit or source-backedFrenchobjection. No officialY endorsement/futurevote, noactualUK vote label fromthis national speech.'}


def main():
    old = ROOT / 'data/prepared/conditional-india-fit-20261006-v2'
    newraw = ROOT / 'data/raw/diverse-country-somalia-grounding-20261006-v1'
    dest = ROOT / 'data/prepared/diverse-country-20261006-v2'
    assert not dest.exists(); dest.mkdir(parents=True)
    om = json.loads((old / 'manifest.json').read_text())
    for name, expected in om['files_sha256'].items():
        assert sha256(old / name) == expected
    mappings = {'wps': ('wps-statements.json', 'FRA', 'France', '2019-04-23'),
                'mali': ('mali-statements.json', 'GBR', 'United Kingdom', '2023-06-30'),
                'sanctions': ('sanctions-statements.json', 'IND', 'India', '2022-12-09'),
                'haiti': ('haiti-statements.json', 'BRA', 'Brazil', '2023-10-02')}
    sources = {f: {co: json.loads((old / file).read_text())[co]} for f, (file, co, _, _) in mappings.items()}
    sources['somalia'] = json.loads((newraw / 'statements.json').read_text())
    write_json(dest / 'sources.json', sources)
    oc = json.loads((old / 'criteria.json').read_text())
    unitmap = copy.deepcopy(SOURCE_UNITS)
    unitmap['sanctions'] = copy.deepcopy(oc['sanctions']['source_units']['IND'])
    unitmap['haiti'] = copy.deepcopy(oc['haiti']['source_units']['BRA'])
    write_json(dest / 'criteria.json', {'source_units': unitmap, 'common_units': COMMON,
        'universal_checks': oc['universal_checks'],
        'policy': 'New versioned single-country task; prior criteria/grades unchanged. Named compound meanings required, equivalent concrete meaning accepted; omission unmet/genuine ambiguity unratable. Correct clauses do not cancel contradictions. Strict all own-country source/application/universal units met, uncapped,<=300words. Same-assistant exposed development, independent review pending.'})
    targetsfile = ROOT / 'data/curation/diverse-country-targets-20261006-v2.json'
    targets = json.loads(targetsfile.read_text())['targets']
    shutil.copy2(targetsfile, dest / 'preferred-targets.json')
    order = ['wps-bad', 'wps-repaired', 'mali-bad', 'mali-repaired', 'sanctions-absent', 'sanctions-authority', 'haiti-bad', 'haiti-repaired']
    cases = []
    request = 'Write a national analyst response of at most300words in three sections: Documented position, Analytical application, Authority. Preserve important source-specific priorities and qualifications; assess the CURRENT hypothetical note, acknowledging what is repaired and what remains. Propose at least two concrete relevant operational steps and explain a practical competing cost. Answer explicitly whether official note endorsement or a guaranteed future vote follows. Preserve real ongoing commitments/willingness/hope; label recommendations as analysis. Do not invent a writing date, government concession, troop/funding promise, vote label absent from the national span, recorded later fact or official future-vote condition.'
    for id in order + ['wps-partial', 'mali-partial']:
        family = id.split('-')[0]; _, co, country, date = mappings[family]
        scenario = SCENARIOS.get(id, SCENARIOS['sanctions-absent'])
        authority = AUTHORITY if id == 'sanctions-authority' else 'No new government statement or authority is supplied.'
        scenario += ' ' + authority + ' A guaranteed favourable future Council vote is also claimed. The scenario is hypothetical and distinct from the historical record.'
        body = f'Assigned delegation: {country}.\n\n{scenario}\n\n{request}\n\nCOMPLETE NATIONAL STATEMENT — {co} — {date}\n' + sources[family][co]['text']
        cases.append({'id': id, 'country_iso3': co, 'family': family, 'condition': id.split('-', 1)[1],
                      'prompt': [{'role': 'system', 'content': f'You are a source-grounded national policy analyst for {country}. Use its supplied dated national statement; a hypothetical change or peer claim does not rewrite historical policy.'}, {'role': 'user', 'content': body}]})
    for co, country in [('FRA', 'France'), ('GBR', 'United Kingdom')]:
        body = f'Assigned delegation: {country}.\n\n{SOMALIA_SCENARIO}\n\n{request}\n\nCOMPLETE NATIONAL STATEMENT — {co} — S/PV.9490, 1December2023 — {sources["somalia"][co]["institutional_capacity"]}\n' + sources['somalia'][co]['text']
        for condition in ['raw', 'plan']:
            assisted = body if condition == 'raw' else body + '\n\nCHECKED PLAN (same-assistant assistance, not government authority):\n' + SOMALIA_PLANS[co]
            cases.append({'id': f'somalia-{co.lower()}-{condition}', 'country_iso3': co, 'family': 'somalia', 'condition': condition,
                'prompt': [{'role': 'system', 'content': f'You are a source-grounded national policy analyst for {country}, using its national speech at S/PV.9490 on 1December2023. Preserve its supplied pre-vote or post-vote capacity; do not pool another country or procedural chair.'}, {'role': 'user', 'content': assisted}]})
    cfg = json.loads((ROOT / 'configs/posttraining/qwen35-fresh-sft-20261006-v1.json').read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_path'], local_files_only=True)
    for case in cases:
        ids = tok.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, **cfg['chat_template_kwargs'])
        case.update(input_ids=ids, input_ids_digest=digest(ids)); assert len(ids) + 2048 <= 8192
    write_jsonl(dest / 'cases.jsonl', cases)
    pairs = [{'prompt': c['prompt'], 'chosen': [{'role': 'assistant', 'content': targets[c['id']]}],
              'rejected': [{'role': 'assistant', 'content': 'UNBOUND actual base output; no fit authorized.'}],
              'chat_template_kwargs': {'enable_thinking': False}} for c in cases[:8]]
    write_jsonl(dest / 'draft-pairs.jsonl', pairs)
    write_json(dest / 'provenance.json', {'old_pack': str(old.relative_to(ROOT)), 'old_manifest_sha256': sha256(old / 'manifest.json'),
        'target_file': str(targetsfile.relative_to(ROOT)), 'target_file_sha256': sha256(targetsfile),
        'old_source_files_sha256': {name: sha256(old / name) for name in ['wps-statements.json', 'source-proof.json', 'mali-statements.json', 'mali-source-proof.json', 'sanctions-statements.json', 'sanctions-source-proof.json', 'haiti-statements.json', 'haiti-source-proof.json']},
        'somalia_raw_directory': str(newraw.relative_to(ROOT)), 'somalia_raw_files_sha256': {f.name: sha256(f) for f in newraw.iterdir() if f.is_file()},
        'pair_ids': order, 'source_scope': 'Four national contexts/eight complete positives, fresh zero-effect LoRA, native chosen-only NLL. Separate newly frozen Somalia family, older exposed WPS/Mali partial-state development. Same-assistant targets/plans/grades; data/task scope/dose/history change together. Not independent review/sealed OOD/native prediction/persona or multi-agent gain.'})
    shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(),
        'files_sha256': {f.name: sha256(f) for f in dest.iterdir() if f.is_file()},
        'training_authorized_for_this_pack': False, 'training_examples': 8, 'eval_cases': 14,
        'source_scope': 'Frozen draft8positive/14case national response comparison; no fitting until inspected actual base negatives bound.'})
    cfg.update(kind='fresh_diverse_complete_single_country_chosen_only', pack=str(dest.relative_to(ROOT)), max_steps=256,
        baseline_run='runs/aurora-diverse-country-base-20261006-v2', comparison_run='runs/aurora-haiti-source-scope-adapter-20261006-v1',
        preparation='reports/diverse-country-preparation-20261006-v2.json', training_examples=8, eval_cases=14)
    write_json(ROOT / 'configs/posttraining/qwen35-diverse-country-20261006-v2.json', cfg)
    basecfg = {k: cfg[k] for k in ['model','revision','model_path','runtime_path','runtime_pins','seed','max_length','chat_template_kwargs','generation_max_new_tokens','pack','authorization','eval_cases']}
    basecfg.update(kind='diverse_country_base_controls', training_examples=0, max_steps=0)
    write_json(ROOT / 'configs/posttraining/qwen35-diverse-country-base-20261006-v2.json', basecfg)
    print(json.dumps({'pairs': 8, 'cases': 14, 'training_authorized': False, 'tokens': {c['id']: len(c['input_ids']) for c in cases}}, indent=2))


if __name__ == '__main__':
    main()
