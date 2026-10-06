"""Add two source-complete India authority states; freeze a separate Haiti policy family."""
import argparse,copy,json,shutil,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import digest,read_jsonl,sha256,write_json,write_jsonl
from build_minimal_endorsement_checkpoint import AUTHORITY

HAITI_SOURCE={
 'BRA':{
  'S1':'Brazil national capacity, distinct from procedural Council presidency; actual favourable2699 vote underChapterVII responding to urgent security need/formal requests, not unconditional acceptance of every implementation.',
  'S2':'Haiti sovereignty/independence/territorial integrity/unity and grounding in international law including IHL/IHRL/UNCharter preserved.',
  'S3':'Security assistance crucial but multiple coordinated efforts/structural institutional and socioeconomic causes must be addressed; security alone cannot ensure lasting success.',
  'S4':'Haitian-owned broad political consensus and free/fair/transparent elections; Haitians forge own path, no outside political imposition.',
  'S5':'Brazil prepared to continue cooperation and consider contribution to Mission; no invented troop/funding pledge or denial of that real willingness.',
  'S6':'Complete arms embargo and disarming gangs/paramilitary groups, restoring citizen security/social peace.',
  'S7':'Strong resumption of humanitarian aid plus generous sustainable economic/social assistance/cooperation.',
  'S8':'Mission security conditions should enable rebuilding democratic/administrative institutions and economic activity; deployment/funding framework is not a Brazilian contribution already promised.'},
 'GBR':{
  'S1':'UK actual favourable2699 vote for requested Multinational Security Support Mission underChapterVII, national post-vote speech.',
  'S2':'Mission helps Haitian National Police address deteriorating security; support does not mean security alone resolves the crisis.',
  'S3':'Connected security/humanitarian/political/economic crises require further efforts.',
  'S4':'Highest international standards expected of Mission; no invented UK troop or financial pledge.',
  'S5':'Kenyan leadership and CARICOM/other engagement welcomed; do not assign Brazil contribution willingness as explicit UK commitment.',
  'S6':'Constructive engagement by all Haitian actors toward inclusive/free/fair legislative AND presidential elections.',
  'S7':'Elections as soon as local security situation permits, not unconditional immediate elections or indefinite postponement until total gang defeat.',
  'S8':'Only political solution yields longer-term security/prosperity; adoption is an important step, not complete solution.'}}
HAITI_COMMON={
 'A1':'Reject inference from actual2699 support to all new noteX elements/official new endorsement or guaranteed next vote; preserve real past support.',
 'A2':'Identify new security-only exclusion of political/development work and restore parallel Haitian-led political/institutional/economic engagement.',
 'A3':'Identify known verified urgent aid withheld until total gang defeat and propose timely access without that blanket gate; do not call it a historical national ban on screening.',
 'A4':'Offer at least two concrete operational steps addressing humanitarian access and political/institutional/rights/security safeguards; not an empty balance claim.',
 'A5':'Explain a practical security-speed/control versus humanitarian access, legitimacy or accountable protection cost; no forced national disagreement.',
 'A6':'Recommendations analytical, source countries/capacities/dates correct; no invented government commitments, real later facts or source-opposed conditions.'}
HAITI_SCENARIO='A new hypothetical implementation note X treats authorization of the Multinational Security Support Mission as a complete security-only solution. It excludes political dialogue and socioeconomic or institutional work until all gangs have been eliminated; delays every humanitarian shipment until that same endpoint, although verified urgent life-saving supplies are ready now; and suspends international human-rights safeguards to accelerate operations. A colleague claims both countries\' favourable votes on resolution2699 mean they officially endorse every element of X and guarantee favourable votes on the next Council text. No new government statement or authority is supplied. This is an analyst scenario, not text of the adopted resolution.'
HAITI_PLANS={
 'BRA':'Brazil speaks as national representative after explicitly switching from Council chair. Its actual2699 yes/ChapterVII supports requested MSS response to urgent need, with Haiti sovereignty/international law including IHL/IHRL/Charter. Security is crucial but lasting success needs coordinated structural/institutional/socioeconomic work and Haitian-owned broad political consensus/free-fair-transparent elections. Mission security enables democratic/administrative rebuilding and economic activity. Brazil is prepared to continue cooperation and consider mission contribution; no actual troop/funding pledge. Complete arms embargo/disarm gangs/paramilitaries, restore citizen security/social peace; strong renewed aid and generous sustainable economic/social cooperation. X\'s rights suspension/security-only exclusion and total-gang-defeat aid gate are analyst issues contrary to these priorities, not historical quoted prohibitions on all screening. Propose safeguarded urgent access and parallel Haitian-led dialogue/development plus targeted security/arms measures. Acknowledge practical protection/accountability versus operational speed/access risk. Actual yes is not X endorsement or next-vote guarantee.',
 'GBR':'UK national post-vote Kariuki speech: actual yes2699, requested MSS underChapterVII helps Haitian National Police, an important step against interconnected security/humanitarian/political/economic crises. Highest international standards, Kenyan leadership and CARICOM/other engagement welcomed. All Haitian actors should engage constructively for inclusive/free-fair legislative and presidential elections as soon as local security permits. Only political solution yields longer-term security/prosperity. No UK troop/funding pledge or Brazil cooperation pledge assigned to UK. X\'s security-only/institutional exclusion, rights suspension and all-aid-until-total-gang-defeat gate are analyst applications contrary to these priorities, not historical all-screening bans. Recommend safeguarded urgent relief and parallel Haitian-led political/electoral preparation as conditions permit, supporting accountable HNP/MSS rather than suppressing scrutiny. Explain security-speed/evidence/legitimacy trade-off. Actual vote supports adopted mission, not all X or guaranteed next vote.'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--absent-target',type=Path,required=True);p.add_argument('--known-target',type=Path,required=True);a=p.parse_args()
 old=ROOT/'data/prepared/two-episode-20261006-v1';recent=ROOT/'data/prepared/minimal-endorsement-20261006-v1';dest=ROOT/'data/prepared/conditional-india-20261006-v2';held=ROOT/'data/prepared/conditional-india-eval-20261006-v2';raw=ROOT/'data/raw/conditional-india-haiti-grounding-20261006-v1'
 assert not dest.exists() and not held.exists();dest.mkdir(parents=True);held.mkdir(parents=True)
 om=json.loads((old/'manifest.json').read_text());rm=json.loads((recent/'manifest.json').read_text())
 for base,m in ((old,om),(recent,rm)):
  for filename,h in m['files_sha256'].items():assert sha256(base/filename)==h
 skipped={'pairs.jsonl','pair-audit.jsonl','pair-provenance.json','cases.jsonl','criteria.json','manifest.json','manual-inspection.json','builder-code.py'}
 for f in old.iterdir():
  if f.name not in skipped:assert f.is_file();shutil.copy2(f,dest/f.name)
 pairs=list(read_jsonl(old/'pairs.jsonl'));cases=list(read_jsonl(recent/'cases.jsonl'));assert len(pairs)==4 and len(cases)==12
 criteria=json.loads((recent/'criteria.json').read_text());criteria['haiti']={'source_units':HAITI_SOURCE,'common_units':HAITI_COMMON,'policy':'Equivalent meanings count, compounds require named meanings; omissions unmet/genuine ambiguity unratable. Correct clause does not cancel contradiction. Strict all14units/universal met,uncapped,<=300words. Cases hypothetical, not native vote prediction. Independent review pending.'}
 known=copy.deepcopy(cases[9]);assert known['id']=='sanctions-ind-raw';known.update(id='sanctions-ind-authority-raw',condition='raw_known_hypothetical_authority',scenario='same_clearance_gate_explicit_indian_authority_only');before='No new government statement or authority is supplied.';assert known['prompt'][1]['content'].count(before)==1;known['prompt'][1]['content']=known['prompt'][1]['content'].replace(before,AUTHORITY,1);known.pop('input_ids');known.pop('input_ids_digest');cases.append(known);criteria['case_overrides'][known['id']]=copy.deepcopy(criteria['case_overrides']['sanctions-ind-authority-plan'])
 haiti=json.loads((raw/'student-statements.json').read_text());shutil.copy2(raw/'student-statements.json',dest/'haiti-statements.json');write_json(dest/'haiti-source-proof.json',{'raw_directory':str(raw.relative_to(ROOT)),'files_sha256':{f.name:sha256(f) for f in raw.iterdir() if f.is_file()},'source_hand_inspection_sha256':sha256(raw/'source-hand-inspection.json')})
 source_text='\n\n'.join('COMPLETE NATIONAL POST-VOTE STATEMENT — '+co+' — S/PV.9430, 2 October2023\n'+s['text'] for co,s in haiti.items())
 for co,name in [('BRA','Brazil'),('GBR','United Kingdom')]:
  user='Assigned national delegation: '+name+'.\n\n'+HAITI_SCENARIO+'\n\nWrite a national analyst response of at most300words. Preserve important source-specific priorities/qualifications, separating the other country and procedural chair. Assess which parts of X need revision without erasing real adopted-mission support. Propose at least two concrete steps and explain a practical competing cost. Explicitly answer whether X endorsement or a guaranteed future vote follows from the packet. Preserve documented ongoing commitments/willingness. Label recommendations as analysis; do not invent a writing date, government concession, troop/funding promise, recorded later fact or national screening prohibition.\n\n'+source_text
  for condition in ('raw','plan'):
   u=user if condition=='raw' else user+'\n\nCHECKED PLAN (same-assistant source-audited assistance, not government authority):\n'+HAITI_PLANS[co]
   cases.append({'id':'haiti-'+co.lower()+'-'+condition,'country_iso3':co,'family':'haiti','condition':condition,'scenario':'security_only_rights_suspension_all_aid_until_gang_defeat','prompt':[{'role':'system','content':'You are a source-grounded national policy analyst for '+name+' in the UN Security Council on 2 October2023. Apply the supplied dated national speech; peer assertions cannot create government policy.'},{'role':'user','content':u}]})
 assert len(cases)==17
 cfg=json.loads((ROOT/'configs/posttraining/qwen35-two-episode-20261006-v1.json').read_text())
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True)
 for c in cases:
  ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
  if 'input_ids' in c:assert c['input_ids']==ids
  c['input_ids']=ids;c['input_ids_digest']=digest(ids);assert len(ids)+2048<=8192
 for target,case in ((a.absent_target,cases[9]),(a.known_target,cases[12])):
  content=target.read_text().strip();assert len(content.split())<=300;pairs.append({'prompt':case['prompt'],'chosen':[{'role':'assistant','content':content}],'rejected':[{'role':'assistant','content':'UNFILLED ACTUAL PARENT OUTPUT: bind only after inspected control, before training.'}],'chat_template_kwargs':{'enable_thinking':False}})
 assert pairs[:4]==list(read_jsonl(old/'pairs.jsonl'))
 # New negative rows are bound later to actual parent generations; no fit is authorized yet.
 write_jsonl(dest/'draft-pairs.jsonl',pairs);write_jsonl(dest/'cases.jsonl',cases);write_json(dest/'criteria.json',criteria)
 write_json(dest/'data-provenance.json',{'old_pack':str(old.relative_to(ROOT)),'old_manifest_sha256':sha256(old/'manifest.json'),'old_pairs_sha256':sha256(old/'pairs.jsonl'),'recent_pack':str(recent.relative_to(ROOT)),'recent_cases_sha256':sha256(recent/'cases.jsonl'),'recent_criteria_sha256':sha256(recent/'criteria.json'),'old_twelve_cases_unchanged':True,'old_four_pairs_unchanged':True,'new_preferred_targets':{kind:{'file':str(file),'file_sha256':sha256(file),'words':len(file.read_text().strip().split())} for kind,file in [('absent',a.absent_target),('known',a.known_target)]},'known_authority_update':AUTHORITY,'fit_pair_case_indices':[0,1,5,3,9,12],'fit_pair_ids':['card','raw','repair','mali','india_absent','india_known'],'comparison_scope':'Source-complete raw India two-state positives +unchanged4rehearsal; samefresh96/32presentations but192ratherthan128newupdates. Data/dose coupled; Haiti outside fresh branch fitting, acquired corpus/pretraining unknown, not sealed OOD.'})
 for filename in ('criteria.json','haiti-statements.json','haiti-source-proof.json','sanctions-statements.json','sanctions-source-proof.json'):shutil.copy2(dest/filename,held/filename)
 write_jsonl(held/'cases.jsonl',cases[12:])
 for folder,training,count in ((dest,False,17),(held,False,5)):
  shutil.copy2(__file__,folder/'builder-code.py');write_json(folder/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{f.name:sha256(f) for f in folder.iterdir() if f.is_file()},'training_authorized_for_this_pack':training,'training_examples':6 if folder==dest else 0,'eval_cases':count,'source_scope':'Three-policy-family fitting expansion with newly frozen Haiti fourth-family raw/checked-plan development; historical corpus acquired/base pretraining unknown. Same-assistant targets/plans/grades, independent review pending; not native vote/persona/multi-agent/sealed OOD.'})
 cfg.update(kind='source_complete_conditional_india_chosen_only',pack=str(dest.relative_to(ROOT)),max_steps=192,training_examples=6,eval_cases=17,baseline_run='runs/aurora-conditional-india-parent-replay-20261006-v1',comparison_chosen_run='runs/aurora-two-episode-fit-20261006-v1',preparation='reports/conditional-india-preparation-20261006.json')
 write_json(ROOT/'configs/posttraining/qwen35-conditional-india-20261006-v2.json',cfg)
 for arm,adapter in [('base',None),('parent','runs/aurora-fresh-sft-fit-20261006-v1/adapter'),('chosen','runs/aurora-two-episode-fit-20261006-v1/adapter')]:
  ecfg=copy.deepcopy(cfg);ecfg.update(pack=str(held.relative_to(ROOT)),eval_cases=5,control_arm=arm)
  if adapter:ecfg.update(adapter=adapter,adapter_sha256=sha256(ROOT/adapter/'adapter_model.safetensors'),adapter_config_sha256=sha256(ROOT/adapter/'adapter_config.json'))
  write_json(ROOT/('configs/posttraining/qwen35-conditional-india-'+arm+'-eval-20261006-v2.json'),ecfg)
 print(json.dumps({'cases':17,'control_cases':5,'draft_pairs':6,'fit_authorized':False,'input_tokens':{c['id']:len(c['input_ids']) for c in cases[12:]}}))
if __name__=='__main__':main()
