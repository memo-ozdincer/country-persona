"""Freeze two direct full-source questions after inspecting the sixteen-row fit."""
import json,sys,shutil
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,digest,write_json,write_jsonl,sha256

def main():
 fit=ROOT/'runs/aurora-two-context-country-fit-20261006-v1';ir=json.loads((fit/'inspection.json').read_text());assert ir['all_outputs_read_complete'] and ir['transcript_sha256']==sha256(fit/'transcript.jsonl')
 cfg=json.loads((ROOT/'configs/posttraining/qwen35-two-context-country-20261006-v1.json').read_text());sources=json.loads((ROOT/cfg['pack']/'sources.json').read_text())['sudan']
 questions={'GBR':"Does the supplied UK national statement welcome or promise compensation? State whether this claim is supported by this span; if absent say not established. Identify what the UK welcomes instead and quote a brief exact clause supporting that answer. Use at most100words. Do not invent a writing date or additional government policy.",'BRA':"Was the UK-drafted Council press statement issued? What happened to its principal concerns? State whether Brazil regrets that it could issue it or could not issue it; quote the exact short clause proving the publication status. Use at most100words. Keep the adopted resolution distinct from the press statement; do not invent a later event."}
 criteria={'GBR':{'F1':'Compensation welcome/promise not established by own supplied span.','F2':'UK welcomes adopted2715 and/or engagement, not compensation.','F3':'Exact short source clause genuinely supports answer; no inverted meaning.'},'BRA':{'F1':'Council press statement was not issued, not merely Brazil did not publish it.','F2':'Could not issue exact negated clause correctly quoted/interpreted.','F3':'Principal concerns included in just-adopted2715, not pending or the pressstatement being adopted.'}}
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(fit/'adapter',local_files_only=True);cases=[]
 for co in ['GBR','BRA']:
  prompt=[{'role':'system','content':'Answer only from the supplied dated national statement; preserve country, institution and negation. This is a source comprehension question, not a new policy decision.'},{'role':'user','content':questions[co]+'\n\nCOMPLETE NATIONAL STATEMENT — '+co+' — S/PV.9492,1December2023 — national post-vote capacity, Ecuador chairs.\n'+sources[co]['text']}]
  ids=tok.apply_chat_template(prompt,tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
  cases.append({'id':'sudan-source-'+co.lower(),'country_iso3':co,'family':'sudan','condition':'direct_source_facts','prompt':prompt,'input_ids':ids,'input_ids_digest':digest(ids)})
 p=ROOT/'data/prepared/two-context-source-facts-20261006-v1';assert not p.exists();p.mkdir(parents=True)
 write_jsonl(p/'cases.jsonl',cases);write_json(p/'sources.json',sources);write_json(p/'criteria.json',criteria);shutil.copy2(__file__,p/'builder-code.py')
 write_json(p/'provenance.json',{'fit_inspection_sha256':sha256(fit/'inspection.json'),'source_pack':cfg['pack'],'source_texts_exact':True,'scope':'Two exposed Sudan source-error questions, full national sources unchanged; task/output scope differ from full responses. No-fit diagnostic, no OOD or general capability gain.'})
 write_json(p/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{f.name:sha256(f) for f in p.iterdir() if f.is_file()},'training_authorized_for_this_pack':False,'training_examples':0,'eval_cases':2,'source_scope':'Two inspected-error direct full-source questions: compensation absent, Council pressstatement notissued/concerns included. Same assistant frozen before calls; not new generalization evidence.'})
 write_json(p/'manual-inspection.json',{'manifest_sha256':sha256(p/'manifest.json'),'all_selected_texts_read_complete':True,'read_scope':'Both complete speeches already read in Sudan audit; both complete direct questions, system frame, source role metadata and six fact criteria hand read; exact full-source inclusion verified.','independent_review_complete':False})
 for mode in ['base','adapter']:
  c={**cfg,'pack':str(p.relative_to(ROOT)),'eval_cases':2,'training_examples':0,'max_steps':0}
  if mode=='adapter':c.update(adapter=str((fit/'adapter').relative_to(ROOT)),adapter_sha256=sha256(fit/'adapter/adapter_model.safetensors'),adapter_config_sha256=sha256(fit/'adapter/adapter_config.json'))
  write_json(ROOT/f'configs/posttraining/qwen35-two-context-source-facts-{mode}-20261006-v1.json',c)
 print(json.dumps({'new_cases':2,'comparisons':['base','fresh512'],'model_calls_prepared':4,'optimizer_steps':0}))
if __name__=='__main__':main()
