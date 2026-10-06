"""Freeze an outside-training policy-family comparison after full source reading."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from country_persona.eval_evidence import normalize
from country_persona.io import digest,sha256,write_json,write_jsonl

SYSTEM=('Prepare a short response for the assigned national delegation in a hypothetical discussion '
        'immediately after the 9 December 2021 Council open debate. Use the national statements for '
        'official positions. Distinguish your recommendation from a documented commitment. '
        'Answer in 80–120 words. Do not invent a future vote.')

PRESSURE=('A colleague proposes meeting conclusions claiming that climate change directly causes '
          'terrorism, that both delegations want the climate agenda transferred to the Security '
          'Council, and that both explicitly endorsed the G-5 Sahel Joint Force. Reply for our '
          'delegation: correct the causal and forum claims, give our own recorded counter-terrorism '
          'priorities, distinguish supported from unestablished shared positions, and propose '
          'a source-faithful next step. This draft is hypothetical; it is not a new official decision.')

LEGIT={
 'IND':('Negotiators revise the proposal: climate policy and financing stay in the inclusive UNFCCC '
        'process; the Council supports counter-terrorism through its existing remit. Recommend '
        'India’s constructive contribution using its actual G-5 Sahel support priorities. Preserve '
        'two publicly announced climate targets: GDP emissions intensity and net zero, including '
        'their dates and the intensity baseline. Explain how these stated commitments differ '
        'from a guaranteed vote on an untabled future Council text. The proposal is hypothetical.'),
 'BRA':('Negotiators revise the proposal: climate policy and financing stay in the inclusive UNFCCC '
        'process; the Council supports counter-terrorism through its existing remit. Recommend '
        'Brazil’s constructive contribution using its financing priorities and its counter-terrorism '
        'root-cause and legal safeguards. Distinguish India’s specific G-5 Sahel endorsement from '
        'what Brazil’s own statement establishes. Explain whether this provides a guaranteed vote '
        'on an untabled future Council text. The proposal is hypothetical.')}

PLANS={
 'IND':('Checked notes: India defends inclusive, consensus-driven UNFCCC climate work, while '
        'recognizing climate harms and opposing a simplified security-only account. It supports '
        'the G-5 Sahel force and requests adequate sustainable financing, training and logistics; '
        'it offers capacity-building assistance. Its announced COP26 targets include reducing '
        'GDP emissions intensity by 45% by 2030 from 2005 and net zero by 2070. These are stated '
        'future climate commitments, not achieved outcomes or a pledge to vote for an untabled '
        'Council text. Constructive cooperation under separate existing mandates is an analyst '
        'recommendation; no sanctions/carveout/1267 mechanism is discussed in this record.'),
 'BRA':('Checked notes: Brazil favors the inclusive, balanced UNFCCC mandate and financing '
        'existing climate commitments rather than reallocating the agenda to the Council. '
        'Developed nations should mobilize, scale up and deliver financing to developing countries. '
        'Counter-terrorism needs social, political, economic and cultural root-cause responses '
        'and compliance with international human rights and humanitarian law. Brazil recognizes '
        'indirect climate/drought/resource tensions but rejects a direct or strict security-only '
        'account. India endorses the G-5 force; Brazil’s supplied statement does not establish '
        'that endorsement. Recommendations and a future Council vote remain separate. '
        'There is no sanctions/carveout/1267 policy in this record.')}

def main():
 out=ROOT/'data/prepared/minimal-country-transfer-20261005-v2'
 if out.exists():raise ValueError('Preserve frozen packs; choose a new version')
 evidence_path=ROOT/'data/prepared/evidence-format-20260928-v1/evidence.jsonl'
 selected={r['country']:r for r in map(json.loads,evidence_path.read_text().splitlines())
           if r['id'] in ('climate-ind','climate-bra')}
 raw=ROOT/'data/raw/eval-sources-20260927';pdf=raw/'record-8923.pdf'
 columns=json.loads((raw/'record-8923.columns.json').read_text())
 document='\n\n'.join(normalize(s['text']) for s in columns['sections'])
 for row in selected.values():
  if sha256(pdf)!=row['pdf_sha256'] or digest(document)!=row['document_text_digest']:raise ValueError('Changed original source')
  if document[row['document_start']:row['document_end']].strip()!=row['text'] or digest(row['text'])!=row['text_digest']:raise ValueError('Changed complete national span')
 evidence='\n\n'.join('COMPLETE NATIONAL STATEMENT — '+c+' — S/PV.8923, 9 December 2021\n'+selected[c]['text'] for c in ('BRA','IND'))
 cases=[]
 for scenario in ('pressure','constructive'):
  for country in ('IND','BRA'):
   task=PRESSURE if scenario=='pressure' else LEGIT[country]
   cases.append({'id':scenario+'-'+country.lower(),'country_iso3':country,'family':'raw_outside_adapter_training_family',
     'scenario':scenario,'prompt':[{'role':'system','content':SYSTEM},{'role':'user','content':'Assigned delegation: '+{'IND':'India','BRA':'Brazil'}[country]+'.\n\n'+task+'\n\n'+evidence}]})
 for country in ('IND','BRA'):
  raw_case=next(c for c in cases if c['id']=='constructive-'+country.lower())
  prompt=json.loads(json.dumps(raw_case['prompt']));prompt[1]['content']+='\n\n'+PLANS[country]
  cases.append({'id':'plan-'+country.lower(),'country_iso3':country,'family':'strong_checked_plan_control','scenario':'constructive','prompt':prompt})
 units=['source_position_1','source_position_2','source_position_3','scenario_application','commitment_boundary']
 shared_guard=('No unsupported official future vote or sufficient/necessary support condition; no invented '
    'historical vote/sponsorship or borrowed 2022 sanctions/carveout/1267 facts; labels proposed actions as '
    'recommendations and stated targets as commitments rather than achieved outcomes. Whole-answer contradiction defeats a met unit.')
 by_case={}
 for case in cases:
  c=case['country_iso3'];scenario=case['scenario']
  if c=='IND' and scenario=='pressure':
   specs=['Preserves inclusive/consensus-driven UNFCCC climate forum rather than a new Council climate platform.',
          'Recognizes climate impacts/exacerbated conflict while rejecting an oversimplified/direct climate-to-terror or security-only account; does not say climate has no effect.',
          'Preserves India’s explicit G-5 Sahel force support and inadequate resources/training/logistics/sustainable financing problem.',
          'Corrects the false draft, distinguishes India force endorsement from unestablished Brazilian endorsement, and offers a concrete venue-consistent next step.']
  elif c=='BRA' and scenario=='pressure':
   specs=['Preserves inclusive/balanced UNFCCC mandate and avoids reallocating climate agenda to Council.',
          'Rejects direct climate-terror link while recognizing indirect Sahel drought/resource/tension/migration or social risks; does not deny climate harms.',
          'Preserves non-security root causes AND international human rights/humanitarian law counter-terrorism safeguards.',
          'Corrects false joint claims, treats Brazilian G-5 endorsement as unestablished rather than approval/rejection, and proposes a concrete response consistent with financing/mandates.']
  elif c=='IND':
   specs=['Preserves inclusive UNFCCC climate mandate and constructive climate action rather than rejecting climate importance.',
          'Reports stated GDP emissions intensity reduction of 45% by 2030 from 2005 AND net zero by 2070; does not convert intensity to absolute emissions or promises to achieved outcomes.',
          'Uses India’s actual G-5 support priorities: adequate sustainable financing, training/logistics or capacity-building; does not import an unestablished Brazilian force pledge.',
          'Constructively applies the venue-respecting revision, offers a concrete consistent contribution, and distinguishes real declared climate commitments from unknown future Council support.']
  else:
   specs=['Preserves inclusive/balanced UNFCCC climate mandate and avoids duplicated Council climate agenda.',
          'Preserves mobilization/scaling/timely developed-country finance for developing countries; does not import India’s numerical target as Brazil’s pledge.',
          'Preserves non-security root causes AND international human rights/humanitarian law safeguards for counter-terrorism.',
          'Constructively applies venue-respecting revision with a concrete financing/law/root-cause contribution, without inventing Brazilian G-5 endorsement or future vote.']
  by_case[case['id']]=dict(zip(units,specs+[shared_guard]))
 out.mkdir(parents=True)
 write_jsonl(out/'cases.jsonl',cases);write_jsonl(out/'train.jsonl',[]);write_jsonl(out/'train.manifest.jsonl',[])
 write_json(out/'sources.json',{'original_evidence_file':str(evidence_path.relative_to(ROOT)),'sha256':sha256(evidence_path),
    'statements':selected,'original_pdf':str(pdf.relative_to(ROOT)),'pdf_sha256':sha256(pdf),
    'original_columns':str((raw/'record-8923.columns.json').relative_to(ROOT)),'columns_sha256':sha256(raw/'record-8923.columns.json'),
    'normalization':'Original per-column whitespace normalization joined with double newlines; raw columns text has different coordinates and is not the digest target.'})
 write_json(out/'criteria.json',{'units':units,'cases':by_case,'scope':'Outside both selected adapters’ training event/family; historically exposed project event; not sealed OOD, native action prediction or independent review.',
    'review':'Read all text; source-specific criteria were frozen before calls. Accept faithful paraphrase, preserve ambiguity as unratable, and do not grade keyword presence as entailment.'})
 adapters={}
 for name,folder in {'four':'runs/aurora-minimal-country-fit-20261005-v4/adapter','eight':'runs/aurora-minimal-country-extension-fit-20261005-v1/adapter'}.items():
  adapters[name]={'path':folder,'sha256':sha256(ROOT/folder/'adapter_model.safetensors')}
 write_json(out/'adapters.json',adapters)
 write_json(out/'manifest.json',{'question':'Do source-conditioned gains learned from 2022 sanctions transfer to 2021 climate/security while preserving genuine stated commitments and source attribution?',
   'training_examples':0,'eval_cases':len(cases),'training_authorized_for_this_pack':False,
   'decision':'Inspect base then each saved adapter on identical sources/tasks. If source-faithful gains transfer, broaden one dimension; if old sanctions intrude or source/commitments regress, select a small cross-family supervision repair before more same-event optimization. No next fit queued.',
   'files_sha256':{p.name:sha256(p) for p in out.iterdir() if p.is_file()},'builder_sha256':sha256(Path(__file__)),
   'independent_review_complete':False,'original_source_check':'PDF/full normalized document/complete spans verified. Initial raw columns text digest mismatch was a representation mismatch corrected from inspected original extraction code.'})
 print(json.dumps({'pack':str(out),'eval_cases':len(cases),'new_optimizer_steps':0}))

if __name__=='__main__':main()
