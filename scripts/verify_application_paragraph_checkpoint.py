"""Replay identical component inputs, real launches/tokens/weights and manual reviews."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,digest,write_json
from country_persona.reasoning_output import split_native_output

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 from transformers import AutoTokenizer
 original=ROOT/'data/prepared/repaired-state-20261006-v1';oldcriteria=json.loads((original/'criteria.json').read_text())
 oldcase=next(c for c in read_jsonl(original/'cases.jsonl') if c['id']=='wps-partial-repair')
 common=None;inputs=None;summary={};allruns={};totaltokens=0;totalseconds=0.
 for arm in ['base','parent','combined','chosen']:
  packarm='parent' if arm=='base' else arm
  cfgpath=ROOT/('configs/posttraining/qwen35-application-paragraph-20261006-v2-'+packarm+'.json');cfg=json.loads(cfgpath.read_text())
  pack=ROOT/cfg['pack'];manifest=json.loads((pack/'manifest.json').read_text());hand=json.loads((pack/'manual-inspection.json').read_text())
  assert manifest['training_authorized_for_this_pack'] is False and hand['all_selected_texts_read_complete'] and hand['manifest_sha256']==sha256(pack/'manifest.json')
  for name,h in manifest['files_sha256'].items():assert sha256(pack/name)==h
  if common is None:common=manifest['files_sha256']
  assert common==manifest['files_sha256']
  cases=list(read_jsonl(pack/'cases.jsonl'));assert len(cases)==1;case=cases[0]
  proof=json.loads((pack/'prompt-proof.json').read_text());criteria=json.loads((pack/'criteria.json').read_text())
  assert sha256(ROOT/proof['original_cases_file'])==proof['original_cases_sha256'] and digest(oldcase['prompt'])==proof['original_request_digest']
  assert sha256(ROOT/proof['original_pairs_file'])==proof['original_pairs_sha256']
  pairs=list(read_jsonl(ROOT/proof['original_pairs_file']))
  prefix=pairs[0]['chosen'][0]['content'].rsplit('\n\n',1)[0]
  assert prefix==proof['factual_prefix']==(pack/'factual-prefix.txt').read_text() and digest(prefix)==proof['factual_prefix_digest']
  assert pairs[2]['chosen'][0]['content'].rsplit('\n\n',1)[0]==prefix
  assert case['prompt'][:-1]==oldcase['prompt'][:-1] and case['prompt'][-1]['role']==oldcase['prompt'][-1]['role']
  assert case['prompt'][-1]['content']==oldcase['prompt'][-1]['content']+proof['appended_footer'] and digest(case['prompt'])==proof['new_prompt_digest']
  assert criteria['core_units']==oldcriteria['partial_state_units'] and criteria['universal_checks']==oldcriteria['universal_checks']
  source=json.loads((pack/'wps-statements.json').read_text());raw=ROOT/'data/raw/source-application-grounding-20261003-v1'
  record=(raw/'record-8514.txt').read_text()
  for s in source.values():assert record[s['start']:s['end']].strip()==s['text'] and digest(s['text'])==s['text_digest'] and s['text'] in case['prompt'][-1]['content']
  for fn,h in json.loads((pack/'source-proof.json').read_text())['wps_raw_files_sha256'].items():assert sha256(raw/fn)==h
  tok=AutoTokenizer.from_pretrained(ROOT/cfg['adapter'],local_files_only=True)
  ids=tok.apply_chat_template(case['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,**cfg['chat_template_kwargs'])
  assert ids==case['input_ids'] and digest(ids)==case['input_ids_digest'] and len(ids)+2048<=8192
  d=ROOT/('runs/aurora-application-paragraph-'+arm+'-20261006-v2');r=json.loads((d/'run.json').read_text());review=json.loads((d/'inspection.json').read_text());rows=list(read_jsonl(d/'transcript.jsonl'))
  assert r['status']=='completed' and r['optimizer_steps']==0 and r['outputs']==len(rows)==1
  assert r['config_sha256']==sha256(cfgpath) and r['pack_manifest_sha256']==sha256(pack/'manifest.json') and r['manual_inspection_sha256']==sha256(pack/'manual-inspection.json')
  assert r['versions']==cfg['runtime_pins'] and r['gpu']['name']=='NVIDIA RTX PRO 6000 Blackwell Server Edition'
  for filename,h in r['source_code_sha256'].items():assert sha256(d/Path(filename).name)==h
  if arm=='base':assert r['mode']=='base' and 'loaded_adapter_sha256' not in r
  else:
   assert r['mode']=='adapter' and r['loaded_adapter_sha256']==cfg['adapter_sha256']==manifest['adapter_sha256']==sha256(ROOT/cfg['adapter']/'adapter_model.safetensors')
   assert manifest['adapter_config_sha256']==sha256(ROOT/cfg['adapter']/'adapter_config.json')
  if r['previous_inspected_run']:
   previous=ROOT/r['previous_inspected_run']['run'];assert r['previous_inspected_run']['inspection_sha256']==sha256(previous/'inspection.json')
  row=rows[0];assert row['id']==case['id'] and row['input_ids']==ids and row['input_ids_digest']==digest(ids)
  markers=manifest['thinking_marker_ids'];assert all(tok.convert_tokens_to_ids(k)==v for k,v in markers.items())
  split=split_native_output(row['output_ids'],thinking=False,open_id=markers['<think>'],close_id=markers['</think>'],eos_id=tok.eos_token_id)
  assert tok.decode(split['public_ids'],skip_special_tokens=True)==row['output'] and row['reasoning']=='' and row['protocol_status']=='public_answer'
  assert row['generated_tokens']==len(row['output_ids']) and row['at_output_cap']==(len(row['output_ids'])==2048)
  assert review['all_outputs_read_complete'] and review['all_reasoning_read_complete'] and review['transcript_sha256']==r['transcript_sha256']==sha256(d/'transcript.jsonl') and review['criteria_sha256']==sha256(pack/'criteria.json')
  assert len(review['reviews'])==1;v=review['reviews'][0]
  assert v['id']==row['id'] and v['all_output_read_complete'] and v['output_sha256']==hashlib.sha256(row['output'].encode()).hexdigest()
  for ratings,key in [('core_ratings','core_units'),('additional_ratings','additional_units'),('universal_checks','universal_checks')]:
   assert set(v[ratings])==set(criteria[key]) and all(x['status'] in ['met','unmet','unratable'] and x['reason'].strip() for x in v[ratings].values())
  core=list(v['core_ratings'].values());additional=list(v['additional_ratings'].values());guards=list(v['universal_checks'].values())
  assert v['format_observation']['words']==len(row['output'].split()) and v['format_observation']['within100words']==(len(row['output'].split())<=100)
  summary[arm]={'core_met':sum(x['status']=='met' for x in core),'core_unratable':sum(x['status']=='unratable' for x in core),'core_units':4,
   'additional_met':sum(x['status']=='met' for x in additional),'additional_unratable':sum(x['status']=='unratable' for x in additional),'additional_units':2,
   'words':len(row['output'].split()),'within100words':len(row['output'].split())<=100,'at_cap':row['at_output_cap'],
   'strict_component_pass':not row['at_output_cap'] and len(row['output'].split())<=100 and all(x['status']=='met' for x in core+additional+guards)}
  if inputs is None:inputs=row['input_ids']
  assert row['input_ids']==inputs
  allruns[arm]=r;totaltokens+=row['generated_tokens'];totalseconds+=row['generation_seconds']
 first=allruns['base']
 for r in allruns.values():
  assert r['versions']==first['versions'] and r['gpu']['name']==first['gpu']['name'] and r['source_code_sha256']==first['source_code_sha256']
  for k in ['model','revision','seed','max_length','generation_max_new_tokens','chat_template_kwargs']:assert r['config'][k]==first['config'][k]
 failed=ROOT/'runs/aurora-application-paragraph-base-20261006-v1';failure=json.loads((failed/'failure.json').read_text());audit=json.loads((failed/'failure-audit.json').read_text())
 assert failure['status']=='failed' and failure['optimizer_steps']==0 and audit['completed_generation_not_saved']==1 and audit['inspectable_public_answers']==0 and not (failed/'transcript.jsonl').exists()
 write_json(a.output,{'status':'same_component_sources_prefix_requests_tokens_real_four_weight_runs_and_manual_grades_replayed',
  'new_model_generations_completed':5,'new_inspectable_public_answers':4,'failed_recording_generation_lost':1,'new_optimizer_steps':0,'cumulative_aurora_qwen35_steps':702,'reference_qwen25_steps':582,
  'input_tokens_each':len(inputs),'stored_generated_tokens':totaltokens,'stored_generation_seconds':totalseconds,'lost_generation_tokens':None,'lost_generation_seconds':None,'summary':summary,
  'scope':first['scope'],'comparison_scope':'Identical component inputs across four weights; differs from original full task by supplied factual prefix, application-only request and100word limit. Not an isolated composition effect, independent source parsing, full-task, sealed OOD or persona/multi-agent gain.','independent_review_complete':False})
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
