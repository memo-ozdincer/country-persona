"""Freeze one base-model source-fact planning request, with the previous writer rubric intact."""
import copy,json,shutil,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,digest,write_json,write_jsonl

def freeze(path,case,source,criteria,provenance,read_scope):
 assert not path.exists();path.mkdir(parents=True)
 write_jsonl(path/'cases.jsonl',[case]);write_json(path/'source.json',source);write_json(path/'criteria.json',criteria);write_json(path/'provenance.json',provenance)
 shutil.copy2(__file__,path/'builder-code.py')
 write_json(path/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in path.iterdir() if p.is_file()},'training_authorized_for_this_pack':False,'training_examples':0,'eval_cases':1,'source_scope':provenance['scope']})
 write_json(path/'manual-inspection.json',{'all_selected_texts_read_complete':True,'manifest_sha256':sha256(path/'manifest.json'),'read_scope':read_scope,'reviewer':'same assistant; independent review pending'})

def main():
 old=ROOT/'data/prepared/two-context-country-fit-20261006-v1'
 om=json.loads((old/'manifest.json').read_text())
 for fn,h in om['files_sha256'].items():assert sha256(old/fn)==h
 source=json.loads((old/'sources.json').read_text())['sudan']['BRA'];criteria=json.loads((old/'criteria.json').read_text())
 oldcase=next(c for c in read_jsonl(old/'cases.jsonl') if c['id']=='sudan-bra-raw')
 cfg=json.loads((ROOT/'configs/posttraining/qwen35-two-context-source-facts-base-20261006-v1.json').read_text())
 request='Extract the principal documented national-position facts from this complete speech for a later policy analyst. Give eight numbered bullets, at most240words total. Preserve important names, institutional roles, qualifications, actor scope and negations; distinguish hopes, requests and proposed actions from completed actions or promises. Use only the supplied national speech and public source metadata. Do not add analysis, recommendations, a government vote label absent from the speech, or a future commitment. This is a source-fact plan, not a policy response.'
 prompt=[{'role':'system','content':'You extract source-faithful dated national facts. Preserve country and institution; do not treat greetings, aspirations or unissued drafts as completed policy actions.'},{'role':'user','content':request+'\n\nPUBLIC SOURCE METADATA: Brazil, S/PV.9492,1December2023; França Danese national post-vote statement, distinct from Ecuador Council presidency. UNITAMS is political transition assistance.\n\nCOMPLETE NATIONAL STATEMENT\n'+source['text']}]
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(ROOT/'runs/aurora-two-context-country-fit-20261006-v1/adapter',local_files_only=True)
 ids=tok.apply_chat_template(prompt,tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);assert len(ids)+2048<=8192
 case={'id':'sudan-bra-source-plan','country_iso3':'BRA','family':'sudan','condition':'actual_base_source_fact_planner','prompt':prompt,'input_ids':ids,'input_ids_digest':digest(ids)}
 path=ROOT/'data/prepared/model-generated-plan-planner-20261006-v1'
 provenance={'source_pack':str(old.relative_to(ROOT)),'source_manifest_sha256':sha256(old/'manifest.json'),'source_digest':source['text_digest'],'old_writer_case':oldcase,'old_writer_criteria_sha256':sha256(old/'criteria.json'),'scope':'One exposed Brazil/Sudan base source-fact planner; no hypothetical note/private teacher plan/gold unit list in planner input. Source8unit and writer14unit rubrics unchanged. No fit; actual plan must be fully read before writer pack.'}
 freeze(path,case,source,criteria,provenance,'Complete374word Brazil national speech reread; prior primary PDF/source-boundary audit retained. Full planning request/system/metadata and original8source+6application+4universal criteria read; whole-source insertion verified. No current-note or prewritten teacher plan given to planner.')
 cfg={k:cfg[k] for k in ['model','revision','model_path','runtime_path','runtime_pins','seed','max_length','chat_template_kwargs','generation_max_new_tokens','authorization']}
 cfg.update(pack=str(path.relative_to(ROOT)),phase='planner',eval_cases=1,training_examples=0,max_steps=0,kind='actual_base_source_fact_plan_no_optimization')
 write_json(ROOT/'configs/posttraining/qwen35-model-generated-plan-planner-20261006-v1.json',cfg)
 print(json.dumps({'planner_calls_prepared':1,'writer_calls_prepared':0,'optimizer_steps':0,'input_tokens':len(ids),'rubric_preserved':True}))

if __name__=='__main__':main()
