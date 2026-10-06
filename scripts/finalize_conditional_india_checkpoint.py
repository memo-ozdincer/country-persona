"""Bind new SFT rows to actual inspected parent negatives in a fresh fitting pack."""
import copy,json,shutil,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import digest,read_jsonl,sha256,write_json,write_jsonl
def main():
 draft=ROOT/'data/prepared/conditional-india-20261006-v2';dest=ROOT/'data/prepared/conditional-india-fit-20261006-v2';assert not dest.exists()
 dm=json.loads((draft/'manifest.json').read_text());dh=json.loads((draft/'manual-inspection.json').read_text());assert not dm['training_authorized_for_this_pack'] and dh['all_selected_texts_read_complete'] and dh['manifest_sha256']==sha256(draft/'manifest.json')
 for name,h in dm['files_sha256'].items():assert sha256(draft/name)==h
 cfgpath=ROOT/'configs/posttraining/qwen35-conditional-india-20261006-v2.json';cfg=json.loads(cfgpath.read_text());cases=list(read_jsonl(draft/'cases.jsonl'));pairs=list(read_jsonl(draft/'draft-pairs.jsonl'));assert len(cases)==17 and len(pairs)==6
 links=[]
 for index,directory,caseid in [(4,'runs/aurora-two-episode-parent-replay-20261006-v1','sanctions-ind-raw'),(5,'runs/aurora-conditional-india-parent-20261006-v2','sanctions-ind-authority-raw')]:
  d=ROOT/directory;r=json.loads((d/'run.json').read_text());inspection=json.loads((d/'inspection.json').read_text());rows=list(read_jsonl(d/'transcript.jsonl'));assert r['status'] in ('completed','completed_cpu_replay') and inspection['all_outputs_read_complete'] and r['transcript_sha256']==inspection['transcript_sha256']==sha256(d/'transcript.jsonl')
  row=next(x for x in rows if x['id']==caseid);case=next(x for x in cases if x['id']==caseid);assert row['input_ids']==case['input_ids']
  if r['status']=='completed_cpu_replay':origin=ROOT/r['source_links'][next(j for j,x in enumerate(rows) if x['id']==caseid)]['run'];actual=json.loads((origin/'run.json').read_text())
  else:origin=d;actual=r
  loaded=actual['loaded_adapter_sha256'] if actual['mode']!='fit' else actual['serialization_checks']['files_sha256']['adapter_model.safetensors'];assert loaded==cfg['starting_adapter_sha256']
  actualrow=next(x for x in read_jsonl(origin/'transcript.jsonl') if x['id']==caseid);assert row['output']==actualrow['output'] and row['output_ids']==actualrow['output_ids']
  pairs[index]['rejected']=[{'role':'assistant','content':row['output']}];links.append({'pair_index':index,'id':caseid,'run':str(origin.relative_to(ROOT)),'run_sha256':sha256(origin/'run.json'),'transcript_sha256':sha256(origin/'transcript.jsonl'),'inspection_sha256':sha256(origin/'inspection.json'),'actual_identity':actual['identity']})
 dest.mkdir(parents=True)
 for f in draft.iterdir():
  if f.name not in ('manifest.json','manual-inspection.json','draft-pairs.jsonl'):assert f.is_file();shutil.copy2(f,dest/f.name)
 write_jsonl(dest/'pairs.jsonl',pairs)
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True);prov=json.loads((draft/'data-provenance.json').read_text());audits=[]
 for pair,case_index,id in zip(pairs,prov['fit_pair_case_indices'],prov['fit_pair_ids'],strict=True):
  assert pair['prompt']==cases[case_index]['prompt']
  prefix=tok.apply_chat_template(pair['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);assert prefix==cases[case_index]['input_ids'];audit={'id':id,'pair_sha256':digest(pair),'prompt_ids':prefix}
  for k in ('chosen','rejected'):
   ids=tok.apply_chat_template(pair['prompt']+pair[k],tokenize=True,return_dict=False,enable_thinking=False);assert ids[:len(prefix)]==prefix and len(ids)<=8192;audit[k+'_ids']=ids[len(prefix):]
  audits.append(audit)
 assert pairs[:4]==list(read_jsonl(ROOT/prov['old_pack']/'pairs.jsonl'))
 write_jsonl(dest/'pair-audit.jsonl',audits);write_json(dest/'actual-negative-provenance.json',{'links':links,'draft_manifest_sha256':sha256(draft/'manifest.json'),'all_new_negatives_actual_parent_outputs':True,'negative_gradient_enabled':False,'scope':'Native chosen-only SFT retains rejected/reference forward compute; negative quality is not preference-supervision gain.'});shutil.copy2(__file__,dest/'finalizer-code.py')
 write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{f.name:sha256(f) for f in dest.iterdir() if f.is_file()},'training_authorized_for_this_pack':True,'training_examples':6,'eval_cases':17,'source_scope':dm['source_scope']})
 write_json(dest/'manual-inspection.json',{**dh,'reviewed_at':datetime.now(timezone.utc).isoformat(),'manifest_sha256':sha256(dest/'manifest.json'),'actual_negative_binding_complete':True,'negative_continuity':'New known-raw parent199word output read complete at control review; retained unknown-raw parent output previously hand-read and byte-verified, full text reread before fit. All preferred texts unchanged from audited draft.'})
 cfg.update(pack=str(dest.relative_to(ROOT)),baseline_run='runs/aurora-conditional-india-parent-replay-20261006-v2',preparation='reports/conditional-india-preparation-20261006-v2.json');write_json(cfgpath,cfg)
 print(json.dumps({'status':'six_actual_pairs_native_tokens_masks_audited_and_frozen','pairs':6,'cases':17,'manifest_sha256':sha256(dest/'manifest.json'),'config_sha256':sha256(cfgpath)}))
if __name__=='__main__':main()
