"""Replay seven fully inspected actual-plan calls, exact plan binding and older control grades."""
import json,sys,hashlib
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,digest,write_json
from verify_two_context_country import exited

def summary(review):
 counts=Counter(v['status'] for v in review['ratings'].values());source=Counter(v['status'] for k,v in review['ratings'].items() if k.startswith('S'));app=Counter(v['status'] for k,v in review['ratings'].items() if k.startswith('A'))
 fmt=review['format_observation'];within=next(v for k,v in fmt.items() if k.startswith('within'))
 strict=all(v['status']=='met' for v in list(review['ratings'].values())+list(review['universal_checks'].values())) and within and not fmt['at_cap']
 return {'content':dict(counts),'source':dict(source),'application':dict(app),'words':fmt['words'],'within_requested_words':within,'strict_pass':strict}

def main():
 names=['aurora-model-generated-plan-planner-20261006-v1','aurora-model-generated-plan-base-20261006-v1','aurora-model-generated-plan-adapter-20261006-v1','aurora-model-decision-plan-planner-20261006-v1','aurora-question-guided-plan-planner-20261006-v1','aurora-question-guided-plan-base-20261006-v1','aurora-question-guided-plan-adapter-20261006-v1']
 from transformers import AutoTokenizer
 adapter=ROOT/'runs/aurora-two-context-country-fit-20261006-v1/adapter';tok=AutoTokenizer.from_pretrained(adapter,local_files_only=True)
 oldpack=ROOT/'data/prepared/two-context-country-fit-20261006-v1';oldsource=json.loads((oldpack/'sources.json').read_text())['sudan']['BRA'];oldcase=next(c for c in read_jsonl(oldpack/'cases.jsonl') if c['id']=='sudan-bra-raw');oldcriteria=json.loads((oldpack/'criteria.json').read_text())
 records=[];resources=[];summaries={};tokens=0;seconds=0
 for name in names:
  p=ROOT/'runs'/name;r=json.loads((p/'run.json').read_text());i=json.loads((p/'inspection.json').read_text());pack=ROOT/r['config']['pack'];m=json.loads((pack/'manifest.json').read_text());h=json.loads((pack/'manual-inspection.json').read_text());cases=list(read_jsonl(pack/'cases.jsonl'));rows=list(read_jsonl(p/'transcript.jsonl'))
  assert r['status']=='completed' and r['optimizer_steps']==0 and i['all_outputs_read_complete'] and len(rows)==len(cases)==len(i['reviews'])==1 and exited(r['identity'])
  assert r['pack_manifest_sha256']==h['manifest_sha256']==sha256(pack/'manifest.json') and h['all_selected_texts_read_complete']
  for fn,expected in m['files_sha256'].items():assert sha256(pack/fn)==expected
  assert r['transcript_sha256']==i['transcript_sha256']==sha256(p/'transcript.jsonl') and i['criteria_sha256']==sha256(pack/'criteria.json') and json.loads((pack/'criteria.json').read_text())==oldcriteria
  for path,expected in r['source_code_sha256'].items():assert sha256(p/Path(path).name)==expected
  assert json.loads((pack/'source.json').read_text())==oldsource
  c=cases[0];row=rows[0];rev=i['reviews'][0]
  assert c['id']==row['id']==rev['id'] and c['input_ids']==row['input_ids'] and tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)==c['input_ids'] and digest(c['input_ids'])==c['input_ids_digest']
  assert oldsource['text'] in c['prompt'][1]['content'] and tok.decode(row['output_ids'],skip_special_tokens=True)==row['output'] and hashlib.sha256(row['output'].encode()).hexdigest()==rev['output_sha256'] and rev['all_output_read_complete'] and not row['at_output_cap']
  assert r['versions']==r['config']['runtime_pins'] and r['gpu']['name']=='NVIDIA RTX PRO 6000 Blackwell Server Edition'
  if r['mode']=='adapter':assert r['loaded_adapter_sha256']==sha256(adapter/'adapter_model.safetensors')
  if r.get('previous_inspected_run'):
   prev=Path(r['previous_inspected_run']['run']);assert sha256(prev/'inspection.json')==r['previous_inspected_run']['inspection_sha256']
  summaries[name]=summary(rev);resources.append({'run':str(p.relative_to(ROOT)),'identity':r['identity'],'gpu':r['gpu'],'exited':True});records.append((r,c,row,pack));tokens+=row['generated_tokens'];seconds+=row['generation_seconds']
 # Both writer arms see the exact same actual, unedited planner output and realization contract.
 for planner_index,base_index,adapter_index in [(0,1,2),(4,5,6)]:
  planner=records[planner_index];base=records[base_index];trained=records[adapter_index];assert base[1]['input_ids']==trained[1]['input_ids'] and base[3]==trained[3]
  provenance=json.loads((base[3]/'provenance.json').read_text());assert not provenance['actual_plan_edited'] and provenance['planner_output_digest']==digest(planner[2]['output'])
  assert base[1]['prompt'][0]==oldcase['prompt'][0] and base[1]['prompt'][1]['content']==oldcase['prompt'][1]['content']+provenance['plan_suffix'] and planner[2]['output'] in provenance['plan_suffix']
  for suffix,key in [('run.json','planner_run_sha256'),('transcript.jsonl','planner_transcript_sha256'),('inspection.json','planner_inspection_sha256')]:assert sha256(ROOT/provenance['planner_run']/suffix)==provenance[key]
  for k in ['model','revision','seed','max_length','generation_max_new_tokens','chat_template_kwargs']:assert base[0]['config'][k]==trained[0]['config'][k]
 assert 'Hypothetical note Y' not in records[0][1]['prompt'][1]['content']
 assert not (ROOT/'data/prepared/model-decision-plan-writer-20261006-v1').exists()
 # Replay original actual before/checked-plan controls without altering their primitive grades.
 historical={};links=[]
 for model,name in [('base','aurora-two-context-country-base-20261006-v1'),('fresh512','aurora-two-context-country-fit-20261006-v1')]:
  p=ROOT/'runs'/name;r=json.loads((p/'run.json').read_text());i=json.loads((p/'inspection.json').read_text());assert i['all_outputs_read_complete'] and i['transcript_sha256']==sha256(p/'transcript.jsonl')
  for id in ['sudan-bra-raw','sudan-bra-plan']:
   row=next(v for v in read_jsonl(p/'transcript.jsonl') if v['id']==id);rev=next(v for v in i['reviews'] if v['id']==id);historical[model+'_'+id]=summary(rev);links.append({'run':str(p.relative_to(ROOT)),'id':id,'actual_identity':r['identity'],'record_digest':digest(row),'review_digest':digest(rev),'transcript_sha256':sha256(p/'transcript.jsonl'),'inspection_sha256':sha256(p/'inspection.json')})
 receipt={'status':'pass','verified_at':datetime.now(timezone.utc).isoformat(),'new_model_outputs':7,'new_optimizer_steps':0,'cumulative_qwen35_steps':2014,'reference_qwen25_steps':582,'all_seven_complete_outputs_read':True,'all_seven_owned_gpu_process_identities_exited':True,'all_new_outputs_uncapped':True,'resources':resources,'summaries':summaries,'historical_controls':historical,'historical_control_provenance':links,'actual_generated_tokens':tokens,'generation_seconds':seconds,'independent_review_complete':False,'scope':'Same-assistant exposed Brazil/Sudan development. More questions, input length, plan budget, information and realization contract change together. No causal component isolation, native prediction/persona/multi-agent/strongOOD gain. Criteria/oldgrades unchanged. Actual plans unedited; failed full planner stopped before writers.','next_decision':'Question-guided teacher can supply most requested facts/decisions; raw-task-trained writer still flips known negation and drops two given steps. Next candidate after full hand audit and a separately frozen family: plan-input realization SFT with unchanged original eight preferred target texts, freshzeroLoRA and matched256update/32presentations budget versus saved raw8. Retain current actual QAplan and stronger checked-plan/base controls as exposed development. No next pack/fit/queue/sweep prepared.'}
 write_json(ROOT/'reports/actual-plan-checkpoint-20261006-v1.json',receipt)
 print(json.dumps({k:receipt[k] for k in ['status','new_model_outputs','new_optimizer_steps','summaries','historical_controls']},indent=2))

if __name__=='__main__':main()
