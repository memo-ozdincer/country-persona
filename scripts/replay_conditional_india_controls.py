"""Join twelve retained real answers and five inspected India/Haiti controls; zero new calls."""
import argparse,copy,json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,write_json,write_jsonl
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--arm',choices=['base','parent','chosen'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 assert not a.output.exists();cfg=json.loads((ROOT/'configs/posttraining/qwen35-conditional-india-20261006-v2.json').read_text());pack=ROOT/cfg['pack'];cases=list(read_jsonl(pack/'cases.jsonl'));assert len(cases)==17
 old={'base':'runs/aurora-minimal-endorsement-base-replay-20261006-v1','parent':'runs/aurora-minimal-endorsement-parent-replay-20261006-v1','chosen':'runs/aurora-minimal-endorsement-chosen-replay-20261006-v1'}[a.arm]
 extra='runs/aurora-conditional-india-'+a.arm+'-20261006-v2';records={};rows=[];reviews=[];links=[]
 expected_weight=cfg['starting_adapter_sha256'] if a.arm=='parent' else json.loads((ROOT/cfg['comparison_chosen_run']/'run.json').read_text())['serialization_checks']['files_sha256']['adapter_model.safetensors'] if a.arm=='chosen' else None
 for directory in [old,extra]:
  d=ROOT/directory;r=json.loads((d/'run.json').read_text());i=json.loads((d/'inspection.json').read_text());rr=list(read_jsonl(d/'transcript.jsonl'))
  assert r['status'] in ['completed','completed_cpu_replay'] and i['all_outputs_read_complete'] and i['transcript_sha256']==r['transcript_sha256']==sha256(d/'transcript.jsonl');records[directory]=(r,i,rr)
 for index,c in enumerate(cases):
  directory=old if index<12 else extra;r,i,rr=records[directory];row=next(x for x in rr if x['id']==c['id']);review=next(x for x in i['reviews'] if x['id']==c['id']);assert row['input_ids']==c['input_ids'] and review['all_output_read_complete']
  if r['status']=='completed_cpu_replay':
   link=r['source_links'][next(j for j,x in enumerate(rr) if x['id']==c['id'])];source=link['run'];origin=ROOT/source;actual=json.loads((origin/'run.json').read_text())
   for name in ['run','transcript','inspection']:assert sha256(origin/(name+('.jsonl' if name=='transcript' else '.json')))==link[name+'_sha256']
  else:source=directory;origin=ROOT/source;actual=r
  actualrow=next(x for x in read_jsonl(origin/'transcript.jsonl') if x['id']==c['id']);assert actualrow['input_ids']==row['input_ids'] and actualrow['output_ids']==row['output_ids'] and actualrow['output']==row['output']
  assert actual['versions']==cfg['runtime_pins'] and actual['gpu']['name']=='NVIDIA RTX PRO 6000 Blackwell Server Edition'
  for key in ['model','revision','max_length','generation_max_new_tokens','chat_template_kwargs']:assert actual['config'][key]==cfg[key]
  assert actual['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py']==sha256(ROOT/'scripts/run_aurora_qwen35_smoke.py')
  if a.arm=='base':assert actual['mode']=='base'
  else:
   loaded=actual['serialization_checks']['files_sha256']['adapter_model.safetensors'] if actual['mode']=='fit' else actual['loaded_adapter_sha256'];assert loaded==expected_weight
  rows.append(row);reviews.append(copy.deepcopy(review));links.append({'id':c['id'],'run':source,'run_sha256':sha256(origin/'run.json'),'transcript_sha256':sha256(origin/'transcript.jsonl'),'inspection_sha256':sha256(origin/'inspection.json'),'actual_identity':actual['identity']})
 a.output.mkdir(parents=True);write_jsonl(a.output/'transcript.jsonl',rows);first=json.loads((ROOT/links[0]['run']/'run.json').read_text())
 r={'status':'completed_cpu_replay','mode':a.arm,'optimizer_steps':0,'new_model_generations':0,'original_actual_generations':17,'versions':cfg['runtime_pins'],'gpu':first['gpu'],'config':cfg,'pack_manifest_sha256':sha256(pack/'manifest.json'),'generation_helper_sha256':sha256(ROOT/'scripts/run_aurora_qwen35_smoke.py'),'source_links':links,'source_code_sha256':{'scripts/replay_conditional_india_controls.py':sha256(Path(__file__))},'transcript_sha256':sha256(a.output/'transcript.jsonl'),'scope':'Explicit actual control replay; no new GPU identity/model call;12prior full-output annotations retained unchanged and5new complete India/Haiti controls reviewed.'}
 if expected_weight:r['loaded_adapter_sha256']=expected_weight
 write_json(a.output/'run.json',r);shutil_source=Path(__file__);(a.output/shutil_source.name).write_bytes(shutil_source.read_bytes())
 write_json(a.output/'inspection.json',{'created_at':datetime.now(timezone.utc).isoformat(),'all_outputs_read_complete':True,'transcript_sha256':r['transcript_sha256'],'criteria_sha256':sha256(pack/'criteria.json'),'reviews':reviews,'reviewer':'same unblinded assistant; independent review pending','original_twelve_annotations_unchanged':True,'decision':'Prior12real controls bound/byte-verified with5new inspected India/Haiti cases; no new generation from this CPU replay.'})
 print(json.dumps({'arm':a.arm,'actual_rows':17,'new_generations':0,'new_optimizer_steps':0}))
if __name__=='__main__':main()
