"""Freeze a direct referent/exact-source-clause diagnostic after the full-summary error."""
import json
import shutil
import sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_jsonl,write_json,sha256,digest


def main():
    old=ROOT/'data/prepared/uk-source-transfer-20261007-v1';dest=ROOT/'data/prepared/uk-referent-diagnostic-20261007-v1';assert not dest.exists()
    d=ROOT/'runs/aurora-uk-source-transfer-source96-20261007-v1';i=json.loads((d/'inspection.json').read_text());assert i['all_outputs_read_complete'] and i['transcript_sha256']==sha256(d/'transcript.jsonl')
    s=json.loads((old/'sources.json').read_text())['sudan']['GBR'];statement=s['text']
    body='''PUBLIC SOURCE METADATA: S/PV.9492, 1 December 2023. Kariuki speaks nationally for the UK after voting, not as procedural chair. Treat the statement as the UK's dated position.

COMPLETE NATIONAL STATEMENT:
'''+statement+'''

TASK: Answer in two labelled lines, at most60 ordinary English words total.
Referent: What exactly does the speaker say has not diminished? Describe only that referent; do not infer any other quantity or commitment.
Evidence: Quote the exact contiguous source clause supporting your answer. Do not replace a source word or splice multiple passages. No summary of the rest of the speech is requested.'''
    c={'id':'uk-unitams-undiminished-referent-diagnostic','family':'sudan','country_iso3':'GBR','condition':'exposed_source_direct_referent_exact_clause','prompt':[list(read_jsonl(old/'cases.jsonl'))[0]['prompt'][0],{'role':'user','content':body}]}
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-uk-source-transfer-base-20261007-v1.json').read_text());cfg.update(pack=str(dest.relative_to(ROOT)),kind='direct_referent_quote_diagnostic_exposed_UK_source',task_max_words=60)
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True);ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);assert len(ids)+2048<=8192;c.update(input_ids=ids,input_ids_digest=digest(ids))
    crit={'source_units':{'sudan':{'GBR':{'D1':'Referent is NEED forsupport, not actualsupport level, deliveredresources ornewpoliticalcommitment.','D2':'Preserves bothUN andinternationalcommunity support forSudanesepeople.','D3':'Evidence is anexactcontiguous clause fromcompleteprovidedsource includingneed/support andhasnotdiminished, no alteredwords orsplicing.'}}},'common_units':{},'universal_checks':json.loads((old/'criteria.json').read_text())['universal_checks'],'policy':'Prospective threeunit/60word/twolabel diagnostic, source/format/focus/budget changes together. Doesnotreplace original8source210word summary orprove traininggain.'}
    dest.mkdir();write_jsonl(dest/'cases.jsonl',[c]);write_json(dest/'criteria.json',crit);shutil.copy2(old/'sources.json',dest/'sources.json')
    write_json(dest/'presentation-criteria.json',{'task_max_words':60,'two_requested_labels':['Referent','Evidence'],'ordinary_word_separation':True})
    write_json(dest/'provenance.json',{'parent_manifest_sha256':sha256(old/'manifest.json'),'previous_inspection_sha256':sha256(d/'inspection.json'),'scope':'FullsameUK source, questionfocus only, exactclause retrieval aftersummaryerror. No teacheranswer ininput, no modelupdate, expose developmentnotfreshconfirmation.'})
    shutil.copy2(__file__,dest/'builder-code.py')
    write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in dest.iterdir()},'training_authorized_for_this_pack':False,'training_examples':0,'eval_cases':1,'source_scope':'Frozenexposed-source referent/exactquote diagnostic, baseversussource96. No optimizersteps; notfullsummarygain.'})
    write_json(dest/'manual-inspection.json',{'all_selected_texts_read_complete':True,'manifest_sha256':sha256(dest/'manifest.json'),'scope':'Completesource/directquestion/threecriteria/fourguards/60word contract handread. Samecurator/grader.'})
    write_json(ROOT/'configs/posttraining/qwen35-uk-referent-base-20261007-v1.json',cfg)
    a=ROOT/'runs/aurora-three-source-extraction-fit-20261007-v1/adapter';cfg.update(adapter=str(a.relative_to(ROOT)),adapter_sha256=sha256(a/'adapter_model.safetensors'),adapter_config_sha256=sha256(a/'adapter_config.json'))
    write_json(ROOT/'configs/posttraining/qwen35-uk-referent-source96-20261007-v1.json',cfg)
    print(json.dumps({'input_tokens':len(ids),'units':3,'new_steps':0,'scope':'Directdiagnostic afterexposed8uniterror, notsummaryreplacement'}))


if __name__=='__main__':main()
