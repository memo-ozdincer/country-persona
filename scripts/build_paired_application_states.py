"""Two audited application states, one neutral untrained opposite-repair state."""
import copy,json,sys,shutil
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_jsonl,write_json,sha256,digest

REPAIRED_TARGET='''Analytical decisions:
- Keep Article 51, aid, directly involved military-target limits, targeted checks, possible-transfer status and continued assistance; those earlier defects are repaired. Reject claimed package adoption and forced-border goals.
- Check French measure-adoption records; frame negotiations around Ukrainian territorial integrity without force. Verification costs staff time versus rapid policy action.
- Support remains for as long as needed; any ballistic response requires confirmation.
Authority:
- No official Z-R endorsement or future Council vote is established. Recommendations are analytical.'''

MONITOR_NOTE='''Alternative hypothetical implementation note Z-S retains Article 51 self-defence, military assistance, military targets directly involved in attacks, and targeted dual-use export checks. It describes Iranian ballistic transfers as confirmed and requires all French assistance to wait until every export check is complete. It proposes further far-reaching measures only after confirmation, with no specified package already adopted. It requires negotiations to respect Ukrainian sovereignty and territorial integrity and prohibits changing borders by force. A colleague claims the speech officially endorses every Z-S clause and guarantees France's next Council vote. No new national authority is supplied; Z-S is hypothetical.'''

def main():
    old=ROOT/'data/prepared/minimal-application-fit-20261007-v1';changed=ROOT/'data/prepared/application-current-state-20261007-v1';dest=ROOT/'data/prepared/paired-application-states-20261007-v1';assert not dest.exists()
    cases=[copy.deepcopy(list(read_jsonl(old/'cases.jsonl'))[0]),copy.deepcopy(list(read_jsonl(changed/'cases.jsonl'))[0])]
    third=copy.deepcopy(cases[0]);text=third['prompt'][1]['content'];a=text.index('CURRENT HYPOTHETICAL NOTE');b=text.index('\n\nTASK:',a)
    text=text[:a]+'CURRENT HYPOTHETICAL NOTE (alternative Z-S):\n'+MONITOR_NOTE+text[b:];text=text.replace('current Z,','current Z-S,').replace('remaining Z claims','remaining Z-S claims').replace('official Z endorsement','official Z-S endorsement');third.update(id='ukraine24-fra-opposite-repairs-application-monitor',condition='untrained_neutral_note_opposite_repairs',prompt=[third['prompt'][0],{'role':'user','content':text}]);cases.append(third)
    third.pop('input_ids', None);third.pop('input_ids_digest', None)
    targets=copy.deepcopy(json.loads((old/'preferred-targets.json').read_text())['targets']);targets[cases[1]['id']]=REPAIRED_TARGET;assert len(targets[cases[0]['id']].split())==83 and len(REPAIRED_TARGET.split())<=90
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-minimal-application-base-20261007-v1.json').read_text());cfg.update(pack=str(dest.relative_to(ROOT)),eval_cases=3,kind='two_current_proposal_states_same_source',baseline_run='runs/aurora-paired-application-base-20261007-v1')
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True)
    for c in cases:
        ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
        if 'input_ids'in c:assert c['input_ids']==ids
        c.update(input_ids=ids,input_ids_digest=digest(ids));assert len(ids)+2048<=8192
    prefix=cases[0]['prompt'][1]['content'].split('CURRENT HYPOTHETICAL NOTE',1)[0];assert all(c['prompt'][1]['content'].startswith(prefix) for c in cases)
    dest.mkdir();write_jsonl(dest/'cases.jsonl',cases)
    for f in ['sources.json','criteria.json','presentation-criteria.json','actual-source-points.json']:shutil.copy2(old/f,dest/f)
    write_json(dest/'preferred-targets.json',{'targets':targets,'author':'same root assistant; unchanged83wordtarget plushand-auditedrepaired-state target','words':[len(t.split()) for t in targets.values()]})
    write_json(dest/'manual-target-audit.json',{'all_targets_hand_read_complete':True,'original_target_unchanged':True,'repaired_state_source_and_Z_R_rechecked':True,'A1':'Keepsalreadycorrecttransfer-status/aid-flow andfouroriginalvalidclauses; rejectsremainingpackageadoption/forced-border defects only, no repetitionofremovedaidgate.','A2':'Frenchmeasure-adoptionrecordcheck andUkraineintegrity-respectingnegotiationterms aretwoconcreterelevantdirections.','A3':'Verificationbenefit/stafftimeversusrapidactioncost explicit.','A4':'OfficialZ-Rendorsement/futurevote notestablished.','A5':'ActualFrenchsupportduration andconfirmation-triggeredresponse preserved.','A6':'Noothercountry/role/date, recommendationsanalytical.','independent_review_complete':False})
    write_json(dest/'provenance.json',{'original_pack_sha256':sha256(old/'manifest.json'),'changed_state_pack_sha256':sha256(changed/'manifest.json'),'source_facts_207_unchanged':True,'scope':'Onefresh2target64step chosen-onlyfit proposedafteractualbase/oldadapterinspection,32presentations each; doubles totalsteps versusone-target32 while retaining original exposure. Source/writer fixed. Thirdnewneutralnote repairsoppositesubset withoutnamedrepairlabels; frozenbeforecalls/fit. Familiar-source/novel-state development, notsealedOOD/persona/autonomousmultiagent gain.'});shutil.copy2(__file__,dest/'builder-code.py')
    write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in dest.iterdir()},'training_authorized_for_this_pack':False,'training_examples':2,'eval_cases':3,'source_scope':'Originalsixapplicationunits/90wordcontract, identicalactualfactualprefix, differentcurrentproposalstates. Full14unit/300wordendpoint stillrequired.'});write_json(dest/'manual-inspection.json',{'all_selected_texts_read_complete':True,'manifest_sha256':sha256(dest/'manifest.json'),'scope':'CompleteprimaryUkraineFrance speech, actual207wordfacts, originalZ/repairedZ-R/neutralZ-S, all6criteria/questions/83wordretainedtarget andnewtarget fullyhandread. No sources/writerweights/oldercriteria changed. Sameauthor/grader.'});write_json(ROOT/'configs/posttraining/qwen35-paired-application-base-20261007-v1.json',cfg)
    print(json.dumps({'cases':3,'target_words':[len(t.split()) for t in targets.values()],'input_tokens':[len(c['input_ids']) for c in cases]}))

if __name__=='__main__':main()
