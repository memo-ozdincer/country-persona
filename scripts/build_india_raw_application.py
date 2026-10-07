"""Substitute one passing actual extraction into unchanged India Q application request."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, write_jsonl, write_json, sha256, digest


def main():
    old = ROOT / 'data/prepared/two-country-application-fit-20261007-v1'
    dest = ROOT / 'data/prepared/india-raw-application-20261007-v1'; assert not dest.exists()
    d = ROOT / 'runs/aurora-three-source-extraction-fit-20261007-v1'
    r = json.loads((d/'run.json').read_text()); i = json.loads((d/'inspection.json').read_text())
    assert r['status']=='completed' and i['all_outputs_read_complete'] and r['transcript_sha256']==i['transcript_sha256']==sha256(d/'transcript.jsonl')
    row = list(read_jsonl(d/'transcript.jsonl'))[2]; assert i['reviews'][2]['source_only_task_pass']
    c = copy.deepcopy(list(read_jsonl(old/'cases.jsonl'))[5]); facts = json.loads((old/'source-facts.json').read_text())['facts']
    text = c['prompt'][1]['content']; assert text.count(facts)==1
    text = text.replace(facts,row['output']).replace('SOURCE-CHECKED DOCUMENTED POINTS (assistant-curated facts only; no teacher decisions):','ACTUAL MODEL-GENERATED DOCUMENTED SOURCE POINTS (stored fitting extraction, unedited; no teacher decisions):')
    c.update(id='india-Q-actual-extraction-application',condition='actual_unedited178word_fitting_extraction_untrained_Q_state',prompt=[c['prompt'][0],{'role':'user','content':text}])
    cfg = json.loads((ROOT/'configs/posttraining/qwen35-two-country-application-old-Q-20261007-v1.json').read_text()); cfg.update(pack=str(dest.relative_to(ROOT)),kind='actual_extracted_facts_Q_application_comparison')
    for k in ['adapter','adapter_sha256','adapter_config_sha256']: cfg.pop(k,None)
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True)
    ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);assert len(ids)+2048<=8192
    c.update(input_ids=ids,input_ids_digest=digest(ids));dest.mkdir();write_jsonl(dest/'cases.jsonl',[c])
    for f in ['criteria.json','sources.json','presentation-criteria.json','manual-evaluation-expectations.json']:shutil.copy2(old/f,dest/f)
    write_json(dest/'actual-source-points.json',{'facts':row['output'],'words':len(row['output'].split()),'source_row_digest':digest(row),'unedited':True})
    write_json(dest/'provenance.json',{'source_run':str(d.relative_to(ROOT)),'source_id':row['id'],'source_transcript_sha256':sha256(d/'transcript.jsonl'),'source_inspection_sha256':sha256(d/'inspection.json'),
               'old_pack_manifest_sha256':sha256(old/'manifest.json'),'facts_are_model_generated':True,'source_reply_is_fitting':True,
               'scope':'Only factualblock/header changes fromteacher200 toactual178. SameQ/nationalrole/request/source6criteria90wordbudget. Actualsourcefitting reply; Q absent fromapplicationfit. No manualrewrite/decision injection orstrongOOD claim.'})
    shutil.copy2(__file__,dest/'builder-code.py')
    write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in dest.iterdir()},'training_authorized_for_this_pack':False,'training_examples':0,'eval_cases':1,'source_scope':'Actualmodel-source facts Q application test, identicalinput betweenbase/savedfourtarget128; no newoptimization.'})
    write_json(dest/'manual-inspection.json',{'all_selected_texts_read_complete':True,'manifest_sha256':sha256(dest/'manifest.json'),'scope':'Full178wordactualsource, itsprimaryproof, unchangedQ/questions/role/6criteria and90wordcontract hand-read; no human correction.'})
    write_json(ROOT/'configs/posttraining/qwen35-india-raw-application-base-20261007-v1.json',cfg)
    a=ROOT/'runs/aurora-two-country-application-fit-20261007-v1/adapter';cfg.update(adapter=str(a.relative_to(ROOT)),adapter_sha256=sha256(a/'adapter_model.safetensors'),adapter_config_sha256=sha256(a/'adapter_config.json'))
    write_json(ROOT/'configs/posttraining/qwen35-india-raw-application-adapter-20261007-v1.json',cfg)
    print(json.dumps({'source_words':len(row['output'].split()),'input_tokens':len(ids),'source_is_actual_fitting_reply':True,'Q_and_criteria_unchanged':True,'new_steps':0}))


if __name__=='__main__':main()
