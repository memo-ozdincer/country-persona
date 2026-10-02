"""Freeze one explicit-boundary repair after all eight initial answers were inspected."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import digest, sha256, write_json, write_jsonl, read_jsonl
from country_persona.probe_checks import validate_cases


def main():
    prior=ROOT/'runs/aurora-qwen35-source-plan-probe-20261002-v1/inspection.json'
    inspection=json.loads(prior.read_text())
    if inspection['status']!='all_eight_complete_answers_inspected_before_next_run':
        raise ValueError('Inspect prior full answers first')
    initial=ROOT/'data/prepared/qwen35-source-plan-probe-20261002-v1'
    spec=json.loads((initial/'spec.json').read_text())
    old_manifest=json.loads((initial/'manifest.json').read_text())
    for name, expected in old_manifest['files_sha256'].items():
        if sha256(initial/name)!=expected:raise ValueError('Original frozen pack changed')
    out=ROOT/'data/prepared/qwen35-source-plan-repair-20261002-v1'
    if out.exists():raise ValueError('Fresh repair pack required')
    constraints={
      'BRA':[
        'Keep Brazil\'s actual sponsorship/support for 2664, civilian and food/inflation harms, predictable humanitarian operations, and the legitimate security purpose of sanctions visible.',
        'Any 1267 role, risk-based screening or reporting you propose is an ANALYST amendment. Do not turn India\'s explicit monitoring demand into a recorded Brazilian red line.',
        'No Brazilian future support contingency is established in this source. Say future support is unknown; do not state "our support is contingent" on an invented mechanism.',
        'Predictability is documented for humanitarian operations. Do not call predictability itself a documented Brazilian anti-diversion mechanism.'
      ],
      'IND':[
        'Keep the Article 41 provisional qualification AND legitimate trade/regional economic activity, timely aid and agency predictability visible.',
        'Keep the specific dangers of evasion/fundraising/recruitment AND POLITICAL mainstreaming of terror entities visible.',
        'India said the proactive 1267 Monitoring Team role and robust reporting concerns were NOT FULLY ADDRESSED; do not strengthen this into "absent" or "not addressed".',
        'Proposed A revision: explicitly give the 1267 Monitoring Team an active monitoring/risk-review role AND robust operational reporting, with targeted due diligence that permits prompt low-risk aid. These implementation mechanics are analyst proposals.',
        'Requiring EVERY end beneficiary to be screened before ANY delivery/fund release recreates B\'s universal gate. Do not recommend that and then claim no delay. Preserve aid operationally by limiting checks to flagged risks and permitting other deliveries.',
        'No future support contingency, operative-text-versus-protocol red line, or comprehensive-package requirement is established in the speech. Say future support is unknown, even if the stated concerns are addressed.',
        'Do not add specific countries/regions where the alleged exploitation occurred; the national speech does not name them. The expanded name of ISIL is not location evidence.'
      ]}
    cases=[]
    for c in read_jsonl(initial/'cases.jsonl'):
        if c['condition']!='raw':continue
        country=c['country_iso3']
        plan=spec['countries'][country]['plan']+constraints[country]+[
            'The hypothetical discussion is immediately after the 9 December 2022 meeting. Omit a briefing-date header; do not invent a next-day writing date.',
            'You may write a substantive national recommendation without manufacturing disagreement with the other country. Keep documented facts and your proposals separate.']
        appendix='\n\nCHECKED RESPONSE PLAN WITH SOURCE/OPERATIONAL BOUNDARIES:\n'+'\n'.join('- '+s for s in plan)
        new={**c,'id':f'9214-{country.lower()}-repair','condition':'checked_plan_repair',
             'prompt':c['prompt'][:-1]+[{'role':'user','content':c['prompt'][-1]['content']+appendix}],
             'plan_appendix':appendix,'plan_sha256':digest(plan)}
        del new['case_sha256'];new['case_sha256']=digest(new);cases.append(new)
    validate_cases(cases,'checked_plan_repair_only')
    out.mkdir(parents=True)
    shutil.copy2(__file__,out/'builder.py');shutil.copy2(initial/'spec.json',out/'spec.json')
    write_jsonl(out/'cases.jsonl',cases)
    write_json(out/'repair-audit.json',{'constraints':constraints,'basis':'Inspected original eight outputs; existing same-source criteria are unchanged. Operational amendments are hypothetical analyst proposals, not historical mandates.',
        'initial_inspection_sha256':sha256(prior),'same_assistant_plan_review':True,'independent_review_complete':False})
    write_json(out/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'status':'frozen_before_generation','comparison_design':'checked_plan_repair_only','cases':2,'expected_calls':4,'new_training_steps':0,
        'spec_sha256':sha256(initial/'spec.json'),'initial_pack_sha256':sha256(initial/'manifest.json'),
        'files_sha256':{p.name:sha256(p) for p in out.iterdir()},'source_files_sha256':old_manifest['source_files_sha256'],
        'decision_rules':['Inspect all four complete outputs with the SAME frozen criteria.','No fitting solely to create a weight change. If boundaries repair substantive behavior, retain them for checked supervision preparation; persistent failures determine further repairs.','Development repair on the now-exposed event; no fresh-OOD improvement claim.']})
    config=json.loads((ROOT/'configs/posttraining/qwen35-source-plan-comparison-20261002.json').read_text())
    config.update(kind='explicit_boundary_plan_repair_comparison',question='Do explicit source-qualification, unknown-commitment and operational-gating boundaries repair inspected national-application failures?',comparison_design='checked_plan_repair_only',eval_pack=str(out.relative_to(ROOT)),eval_pack_manifest_sha256=sha256(out/'manifest.json'),expected_cases=2,expected_calls=4,prerequisite_inspection=str(prior.relative_to(ROOT)),prerequisite_inspection_sha256=sha256(prior),decision_rules=json.loads((out/'manifest.json').read_text())['decision_rules'])
    p=ROOT/'configs/posttraining/qwen35-source-plan-repair-20261002.json'
    if p.exists():raise ValueError('Fresh config required')
    write_json(p,config)
    print(json.dumps({'manifest_sha256':sha256(out/'manifest.json'),'cases':2,'expected_calls':4}))

if __name__=='__main__':main()
