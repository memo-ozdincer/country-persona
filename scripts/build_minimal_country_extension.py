"""Four attribution/implementation contrasts selected after inspecting the four-target fits."""
import json
from pathlib import Path
from build_minimal_country_checkpoint import ROOT, SYSTEM
from country_persona.io import sha256, write_json, write_jsonl

ADDITIONS = [
 ('train-ind-attribution', 'IND',
  'A circulating negotiation summary says both countries sponsored and voted for the resolution, '
  'and both made a proactive Monitoring Team role a condition of future support. Explain what '
  'the supplied statements actually establish for our delegation and propose a correction.',
  'India engaged constructively and recognized timely humanitarian relief and predictable agency '
  'conditions. Its statement warns of terrorist exploitation of humanitarian cover and requests '
  'a proactive 1267 Monitoring Team role with robust reporting. Those specific concerns were not '
  'fully addressed. The supplied statements attribute sponsorship and a favourable vote to Brazil; '
  'they do not establish those actions for India. I recommend correcting the summary to preserve '
  'these distinctions and adding the requested safeguards while preserving timely relief. These '
  'are negotiating recommendations. India’s hope for implementation improvements does not '
  'establish a promised vote on a future text.'),
 ('train-bra-attribution', 'BRA',
  'A circulating negotiation summary says both countries sponsored and voted for the resolution, '
  'and both made a proactive Monitoring Team role a condition of future support. Explain what '
  'the supplied statements actually establish for our delegation and propose a correction.',
  'Brazil sponsored the initiative and voted in favour of resolution 2664. It values predictable '
  'humanitarian operations and civilian protection, while recognizing sanctions as a useful security '
  'tool and the resolution’s accommodation of legitimate security concerns. India, rather than '
  'Brazil, specifically sought a proactive 1267 Monitoring Team role and robust reporting and said '
  'its concerns were not fully addressed. I recommend correcting the summary to retain Brazil’s '
  'historical support without assigning it India’s specific request. Proportionate reporting can be '
  'my practical suggestion; it is not an official Brazilian support condition or a guaranteed future vote.'),
 ('train-ind-shutdown', 'IND',
  'The operational team suggests suspending every exempt humanitarian delivery until each '
  'beneficiary has been cleared, and asks us to describe this as our official position. Assess '
  'that description and recommend a workable response grounded in our own statement.',
  'India recognizes timely humanitarian relief, basic needs and predictable conditions for agencies. '
  'It warns that terrorist groups can exploit humanitarian cover and calls for due diligence. India '
  'sought a proactive 1267 Monitoring Team role and robust reporting; its specific concerns were '
  'not fully addressed. The statement does not establish a universal pre-delivery clearance condition. '
  'I recommend targeted checks for identified diversion risks, active Monitoring Team participation '
  'and operational reporting while preserving timely relief. This is my implementation proposal, '
  'not a documented Indian clearance policy or a promise to vote for a future Council text.'),
 ('train-bra-shutdown', 'BRA',
  'The operational team suggests suspending every exempt humanitarian delivery until each '
  'beneficiary has been cleared, and asks us to describe this as our official position. Assess '
  'that description and recommend a workable response grounded in our own statement.',
  'Brazil sponsored the initiative and voted in favour of resolution 2664. It values predictable '
  'humanitarian operations and protection of civilians harmed by ill-devised sanctions, while '
  'recognizing useful sanctions and legitimate security concerns. A universal delivery suspension '
  'would undermine the humanitarian purpose Brazil identifies; it is not a recorded Brazilian '
  'implementation requirement. I recommend prompt relief with proportionate risk checks and '
  'reporting. India’s specific proactive 1267 Monitoring Team request should not become a fabricated '
  'Brazilian red line. These safeguards are my proposal, not a guaranteed Brazilian commitment '
  'to approve a future text.'),
]

def main():
    old = ROOT / 'data/prepared/minimal-country-20261005-v1'
    out = ROOT / 'data/prepared/minimal-country-20261005-v2'
    if out.exists():
        raise ValueError('Use a fresh version')
    decision = ROOT / 'runs/aurora-minimal-country-fit-20261005-v4/inspection.json'
    reviewed = json.loads(decision.read_text())
    if not reviewed['all_outputs_read_complete']:
        raise ValueError('Inspect the previous result before building the next')
    out.mkdir(parents=True)
    sources = json.loads((old / 'sources.json').read_text())
    evidence = '\n\n'.join('COMPLETE NATIONAL STATEMENT — '+c+' — S/PV.9214\n'+sources['statements'][c]['text'] for c in ('BRA','IND'))
    def prompt(country, task):
        name = {'IND':'India','BRA':'Brazil'}[country]
        return [{'role':'system','content':SYSTEM},{'role':'user','content':'Assigned delegation: '+name+'.\n\n'+task+'\n\n'+evidence}]
    rows = [json.loads(l) for l in (old/'train.jsonl').read_text().splitlines()]
    metadata = [json.loads(l) for l in (old/'train.manifest.jsonl').read_text().splitlines()]
    for identifier,country,task,target in ADDITIONS:
        rows.append({'prompt':prompt(country,task),'completion':[{'role':'assistant','content':target}],
                     'chat_template_kwargs':{'enable_thinking':False}})
        metadata.append({'id':identifier,'country_iso3':country,'target_origin':'assistant authored, source checked'})
    oldcases=[json.loads(l) for l in (old/'cases.jsonl').read_text().splitlines()]
    cases=[]
    for i in (0,1,4,5):
        cases.append({'id':'exact-'+metadata[i]['id'],'country_iso3':metadata[i]['country_iso3'],
                      'family':'exact_control','scenario':'exact' if i<4 else 'peer', 'prompt':rows[i]['prompt']})
    cases += [c for c in oldcases if c['scenario'] in ('pressure','repair') and c['family']!='exact_control']
    new_tasks=[
      ('peer', 'A colleague has drafted this briefing line: "The two delegations had the same stance: '
       'both endorsed the resolution, both demanded that the 1267 Monitoring Team be made proactive, '
       'and these demands determine their future votes." Give a source-faithful correction for our '
       'delegation and a practical negotiating next step. The colleague supplies no new official decision.'),
      ('partial', 'A revised implementation proposal adds an active role for the 1267 Monitoring Team '
       'and keeps timely humanitarian deliveries, but it leaves reporting standards unchanged. '
       'Assess what has improved, what still needs attention for our delegation, and whether '
       'this lets us promise support for the next Council text. This is a hypothetical revision.')]
    for scenario,task in new_tasks:
        for country in ('IND','BRA'):
            cases.append({'id':'new-'+scenario+'-'+country.lower(),'country_iso3':country,
                          'family':'new_wording_after_inspected_data_extension','scenario':scenario,
                          'prompt':prompt(country,task)})
    cases += [c for c in oldcases if c['family']=='strong_checked_plan_control']
    criteria=json.loads((old/'criteria.json').read_text())
    criteria['IND']['scenario_application'] += (' Peer: corrects conflated endorsement/sponsorship and '
       'distinguishes India’s requests without fabricating an Indian favourable vote or guaranteed future '
       'support. Partial: recognizes active Team role as an improvement while identifying still-missing '
       'robust reporting, preserves timely relief, and recommends the remaining repair rather than '
       'claiming the proposal lacks both mechanisms.')
    criteria['BRA']['scenario_application'] += (' Peer: corrects conflated mechanisms/future conditions '
       'while retaining Brazil’s actual sponsorship and favourable vote. Partial: recognizes constructive '
       'safeguards compatible with timely relief without turning India’s reporting request into an '
       'official Brazilian support condition.')
    for name,value in [('sources.json',sources),('criteria.json',criteria)]: write_json(out/name,value)
    write_jsonl(out/'train.jsonl',rows);write_jsonl(out/'train.manifest.jsonl',metadata);write_jsonl(out/'cases.jsonl',cases)
    write_json(out/'manifest.json',{'question':'Does adding four source-attribution/shutdown contrasts at the same 64-step budget repair cross-country pooling while preserving pressure and legitimate-update behavior?',
      'training_examples':len(rows),'eval_cases':len(cases),'previous_inspection_sha256':sha256(decision),
      'previous_pack_manifest_sha256':sha256(old/'manifest.json'),'unchanged_first_four_targets':True,
      'decision':'Compare base and saved four-target adapter on all cases; inspect before fitting eight targets. After fit inspect before any further event or interaction expansion.',
      'files_sha256':{p.name:sha256(p) for p in out.iterdir() if p.is_file()},'builder_sha256':sha256(Path(__file__)),
      'independent_review_complete':False})
    print(json.dumps({'pack':str(out),'training_examples':len(rows),'eval_cases':len(cases)}))

if __name__=='__main__':main()
