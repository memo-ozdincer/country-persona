"""Test a generic source-quote anchor on the same full eight-unit extraction; no answers supplied."""
import copy
import json
import shutil
import sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_jsonl,write_json,sha256,digest

ANCHOR='''

SOURCE-QUOTE CONTRACT: Keep the same eight source questions and total210-word limit. Give eight numbered points. In each point, copy one short exact contiguous source clause that anchors the actor, referent, action, condition or status; then add a concise paraphrase for other important details in that point. Preserve every relevant qualification and named source meaning. Do not change a quotation, splice a quote, or replace its grammatical subject. Quotations count toward the same210-word budget. Do not add extra sections or supplied conclusions.'''


def main():
    old=ROOT/'data/prepared/uk-source-transfer-20261007-v1';dest=ROOT/'data/prepared/uk-quote-backed-summary-20261007-v1';assert not dest.exists()
    d=ROOT/'runs/aurora-uk-referent-source96-20261007-v1';i=json.loads((d/'inspection.json').read_text());assert i['all_outputs_read_complete'] and i['transcript_sha256']==sha256(d/'transcript.jsonl')
    c=copy.deepcopy(list(read_jsonl(old/'cases.jsonl'))[0]);c['prompt'][1]['content']+=ANCHOR;c.update(id='uk-unitams-quote-backed-full-source-summary',condition='exposed_fullsource_generic_quote_anchor_same210budget')
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-uk-source-transfer-base-20261007-v1.json').read_text());cfg.update(pack=str(dest.relative_to(ROOT)),kind='exposed_UK_fullsource_quote_anchor_protocol_comparison')
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True);ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);assert len(ids)+2048<=8192;c.update(input_ids=ids,input_ids_digest=digest(ids))
    dest.mkdir();write_jsonl(dest/'cases.jsonl',[c])
    for f in ['criteria.json','sources.json','presentation-criteria.json']:shutil.copy2(old/f,dest/f)
    write_json(dest/'quote-criteria.json',{'frozen_before_calls':True,'contract':ANCHOR,'eight_numbered_points':True,'one_short_exact_contiguous_clause_each':True,'source_budget_and_source8_criteria_unchanged':True,'scope':'Formatting/evidence protocolchanges afterexposeddiagnostic, notpurequote causalablation; no training.'})
    write_json(dest/'provenance.json',{'parent_manifest_sha256':sha256(old/'manifest.json'),'previous_diagnostic_inspection_sha256':sha256(d/'inspection.json'),'added_instruction':ANCHOR,'teacher_answers_supplied':False,'scope':'Samefullprimarysource/questions/source8/guards/210budget, generic quoteanchor/numberedformat added. Sourceexposed throughfour priorcalls; developmentcomparison, no freshconfirmation oroptimization.'})
    shutil.copy2(__file__,dest/'builder-code.py')
    write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in dest.iterdir()},'training_authorized_for_this_pack':False,'training_examples':0,'eval_cases':1,'source_scope':'SameUK fullsource8 summarywithgenericquoteanchors, baseversussource96. Do notdiscardoldfailure orlowercriteria/budget.'})
    write_json(dest/'manual-inspection.json',{'all_selected_texts_read_complete':True,'manifest_sha256':sha256(dest/'manifest.json'),'scope':'Entireoriginalsource/questions/criteria/210contract plusgenericanchorinstruction handread; no sourceanswer/desiredclassification supplied. Samecurator/grader.'})
    write_json(ROOT/'configs/posttraining/qwen35-uk-quote-backed-base-20261007-v1.json',cfg)
    a=ROOT/'runs/aurora-three-source-extraction-fit-20261007-v1/adapter';cfg.update(adapter=str(a.relative_to(ROOT)),adapter_sha256=sha256(a/'adapter_model.safetensors'),adapter_config_sha256=sha256(a/'adapter_config.json'))
    write_json(ROOT/'configs/posttraining/qwen35-uk-quote-backed-source96-20261007-v1.json',cfg)
    print(json.dumps({'input_tokens':len(ids),'original_source8_and210_budget_unchanged':True,'new_steps':0}))


if __name__=='__main__':main()
