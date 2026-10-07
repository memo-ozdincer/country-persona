"""Freeze audited modal wording repairs and a separate dated national UK monitor."""
import copy,json,shutil,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_jsonl,write_json,sha256,digest

QUESTIONS='''1. Which dated national speaker/capacity, thanked officials, Foreign Secretary visit and military-solution assessment are stated?
2. Which immediate ceasefire/hostage/aid demands, acceptance request, already endorsed proposal and continuing mediation are distinguished?
3. What civilian spaces, named incursions/zone designation, population and IHL/hostage requirements appear?
4. What UNRWA role, actual announced amount/time and partial reform earmark are stated? Is this disbursement or a new condition?
5. Which cooperation, visas/equipment/all aid routes/specific crossing and safe law-and-order requirements are requested?
6. What devastation duration, civilian hospital/supply needs, living conditions and named disease concern are recorded?
7. Which settlement/violence/land-seizure scope, Council-law concern and political viability assessment appear?
8. What diplomatic process, two-State attributes, actual UK political-perspective commitment and irreversible desired future are stated?'''

UNITS={
'S1':'National UK/DameBarbaraWoodward26July2024, not chair or UNRWA official; thanks DeMeo andHadi; ForeignSecretaryvisit heard Israelis/Palestinians suffering and concluded no militarysolution/determinedtohelp.',
'S2':'Calls immediateceasefire, immediateallhostagesrelease andimmediateaidscaleup; urges BOTHsidesacceptdeal alreadyCouncilendorsed; mediationcontinues, no impliedalreadyaccepted/implementeddeal.',
'S3':'Civilianprotection/designatedcivilian spaces; concern IsraeliincursionsKhanYounis andAlMawasi ONLYremaining IDFdesignated humanitarianzone, some1.5m shelter; allsideIHL andHamasimmediateallhostagesrelease.',
'S4':'UNRWA central; UK announced27millionDOLLARS NEWfundinglastweek, SOMEearmarkedforColonna-managementreforms. Actualannouncement, not justrequest, alldisbursed/allearmarked/newconditionalgate.',
'S5':'Calls fullcooperationUN/humanitarianteamsinclUNRWA; visasMUSTgranted/equipmentallowed/ALLaidroutesopenedinclRafah; deterioratinglaw/order urgentlyaddressed forsafeaid. Requests, notclaimedalreadyaccomplished.',
'S6':'After9monthsdevastation civiliansneed functioninghospitals/water/electricity; appalledunsanitaryconditionswomen/children, diseaseinclpolioSPREADING, notonlyfuturetheoreticalrisk.',
'S7':'UK assertsWestBanksettlementexpansion/settler-violence recordlevels; IsraeliGovlandseizureTHISYEAR morethanPAST20YEARS COMBINED; unacceptable/multipleCouncilresviolated/twoStateviabilityundermined.',
'S8':'ONLYdiplomacy/IsraeliPalestinianrenewedpeaceprocess, safe-secureIsrael/viable-sovereignPalestinianState; UKrealcommitmentpoliticalperspectivecrediblepath/newfutureforWestBank/Gaza, route mustbeIRREVERSIBLE. Desiredstate/process notalreadyestablished/futurevote guarantee.'}

REFERENCE='''Documented source points:
- UK, Woodward, 26 July 2024, thanks De Meo/Hadi. Foreign Secretary heard Israeli/Palestinian suffering; determined help, no military solution.
- Calls immediate ceasefire, all hostages' release and aid scale-up; urges both sides accept Council-endorsed deal; mediation continues, acceptance unestablished.
- Civilian protection/spaces; Israeli incursions Khan Younis and Al-Mawasi, only remaining IDF-designated humanitarian zone, 1.5 million sheltering. All-side IHL; Hamas release all hostages immediately.
- UNRWA central; announced $27 million new funding last week, some for Colonna management reforms; no disbursement claim.
- Requests full UN/humanitarian/UNRWA cooperation: visas granted, equipment allowed, all aid routes opened including Rafah; urgently restore law/order for safe delivery.
- Nine months' devastation: hospitals, water, electricity needed; women/children unsanitary conditions, disease including polio spreading.
- UK condemns record West Bank settlement expansion/settler violence; this year's Israeli land seizure exceeds previous twenty years combined; Council resolutions/two-State viability undermined.
- Only diplomacy, renewed Israeli/Palestinian peace process: safe secure Israel, viable sovereign Palestinian State. UK commits political perspective/credible route/new future for West Bank/Gaza; irreversible desired path, not established state.'''

def main():
    old=ROOT/'data/prepared/extraction-diversity-20261007-v1';dest=ROOT/'data/prepared/source-status-20261007-v1';assert not dest.exists()
    cases=copy.deepcopy(list(read_jsonl(old/'cases.jsonl')));sources=json.loads((old/'sources.json').read_text());crit=json.loads((old/'criteria.json').read_text())
    source=json.loads((ROOT/'data/raw/source-status-grounding-20261007-v1/statement.json').read_text());sources['gaza26uk']={'GBR':source};crit['source_units']['gaza26uk']={'GBR':UNITS}
    prompt='PUBLIC SOURCE METADATA: S/PV.9694,26 July2024. Dame Barbara Woodward speaks nationally for the United Kingdom; Russia chairs; she is not a UNRWA official. No vote label in selectedspan. Attribute geopolitical claims to the UK.\n\nQUESTIONS ONLY, NO ANSWERS PROVIDED:\n'+QUESTIONS+'\n\nCOMPLETE NATIONAL STATEMENT:\n'+source['text']+'\n\nTASK: Give at most210 ordinary English words of Documented source points, covering every question and qualification. No application scenario is supplied. Preserve actors/dates, reported versus requested actions, actual announced funding versus disbursement, partial earmark and desired versus established political outcomes. No slash-list/fused-word shortcut or invented commitment, amount, vote or guarantee.'
    cases.append({'id':'gaza26uk-gbr-source-only-monitor','country_iso3':'GBR','family':'gaza26uk','condition':'separate_new_dated_UK_source_monitor','prompt':[cases[0]['prompt'][0],{'role':'user','content':prompt}]})
    targets=json.loads((ROOT/'data/prepared/source-status-draft-20261007-v1/preferred-targets.json').read_text());assert targets['words']==[207,208] and len(REFERENCE.split())<=210
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-extraction-diversity-base-20261007-v1.json').read_text());cfg.update(pack=str(dest.relative_to(ROOT)),eval_cases=4,kind='source_actor_modal_status_supervision_repair',baseline_run='runs/aurora-source-status-base-20261007-v1')
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True)
    for c in cases:
        ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
        if 'input_ids'in c:assert c['input_ids']==ids
        c.update(input_ids=ids,input_ids_digest=digest(ids));assert len(ids)+2048<=8192
    # Every marked exact phrase must actually occur in the bounded source.
    import re
    for c in cases[:2]:
        for q in re.findall(r'"([^"]+)"',targets['targets'][c['id']]):assert q in sources[c['family']]['FRA']['text'],q
    dest.mkdir();write_jsonl(dest/'cases.jsonl',cases);write_json(dest/'sources.json',sources);write_json(dest/'criteria.json',crit);write_json(dest/'preferred-targets.json',targets)
    shutil.copy2(ROOT/'data/prepared/source-status-draft-20261007-v1/initial-preferred-targets.json',dest/'initial-uncalled-target-draft.json');shutil.copy2(old/'presentation-criteria.json',dest/'presentation-criteria.json')
    write_json(dest/'private-monitor-reference.json',{'reference':REFERENCE,'words':len(REFERENCE.split()),'all8_units_hand_audited':True,'not_student_input_or_training_target':True})
    write_json(dest/'status-conventions.json',{'prospective_only':True,'old_criteria_and_grades_unchanged':True,'same_assistant_adjudication':'Source speech act and occurrence are distinct. should be able to expresses desiredCouncilcapacity/action, no explicitcondition-triggered promise. could allow is possibleeffect, notalreadyobservedgrowth. Ifconfirmed marksactualconditionalFrenchresponsecommitment. Retainexactmodalwordsratherthantrainbroadambiguousclasslabels. This interpretation is not independent adjudication.','target_repair':'OriginalLibyabullet investigatedandprosecuted omitsmust; normative reading reliedoncontext. Newtargetquotesmustallbeinvestigatedandprosecuted, addsnationalmetadata andpreservesall8meanings. It is supervisionclarification, notpurequote-format ablation.'})
    write_json(dest/'provenance.json',{'scope':'Two207/208word targetrewrites, unchanged nativefirst3inputs/oldcriteria, fresh64updates/32presentations each proposed onlyafter matchingbaseinspection. NewUK separate26Julyrecord/source/country monitor, sameGazaissue/genre; no sealedOOD/pretrainingabsence claim. Targetcontentclarity/quotes/role/length change together, notisolatedquoteeffect orconstanttokenbudget. Full14unitapplicationgoal retained.','previous_pack_sha256':sha256(old/'manifest.json'),'new_source_proof_sha256':sha256(ROOT/'data/raw/source-status-grounding-20261007-v1/source-proof.json')})
    shutil.copy2(__file__,dest/'builder-code.py');write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in dest.iterdir()},'training_authorized_for_this_pack':False,'training_examples':2,'eval_cases':4,'source_scope':'Source-only8compound/fourguard/210word task; sourceactors/modalsupervisionrepair, full14unitgoal unchanged.'})
    write_json(dest/'manual-inspection.json',{'all_selected_texts_read_complete':True,'manifest_sha256':sha256(dest/'manifest.json'),'scope':'Fourentireselectedspeeches, allquestions/criteria, bothnew207/208wordtargets andinitialuncalleddraft, UKprivatefeasibilitytext andstatusconventions fullyread. Allnewquotescheckedagainstsource; originalUKcover/pages16/17viewed. Sameauthor/grader, independentreviewpending.','fit_ready':False})
    write_json(ROOT/'configs/posttraining/qwen35-source-status-base-20261007-v1.json',cfg);print(json.dumps({'cases':4,'target_words':targets['words'],'private_reference_words':len(REFERENCE.split())}))

if __name__=='__main__':main()
