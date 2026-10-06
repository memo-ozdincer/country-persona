"""Replay frozen sources, actual controls, native token pairs, saved fit and stored human-readable judgments."""
import json,sys
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import sha256,digest,read_jsonl,write_json

def exited(identity):
 p=Path('/proc')/str(identity['pid'])/'stat'
 if not p.exists():return True
 fields=p.read_text().rsplit(')',1)[1].split()
 return int(fields[19])!=identity['process_start_ticks']

def summarize(rows,reviews):
 result={}
 for group,ids in {'fitting_old':[r['id'] for r in rows[:8]],'fitting_new':[r['id'] for r in rows[8:16]],'partial':[r['id'] for r in rows[16:18]],'somalia_raw':[r['id'] for r in rows if r['family']=='somalia' and r['id'].endswith('raw')],'somalia_plan':[r['id'] for r in rows if r['family']=='somalia' and r['id'].endswith('plan')],'sudan_raw':[r['id'] for r in rows if r['family']=='sudan' and r['id'].endswith('raw')],'sudan_plan':[r['id'] for r in rows if r['family']=='sudan' and r['id'].endswith('plan')]}.items():
  subset=[v for v in reviews if v['id'] in ids];statuses=Counter(v['status'] for r in subset for v in r['ratings'].values());checks=Counter(v['status'] for r in subset for v in r['universal_checks'].values())
  strict=sum(all(v['status']=='met' for v in list(r['ratings'].values())+list(r['universal_checks'].values())) and r['format_observation']['within300words'] and not r['format_observation']['at_cap'] for r in subset)
  result[group]={'answers':len(ids),'content':dict(statuses),'checks':dict(checks),'strict_passes':strict,'denominator':sum(statuses.values())}
 return result

def main():
 cfgp=ROOT/'configs/posttraining/qwen35-two-context-country-20261006-v1.json';cfg=json.loads(cfgp.read_text());pack=ROOT/cfg['pack']
 m=json.loads((pack/'manifest.json').read_text());assert m['training_examples']==16 and m['eval_cases']==26 and m['training_authorized_for_this_pack']
 for fn,h in m['files_sha256'].items():assert sha256(pack/fn)==h
 assert json.loads((pack/'manual-inspection.json').read_text())['manifest_sha256']==sha256(pack/'manifest.json')
 cases=list(read_jsonl(pack/'cases.jsonl'));pairs=list(read_jsonl(pack/'pairs.jsonl'));audits=list(read_jsonl(pack/'pair-audit.jsonl'))
 assert all('CHECKED PLAN' not in c['prompt'][1]['content'] for c in cases[:16])
 old=ROOT/'data/prepared/diverse-country-fit-20261006-v2';oldpairs=list(read_jsonl(old/'pairs.jsonl'));assert pairs[:8]==oldpairs
 target_audit=ROOT/'reports/two-context-country-target-audit-20261006-v1.json';ta=json.loads(target_audit.read_text());assert ta['all_targets_read_complete'] and len(ta['reviews'])==16 and ta['preferred_targets_sha256']==sha256(pack/'preferred-targets.json')
 for i,pair in enumerate(pairs):assert digest(pair)==audits[i]['pair_sha256'] and pair['prompt']==cases[i]['prompt']
 sources=json.loads((pack/'sources.json').read_text())
 for c in cases:assert sources[c['family']][c['country_iso3']]['text'] in c['prompt'][1]['content']
 from transformers import AutoTokenizer
 # Saved tokenizer is included in the handoff; base weights are deliberately excluded.
 tok=AutoTokenizer.from_pretrained(ROOT/'runs/aurora-two-context-country-fit-20261006-v1/adapter',local_files_only=True)
 for c in cases:
  ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,**cfg['chat_template_kwargs']);assert ids==c['input_ids'] and digest(ids)==c['input_ids_digest']
 for pair,audit in zip(pairs,audits,strict=True):
  for k in ['chosen','rejected']:
   ids=tok.apply_chat_template(pair['prompt']+pair[k],tokenize=True,return_dict=False,**cfg['chat_template_kwargs']);assert ids==audit['prompt_ids']+audit[k+'_ids']
 composite=ROOT/cfg['baseline_run'];links=json.loads((composite/'actual-record-provenance.json').read_text())['links'];before=list(read_jsonl(composite/'transcript.jsonl'))
 for row,link in zip(before,links,strict=True):
  p=ROOT/link['run'];actual=next(r for r in read_jsonl(p/'transcript.jsonl') if r['id']==row['id']);ir=json.loads((p/'inspection.json').read_text());rv=next(r for r in ir['reviews'] if r['id']==row['id']);assert row==actual and digest(row)==link['record_digest'] and digest(rv)==link['review_digest']
  for fn in ['run','inspection']:assert sha256(p/(fn+'.json'))==link[fn+'_sha256']
  assert sha256(p/'transcript.jsonl')==link['transcript_sha256']
 paths=[ROOT/'runs/aurora-two-context-country-base-20261006-v1',ROOT/'runs/aurora-two-context-country-parent-20261006-v1',ROOT/'runs/aurora-two-context-country-fit-20261006-v1']
 resources=[];records=[]
 for p in paths:
  r=json.loads((p/'run.json').read_text());i=json.loads((p/'inspection.json').read_text());rows=list(read_jsonl(p/'transcript.jsonl'));localcases=list(read_jsonl(ROOT/r['config']['pack']/'cases.jsonl'));assert r['status']=='completed' and r['versions']==cfg['runtime_pins'] and r['gpu']['name']=='NVIDIA RTX PRO 6000 Blackwell Server Edition'
  assert r['transcript_sha256']==i['transcript_sha256']==sha256(p/'transcript.jsonl') and i['all_outputs_read_complete'] and len(rows)==len(i['reviews'])==len(localcases)
  for c,row,rev in zip(localcases,rows,i['reviews'],strict=True):
   assert c['id']==row['id']==rev['id'] and c['input_ids']==row['input_ids'];assert tok.decode(row['output_ids'],skip_special_tokens=True)==row['output'] and sha256_text(row['output'])==rev['output_sha256'] and rev['all_output_read_complete']
  assert exited(r['identity']);resources.append({'run':str(p.relative_to(ROOT)),'identity':r['identity'],'gpu':r['gpu'],'exited':True});records.append((r,i,rows))
 fit,review,after=records[-1];assert fit['optimizer_steps']==512 and fit['optimization_checks']['all_ranks_participated'] and fit['optimization_checks']['all_ranks_same_final_adapter']
 assert fit['optimization_checks']['rank_checks'][0]['steps']==512 and all(v==32 for v in fit['optimization_checks']['rank_checks'][0]['pair_presentations'].values())
 assert fit['initialization_checks']['all_B_tensors_zero'] and fit['initialization_checks']['base_initial_adapter_logits_exact']
 assert all(g['rejected_logit_gradient_zero'] and g['chosen_completion_logit_gradient_nonzero'] and g['prompt_padding_and_final_logit_gradient_zero'] for g in fit['actual_objective_guard']['native_logit_gradient_checks'])
 assert fit['method']['reference_tensor_digest_before']==fit['method']['reference_tensor_digest_after'] and not fit['method']['preference_gradient_enabled']
 for fn,h in fit['serialization_checks']['files_sha256'].items():assert sha256(paths[-1]/'adapter'/fn)==h
 assert [r['input_ids'] for r in before]==[r['input_ids'] for r in after]
 bi=json.loads((composite/'inspection.json').read_text());groups={'base':summarize(before,bi['reviews']),'fresh512':summarize(after,review['reviews'])}
 pi=records[1][1];parentcounts=Counter(v['status'] for r in pi['reviews'] for v in r['ratings'].values())
 receipt={'status':'pass','verified_at':datetime.now(timezone.utc).isoformat(),'config_sha256':sha256(cfgp),'pack_manifest_sha256':sha256(pack/'manifest.json'),'all_three_owned_process_identities_exited':True,'resources':resources,'new_model_answers':sum(len(rs) for _,_,rs in records),'new_optimizer_steps':512,'cumulative_qwen35_steps':2014,'reference_qwen25_steps':582,'groups':groups,'parent256_sudan_content':dict(parentcounts),'actual_generated_tokens':sum(v['generated_tokens'] for _,_,rs in records for v in rs),'generation_seconds':sum(v['generation_seconds'] for _,_,rs in records for v in rs),'training_seconds':fit['training_seconds'],'peak_allocated_gpu_gib':fit['peak_allocated_gpu_gib'],'optimization_checks':fit['optimization_checks'],'serialization_checks':fit['serialization_checks'],'independent_review_complete':False,'scope':'Software/provenance/stored-annotation replay, not independent semantic validation. All42 new answers read;14 old actual controls/grades replay unchanged. Two contexts/country still supplied source, genre overlap and correlated criteria.'}
 receipt['target_audit_sha256']=sha256(target_audit);receipt['source_audit_sha256']=sha256(ROOT/'reports/two-context-country-source-audit-20261006-v1.json')
 write_json(ROOT/'reports/two-context-country-checkpoint-20261006-v1.json',receipt);print(json.dumps({k:receipt[k] for k in ['status','new_model_answers','new_optimizer_steps','groups','parent256_sudan_content']},indent=2))

def sha256_text(text):
 import hashlib
 return hashlib.sha256(text.encode()).hexdigest()

if __name__=='__main__':main()
