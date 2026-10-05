"""Literal partial-mechanism adjudication; no new training or changed historical grades."""
import json
from build_minimal_country_checkpoint import ROOT, SYSTEM
from country_persona.io import sha256, write_json, write_jsonl

def main():
    previous=ROOT/'data/prepared/minimal-country-20261005-v2'
    out=ROOT/'data/prepared/minimal-mechanism-20261005-v1'
    if out.exists():raise ValueError('Fresh output required')
    decision=ROOT/'runs/aurora-minimal-country-extension-fit-20261005-v1/inspection.json'
    if not json.loads(decision.read_text())['all_outputs_read_complete']:raise ValueError('Inspect previous checkpoint')
    out.mkdir(parents=True)
    sources=json.loads((previous/'sources.json').read_text())
    evidence='\n\n'.join('COMPLETE NATIONAL STATEMENT — '+c+' — S/PV.9214\n'+sources['statements'][c]['text'] for c in ('BRA','IND'))
    tasks={
      'proactive-only': 'A hypothetical implementation revision expressly gives the 1267 Monitoring '
       'Team the proactive oversight mandate India requested. For this scenario, that requested '
       'Team role is fully provided. Timely humanitarian delivery continues. The revision does '
       'not add the robust reporting standards and mechanisms India requested. Respond for '
       'India: identify what is fixed and what still needs attention, recommend the remaining '
       'amendment, and distinguish that recommendation from a promised future vote.',
      'reporting-only': 'A hypothetical implementation revision expressly provides the robust '
       'reporting standards and mechanisms India requested. For this scenario, that requested '
       'reporting is fully provided. Timely humanitarian delivery continues. The revision '
       'does not give the 1267 Monitoring Team the proactive role India requested. Respond '
       'for India: identify what is fixed and what still needs attention, recommend the '
       'remaining amendment, and distinguish that recommendation from a promised future vote.'}
    plans={
      'proactive-only': 'Checked state: historically India sought BOTH a proactive 1267 Team role '
       'and robust reporting, and said its concerns were not fully addressed. THIS hypothetical '
       'revision fully supplies the proactive role; robust reporting remains absent. Recognize '
       'that progress and recommend adding reporting, while retaining timely relief and '
       'due diligence against terrorist exploitation. The source does not guarantee a future vote.',
      'reporting-only': 'Checked state: historically India sought BOTH a proactive 1267 Team role '
       'and robust reporting, and said its concerns were not fully addressed. THIS hypothetical '
       'revision fully supplies robust reporting; the proactive role remains absent. Recognize '
       'that progress and recommend adding the proactive role, while retaining timely relief and '
       'due diligence against terrorist exploitation. The source does not guarantee a future vote.'}
    cases=[]
    for treatment in ('raw','checked-plan'):
      for scenario,task in tasks.items():
        content='Assigned delegation: India.\n\n'+task+'\n\n'+evidence
        if treatment=='checked-plan':content+='\n\n'+plans[scenario]
        cases.append({'id':treatment+'-'+scenario,'country_iso3':'IND',
          'family':'literal_mechanism_state' if treatment=='raw' else 'strong_checked_plan_control',
          'scenario':scenario,'prompt':[{'role':'system','content':SYSTEM},{'role':'user','content':content}]})
    criteria=json.loads((previous/'criteria.json').read_text())
    criteria['IND']['scenario_application']=('Literal proactive-only: acknowledges proactive role is fully '
      'provided and adds missing robust reporting, without declaring the supplied role absent. '
      'Literal reporting-only: acknowledges robust reporting is fully provided and adds missing '
      'proactive 1267 role, without declaring supplied reporting absent. In both, preserves timely relief.')
    for name in ('train.jsonl','train.manifest.jsonl'):(out/name).write_bytes((previous/name).read_bytes())
    write_json(out/'sources.json',sources);write_json(out/'criteria.json',criteria);write_jsonl(out/'cases.jsonl',cases)
    write_json(out/'manifest.json',{'question':'Does the partial-role miss survive literal source-matched mechanism wording, and do checked state notes repair it?',
      'training_examples':8,'eval_cases':len(cases),'training_authorized_for_this_pack':False,
      'decision':'Evaluation-only comparison of base and two saved adapters. Read every answer before another fit or scope change; retain previous active/proactive qualification and all previous grades.',
      'previous_inspection_sha256':sha256(decision),'files_sha256':{p.name:sha256(p) for p in out.iterdir() if p.is_file()},
      'independent_review_complete':False})
    print(json.dumps({'pack':str(out),'eval_cases':len(cases),'new_training':False}))

if __name__=='__main__':main()
