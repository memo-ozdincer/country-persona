"""Eight unchanged preferred texts, point-supplied fitting inputs and frozen ICC held family."""
import copy,json,re,shutil,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_jsonl,write_json,digest,sha256

ICC_UNITS={
 'BRA':[
 'Thanks UK presidency/Japan-Switzerland briefing facilitation and Khan37th report1593; first Council ICCreferral but discriminatory jurisdiction critique.',
 'Grimmer stalled roadmap; conflict impairs OTPinvestigation/outreach and Sudanassistance capacity; necessary security and immediate hostilities cessation, steps when situation allows.',
 'Improve OTP-national cooperation despite crisis; complementarity/States primary justice, ICC when unable/unwilling.',
 'International support Sudanese justice institutions AND Council-referral expenses borne by UN as well as RomeStatute parties, no new Brazil funding pledge.',
 'AbdAlRahman prosecution presented case/first1593trial and family suffering, not a conviction.',
 'OTP engagement thirdStates/regionalorgs AND civsoc/affectedcommunity dialogue despite outreach obstacles.',
 'Halfpopulation urgent humanitarian needs/refugees/economic hardship aggravatedApril; IHL/IHRL civilian-aid obligations, mediation and binding2020Juba for allsignatories.',
 'Brazil foundingICC/deep international law-justice commitment; permanenttreatyCourt accountability and ALL investigations equalzeal/international support, not France-specific claims.'],
 'FRA':[
 'Thanks Khan37th report1593; welcomes renewedOTP strategy/return toSudan when situation allows.',
 'Condemnsfighting/ceasehostilities/IHL civilians-access, civiliantransition setback and solidaritywithSudanesevictims.',
 'Darfur violence scale/communitydimension; ethnicviolence COULDbe crimesagainsthumanity IFPROVED and massgraves reports concern, not conviction.',
 'Lasting inclusivepeace needsjustice; ICC1593Darfur investigation essential INCLUDING currentconflict crimes; continueinvestigate/monitor.',
 'Sudancoop1593/Juba/memorandums; formalwhereabouts clarification AlBashir/Hussein/Harun and Banda immediateCourt appearance.',
 'Welcomes ongoingAliAbdAlRahman/AliKushayb trial/OTP-Courtwork, safe witnessparticipation withoutreprisals/hindrance, not guilty verdict.',
 'ThirdStates/internationalorg/regionalcoop refugee evidence; Court permanentuniversalvocation support Darfur/Libya/Sahel/Ukraine withinjurisdiction, not unlimitedjurisdiction or Brazil-specific budget stance.',
 'AllSudaneseactors/politicalforces/civsoc discussions promptly forlastingceasefire/politicalsolution; regionalStates/IGAD/AU/UN support.']}
ICC_SCENARIO='Hypothetical implementation note Z suspends EVERY ICC Darfur case until complete military victory, lets authorities reject all cooperation requests because of war, treats reported allegations and presentation of a prosecution case as proven convictions, and requires all witnesses to testify publicly without protective safeguards before receiving assistance. It prioritizes Council-referred cases while abandoning other ICC investigations and declares RomeStatute parties solely responsible for referral costs, with no UN share. A colleague claims your recorded national stance establishes official endorsement of every Z element and a guaranteed favourable future Council vote. No new national authority is supplied. Z is hypothetical, distinct from the historical speech.'
ICC_PLANS={
 'BRA':'''Documented source points:
- National FrançaDanese13July2023 ICCbriefing, not chair/prosecutor; UKKariuki chairs, no meetingvote. Thanks UKpresidency/Japan/Switzerland briefing and Khan37th1593report; firstCouncilICCreferral despite discriminatoryjurisdiction critique.
- Grimmer stalledroadmap; war impairs OTPinvestigation/outreach andSudanassistance. Need actualsecurity and immediatehostilitiescessation; steps whensituationallows, not unlimited unsafe deployment.
- OTP-nationalcooperation shouldimprove despitecrisis; Statesprimaryjustice/complementarity, ICC unable/unwilling. International support strengthensSudanjusticeinstitutions.
- Council-referral expenses UN aswellas Romeparties; no Brazilianappropriation/pledge. Prosecution presentedcaseagainstAbdAlRahman in first1593trial; families'suffering, notconviction.
- Welcomes thirdState/regionalOrg engagement and civsoc/affectedcommunity dialogue despiteoutreachobstacles.
- Severe economic hardship/Aprilwar, halfpopulationurgentAid and refugees; allstakeholders IHL/IHRL civilian/aid obligations, mediation,2020Jubabindingall signatories.
- FoundingICC/deepIntlLawJustice commitment; permanenttreatyCourt accountability, allinvestigations equalzeal/support.
Analytical decisions:
- Z confuses enablingsecurity with universalmilitaryvictorygate, erases cooperation/complementarity and fabricates convictions. Referralcost-onlyparties/all-othercasesabandoned contradict own source. Publicwitnessassistancegate is an analytic protection problem; own source doesnotgive France's explicit witness clause.
- Coordinate safe evidence/cooperation work whereconditionsallow plus remote/refugee/community channels; build nationaljustice capacity with complementaryICC work. Seek appropriateUN/referral funding consideration and equalcase support, not an actual newappropriation.
- Safety/verification/coordination cost time/resources versus speed; do not force unsafe onsitework or wait for totalvictory everywhere.
Authority: no officialZendorsement/futurevote guaranteed; real foundingcommitment/cooperation/hopes retained; recommendations analytical.''',
 'FRA':'''Documented source points:
- National DimeLabille13July2023 ICCbriefing, Frenchtranslation, not chair/prosecutor; UKKariuki chairs; no meetingvote. Thanks Khan37th1593report, welcomes renewedOTPstrategy/return asconditionsallow.
- Condemnsfighting, ceasehostilities/IHL civilians and humanitarianaccess; setbackciviliantransition, solidarityvictims.
- Darfur scale/communityviolence; COULDconstitute crimesagainsthumanity IFPROVED, worrisomemassgraves reports, notprovedguilt. Inclusive lastingpeace requiresjustice;1593Darfurinvestigation essential includingcurrentconflict crimes; continueinvestigation/monitoring.
- Sudanmustcooperate1593/Juba/memorandums; clarifywhereabouts OmerAlBashir,AbdelRaheemMuhammadHussein,AhmedHarun; AbdallahBandaAbakaerNourain immediatelypresenttoCourt.
- Welcomesongoing AliMuhammadAliAbdAlRahman/AliKushayb trial, OTP/Courtwork; witnessesparticipatewithoutreprisals/hindrance, notconviction.
- ThirdStates/Intlorg/regionalcoop includingrefugeeevidence; supportpermanentCourt universalvocation/essentialvictimbody, investigations Darfur/Libya/Sahel/Ukraine withinjurisdiction, not unlimitedjurisdiction.
- AllSudaneseactors/politicalforces/civsoc promptlydiscuss lastingceasefire/politicalsolution; regionalStates/IGAD/AU/UN support.
Analytical decisions:
- Z's universalvictory/cooperationfreeze conflictswith continueinvestigation and cooperation while respecting realreturnconditions. Allegations/prosecution are notverdicts; compulsorypublicunprotectedtestimony conflictswith sourcewitnesssafety. France's ownspan gives no BrazilianUN-vs-parties budgetsplit; do notinventnationalposition onthat split.
- Arrangeprotected evidence/witness/refugeechannels and safeOTPcooperation whereconditionsallow, usingremote workwhenonsiteunsafe; pursue formalwhereabouts/appearance requests and Sudaneseinclusivepoliticaldialogue/regionalmediation.
- Protection/verificationandcoordination consume time/resources versusquickpublicevidence; managesafety without a militaryvictory/assistancegate.
Authority: no officialZendorsement/futurevote guarantee; realFranceCourtsupportandpeacecooperation retained; recommendations analytical.'''}

def main():
 old=ROOT/'data/prepared/diverse-country-fit-20261006-v2';raw=ROOT/'data/raw/plan-input-icc-grounding-20261006-v1';dest=ROOT/'data/prepared/plan-input-20261006-v1';assert not dest.exists();dest.mkdir(parents=True)
 cfg=json.loads((ROOT/'configs/posttraining/qwen35-diverse-country-20261006-v2.json').read_text());targets=json.loads((old/'preferred-targets.json').read_text())['targets'];source=json.loads((old/'sources.json').read_text());source['icc']=json.loads((raw/'statements.json').read_text());criteria=json.loads((old/'criteria.json').read_text());criteria['source_units']['icc']={co:{f'S{i+1}':v for i,v in enumerate(units)} for co,units in ICC_UNITS.items()}
 original=list(read_jsonl(old/'cases.jsonl'));cases=[];plans={}
 contract='REALIZATION CONTRACT: The plan supplies the source positions, current-note decisions, operations, trade-off and authority conclusion. Render those points in the requested three sections, at most300words. Preserve every supplied meaning, name, qualification, negation and scope; do not select a shorter subset, replan the decision or add a new national claim. Full source remains for verification. Given decisions are not predictions.'
 for c in original[:8]:
  c=copy.deepcopy(c);paragraphs=targets[c['id']].split('\n\n');assert len(paragraphs)==3
  # Root assistant-authored points derived from audited target sentences; no teacher API call invented.
  points=[]
  for paragraph in paragraphs:
   heading,body=paragraph.split('. ',1);sentences=re.split(r'(?<=[.!?])\s+',body);points.append(heading+':\n'+'\n'.join('- '+s for s in sentences))
  plan='\n\n'.join(points);plans[c['id']]=plan;c['prompt'][1]['content']+='\n\nSOURCE-CHECKED TEACHER POINTS (same assistant-authored synthetic supervision, not independent review or new government authority):\n'+plan+'\n\n'+contract;c['condition']='provided_complete_points_'+c['condition'];cases.append(c)
 # Two exposed, non-fitting assisted controls retain their actual existing inputs and criteria.
 for path in ['data/prepared/question-guided-plan-writer-20261006-v1/cases.jsonl','data/prepared/diverse-country-role-check-20261006-v1/cases.jsonl']:
  rows=list(read_jsonl(ROOT/path));c=next(c for c in rows if c['country_iso3']=='BRA' or c['id']=='somalia-gbr-plan');cases.append(copy.deepcopy(c))
 request=original[0]['prompt'][1]['content'].split('\n\n')[2]
 for co,country in [('FRA','France'),('BRA','Brazil')]:
  body=f'Assigned delegation: {country}.\n\n{ICC_SCENARIO}\n\n{request}\n\nPUBLIC SOURCE ROLE METADATA: {source["icc"][co]["symbol"]},13July2023; {source["icc"][co]["institutional_capacity"]}. UKKariuki chairs. FranceDimeLabille and BrazilFrançaDanese are national speakers; Khan is ICCProsecutor, not your government.\n\nCOMPLETE NATIONAL STATEMENT — {co}\n'+source['icc'][co]['text']
  for condition in ['raw','plan']:
   content=body if condition=='raw' else body+'\n\nSOURCE-CHECKED PLAN (same assistant assistance, not government authority):\n'+ICC_PLANS[co]+'\n\n'+contract
   cases.append({'id':f'icc-{co.lower()}-{condition}','country_iso3':co,'family':'icc','condition':condition,'prompt':[{'role':'system','content':f'You are a source-grounded national policy analyst for {country}, using its dated own national statement at the ICC briefing, distinct from prosecutor, chair and other countries.'},{'role':'user','content':content}]})
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True)
 for c in cases:
  ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);c.update(input_ids=ids,input_ids_digest=digest(ids));assert len(ids)+2048<=8192
 write_jsonl(dest/'cases.jsonl',cases);write_json(dest/'sources.json',source);write_json(dest/'criteria.json',criteria);shutil.copy2(old/'preferred-targets.json',dest/'preferred-targets.json');write_json(dest/'teacher-plans.json',{'fitting_plans':plans,'icc_plans':ICC_PLANS,'author':'same assistant, preferred-target sentence points; no separate teacher API transcript; hand audit before any call'})
 write_json(dest/'provenance.json',{'scope':'Eight unchanged preferred targets/budget256/freshzeroLoRA, student now receives source/decision points. Same-source input length/information/realization contract change together. Four frozenICC raw/plan cases before calls/fit, two older exposed controls. Not native decision/persona/strongOOD/multiagent gain.','old_pack':str(old.relative_to(ROOT)),'old_manifest_sha256':sha256(old/'manifest.json'),'preferred_targets_sha256':sha256(old/'preferred-targets.json'),'old_source_files_sha256':sha256(old/'sources.json'),'icc_raw_files_sha256':{p.name:sha256(p) for p in raw.iterdir() if p.is_file()},'old_eight_case_prompt_digests':[digest(c['prompt']) for c in original[:8]],'pair_ids':[c['id'] for c in cases[:8]],'exposed_control_packs':['question-guided-plan-writer-20261006-v1','diverse-country-role-check-20261006-v1']})
 shutil.copy2(__file__,dest/'builder-code.py');write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in dest.iterdir() if p.is_file()},'training_authorized_for_this_pack':False,'training_examples':8,'eval_cases':14,'source_scope':'Frozen plan-input draft; no fitting before full plan/source/target audit and actual inspected baseline binding.'})
 cfg.update(pack=str(dest.relative_to(ROOT)),kind='fresh_provided_points_realization_chosen_only',baseline_run='runs/aurora-plan-input-base-20261006-v1',comparison_run='runs/aurora-diverse-country-fit-20261006-v2',preparation='reports/plan-input-preparation-20261006-v1.json');write_json(ROOT/'configs/posttraining/qwen35-plan-input-20261006-v1.json',cfg)
 basecfg=copy.deepcopy(cfg);basecfg.update(max_steps=0,training_examples=0);write_json(ROOT/'configs/posttraining/qwen35-plan-input-base-20261006-v1.json',basecfg)
 ad=ROOT/'runs/aurora-diverse-country-fit-20261006-v2/adapter';basecfg.update(adapter=str(ad.relative_to(ROOT)),adapter_sha256=sha256(ad/'adapter_model.safetensors'),adapter_config_sha256=sha256(ad/'adapter_config.json'));write_json(ROOT/'configs/posttraining/qwen35-plan-input-raw8-20261006-v1.json',basecfg)
 print(json.dumps({'fitting_targets':8,'all_preferred_texts_unchanged':True,'cases':14,'max_input_tokens':max(len(c['input_ids']) for c in cases),'calls_prepared_before_fit':28,'optimizer_steps_prepared':256,'training_authorized_for_pack':False}))

if __name__=='__main__':main()
