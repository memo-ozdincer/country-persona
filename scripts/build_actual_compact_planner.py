"""Freeze one new national source, a checked compact control and a questions-only planner call."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl

SCENARIO = '''Hypothetical implementation note Z keeps Article 51 self-defence, military assistance and a boundary limiting strikes to military targets directly involved in attacks, with targeted dual-use export checks. These are retained provisions. However, Z treats reported possible Iranian ballistic-missile transfers as confirmed on 25 July 2024, claims France already adopted a specified punitive package regardless of verification, suspends all French aid until every export check is complete, and accepts territorial changes by force as the goal of negotiations. A colleague claims the speech officially endorses every Z clause and guarantees France's next Council vote. No new national authority is supplied; Z is hypothetical.'''
UNITS = {
    'S1': 'Dated national France/deRiviere substantive Council role; thanksEbo; criticizes Russian multilateral-order meeting9686 and seventeenth arms-delivery meeting as inconsistent with Charter sovereignty/Russia-alone illegal unprovoked aggression, no Ukraine threat, majorityUNGA condemnation. No vote label in selected span.',
    'S2': 'France asserts aggression weakens nonproliferation/collective security; NorthKorean weapons/ammunition and ballistic missile use violate Council resolutions; Russia-Pyongyang cooperation COULD advance illicit programmes and trivializes nuclear threats.',
    'S3': 'Iran armed drones/2231(2015) versus reports of POSSIBLE Iranian ballistic transfers; IFCONFIRMED real resolute coordinated response including further far-reaching measures. Urges allStates refrain dual-use goods and components supporting Russian aggression; no invented specified package.',
    'S4': 'France asserts deliberate civilian/infrastructure strikes violate IHL; cites Okhmatdyt children hospital8July, not an independently verified new finding.',
    'S5': 'Article 51 Ukrainian selfdefence; France actually chose military support and equipment transfers with partners, not merely considering future support.',
    'S6': 'Military targets on Russian territory DIRECTLY involved in operations against Ukraine; not all Russian/civilian targets. Actual continued necessary French support for aslongasit takes preserved, no invented aid-suspension condition.',
    'S7': 'France says Russia alone prolongs war and can end by withdrawing troops from Ukraine; cites ICJ16March2022 request as French legal attribution, not independent adjudication or later event.',
    'S8': 'Military support defends Ukrainian sovereignty and territorial integrity and aims at conditions for negotiations/justlastingpeace; rejects peace imposed by aggression or borders changed by force.'
}
QUESTIONS = '''Questions to cover, without answers supplied:
1. Who speaks in which dated institutional capacity; whom is thanked; what prior meeting, current meeting count and explanation of the war are given?
2. What non-proliferation concerns, supplier relationships and conditional risks are asserted?
3. Which Iranian transfers are asserted, which are only possible, what response is conditional, and what export restraint is urged?
4. What civilian-protection law, incident and date are cited?
5. What legal self-defence basis and actual French assistance decision are stated?
6. Which targets are permitted, with what restriction; how long is real support to continue?
7. Who can end the war, how, and which Court/date is cited? Attribute the interpretation to the speaker.
8. What negotiation/peace goal and territorial limit are stated?
Then assess current Z's retained provisions and remaining conflicts, give two specific relevant operational recommendations, one practical competing cost, and distinguish actual recorded commitments from official Z endorsement or a future Council vote.'''
CHECKED = '''Documented source points:
- France’s national speaker de Rivière, Council 25 July 2024, thanks Ebo. France criticizes Russia's multilateral-order meeting 9686 and seventeenth arms-delivery meeting: Russia alone launched illegal unprovoked aggression, Ukraine posed no threat, majority UNGA condemned it; Charter sovereignty undermined.
- France asserts weakened non-proliferation and collective security, North Korean arms and ammunition and ballistic use violating Council resolutions; Pyongyang cooperation could advance illicit programmes, trivializing nuclear threats.
- Iran drones violate resolution 2231(2015); ballistic transfers only reported possible. If confirmed, real resolute coordinated response including further far-reaching measures; urge all States to refrain from dual-use goods and components supporting aggression. No specified package.
- France alleges deliberate civilian and infrastructure IHL violations, citing Okhmatdyt children's hospital, 8 July.
- Ukraine has Article 51 self-defence; France actually chose military support and equipment with partners.
- Russian-territory military targets directly involved in attacks, not unrestricted targets; real necessary support continues as long as needed.
- France says Russia alone prolongs war, can end by withdrawing troops from Ukraine; cites ICJ 16 March 2022 request as its legal attribution.
- Support protects sovereignty and territorial integrity, enables negotiations for just lasting peace; no aggression-imposed peace or forced borders.

Analytical decisions:
- Keep Z's self-defence, assistance, target boundary and targeted checks. Correct confirmed-transfer and punitive-package claims, universal aid halt and forced-border goal.
- Coordinate targeted dual-use checks alongside legitimate assistance; verify missile reports before proposed coordinated response.
- Verification consumes time versus immediate action; no universal aid gate. Record conditional response and ongoing support without new conditions.

Authority:
- No official all-Z endorsement or future-vote guarantee. Recommendations analytic; source assertions remain attributed to France.'''


def freeze(dest, cases, common_files, scope, tok, cfg):
    assert not dest.exists(); dest.mkdir()
    for name, value in common_files.items():
        write_json(dest / name, value)
    for c in cases:
        ids = tok.apply_chat_template(c['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
        c.update(input_ids=ids, input_ids_digest=digest(ids)); assert len(ids)+2048<=8192
    write_jsonl(dest / 'cases.jsonl', cases); shutil.copy2(__file__, dest / 'builder-code.py')
    write_json(dest / 'manifest.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'files_sha256': {p.name:sha256(p) for p in dest.iterdir()},
        'training_authorized_for_this_pack':False,'training_examples':0,'eval_cases':len(cases),'source_scope':scope})
    write_json(dest / 'manual-inspection.json', {'manifest_sha256':sha256(dest/'manifest.json'),'all_selected_texts_read_complete':True,
        'read_scope':'Full selected national speech/page13 and cover viewed; all eight source criteria, current Z, common criteria, actual-planner questions and checked compact points hand-read. Original procedural speech excluded. Recorded assertions attributed to France; no independent adjudication. No answers or checked plan supplied to planner.'})


def main():
    raw = ROOT/'data/raw/compact-planner-ukraine-grounding-20261007-v1'
    statement=json.loads((raw/'statement.json').read_text());proof=json.loads((raw/'source-proof.json').read_text())
    assert sha256(raw/'statement.json')==proof['statement_sha256'] and proof['source_hand_read_complete']
    old=ROOT/'data/prepared/compact-france-20261007-v1';criteria=json.loads((old/'criteria.json').read_text());criteria['source_units']['ukraine24']={'FRA':UNITS}
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-compact-france-base-20261007-v1.json').read_text())
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True)
    metadata='PUBLIC SOURCE METADATA: S/PV.9693, 25 July 2024. De Rivière speaks nationally for France; Russia/Nebenzia–Polyanskiy chair. This is the complete bounded substantive national speech, not the earlier procedural intervention; selected span supplies no vote label. Treat geopolitical assertions and Court interpretations as France’s recorded claims, not independently adjudicated facts.'
    planner_prompt=metadata+'\n\nCURRENT HYPOTHETICAL NOTE:\n'+SCENARIO+'\n\n'+QUESTIONS+'\n\nCOMPLETE NATIONAL STATEMENT:\n'+statement['text']+'\n\nTASK: Produce at most280 ordinary English words of complete compact points under Documented source points, Analytical decisions, Authority. Preserve actors, dates, legal and military-target scope, conditional versus established claims, real commitments and current repairs. No slash-list/fused-word shortcut. Do not reproduce the questions, source prose or instructions. Do not invent a concession, package, vote or guarantee.'
    planner_case={'id':'ukraine24-fra-actual-planner','country_iso3':'FRA','family':'ukraine24','condition':'raw_source_questions_only_compact_planning','prompt':[{'role':'system','content':'Extract and plan from the supplied dated own-national speech. Every documentary assertion remains attributed to that delegation. Recommendations are analysis. Preserve real recorded ongoing and conditional commitments.'},{'role':'user','content':planner_prompt}]}
    request=list(read_jsonl(old/'cases.jsonl'))[0]['prompt'][1]['content'].split('\n\n')[2]
    contract=list(read_jsonl(old/'cases.jsonl'))[0]['prompt'][1]['content'].split('\n\nREALIZATION CONTRACT: ',1)[1]
    writer_prompt='Assigned delegation: France.\n\n'+SCENARIO+'\n\n'+request+'\n\n'+metadata+'\n\nSOURCE-CHECKED PLAN (same assistant assistance, not government authority):\n'+CHECKED+'\n\nREALIZATION CONTRACT: '+contract
    writer_case={'id':'ukraine24-fra-checked-writer','country_iso3':'FRA','family':'ukraine24','condition':'checked_compact_plan_writer_control','prompt':[{'role':'system','content':'You are a source-grounded national policy analyst for France, using its dated own-national Council speech. Source assertions remain attributed to France, not independent findings.'},{'role':'user','content':writer_prompt}]}
    common={'criteria.json':criteria,'sources.json':{'ukraine24':{'FRA':statement}},'presentation-criteria.json':json.loads((old/'presentation-criteria.json').read_text()),
        'provenance.json':{'scope':'New source/task for this branch, sameUNgenre; pretraining/corpus exposure unknown. No labels or checked points supplied to actual planner; all source/criteria/control frozen before calls. Source claims, not factual-world adjudication.','raw_proof_sha256':sha256(raw/'source-proof.json'),'statement_sha256':sha256(raw/'statement.json'),'questions':QUESTIONS,'checked_plan_words':len(CHECKED.split())}}
    assert len(CHECKED.split())<=300
    planner=ROOT/'data/prepared/actual-compact-planner-20261007-v1';writer=ROOT/'data/prepared/actual-compact-planner-checked-20261007-v1'
    freeze(planner,[planner_case],common,'One actual source-to-compact-planner probe; no optimization.',tok,cfg)
    freeze(writer,[writer_case],{**common,'checked-plan.json':{'plan':CHECKED,'author':'same assistant; hand source checked, not actual model-generated planner output'}},'Strong checked-plan writer control, prospective/new source; no optimization.',tok,cfg)
    for name,pack in [('planner',planner),('checked-base',writer),('checked-point8',writer)]:
        new=copy.deepcopy(cfg);new.update(pack=str(pack.relative_to(ROOT)),kind='actual_compact_planner_'+name)
        if name=='checked-point8':
            ad=ROOT/'runs/aurora-plan-input-fit-20261006-v1/adapter';new.update(adapter=str(ad.relative_to(ROOT)),adapter_sha256=sha256(ad/'adapter_model.safetensors'),adapter_config_sha256=sha256(ad/'adapter_config.json'))
        write_json(ROOT/f'configs/posttraining/qwen35-actual-compact-{name}-20261007-v1.json',new)
    print(json.dumps({'checked_plan_words':len(CHECKED.split()),'actual_planner_calls_prepared':1,'checked_controls_prepared':2,'optimization_prepared':0}))


if __name__=='__main__':main()
