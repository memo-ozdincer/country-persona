"""Freeze the original four-country climate questions for a matched initial-response check."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from country_persona.deliberation import make_case,validate_scenario
from country_persona.eval_evidence import normalize
from country_persona.io import digest,sha256,write_json,write_jsonl

def main():
 out=ROOT/'data/prepared/minimal-deliberation-initials-20261006-v1'
 if out.exists():raise ValueError('Fresh pack required')
 parent=ROOT/'data/prepared/deliberation-probe-20260928-v1'
 scenario=next(s for s in map(json.loads,(parent/'scenarios.jsonl').read_text().splitlines()) if s['id']=='climate-policy-workshop-v1')
 validate_scenario(scenario)
 original=next(r for r in map(json.loads,(parent/'review.references.jsonl').read_text().splitlines()) if r['scenario_id']==scenario['id'])
 columns=json.loads((ROOT/'data/raw/eval-sources-20260927/record-8923.columns.json').read_text())
 document='\n\n'.join(normalize(s['text']) for s in columns['sections'])
 for e in scenario['evidence']:
  if digest(document)!=e['document_text_digest'] or document[e['document_start']:e['document_end']].rstrip()!=e['text']:raise ValueError('Changed complete source span')
 cases=[];criteria={}
 for country in ('FRA','GBR','IND','BRA'):
  case=make_case(scenario,'independent_revision','initial',country,[])
  cases.append({'id':'initial-'+country.lower(),'country_iso3':country,'family':'four_country_initial','scenario':'original_climate_question',
    'prompt':case['prompt'],'original_case':case})
  criteria[country]={'criteria':original['national_policy_rubrics'][country]['criteria'],
      'universal_checks':original['national_policy_rubrics'][country]['universal_checks'],
      'reference_notes':original['national_policy_rubrics'][country]['reference_notes']}
 out.mkdir(parents=True)
 write_jsonl(out/'train.jsonl',[]);write_jsonl(out/'train.manifest.jsonl',[]);write_jsonl(out/'cases.jsonl',cases)
 write_json(out/'scenario.json',scenario);write_json(out/'criteria.json',criteria)
 write_json(out/'manifest.json',{'question':'Does the inspected four-target fit improve all four national responses under the original source-grounded deliberation questions, including two roles never fitted?',
   'training_examples':0,'eval_cases':4,'training_authorized_for_this_pack':False,
   'decision':'Read matched base/adapter initials before selecting self/peer revision. No autonomous continuation until those initial responses are inspected.',
   'parent_manifest_sha256':sha256(parent/'manifest.json'),'parent_reference_sha256':sha256(parent/'review.references.jsonl'),
   'selected_adapter':'runs/aurora-minimal-country-fit-20261005-v4/adapter',
   'adapter_sha256':sha256(ROOT/'runs/aurora-minimal-country-fit-20261005-v4/adapter/adapter_model.safetensors'),
   'generation_protocol':'Original make_case initial prompts and 384-token agent cap; 8192 context. No revised notes or gold responses in inputs.',
   'files_sha256':{p.name:sha256(p) for p in out.iterdir() if p.is_file()},'builder_sha256':sha256(Path(__file__)),
   'independent_review_complete':False})
 print(json.dumps({'pack':str(out),'cases':4,'country_roles':['FRA','GBR','IND','BRA'],'optimizer_steps':0}))

if __name__=='__main__':main()
