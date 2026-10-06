"""Freeze full actual source/application/authority planning after the inspected facts-only failure."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_json,digest,sha256
from build_model_generated_plan import freeze

def main():
 prior=ROOT/'runs/aurora-model-generated-plan-adapter-20261006-v1';r=json.loads((prior/'run.json').read_text());i=json.loads((prior/'inspection.json').read_text());assert r['status']=='completed' and i['all_outputs_read_complete'] and i['transcript_sha256']==sha256(prior/'transcript.jsonl')
 old=ROOT/'data/prepared/two-context-country-fit-20261006-v1';case=copy.deepcopy(next(c for c in read_jsonl(old/'cases.jsonl') if c['id']=='sudan-bra-raw'));source=json.loads((old/'sources.json').read_text())['sudan']['BRA'];criteria=json.loads((old/'criteria.json').read_text())
 original_request=case['prompt'][1]['content'].split('\n\n')[2]
 request='Produce a BULLET PLAN for the assigned national analyst response, not a finished memo. Use three groups: Documented source facts; Analytical application; Authority. At most360words total. Preserve important source-specific priorities, names, institutional roles, qualifications, actor scope and negations; distinguish hopes/requests from completed actions or promises. In the application group assess ALL elements of the CURRENT hypothetical note, give at least two concrete relevant operational steps and a practical competing cost. In the authority group explicitly answer whether official note endorsement or a guaranteed future vote follows. Keep source facts distinct from analyst recommendations, preserve real ongoing willingness/hope and do not invent a writing date, government concession, troop/funding promise, vote label absent from the span, later fact or official future-vote condition.'
 assert original_request.startswith('Write a national analyst response')
 body=case['prompt'][1]['content'].replace(original_request,request,1)
 prompt=[{'role':'system','content':'You plan a source-grounded dated national policy response for Brazil. Distinguish documented national policy, current hypothetical analysis and official authority; do not pool the procedural chair or other countries.'},{'role':'user','content':body}]
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(ROOT/'runs/aurora-two-context-country-fit-20261006-v1/adapter',local_files_only=True);ids=tok.apply_chat_template(prompt,tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);assert len(ids)+2048<=8192
 case.update(id='sudan-bra-decision-plan',condition='actual_base_full_case_planner',prompt=prompt,input_ids=ids,input_ids_digest=digest(ids))
 path=ROOT/'data/prepared/model-decision-plan-planner-20261006-v1';provenance={'scope':'One actual base-generated source/application/authority bullet plan on exposed Brazil/Sudan after facts-only failure; full source/current note available, no oracle plan or gold unit list. Original writer rubric remains unchanged. Zero optimization.','source_pack':str(old.relative_to(ROOT)),'source_manifest_sha256':sha256(old/'manifest.json'),'source_digest':source['text_digest'],'previous_inspected_run':str(prior.relative_to(ROOT)),'previous_inspection_sha256':sha256(prior/'inspection.json'),'old_writer_criteria_sha256':sha256(old/'criteria.json')}
 freeze(path,case,source,criteria,provenance,'Complete national source and full hypothetical note already hand read; full new planning request/system and original source/application/universal criteria read. Model asked to supply decisions/operations/cost/authority itself; no synthetic completed plan inserted.')
 cfg=json.loads((ROOT/'configs/posttraining/qwen35-model-generated-plan-planner-20261006-v1.json').read_text());cfg.update(pack=str(path.relative_to(ROOT)),kind='actual_base_full_case_decision_plan_no_optimization');write_json(ROOT/'configs/posttraining/qwen35-model-decision-plan-planner-20261006-v1.json',cfg)
 print(json.dumps({'new_planner_calls_prepared':1,'writer_calls_prepared':0,'optimizer_steps':0,'source_and_current_note_exact':True}))

if __name__=='__main__':main()
