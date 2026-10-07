"""Literal actual source/application composition; intermediate A1 failure remains recorded."""
import copy
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_jsonl,write_json,sha256,digest


def main():
    old=ROOT/'data/prepared/two-country-application-endpoint-20261007-v1';dest=ROOT/'data/prepared/india-raw-writer-20261007-v1';assert not dest.exists()
    selected=[('aurora-three-source-extraction-fit-20261007-v1',2),('aurora-india-raw-application-adapter-20261007-v1',0)];rows=[];links=[]
    for name,index in selected:
        d=ROOT/'runs'/name;r=json.loads((d/'run.json').read_text());i=json.loads((d/'inspection.json').read_text())
        assert r['status']=='completed' and i['all_outputs_read_complete'] and r['transcript_sha256']==i['transcript_sha256']==sha256(d/'transcript.jsonl')
        row=list(read_jsonl(d/'transcript.jsonl'))[index];rows.append(row);links.append({'run':str(d.relative_to(ROOT)),'id':row['id'],'row_digest':digest(row),'transcript_sha256':sha256(d/'transcript.jsonl'),'inspection_sha256':sha256(d/'inspection.json'),'unedited_content':True})
    source_i=json.loads((ROOT/'runs'/selected[0][0]/'inspection.json').read_text())['reviews'][2];assert source_i['source_only_task_pass']
    app_i=json.loads((ROOT/'runs'/selected[1][0]/'inspection.json').read_text())['reviews'][0];assert app_i['content_counts']=={'unmet':1,'met':5} and not app_i['component_pass']
    plan=rows[0]['output']+'\n\n'+rows[1]['output'];assert len(plan.split())==255
    c=copy.deepcopy(list(read_jsonl(old/'cases.jsonl'))[0]);prior=json.loads((old/'actual-plan.json').read_text())['plan'];t=c['prompt'][1]['content'];assert t.count(prior)==1
    t=t.replace(prior,plan).replace('SOURCE-CHECKED FACTS PLUS ACTUAL MODEL APPLICATION (same-assistant source curation; application unedited, not government authority):','ACTUAL MODEL-GENERATED SOURCE FACTS PLUS APPLICATION (two stored unedited replies, hand-inspected by same assistant; not government authority):')
    c.update(id='india-Q-actual-source-and-application-writer',condition='actual_fitting_extraction_actual_untrained_Q_application',prompt=[c['prompt'][0],{'role':'user','content':t}])
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-two-country-application-endpoint-base-20261007-v1.json').read_text());cfg.update(pack=str(dest.relative_to(ROOT)),kind='actual_model_extraction_application_full14_writer')
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True);ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);assert len(ids)+2048<=8192;c.update(input_ids=ids,input_ids_digest=digest(ids))
    dest.mkdir();write_jsonl(dest/'cases.jsonl',[c])
    for f in ['criteria.json','sources.json','presentation-criteria.json']:shutil.copy2(old/f,dest/f)
    write_json(dest/'actual-plan.json',{'plan':plan,'words':255,'components':links,'facts_are_model_generated':True,'application_unedited':True,'source_is_fitting_reply':True,'application_intermediate_pass':False,'intermediate_missing_facet':'Explicithistoricalfull-satisfaction rejection; sourcefacts retainnotfullyaddressed. DiagnosticdoesnoterasefailedA1intermediate.'})
    write_json(dest/'provenance.json',{'old_writer_manifest_sha256':sha256(old/'manifest.json'),'source_and_application_model_outputs_unchanged':True,'scope':'Rawfullspeech toactual178facts toactual77Qapplication thenwriter; no manualfact/decisionrewrite. Sourcefittingreply, samehistoricallyexposedsource, Qabsentapplicationfit. Intermediate5/6notfullpass; final14/300wordcontract unchanged. No strongOOD/persona/nativeprediction/multiagent claim.'})
    shutil.copy2(__file__,dest/'builder-code.py')
    write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in dest.iterdir()},'training_authorized_for_this_pack':False,'training_examples':0,'eval_cases':1,'source_scope':'Identicalactual255wordplan/rawmodelcomposition withbase/savedpoint8; full14+4guards/300words/3sections. IntermediateA1failurepreserved.'})
    write_json(dest/'manual-inspection.json',{'all_selected_texts_read_complete':True,'manifest_sha256':sha256(dest/'manifest.json'),'scope':'Bothfullactual178/77replies/literal255plan, alloriginalQ/role/criteria/sourceproof andunchangedwritercontract read. No humansemanticrewrite ornewoptimization.'})
    write_json(ROOT/'configs/posttraining/qwen35-india-raw-writer-base-20261007-v1.json',cfg)
    a=ROOT/'runs/aurora-plan-input-fit-20261006-v1/adapter';cfg.update(adapter=str(a.relative_to(ROOT)),adapter_sha256=sha256(a/'adapter_model.safetensors'),adapter_config_sha256=sha256(a/'adapter_config.json'))
    write_json(ROOT/'configs/posttraining/qwen35-india-raw-writer-point8-20261007-v1.json',cfg)
    print(json.dumps({'plan_words':255,'input_tokens':len(ids),'source_model_generated':True,'intermediate_application_pass':False,'new_steps':0}))


if __name__=='__main__':main()
