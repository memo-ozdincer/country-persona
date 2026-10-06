"""Replay four direct source-question records after manual review; combine with the saved fitting checkpoint."""
import copy,json,hashlib,sys
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,write_json
from verify_two_context_country import exited

def main():
 pack=ROOT/'data/prepared/two-context-source-facts-20261006-v1';m=json.loads((pack/'manifest.json').read_text());assert not m['training_authorized_for_this_pack'] and m['eval_cases']==2
 for fn,h in m['files_sha256'].items():assert sha256(pack/fn)==h
 assert json.loads((pack/'manual-inspection.json').read_text())['manifest_sha256']==sha256(pack/'manifest.json')
 sources=json.loads((pack/'sources.json').read_text());cases=list(read_jsonl(pack/'cases.jsonl'))
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(ROOT/'runs/aurora-two-context-country-fit-20261006-v1/adapter',local_files_only=True)
 for c in cases:
  assert tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)==c['input_ids'] and sources[c['country_iso3']]['text'] in c['prompt'][1]['content']
 runs=[];resources=[];stats={}
 for mode in ['base','adapter']:
  p=ROOT/f'runs/aurora-two-context-source-facts-{mode}-20261006-v1';r=json.loads((p/'run.json').read_text());i=json.loads((p/'inspection.json').read_text());rows=list(read_jsonl(p/'transcript.jsonl'));assert r['status']=='completed' and r['optimizer_steps']==0 and i['all_outputs_read_complete'] and r['transcript_sha256']==i['transcript_sha256']==sha256(p/'transcript.jsonl') and i['criteria_sha256']==sha256(pack/'criteria.json') and exited(r['identity'])
  for c,row,review in zip(cases,rows,i['reviews'],strict=True):
   assert c['id']==row['id']==review['id'] and c['input_ids']==row['input_ids'] and tok.decode(row['output_ids'],skip_special_tokens=True)==row['output'] and hashlib.sha256(row['output'].encode()).hexdigest()==review['output_sha256'] and review['all_output_read_complete'] and not row['at_output_cap']
  if mode=='adapter':assert r['loaded_adapter_sha256']==sha256(ROOT/r['config']['adapter']/'adapter_model.safetensors')
  stats[mode]={'fact_units':dict(Counter(v['status'] for rev in i['reviews'] for v in rev['ratings'].values())),'core_error_facts_correct':sum(v['core_error_fact_correct'] for v in i['reviews']),'answers':2,'rubric_scope':'Frozen UKF2 demands2715/engagement, but valid envoy welcome also answers prompt; ambiguity preserved, no artificial model ranking.'}
  resources.append({'run':str(p.relative_to(ROOT)),'identity':r['identity'],'gpu':r['gpu'],'exited':True});runs.append((r,rows))
 for key in ['model','revision','seed','max_length','generation_max_new_tokens','chat_template_kwargs']:
  assert runs[0][0]['config'][key]==runs[1][0]['config'][key]
 assert runs[0][0]['versions']==runs[1][0]['versions'] and runs[0][0]['gpu']['name']==runs[1][0]['gpu']['name']=='NVIDIA RTX PRO 6000 Blackwell Server Edition'
 assert runs[0][0]['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py']==runs[1][0]['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py']
 receipt={'status':'pass','verified_at':datetime.now(timezone.utc).isoformat(),'new_model_answers':4,'optimizer_steps':0,'stats':stats,'resources':resources,'all_two_owned_process_identities_exited':True,'actual_generated_tokens':sum(v['generated_tokens'] for _,rs in runs for v in rs),'generation_seconds':sum(v['generation_seconds'] for _,rs in runs for v in rs),'scope':'Two exposed source-error questions; task and output scope changed. Stored hand-judgment replay, no independent validation/OOD/persona gain.','independent_review_complete':False}
 write_json(ROOT/'reports/two-context-source-facts-20261006-v1.json',receipt)
 mainpath=ROOT/'reports/two-context-country-checkpoint-20261006-v1.json';combined=copy.deepcopy(json.loads(mainpath.read_text()));combined.update(new_model_answers=46,main_new_model_answers=42,source_fact_new_model_answers=4,source_fact_diagnostic=receipt,main_replay_sha256=sha256(mainpath),source_fact_replay_sha256=sha256(ROOT/'reports/two-context-source-facts-20261006-v1.json'),resources=combined['resources']+resources,all_five_owned_process_identities_exited=True)
 combined['actual_generated_tokens']+=receipt['actual_generated_tokens'];combined['generation_seconds']+=receipt['generation_seconds']
 combined['next_decision']='Both base and trained model recover the two critical error facts directly; trained answers still lose quote/length constraints and add another unsupported source claim. This does not establish the causal mechanism, but absent local fact knowledge is insufficient as a diagnosis. Next candidate: one actual base-generated Brazil/Sudan source-fact bullet plan, hand-audited unchanged, then identical plan/source/current-note inputs to base and fresh512 writers: three calls/no fit. Preserve smaller256 and strong original checked-plan controls; do not increase fitting budget blindly. No next pack/fit/queue/sweep prepared.'
 write_json(ROOT/'reports/two-context-country-combined-20261006-v1.json',combined);print(json.dumps({'status':'pass','new_answers_total':46,'source_facts':stats,'all_five_owned_process_identities_exited':True},indent=2))

if __name__=='__main__':main()
