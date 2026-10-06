"""Freeze a four-weight component diagnostic with a given faithful factual prefix."""
import argparse,copy,json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_json,write_jsonl,sha256,digest

def main():
 p=argparse.ArgumentParser(description=__doc__);p.parse_args()
 from transformers import AutoTokenizer
 original=ROOT/'data/prepared/repaired-state-20261006-v1'
 cases=list(read_jsonl(original/'cases.jsonl'));old=next(c for c in cases if c['id']=='wps-partial-repair')
 pairs=list(read_jsonl(original/'pairs.jsonl'));prefix=pairs[0]['chosen'][0]['content'].rsplit('\n\n',1)[0]
 assert prefix==pairs[1]['chosen'][0]['content'].rsplit('\n\n',1)[0]==pairs[2]['chosen'][0]['content'].rsplit('\n\n',1)[0]
 footer="""\n\nCOMPONENT DIAGNOSTIC: The source-faithful national-fact paragraphs below are already supplied. For this diagnostic, supersede the request to write the entire memo: write only its final analytical application paragraph, at most 100 words. Do not repeat the supplied factual summary. State which parts of the current partial revision have been repaired and which access barrier remains; recommend a concrete feasible next step and explain one practical care/accountability trade-off. Distinguish your proposal from official endorsement and any guaranteed future vote. Keep the known hypothetical mechanism separate from unknown national authority.\n\nSUPPLIED FACTUAL PREFIX (assistant-authored source-checked material; no new government authority):\n"""+prefix
 prompt=copy.deepcopy(old['prompt']);prompt[-1]['content']+=footer
 original_config=ROOT/'configs/posttraining/qwen35-repaired-state-partial-20261006-v1.json';cfg=json.loads(original_config.read_text())
 tok=AutoTokenizer.from_pretrained(ROOT/cfg['adapter'],local_files_only=True)
 ids=tok.apply_chat_template(prompt,tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
 assert len(ids)+2048<=8192
 criteria=json.loads((original/'criteria.json').read_text())
 selected={'core_units':criteria['partial_state_units'],'additional_units':{'T1':'Explain one concrete practical care/accountability trade-off, not only claim both goals can coexist.','T2':'Concrete recommendation is clearly analytical; no unsupported national condition, commitment, agreement, writing date or later fact.'},'universal_checks':criteria['universal_checks'],
 'policy':'Equivalent meaning counts; omissions unmet, genuine ambiguity unratable. Source text and real ongoing promises remain authoritative; do not require repeating supplied factual paragraphs. Strict component pass: all core/additional/guards met, public output not capped, within100words. This easier component task does not replace original full-task grades or measure independent source parsing.', 'independent_review':False}
 shared={'cases.jsonl':[{'id':'wps-partial-application-paragraph','country_iso3':'FRA_GBR','family':'wps','condition':'given_factual_prefix_application_only','prompt':prompt,'input_ids':ids,'input_ids_digest':digest(ids)}],
 'criteria.json':selected,'wps-statements.json':json.loads((original/'wps-statements.json').read_text()),'source-proof.json':json.loads((original/'source-proof.json').read_text()),
 'prompt-proof.json':{'original_cases_file':str((original/'cases.jsonl').relative_to(ROOT)),'original_cases_sha256':sha256(original/'cases.jsonl'),'original_case_id':old['id'],'original_input_ids':old['input_ids'],'original_request_digest':digest(old['prompt']),
 'original_pairs_file':str((original/'pairs.jsonl').relative_to(ROOT)),'original_pairs_sha256':sha256(original/'pairs.jsonl'),'factual_prefix':prefix,'factual_prefix_digest':digest(prefix),'appended_footer':footer,'new_prompt_digest':digest(prompt),
 'changes':['append given factual prefix','request final application paragraph only,100words','explicit no-repeat/source-authority distinction'],'not_isolated_composition_effect':True},
 'factual-prefix.txt':prefix}
 adapters={'parent':'runs/aurora-raw-coverage-fit-20261006-v1/adapter','combined':'runs/aurora-repaired-state-fit-20261006-v1/adapter','chosen':'runs/aurora-chosen-sft-fit-20261006-v2/adapter'}
 common_hashes=None;result=[]
 for arm,adapter in adapters.items():
  pack=ROOT/('data/prepared/application-paragraph-20261006-v2-'+arm);config_path=ROOT/('configs/posttraining/qwen35-application-paragraph-20261006-v2-'+arm+'.json')
  if pack.exists() or config_path.exists():raise ValueError('Fresh packs/configs required')
  pack.mkdir(parents=True)
  for name,value in shared.items():
   if name.endswith('.jsonl'):write_jsonl(pack/name,value)
   elif name.endswith('.json'):write_json(pack/name,value)
   else:(pack/name).write_text(value)
  (pack/'builder-code.py').write_bytes(Path(__file__).read_bytes())
  hashes={p.name:sha256(p) for p in pack.iterdir()}
  if common_hashes is None:common_hashes=hashes
  assert hashes==common_hashes
  manifest={'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':hashes,'training_authorized_for_this_pack':False,
   'source_scope':'Same exposed WPS event and mixed analyst scenario; supplied factual prefix/application-only task is a new easier component condition, not sealed OOD or full-task success.',
   'adapter_sha256':sha256(ROOT/adapter/'adapter_model.safetensors'),'adapter_config_sha256':sha256(ROOT/adapter/'adapter_config.json'),
   'thinking_marker_ids':{s:tok.convert_tokens_to_ids(s) for s in ['<think>','</think>']},'comparison_arm':arm,
   'public_generations_planned':1,'optimizer_steps_planned':0,'manual_inspection_required_before_launch':True}
  write_json(pack/'manifest.json',manifest)
  current=copy.deepcopy(cfg);current.update(pack=str(pack.relative_to(ROOT)),adapter=adapter,adapter_sha256=manifest['adapter_sha256'],kind='given_factual_prefix_application_component',authorization='Recursive minimal informative experiments; four inspected component answers before choosing more fitting.')
  write_json(config_path,current);result.append({'arm':arm,'pack':str(pack.relative_to(ROOT)),'config':str(config_path.relative_to(ROOT)),'input_tokens':len(ids),'manifest_sha256':sha256(pack/'manifest.json')})
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
