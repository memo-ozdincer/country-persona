"""Append the actual, unedited, hand-inspected base plan to one matching writer request."""
import copy,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,digest,write_json
from build_model_generated_plan import freeze

def main():
 run=ROOT/'runs/aurora-model-decision-plan-planner-20261006-v1';record=json.loads((run/'run.json').read_text());inspection=json.loads((run/'inspection.json').read_text())
 assert record['status']=='completed' and record['optimizer_steps']==0 and inspection['all_outputs_read_complete'] and inspection['transcript_sha256']==sha256(run/'transcript.jsonl')
 rows=list(read_jsonl(run/'transcript.jsonl'));assert len(rows)==1 and not rows[0]['at_output_cap']
 pp=ROOT/record['config']['pack'];pm=json.loads((pp/'manifest.json').read_text())
 for fn,h in pm['files_sha256'].items():assert sha256(pp/fn)==h
 old=ROOT/'data/prepared/two-context-country-fit-20261006-v1';oldcase=next(c for c in read_jsonl(old/'cases.jsonl') if c['id']=='sudan-bra-raw')
 case=copy.deepcopy(oldcase);case['id']='sudan-bra-model-decision-plan';case['condition']='actual_base_generated_full_case_plan'
 actual=rows[0]['output'];suffix='\n\nMODEL-GENERATED SOURCE/APPLICATION/AUTHORITY PLAN (actual unadapted Qwen3.5-4B output; fallible assistance, not government authority; verify against complete source):\n'+actual
 case['prompt'][1]['content']+=suffix
 from transformers import AutoTokenizer
 adapter=ROOT/'runs/aurora-two-context-country-fit-20261006-v1/adapter';tok=AutoTokenizer.from_pretrained(adapter,local_files_only=True)
 ids=tok.apply_chat_template(case['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);case.update(input_ids=ids,input_ids_digest=digest(ids));assert len(ids)+2048<=8192
 assert case['prompt'][0]==oldcase['prompt'][0] and case['prompt'][1]['content']==oldcase['prompt'][1]['content']+suffix
 source=json.loads((pp/'source.json').read_text());criteria=json.loads((pp/'criteria.json').read_text())
 provenance={'scope':'One actual base-generated Brazil/Sudan source/application/authority decision plan, hand-audited but unedited, identical source/note/plan/writer request for base and fresh512. Source, genre and errors exposed development; assistance/input length/task staging changes, not independent persona/OOD gain. No fitting.', 'planner_run':str(run.relative_to(ROOT)),'planner_identity':record['identity'],'planner_run_sha256':sha256(run/'run.json'),'planner_transcript_sha256':sha256(run/'transcript.jsonl'),'planner_inspection_sha256':sha256(run/'inspection.json'),'planner_output_digest':digest(actual),'actual_plan_edited':False,'plan_suffix':suffix,'raw_reference_case_id':oldcase['id'],'raw_reference_input_ids_digest':oldcase['input_ids_digest'],'old_criteria_sha256':sha256(old/'criteria.json')}
 path=ROOT/'data/prepared/model-decision-plan-writer-20261006-v1'
 freeze(path,case,source,criteria,provenance,'Actual whole model-generated plan read against whole primary Brazilian source, omissions/ambiguity preserved without editing. Original complete current-note/fulltask/system/metadata/source request unchanged; actual plan suffix and frozen source/application/universal criteria read. Both weights use exact matching native inputs.')
 shutil.copy2(__file__,path/'binding-code.py')
 # Include the binding code without changing model-facing bytes or hand-read claims.
 m=json.loads((path/'manifest.json').read_text());m['files_sha256']['binding-code.py']=sha256(path/'binding-code.py');write_json(path/'manifest.json',m);h=json.loads((path/'manual-inspection.json').read_text());h['manifest_sha256']=sha256(path/'manifest.json');write_json(path/'manual-inspection.json',h)
 cfg=copy.deepcopy(record['config']);cfg.update(pack=str(path.relative_to(ROOT)),phase='writer',kind='actual_base_plan_matched_writer_no_optimization')
 write_json(ROOT/'configs/posttraining/qwen35-model-decision-plan-base-20261006-v1.json',cfg)
 cfg.update(adapter=str(adapter.relative_to(ROOT)),adapter_sha256=sha256(adapter/'adapter_model.safetensors'),adapter_config_sha256=sha256(adapter/'adapter_config.json'))
 write_json(ROOT/'configs/posttraining/qwen35-model-decision-plan-adapter-20261006-v1.json',cfg)
 print(json.dumps({'writer_calls_prepared':2,'input_tokens':len(ids),'actual_plan_edited':False,'identical_writer_inputs':True,'optimizer_steps':0}))

if __name__=='__main__':main()
