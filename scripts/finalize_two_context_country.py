"""Replay exact actual controls, then bind sixteen chosen-only pairs after whole-output inspection."""
import copy,json,shutil,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_jsonl,write_json,sha256,digest
from run_aurora_qwen35_smoke import identity

def main():
 draft=ROOT/'data/prepared/two-context-country-20261006-v1';dest=ROOT/'data/prepared/two-context-country-fit-20261006-v1'
 composite=ROOT/'runs/two-context-country-composite-base-20261006-v1';assert not composite.exists() and not dest.exists()
 cfgpath=ROOT/'configs/posttraining/qwen35-two-context-country-20261006-v1.json';cfg=json.loads(cfgpath.read_text())
 cases=list(read_jsonl(draft/'cases.jsonl'));targets=json.loads((draft/'preferred-targets.json').read_text())['targets']
 sources=['runs/aurora-diverse-country-base-20261006-v2','runs/aurora-diverse-country-role-base-20261006-v1','runs/aurora-two-context-country-base-20261006-v1']
 loaded=[]
 for name in sources:
  runpath=ROOT/name;r=json.loads((runpath/'run.json').read_text());i=json.loads((runpath/'inspection.json').read_text())
  assert r['status']=='completed' and r['optimizer_steps']==0 and i['all_outputs_read_complete'] and i['transcript_sha256']==sha256(runpath/'transcript.jsonl')
  for key in ['model','revision','seed','max_length','generation_max_new_tokens','chat_template_kwargs']:assert r['config'][key]==cfg[key]
  assert r['versions']==cfg['runtime_pins'] and r['gpu']['name']=='NVIDIA RTX PRO 6000 Blackwell Server Edition'
  loaded.append((runpath,r,{row['id']:row for row in read_jsonl(runpath/'transcript.jsonl')},{v['id']:v for v in i['reviews']}))
 rows=[];reviews=[];links=[]
 for c in cases:
  found=[(p,r,rs[c['id']],is_[c['id']]) for p,r,rs,is_ in loaded if c['id'] in rs and rs[c['id']]['input_ids']==c['input_ids']]
  assert len(found)==1,(c['id'],len(found))
  p,r,row,review=found[0];assert row['input_ids_digest']==c['input_ids_digest']
  rows.append(copy.deepcopy(row));reviews.append(copy.deepcopy(review))
  links.append({'id':c['id'],'run':str(p.relative_to(ROOT)),'actual_identity':r['identity'],'run_sha256':sha256(p/'run.json'),'transcript_sha256':sha256(p/'transcript.jsonl'),'inspection_sha256':sha256(p/'inspection.json'),'record_digest':digest(row),'review_digest':digest(review),'output_digest':digest(row['output'])})
 composite.mkdir(parents=True);write_jsonl(composite/'transcript.jsonl',rows)
 cr=copy.deepcopy(loaded[-1][1]);cr.update(kind='CPU exact-record provenance replay; no model call/GPU launch',identity=identity(),run_directory=str(composite),config={**cfg,'pack':str(draft.relative_to(ROOT))},outputs=26,optimizer_steps=0,pack_manifest_sha256=sha256(draft/'manifest.json'),transcript_sha256=sha256(composite/'transcript.jsonl'),actual_gpu_identities=[r['identity'] for _,r,_,_ in loaded])
 write_json(composite/'run.json',cr);write_json(composite/'actual-record-provenance.json',{'links':links,'all_records_and_reviews_unchanged':True,'new_model_calls':0,'optimizer_steps':0})
 write_json(composite/'inspection.json',{'all_outputs_read_complete':True,'transcript_sha256':sha256(composite/'transcript.jsonl'),'criteria_sha256':sha256(draft/'criteria.json'),'reviews':reviews,'reviewer':'same assistant, exact prior primitive grades retained; independent review pending','scope':'26 exact actual records:12new +14matching old/role controls; no new execution in replay'})
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True)
 oldpairs=list(read_jsonl(ROOT/'data/prepared/diverse-country-fit-20261006-v2/pairs.jsonl'));pairs=[];audits=[]
 for idx,c in enumerate(cases[:16]):
  pair={'prompt':c['prompt'],'chosen':[{'role':'assistant','content':targets[c['id']]}],'rejected':[{'role':'assistant','content':rows[idx]['output']}],'chat_template_kwargs':{'enable_thinking':False}}
  if idx<8:assert pair==oldpairs[idx]
  prefix=tok.apply_chat_template(pair['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);assert prefix==c['input_ids']
  audit={'id':c['id'],'pair_sha256':digest(pair),'prompt_ids':prefix}
  for k in ['chosen','rejected']:
   full=tok.apply_chat_template(pair['prompt']+pair[k],tokenize=True,return_dict=False,enable_thinking=False);assert full[:len(prefix)]==prefix and len(full)<=8192;audit[k+'_ids']=full[len(prefix):]
  pairs.append(pair);audits.append(audit)
 dest.mkdir(parents=True)
 for p in draft.iterdir():
  if p.name not in ['manifest.json','manual-inspection.json']:shutil.copy2(p,dest/p.name)
 write_jsonl(dest/'pairs.jsonl',pairs);write_jsonl(dest/'pair-audit.jsonl',audits)
 write_json(dest/'actual-negative-provenance.json',{'links':links[:16],'first_eight_pairs_exact':True,'all_negatives_actual_inspected_base_outputs':True,'negative_gradient_enabled':False})
 shutil.copy2(__file__,dest/'finalizer-code.py')
 write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in dest.iterdir() if p.is_file()},'training_authorized_for_this_pack':True,'training_examples':16,'eval_cases':26,'source_scope':json.loads((draft/'provenance.json').read_text())['scope']})
 hand=json.loads((draft/'manual-inspection.json').read_text());hand.update(manifest_sha256=sha256(dest/'manifest.json'),actual_negative_binding_complete=True,negative_read_continuity='12new baseline outputs fully read; eight old actual negatives retain prior complete inspection and exact pair bytes. All16 positives audited; no negative loss gradient.')
 write_json(dest/'manual-inspection.json',hand);cfg['pack']=str(dest.relative_to(ROOT));write_json(cfgpath,cfg)
 write_json(ROOT/cfg['preparation'],{'config_sha256':sha256(cfgpath),'manifest_sha256':sha256(dest/'manifest.json'),'all_selected_texts_read_complete':True,'independent_review_complete':False,'training_examples':16,'eval_cases':26,'steps':512,'source_audit_sha256':sha256(ROOT/'reports/two-context-country-source-audit-20261006-v1.json'),'actual_baseline_inspection_sha256':sha256(composite/'inspection.json')})
 print(json.dumps({'pairs':len(pairs),'cases':len(cases),'new_base_calls':12,'replayed_actual_controls':14,'initialization':'fresh zero-effect LoRA','updates':512}))

if __name__=='__main__':main()
