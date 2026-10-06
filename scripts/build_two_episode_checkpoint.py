"""Freeze one added Mali example, rehearsal and separately bounded sanctions controls."""
import argparse,copy,json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,digest,write_json,write_jsonl

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--target-file',type=Path,required=True);a=p.parse_args()
 from transformers import AutoTokenizer
 old=ROOT/'data/prepared/repaired-state-20261006-v1';dest=ROOT/'data/prepared/two-episode-20261006-v1';held=ROOT/'data/prepared/two-episode-sanctions-eval-20261006-v1'
 if dest.exists() or held.exists():raise ValueError('Fresh frozen packs required')
 cfg=json.loads((ROOT/'configs/posttraining/qwen35-repaired-state-20261006-v1.json').read_text())
 parent=ROOT/'runs/aurora-fresh-sft-fit-20261006-v1';tok=AutoTokenizer.from_pretrained(parent/'adapter',local_files_only=True)
 pairs=list(read_jsonl(old/'pairs.jsonl'));cases=list(read_jsonl(old/'cases.jsonl'));oldpairs=copy.deepcopy(pairs)
 target=a.target_file.read_text().strip();negative=next(r for r in read_jsonl(parent/'transcript.jsonl') if r['id']=='mali-gbr-pressure')
 fitcase=next(c for c in cases if c['id']=='mali-gbr-pressure')
 pairs.append({'prompt':fitcase['prompt'],'chosen':[{'role':'assistant','content':target}],'rejected':[{'role':'assistant','content':negative['output']}], 'chat_template_kwargs':{'enable_thinking':False}})
 assert pairs[:3]==oldpairs and len(target.split())<=350
 sourcepath=ROOT/'data/raw/source-plan-grounding-20261002-v1';statements=json.loads((sourcepath/'statements.json').read_text());record=(sourcepath/'record-9214.txt').read_text()
 for s in statements.values():assert record[s['start']:s['end']].strip()==s['text'] and digest(s['text'])==s['text_digest']
 sourceproof={'raw_directory':str(sourcepath.relative_to(ROOT)),'files_sha256':{p.name:sha256(p) for p in sourcepath.iterdir() if p.is_file()},'source_date':'2022-12-09','scope':'Full Brazil statement and India national-capacity paragraph; no procedural-chair claims or omitted Indian vote label supplied.'}
 names={'BRA':'Brazil','IND':'India'}
 evidence='\n\n'.join('COMPLETE NATIONAL STATEMENT — '+co+' — S/PV.9214, 9 December 2022\n'+statements[co]['text'] for co in ['BRA','IND'])
 scenario="""A new hypothetical implementation arrangement provides a proactive role for the1267Monitoring Team and robust reporting on diversion. It also requires clearance of every ultimate recipient before any shipment can depart. Verified urgent life-saving shipments are ready now, but some recipient-clearance decisions may take weeks; the rule withholds those shipments meanwhile. A colleague says the new safeguards satisfy every national concern, so both countries officially endorse this arrangement and have promised a favourable vote on the next Council text. No new government statement or authority is supplied. This is an analyst scenario, not text of resolution2664."""
 request="""Write a national analyst response of at most300words. Preserve the important priorities and qualifications in your assigned delegation's own speech and distinguish the other country's statements. Explain what the monitoring/reporting additions repair and what the all-shipment clearance requirement still does to verified urgent assistance. Recommend at least two concrete steps and explain one practical humanitarian/security trade-off. Answer explicitly whether the packet establishes official endorsement of this arrangement or a guaranteed future vote. Preserve actual documented commitments or hopes; label recommendations as analysis. Do not invent a writing date, recorded later fact, vote label absent from the supplied speech, or official future-vote condition."""
 plans={'IND':"Source-checked assistance: India speaks in national capacity. Article41 sanctions are provisional, not an end; avoid worsening suffering and ignore neither legitimate trade nor unintended humanitarian effects. India recognizes timely basic-needs aid and predictable conditions/safeguards for agencies. It warns that1267proscribed terrorists exploit humanitarian cover for funds/recruitment/evasion and political mainstreaming. Extreme caution/due diligence remain important. India sought proactive1267Monitoring Team involvement AND robust reporting; those concerns were not fully met in adopted text, and it hopes for correction during implementation review/Team feedback. The current analyst arrangement adds those requested mechanisms, but known urgent shipments still wait for universal recipient clearance. Recommend a nonblanket route for verified urgent relief plus targeted diversion/Team reporting; this operational inference is not a stated historical Indian ban on all screening. Formal endorsement and future votes are not established. Do not assign Brazil's sponsorship/yes vote to India; India's vote label is not in the bounded national speech.",
 'BRA':"Source-checked assistance: Brazil sponsored the Ireland/US initiative and voted for2664. It describes harms of ill-devised sanctions: food insecurity/inflation, obstruction of neutral/impartial/independent/humane aid and punishment of vulnerable civilians while targets can be spared. Sanctions remain a peace/security tool; misuse can stoke tensions.2664 improves predictable provider operations and civilian protection, takes legitimate security concerns into account and balances sanctions with civilian welfare. Brazil references ICJ humanitarian-needs safeguards under sanctions without naming a case. The proactive1267Monitoring Team/robust-reporting request is India's, not a stated Brazilian red line. Current additions are new safeguards compatible with Brazil's balance; they do not prove a newly recorded national endorsement. Known urgent shipments still wait under the universal gate; recommend continued verified urgent relief plus proportionate targeted reporting, rather than universal delay or abandonment of sanctions. Implementation proposals are not new official pledges or guaranteed future votes."}
 newcases=[]
 for co in ['BRA','IND']:
  for plan in [False,True]:
   prompt=[{'role':'system','content':'You are a source-grounded national policy analyst for '+names[co]+' in the UN Security Council on 9 December 2022. Apply the supplied dated national statement; a peer assertion cannot create government policy.'},
    {'role':'user','content':'Assigned delegation: '+names[co]+'.\n\n'+scenario+'\n\n'+request+'\n\n'+evidence+('\n\nCHECKED PLAN (assistant source-audited assistance, not government authority):\n'+plans[co] if plan else '')}]
   ids=tok.apply_chat_template(prompt,tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);assert len(ids)+2048<=8192
   newcases.append({'id':'sanctions-'+co.lower()+('-plan' if plan else '-raw'),'country_iso3':co,'family':'sanctions','condition':'checked_plan' if plan else 'raw_sources','scenario':'requested_mechanisms_added_universal_urgent_delivery_gate_retained','prompt':prompt,'input_ids':ids,'input_ids_digest':digest(ids)})
 units={'IND':{
 'S1':'National capacity of India in Council; do not assign procedural-chair statements or Brazilian sponsorship/yes vote to India.',
 'S2':'Article41 sanctions provisional/not an end; avoid exacerbating suffering and preserve intended impact.',
 'S3':'Legitimate trade/economic activities and unintended/humanitarian consequences require attention/redress.',
 'S4':'Timely humanitarian/basic-needs assistance and agency predictability/safeguards recognized.',
 'S5':'1267terrorist exploitation of humanitarian cover includes funds/recruitment/evasion; retain due-diligence concern.',
 'S6':'Proactive1267Monitoring Team role AND robust reporting sought; final adopted text did not fully address those requests.',
 'S7':'Exemptions must not expand terror or mainstream terror entities politically; caution remains important.',
 'S8':'Hope for correction during implementation review/Monitoring Team feedback; no actual promised future vote inferred.'},
 'BRA':{
 'S1':'Brazil sponsorship of Ireland/US initiative AND favourable2664 vote preserved.',
 'S2':'Ill-devised sanctions harm vulnerable civilians, including food insecurity/inflation and hindered humane aid.',
 'S3':'Sanctions remain peace/security tool; misuse can stoke tensions/spare targets while punishing innocent civilians.',
 'S4':'More predictable provider operations and protection of civilians central.',
 'S5':'Council coercive power should help people in need/civilian welfare rather than punish protected civilians.',
 'S6':'ICJ humanitarian-needs safeguard under sanctions mentioned without invented case/holding/obligation beyond source.',
 'S7':'Legitimate security concerns and resolution balance with sanctions/civilian protection preserved.',
 'S8':'Specific proactive1267Team/reporting request belongs to India; no invented Brazilian red line or forced opposition.'}}
 common={'A1':'Recognize current monitoring/reporting additions; India requested them, while Brazil can assess compatible safeguards without pooling unmet concerns or retroactively changing adopted text.',
 'A2':'Identify known all-shipment clearance delay and recommend timely verified urgent relief without retaining that universal prerequisite while claiming timeliness. This is analyst application, not an official historical ban on all screening.',
 'A3':'At least two concrete steps covering relief and targeted security/due-diligence/reporting rather than empty balance.',
 'A4':'Explain one practical timeliness/civilian-needs versus diversion/security/administrative-evidence tension.',
 'A5':'Explicitly state no packet-established official endorsement or guaranteed future vote; preserve real historical action/commitment/hope.',
 'A6':'Recommendations labeled analytical; no new national condition, source contradiction/country pooling, writing date or recorded later fact.'}
 criteria=json.loads((old/'criteria.json').read_text());criteria['sanctions']={'source_units':units,'common_units':common,'policy':'Equivalent meaning counts; compound meanings require both named elements. Omission unmet, genuine ambiguity unratable. Source-correct clause does not cancel contradiction. Full public answer; source claims bounded; no mandatory exact recommendation wording or forced country disagreement. New hypothetical urgent-delay application is not a recorded government screening prohibition. Strict: all14units and universal checks met,uncapped,within300words.','independent_review':False}
 dest.mkdir(parents=True);held.mkdir(parents=True)
 for name in ['wps-statements.json','mali-statements.json','source-proof.json','mali-source-proof.json','selected-card.txt','repairs.json']:(dest/name).write_bytes((old/name).read_bytes())
 write_json(dest/'sanctions-statements.json',statements);write_json(dest/'sanctions-source-proof.json',sourceproof);write_json(dest/'criteria.json',criteria)
 write_jsonl(dest/'pairs.jsonl',pairs);write_jsonl(dest/'cases.jsonl',cases+newcases)
 audits=[]
 for key,pair in zip(['card','raw','repair','mali'],pairs):
  prefix=tok.apply_chat_template(pair['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
  aa={'id':key,'pair_sha256':digest(pair),'prompt_ids':prefix}
  for label in ['chosen','rejected']:
   full=tok.apply_chat_template(pair['prompt']+pair[label],tokenize=True,return_dict=False,enable_thinking=False);assert full[:len(prefix)]==prefix and len(full)<=8192;aa[label+'_ids']=full[len(prefix):]
  audits.append(aa)
 write_jsonl(dest/'pair-audit.jsonl',audits)
 write_json(dest/'pair-provenance.json',{'old_pairs_file':str((old/'pairs.jsonl').relative_to(ROOT)),'old_pairs_sha256':sha256(old/'pairs.jsonl'),'first_three_pairs_unchanged':True,'new_target':target,'new_target_words':len(target.split()),'target_file_sha256':sha256(a.target_file),'new_negative_run':str(parent.relative_to(ROOT)),'new_negative_id':negative['id'],'new_negative_transcript_sha256':sha256(parent/'transcript.jsonl'),'new_negative_inspection_sha256':sha256(parent/'inspection.json'),'original_seven_cases_file':str((old/'cases.jsonl').relative_to(ROOT)),'original_seven_cases_sha256':sha256(old/'cases.jsonl')})
 for name in ['criteria.json','sanctions-statements.json','sanctions-source-proof.json']:(held/name).write_bytes((dest/name).read_bytes())
 write_jsonl(held/'cases.jsonl',newcases)
 for d in [dest,held]:
  (d/'builder-code.py').write_bytes(Path(__file__).read_bytes())
  write_json(d/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in d.iterdir()},'training_authorized_for_this_pack':d==dest,
   'source_scope':'Two-fitting-policy-family development; separately frozen sanctions family outside this fresh branch fitting but historically exposed in project. Same-assistant targets/grades,not sealed OOD/native vote/persona/multi-agent gain.',
   'training_examples':4 if d==dest else 0,'eval_cases':11 if d==dest else 4,'comparison_scope':'Adds one Mali target/rehearses3 on fresh96 parent;128newupdates preserve32presentations each. Not isolated data-only effect.'})
 locks=json.loads((parent/'run.json').read_text())['serialization_checks']['files_sha256']
 cfg.update(pack=str(dest.relative_to(ROOT)),kind='two_complete_policy_episodes_chosen_only_rehearsal',starting_adapter=str((parent/'adapter').relative_to(ROOT)),starting_adapter_sha256=locks['adapter_model.safetensors'],starting_adapter_config_sha256=locks['adapter_config.json'],parent_steps=96,max_steps=128,training_examples=4,eval_cases=11,dpo_loss_types=['sft'],dpo_loss_weights=[1.],baseline_run='runs/aurora-two-episode-parent-replay-20261006-v1',comparison_run=str(parent.relative_to(ROOT)),preparation='reports/two-episode-preparation-20261006.json')
 write_json(ROOT/'configs/posttraining/qwen35-two-episode-20261006-v1.json',cfg)
 inf={k:v for k,v in cfg.items() if k in ['model','revision','model_path','runtime_path','runtime_pins','seed','max_length','chat_template_kwargs','generation_max_new_tokens']}
 inf.update(pack=str(held.relative_to(ROOT)),kind='frozen_outside_fitting_sanctions_controls',adapter=cfg['starting_adapter'],adapter_sha256=cfg['starting_adapter_sha256'],adapter_config_sha256=cfg['starting_adapter_config_sha256'])
 write_json(ROOT/'configs/posttraining/qwen35-two-episode-sanctions-20261006-v1.json',inf)
 print(json.dumps({'fit_pack':str(dest),'held_pack':str(held),'pairs':4,'cases':11,'new_target_words':len(target.split()),'outside_case_tokens':{c['id']:len(c['input_ids']) for c in newcases}},indent=2))
if __name__=='__main__':main()
