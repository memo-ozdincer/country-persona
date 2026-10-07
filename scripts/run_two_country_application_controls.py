"""Owned six-case two-country application comparison; no optimization."""
import argparse,json,os,sys,shutil,importlib.metadata
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,write_json,write_jsonl
from run_aurora_qwen35_smoke import identity,current_gpu,verify_model,generate_controls

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=['base','adapter'],required=True);p.add_argument('--config',type=Path,required=True);p.add_argument('--gpu-uuid',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--previous-inspected-run',type=Path);a=p.parse_args();os.chdir(ROOT)
 cfg=json.loads(a.config.read_text());pack=ROOT/cfg['pack'];manifest=json.loads((pack/'manifest.json').read_text());hand=json.loads((pack/'manual-inspection.json').read_text());cases=list(read_jsonl(pack/'cases.jsonl'))
 assert not manifest['training_authorized_for_this_pack'] and hand['all_selected_texts_read_complete'] and hand['manifest_sha256']==sha256(pack/'manifest.json')
 for fn,h in manifest['files_sha256'].items():assert sha256(pack/fn)==h
 assert len(cases)==cfg['eval_cases']==6 and cfg['max_steps']==0 and cfg['training_examples']==0 and all({'id','country_iso3','prompt','input_ids'}<=set(c) for c in cases)
 assert not a.output.exists() and not os.environ.get('SLURM_JOB_ID') and os.environ.get('CUDA_VISIBLE_DEVICES')==a.gpu_uuid
 previous=None
 if a.previous_inspected_run:
  rr=json.loads((a.previous_inspected_run/'run.json').read_text());ii=json.loads((a.previous_inspected_run/'inspection.json').read_text());assert rr['status']=='completed' and ii['all_outputs_read_complete'] and ii['transcript_sha256']==sha256(a.previous_inspected_run/'transcript.jsonl');previous={'run':str(a.previous_inspected_run),'inspection_sha256':sha256(a.previous_inspected_run/'inspection.json')}
 gpu=current_gpu(a.gpu_uuid);a.output.mkdir(parents=True)
 sources=[Path(__file__),ROOT/'scripts/run_aurora_qwen35_smoke.py',ROOT/'src/country_persona/io.py']
 r={'status':'initializing','mode':a.mode,'identity':identity(),'gpu':gpu,'config':cfg,'config_sha256':sha256(a.config),'pack_manifest_sha256':sha256(pack/'manifest.json'),'manual_inspection_sha256':sha256(pack/'manual-inspection.json'),'source_code_sha256':{str(f.relative_to(ROOT)):sha256(f) for f in sources},'previous_inspected_run':previous,'run_directory':str(a.output.resolve()),'optimizer_steps':0,'created_at':datetime.now(timezone.utc).isoformat(),'scope':manifest['source_scope'],'independent_review_complete':False}
 write_json(a.output/'launch.json',r)
 for f in sources:shutil.copy2(f,a.output/f.name)
 try:
  import torch
  from transformers import AutoTokenizer,Qwen3_5ForCausalLM
  from peft import PeftModel
  r['versions']={k:importlib.metadata.version(k) for k in cfg['runtime_pins']};assert r['versions']==cfg['runtime_pins'] and torch.cuda.device_count()==1 and torch.cuda.is_bf16_supported();torch.cuda.set_device(0);torch.manual_seed(cfg['seed'])
  r['model_verification']=verify_model(cfg);tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True)
  for c in cases:assert tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,**cfg['chat_template_kwargs'])==c['input_ids'] and len(c['input_ids'])+2048<=8192
  model,loading=Qwen3_5ForCausalLM.from_pretrained(cfg['model_path'],local_files_only=True,dtype=torch.bfloat16,attn_implementation='sdpa',output_loading_info=True);assert not loading['missing_keys'] and not loading['mismatched_keys'] and not loading['error_msgs'];r['text_model_loading']={k:sorted(v) if isinstance(v,set) else v for k,v in loading.items()};model.to('cuda:0')
  if a.mode=='adapter':
   adapter=ROOT/cfg['adapter'];assert sha256(adapter/'adapter_model.safetensors')==cfg['adapter_sha256'] and sha256(adapter/'adapter_config.json')==cfg['adapter_config_sha256'];model=PeftModel.from_pretrained(model,str(adapter),is_trainable=False);r['loaded_adapter_sha256']=cfg['adapter_sha256']
  r['status']='generating';write_json(a.output/'run.json',r);rows=[]
  for c in cases:
   row=generate_controls(model,tok,[c],[c],cfg)[0];row.update(family=c['family'],condition=c['condition'],scope=manifest['source_scope']);rows.append(row);write_jsonl(a.output/'transcript.jsonl',rows);print(json.dumps({'id':row['id'],'tokens':row['generated_tokens'],'cap':row['at_output_cap']}),flush=True)
  r.update(status='completed',outputs=len(rows),transcript_sha256=sha256(a.output/'transcript.jsonl'),completed_at=datetime.now(timezone.utc).isoformat());write_json(a.output/'run.json',r)
 except BaseException as e:
  r.update(status='failed',error=type(e).__name__+': '+str(e),failed_at=datetime.now(timezone.utc).isoformat());write_json(a.output/'run.json',r);write_json(a.output/'failure.json',r);raise
if __name__=='__main__':main()
