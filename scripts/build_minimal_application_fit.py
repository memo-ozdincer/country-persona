"""One complete source-grounded application target, separate Libya application monitor."""
import copy,json,sys,shutil
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_jsonl,write_json,sha256,digest

TARGET='''Analytical decisions:
- Keep Article 51, military aid, directly involved military-target limits and targeted dual-use checks. Iranian ballistic transfers remain possible; no package adopted. Remove blanket aid suspension and forced-border goals.
- Verify ballistic reports; review Russia-bound dual-use components alongside continued aid to Ukraine. Precision costs staff time versus delivery speed.
- French support continues as long as needed, without a withdrawal condition; ballistic response only if confirmed.
Authority:
- No official Z endorsement or future Council vote is established. Recommendations are analytical.'''

QUESTIONS='''TASK: Return at most90 ordinary English words under Analytical decisions and Authority. Cover each of these six questions explicitly:
1. Which clauses are actually retained in current Q, rather than desired source corrections?
2. Which remaining Q claims conflict with the source, including alleged past actions?
3. Give two concrete relevant operational directions, specifying their scope and recipients.
4. What practical competing benefit/cost follows?
5. Which real French commitments remain, keeping their stated duration and conditions?
6. Is official Q endorsement or the future Council vote established?
No source restatement or supplied analytical answers. Recommendations must not be presented as official positions. Do not replace source commitments with new endpoints or conditions.'''

def main():
    old=ROOT/'data/prepared/source-status-application-block-20261007-v2';dest=ROOT/'data/prepared/minimal-application-20261007-v1';assert not dest.exists()
    cases=copy.deepcopy(list(read_jsonl(old/'cases.jsonl')));parent=ROOT/'runs/aurora-source-status-fit-20261007-v2';ir=json.loads((parent/'inspection.json').read_text());assert ir['all_outputs_read_complete'] and ir['transcript_sha256']==sha256(parent/'transcript.jsonl')
    librow=list(read_jsonl(parent/'transcript.jsonl'))[1];assert len(librow['output'].split())==210
    text=list(read_jsonl(ROOT/'data/prepared/compact-france-20261007-v1/cases.jsonl'))[0]['prompt'][1]['content'];q=text.split('Current hypothetical implementation note Q',1)[1].split('\n\nWrite a national analyst',1)[0];q='Current hypothetical implementation note Q'+q
    prompt='COUNTRY/ROLE/DATE: France, national Dime Labille,8 November2023, ICC Libya Councilbriefing; not chair/Prosecutor.\n\nACTUAL MODEL-GENERATED DOCUMENTED SOURCE POINTS (not teacher decisions):\n'+librow['output']+'\n\nCURRENT HYPOTHETICAL NOTE (unchanged):\n'+q+'\n\n'+QUESTIONS
    cases.append({'id':'libya-fra-actual-facts-application-monitor','country_iso3':'FRA','family':'libya','condition':'separate_policy_application_monitor_from_actual_fitted_facts','prompt':[cases[0]['prompt'][0],{'role':'user','content':prompt}]})
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-source-status-application-block-base-20261007-v2.json').read_text());cfg.update(pack=str(dest.relative_to(ROOT)),eval_cases=2,kind='one_complete_application_target_from_actual_source_facts',baseline_run='runs/aurora-minimal-application-base-20261007-v1')
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True)
    for c in cases:
        ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
        if 'input_ids'in c:assert ids==c['input_ids']
        c.update(input_ids=ids,input_ids_digest=digest(ids));assert len(ids)+2048<=8192
    assert len(TARGET.split())<=90
    crit=json.loads((old/'criteria.json').read_text());crit['source_units']['libya']={'FRA':{}};crit['policy']='Separate6unit/90wordapplication component, oneUkrainefittinginput/oneLibyamonitor. Full14unit/300wordwriterendpoint remainsrequired; no source facts rewritten.'
    sources=json.loads((old/'sources.json').read_text());sources['libya']=json.loads((ROOT/'data/prepared/compact-france-20261007-v1/sources.json').read_text())['libya']
    dest.mkdir();write_jsonl(dest/'cases.jsonl',cases);write_json(dest/'sources.json',sources);write_json(dest/'criteria.json',crit);shutil.copy2(old/'presentation-criteria.json',dest/'presentation-criteria.json');write_json(dest/'preferred-targets.json',{'targets':{cases[0]['id']:TARGET},'words':len(TARGET.split()),'author':'same root assistant; source/proposalchecked complete applicationtarget, no independentteacher'});write_json(dest/'actual-source-points.json',{'ukraine':json.loads((old/'actual-source-points.json').read_text()),'libya':{'row':librow,'run':str(parent.relative_to(ROOT)),'transcript_sha256':sha256(parent/'transcript.jsonl'),'inspection_sha256':sha256(parent/'inspection.json')},'all_actual_source_outputs_unedited':True})
    write_json(dest/'provenance.json',{'selected_after_failed_application2_inspection_sha256':sha256(ROOT/'runs/aurora-source-status-application-block-base-20261007-v2/inspection.json'),'scope':'Onecomplete6unitUkraineapp target, fresh32updates proposedafter2 matchingbaseanswersread/negativebinding. SeparateLibyapolicy/application outsidefit; bothfactualsources alreadyexposed/fitted inupstream sourceadapter. NotsealedOOD orpersona/nativeprediction gain. Nativefirstappinputidentical toactualv2base; no troopwithdrawal condition.'});shutil.copy2(__file__,dest/'builder-code.py')
    write_json(dest/'manual-target-audit.json',{'all_targets_hand_read_complete':True,'preferred_target_sha256':sha256(dest/'preferred-targets.json'),'source_primary_speech_and_Z_rechecked':True,'A1':'Fourvalidclauses andall4remainingdefects explicitlycovered; no forced-border sourcecorrectionmisstatedasretained.','A2':'Twoappropriate scopedactions: verifyIranballisticreports; reviewRussia-bounddualusecomponents alongsideUkrainianaid, noblanketgate.','A3':'Precisionbenefit versus stafftime/aid-deliveryspeed cost explicit.','A4':'OfficialZendorsement/futurevote notestablished explicit.','A5':'SourceFrenchsupport aslongneededandconditionalballisticresponse preserved; noconditiononwithdrawal.','A6':'Recommendationslabelledanalytical, noothercountry/role/date extrapolation.','independent_review_complete':False})
    write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in dest.iterdir()},'training_authorized_for_this_pack':False,'training_examples':1,'eval_cases':2,'source_scope':crit['policy']});write_json(dest/'manual-inspection.json',{'all_selected_texts_read_complete':True,'manifest_sha256':sha256(dest/'manifest.json'),'scope':'Bothcompletefactualmodeloutputs, primarysource/currentZ-Q/all6criteria/questions/90wordtarget andcontract fullyread. Libyaapplicationfrozenbefore2basecalls/fit, sourcealreadyexposed. Sameunblindedauthor/grader.'})
    write_json(ROOT/'configs/posttraining/qwen35-minimal-application-base-20261007-v1.json',cfg);print(json.dumps({'cases':2,'target_words':len(TARGET.split()),'input_tokens':[len(c['input_ids']) for c in cases]}))

if __name__=='__main__':main()
