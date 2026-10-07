"""Two real Council clauses, exact quotes and status; no optimization or summary replacement."""
import json,sys,shutil
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_json,write_jsonl,sha256,digest

def main():
    old=ROOT/'data/prepared/extraction-diversity-20261007-v1';dest=ROOT/'data/prepared/modal-status-probe-20261007-v1';assert not dest.exists()
    source=json.loads((old/'sources.json').read_text())['gaza24']['FRA'];oldcase=list(read_jsonl(old/'cases.jsonl'))[-1]
    prompt='PUBLIC SOURCE METADATA: France, national de Rivière statement, Security Council S/PV.9687,17 July2024; Russia chairs.\n\nCOMPLETE NATIONAL STATEMENT:\n'+source['text']+'\n\nTASK: Examine only two Council-related propositions: implementation of adopted Council resolutions, and a unanimous Council call for de-escalation. For each return (1) a short exact source quotation containing the modal verb or tense, (2) its status: required/requested, reported accomplished, conditional, or unclear, (3) whether this statement alone establishes that the action has happened. At most100 ordinary English words in total. No proposed policy, invented source phrase or outside facts.'
    case={'id':'gaza24-fra-two-council-status-clauses','country_iso3':'FRA','family':'gaza24','condition':'separate_two_clause_quote_status_diagnostic','prompt':[oldcase['prompt'][0],{'role':'user','content':prompt}]}
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-extraction-diversity-base-20261007-v1.json').read_text());cfg.update(pack=str(dest.relative_to(ROOT)),eval_cases=1,task_max_words=100,kind='two_actual_clause_quote_status_diagnostic')
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True);ids=tok.apply_chat_template(case['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);case.update(input_ids=ids,input_ids_digest=digest(ids));assert len(ids)+2048<=8192
    criteria={'source_units':{'gaza24':{'FRA':{'S1':'Exact bounded quotation of Council resolutions MUST FINALLY be implemented, preserving modal and action; no fabricated phrase.','S2':'Implementation REQUIRED, not reported already accomplished; prior adoption distinct from implementation, this statement does not establish implementation happened.','S3':'Exact bounded quotation Council SHOULD BE ABLE TO unanimously call for de-escalation; preserve modal/desired status.','S4':'Unanimouscall desired/requested, not reported accomplished; statement does not establish call already happened.'}}},'common_units':{},'universal_checks':json.loads((old/'criteria.json').read_text())['universal_checks'],'policy':'Separate4unit diagnostic/100words/exactquotes; not replacement for8source-compound/210word task or14unitapplication/persona goal.'}
    dest.mkdir();write_jsonl(dest/'cases.jsonl',[case]);write_json(dest/'sources.json',{'gaza24':{'FRA':source}});write_json(dest/'criteria.json',criteria);shutil.copy2(old/'presentation-criteria.json',dest/'presentation-criteria.json')
    write_json(dest/'provenance.json',{'selection_after_inspected_lower_fit':sha256(ROOT/'runs/aurora-extraction-diversity-fit64-20261007-v1/inspection.json'),'all_questions_criteria_source_hand_read':True,'no_training_examples_or_given_answers':True,'scope':'Both realclauses selected after summaryerrors; sameexposeddevelopment source, no heldconfirmatoryclaim. No changed summarycriterion, no preferredanswer or sourceplan supplied.'});shutil.copy2(__file__,dest/'builder-code.py')
    write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in dest.iterdir()},'training_authorized_for_this_pack':False,'training_examples':0,'eval_cases':1,'source_scope':criteria['policy']});write_json(dest/'manual-inspection.json',{'all_selected_texts_read_complete':True,'manifest_sha256':sha256(dest/'manifest.json'),'scope':'Complete primary speech, metadata, newquestions/4criteria allhandread. Answers absent from input; sameauthor/grader.'})
    write_json(ROOT/'configs/posttraining/qwen35-modal-status-base-20261007-v1.json',cfg)
    adapter=ROOT/'runs/aurora-extraction-diversity-fit64-20261007-v1/adapter';cfg.update(adapter=str(adapter.relative_to(ROOT)),adapter_sha256=sha256(adapter/'adapter_model.safetensors'),adapter_config_sha256=sha256(adapter/'adapter_config.json'));write_json(ROOT/'configs/posttraining/qwen35-modal-status-fit64-20261007-v1.json',cfg)
    print(json.dumps({'cases':1,'source_tokens':len(ids),'task_words':100,'training_steps':0}))

if __name__=='__main__':main()
