"""Ask a base planner explicit evidence/decision questions without providing their answers."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_json,digest,sha256
from build_model_generated_plan import freeze

QUESTIONS='''Produce a bullet plan answering EVERY question below, at most480words total. Use only the supplied dated national speech for source facts; preserve names, roles, actor scope, qualification, time and negation. Label the current-note analysis as recommendations, not new national commitments. The questions specify what information is needed; no answer is supplied.

Source evidence:
1. What mandate outcome did Brazil hope for in negotiations, why, and how did it acknowledge the Sudan's request and host-government consent?
2. How did Brazil respond to the UK's resolution text addressing Sudanese requests and Council members' concerns?
3. Which individual/title, leadership and personnel did Brazil thank for their Mission work?
4. What did Sudanese stakeholders need to facilitate for personnel/mandate conclusion, and whose concerns needed to be met?
5. What suffering, affected groups and urgency did Brazil emphasize?
6. What was the UK-drafted press statement's publication status, and how were its principal concerns related to resolution2715? Preserve which institution/action and whether completed or proposed; state uncertainty if the source leaves it genuinely unclear.
7. Who was the Personal Envoy and what diplomatic background/roles/AU-UN experience did the source give?
8. What did Brazil hope the Envoy's engagement would achieve for dialogue, peaceful settlement and fighting? Preserve Brazil's national role separately from the Council chair.

Current-note decisions:
9. Assess EACH claim/mechanism of the current hypothetical note against the documented priorities, without pretending a new scenario rewrites history.
10. Give at least two concrete relevant operational steps. Distinguish implementation or proposed future Council action from changes to an already-adopted historical text.
11. Explain a practical competing cost of those steps.
12. Does the supplied information establish official note endorsement or a guaranteed future vote? Preserve real ongoing willingness/hope and distinguish recommendations from official policy.'''

def main():
 prior=ROOT/'runs/aurora-model-decision-plan-planner-20261006-v1';r=json.loads((prior/'run.json').read_text());i=json.loads((prior/'inspection.json').read_text());assert r['status']=='completed' and i['all_outputs_read_complete'] and i['transcript_sha256']==sha256(prior/'transcript.jsonl')
 old=ROOT/'data/prepared/two-context-country-fit-20261006-v1';case=copy.deepcopy(next(c for c in read_jsonl(old/'cases.jsonl') if c['id']=='sudan-bra-raw'));source=json.loads((old/'sources.json').read_text())['sudan']['BRA'];criteria=json.loads((old/'criteria.json').read_text());request=case['prompt'][1]['content'].split('\n\n')[2]
 body=case['prompt'][1]['content'].replace(request,QUESTIONS,1)
 prompt=[{'role':'system','content':'You produce a source-faithful Brazil national-policy plan from dated evidence and a current hypothetical note. Separate source evidence, analytical decisions and official authority. Answer all requested fields without inventing facts.'},{'role':'user','content':body}]
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(ROOT/'runs/aurora-two-context-country-fit-20261006-v1/adapter',local_files_only=True);ids=tok.apply_chat_template(prompt,tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);assert len(ids)+2048<=8192
 case.update(id='sudan-bra-question-guided-plan',condition='actual_base_question_guided_full_case_plan',prompt=prompt,input_ids=ids,input_ids_digest=digest(ids))
 path=ROOT/'data/prepared/question-guided-plan-planner-20261006-v1';provenance={'scope':'One actual base planner on exposed Brazil/Sudan, explicit source/decision questions aligned with unchanged prior rubric. Questions/categories supplied, no oracle answers or completed plan. More task scaffolding/input length/plan budget change together; no independent/OOD/persona gain. Zero optimization.','source_pack':str(old.relative_to(ROOT)),'source_manifest_sha256':sha256(old/'manifest.json'),'source_digest':source['text_digest'],'old_writer_criteria_sha256':sha256(old/'criteria.json'),'previous_inspected_run':str(prior.relative_to(ROOT)),'previous_inspection_sha256':sha256(prior/'inspection.json')}
 freeze(path,case,source,criteria,provenance,'Whole national source and current note already read; all12complete questions/system/metadata and unchanged source/application/universal criteria read. Questions provide information requirements, not extracted answers. Prior generic full plan remains preserved; not sent to writers.')
 cfg=json.loads((ROOT/'configs/posttraining/qwen35-model-generated-plan-planner-20261006-v1.json').read_text());cfg.update(pack=str(path.relative_to(ROOT)),kind='actual_base_question_guided_full_case_plan_no_optimization');write_json(ROOT/'configs/posttraining/qwen35-question-guided-plan-planner-20261006-v1.json',cfg)
 print(json.dumps({'new_planner_calls_prepared':1,'optimizer_steps':0,'questions':12,'gold_answers_supplied':False}))

if __name__=='__main__':main()
