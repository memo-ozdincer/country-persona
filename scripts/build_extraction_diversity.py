"""Retain one extraction target, add one source, freeze a third source before fitting."""
import copy,json,shutil,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_jsonl,write_json,sha256,digest

QUESTIONS='''1. What dated national capacity, Gaza escalation/ceasefire requirements and Council implementation are stated?
2. What solidarity/security, particular strikes, civilian protection and legal principles are recorded?
3. What settlement/West Bank violence, accountability and concrete settlement decisions are condemned?
4. What political solution and actual French participation are stated?
5. What Blue Line risk/restraint, desired Council action and UNIFIL protection appear?
6. What Lebanon/Israel/regional security, sovereignty, resolution and diplomatic commitments are retained?
7. What Yemen attacks/peace process, Iran role and conditions for releasing detained staff appear?
8. What Syria solution/legal basis, named pressures and real de-escalation partnership are recorded?'''

HELD_UNITS={
'S1':'National France/de Riviere on17July2024, not Russian chair; halt escalation, Macron ceasefire with protection of all civilians, unhindered humanitarian access and release of all hostages; adopted Council resolutions must be implemented, not already accomplished.',
'S2':'Solidarity with Israeli people after7October2023 attacks/Israel security; outrage at Israeli UNRWA school and Al-Mawasi camp strikes14/15July; protect civilians in military operations, international law/proportionality/distinction.',
'S3':'End settlement activity violating international law and West Bank cycle of violence; accountability for settlers attacking Palestinians; condemn recognition of five settlements and more than5000 additional housing units.',
'S4':'Urgent political settlement based on two-State solution; real French resolve to play full part in efforts, no invented recognition timetable or guaranteed outcome.',
'S5':'Blue Line Lebanon-Israel clashes risk regional conflagration; all-party restraint; Council SHOULD be able to unanimously call for de-escalation, not assertion that it did; threat to UNIFIL, maintain capacity and security.',
'S6':'Real commitment Lebanon/Israel/region security and Lebanon sovereignty; full resolution1701(2006) implementation and continued diplomatic solution efforts.',
'S7':'Houthis end illegal Red Sea attacks and engage in good faith in UN Special Envoy Yemen peace process; France says Iran funds/arms Houthis, urges end destabilizing actions; immediate UNCONDITIONAL release of UN and NGO staff held by Houthis.',
'S8':'Syria ONLY political solution under2254(2015), amid tensions/Daesh resurgence/Captagon trafficking/deteriorating humanitarian situation; actual rapid de-escalation engagement with regional/international partners.'}

# Private feasibility witness. Never supplied as input or used in either fit.
HELD_REFERENCE='''Documented source points:
- France, de Rivière, 17 July 2024: halt escalation; Macron urges ceasefire protecting all civilians, unhindered aid and all hostages' release; implement Council resolutions.
- Solidarity after 7 October 2023 and Israel's security; outrage at UNRWA school and Al-Mawasi strikes, 14–15 July; civilian protection, proportionality and distinction.
- End illegal settlements and West Bank violence; hold attacking settlers accountable; condemn five settlements and over 5,000 additional homes.
- Urgent two-State political settlement; France resolved to play its full part.
- Blue Line clashes risk regional conflagration: all-party restraint; Council should unanimously urge de-escalation, not already agreed. UNIFIL threatened; maintain capacity and security.
- Lebanon, Israel and regional security, Lebanon sovereignty, full 1701(2006) implementation; continued diplomacy.
- Houthis: end illegal Red Sea attacks; good-faith UN Special Envoy Yemen peace process. France says Iran funds and arms Houthis; cease destabilization. Immediately, unconditionally release UN and NGO staff.
- Syria: only political solution under 2254(2015), amid tensions, Daesh resurgence, Captagon trafficking and worsening humanitarian conditions. France engages for rapid de-escalation with regional and international partners.'''

def main():
    old=ROOT/'data/prepared/source-extraction-20261007-v1';dest=ROOT/'data/prepared/extraction-diversity-20261007-v1';assert not dest.exists()
    cases=copy.deepcopy(list(read_jsonl(old/'cases.jsonl')));sources=json.loads((old/'sources.json').read_text());criteria=json.loads((old/'criteria.json').read_text())
    source=json.loads((ROOT/'data/raw/extraction-diversity-gaza-grounding-20261007-v1/statement.json').read_text());sources['gaza24']={'FRA':source};criteria['source_units']['gaza24']={'FRA':HELD_UNITS}
    prompt='PUBLIC SOURCE METADATA: S/PV.9687, 17 July 2024. De Rivière speaks nationally for France; Russia chairs. No vote label in selected span. Attribute geopolitical assertions to France.\n\nQUESTIONS ONLY, NO ANSWERS PROVIDED:\n'+QUESTIONS+'\n\nCOMPLETE NATIONAL STATEMENT:\n'+source['text']+'\n\nTASK: Give at most210 ordinary English words of Documented source points, covering every question and qualification. No application scenario is supplied. Preserve actors, dates, conditional versus established claims, actual ongoing support, desired-versus-accomplished Council action and unconditional-versus-conditional release. No slash-list/fused-word shortcut or invented commitment, amount, vote or guarantee.'
    cases.append({'id':'gaza24-fra-source-only-monitor','country_iso3':'FRA','family':'gaza24','condition':'separate_new_source_factual_extraction_monitor','prompt':[cases[0]['prompt'][0],{'role':'user','content':prompt}]})
    target=json.loads((ROOT/'data/prepared/source-extraction-fit-20261007-v1/preferred-targets.json').read_text())['targets'];target[cases[1]['id']]=json.loads((ROOT/'data/prepared/compact-france-20261007-v1/checked-plan.json').read_text())['plan'].split('\n\n')[0]
    assert [len(target[c['id']].split()) for c in cases[:2]]==[198,194] and len(HELD_REFERENCE.split())<=210
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-source-extraction-base-20261007-v1.json').read_text());cfg.update(pack=str(dest.relative_to(ROOT)),eval_cases=3,kind='two_source_extraction_data_diversity',baseline_run='runs/aurora-extraction-diversity-base-20261007-v1')
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True)
    for c in cases:
        ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
        if 'input_ids'in c:assert c['input_ids']==ids
        c.update(input_ids=ids,input_ids_digest=digest(ids));assert len(ids)+2048<=8192
    dest.mkdir();write_jsonl(dest/'cases.jsonl',cases);write_json(dest/'sources.json',sources);write_json(dest/'criteria.json',criteria)
    shutil.copy2(old/'presentation-criteria.json',dest/'presentation-criteria.json');write_json(dest/'preferred-targets.json',{'targets':target,'author':'same root assistant; existing source-checked documentary blocks unchanged; complete original speeches reread','training_target_words':[198,194]})
    write_json(dest/'private-monitor-reference.json',{'reference':HELD_REFERENCE,'words':len(HELD_REFERENCE.split()),'all8_compounds_and_source_guards_hand_audited':True,'never_student_input_or_optimized':True})
    write_json(dest/'provenance.json',{'scope':'Two source-only positives, one newly acquired source monitor. France-only diplomatic task, same genre; no strong OOD/persona/application gain claim. First two native input IDs and first198word target unchanged. Fresh128updates,64presentations each proposed after actual base inspection; doubles total budget versus one-target64, not a fixed-total-budget causal data ablation. No next fit before inspection.','old_manifest_sha256':sha256(old/'manifest.json'),'new_source_proof_sha256':sha256(ROOT/'data/raw/extraction-diversity-gaza-grounding-20261007-v1/source-proof.json'),'task_max_words':210,'independent_review_complete':False})
    shutil.copy2(__file__,dest/'builder-code.py');write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in dest.iterdir()},'training_authorized_for_this_pack':False,'training_examples':2,'eval_cases':3,'source_scope':'Source-only extraction, eight full source compounds plus four guards, <=210words/uncapped; application fourteen-unit goal unchanged.'})
    write_json(dest/'manual-inspection.json',{'all_selected_texts_read_complete':True,'manifest_sha256':sha256(dest/'manifest.json'),'read_scope':'All3 complete national statements, questions/input contracts, retained198word and added194word targets, all8 criteria per source, private held feasibility reference; PDF cover and source pages24/25 viewed. Root assistant author/grader; no independent review.','fit_ready':False})
    write_json(ROOT/'configs/posttraining/qwen35-extraction-diversity-base-20261007-v1.json',cfg)
    print(json.dumps({'cases':3,'targets':2,'private_monitor_words':len(HELD_REFERENCE.split()),'input_tokens':[len(c['input_ids']) for c in cases]}))

if __name__=='__main__':main()
