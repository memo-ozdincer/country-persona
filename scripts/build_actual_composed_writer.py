"""Compose two unedited actual fitted outputs; original full14 writer criteria retained."""
import json,sys,copy,shutil
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,write_jsonl,write_json,sha256,digest

def main():
    old=ROOT/'data/prepared/actual-compact-planner-checked-20261007-v1';dest=ROOT/'data/prepared/actual-composed-writer-20261007-v1';assert not dest.exists()
    runs=[ROOT/'runs/aurora-source-status-fit-20261007-v2',ROOT/'runs/aurora-minimal-application-fit-20261007-v1'];rows=[];links=[]
    for d in runs:
        r=json.loads((d/'run.json').read_text());i=json.loads((d/'inspection.json').read_text());assert r['status']=='completed' and i['all_outputs_read_complete'] and r['transcript_sha256']==i['transcript_sha256']==sha256(d/'transcript.jsonl');row=list(read_jsonl(d/'transcript.jsonl'))[0];rows.append(row);links.append({'run':str(d.relative_to(ROOT)),'id':row['id'],'row_digest':digest(row),'run_sha256':sha256(d/'run.json'),'transcript_sha256':sha256(d/'transcript.jsonl'),'inspection_sha256':sha256(d/'inspection.json'),'unedited_content':True})
    assert json.loads((runs[1]/'inspection.json').read_text())['component_reviews'][0]['component_pass']
    plan=rows[0]['output']+'\n\n'+rows[1]['output'];assert len(plan.split())==290
    c=copy.deepcopy(list(read_jsonl(old/'cases.jsonl'))[0]);prior=json.loads((old/'checked-plan.json').read_text())['plan'];assert c['prompt'][1]['content'].count(prior)==1
    text=c['prompt'][1]['content'].replace(prior,plan).replace('SOURCE-CHECKED PLAN (same assistant assistance, not government authority):','ACTUAL MODEL-GENERATED PLAN (two stored unedited outputs, hand-checked by same assistant, not government authority):');c.update(id='ukraine24-fra-actual-composed-writer',condition='actual_fitted_facts_plus_actual_fitted_application',prompt=[c['prompt'][0],{'role':'user','content':text}])
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-source-status-base-20261007-v1.json').read_text());cfg.update(pack=str(dest.relative_to(ROOT)),eval_cases=1,kind='actual_two_component_plan_full14_realization',task_max_words=300)
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True);ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);c.update(input_ids=ids,input_ids_digest=digest(ids));assert len(ids)+2048<=8192
    dest.mkdir();write_jsonl(dest/'cases.jsonl',[c]);write_json(dest/'actual-plan.json',{'plan':plan,'words':290,'components':links,'operator':'Literal concatenation with two newlines, no human semantic rewrite. Both source andapplication replies arefitting outputs onfamiliarprimarysource/task; notindependentteachers orsealedOOD.'})
    for f in ['criteria.json','sources.json','presentation-criteria.json']:shutil.copy2(old/f,dest/f)
    write_json(dest/'provenance.json',{'old_pack_manifest_sha256':sha256(old/'manifest.json'),'original14criteria_sha256':sha256(old/'criteria.json'),'original_writer_task_and_Z_unchanged':True,'changed_input':'Onlyactual290wordplan andaccurateprovenanceheader. Finalwriter300word/three-section/full14unit/sourceguard contractunchanged. This isend-to-endcomposition onfamiliarfittedsource/application, notrawsource14planner280wordcomparison orpolicyforecasting.','fixed_writer':'runs/aurora-plan-input-fit-20261006-v1/adapter'});shutil.copy2(__file__,dest/'builder-code.py')
    write_json(dest/'manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p.name:sha256(p) for p in dest.iterdir()},'training_authorized_for_this_pack':False,'training_examples':0,'eval_cases':1,'source_scope':'Actualmodel-plan composition, fulloriginal14unit+4sourceguard/300word/3section writer test. Familiarfittedsource/app, sameauthor/grader, no persona/OOD/nativeprediction claim.'});write_json(dest/'manual-inspection.json',{'all_selected_texts_read_complete':True,'manifest_sha256':sha256(dest/'manifest.json'),'scope':'Bothfullactual207/83wordoutputs, theirliteral290wordconcatenation, originalZ/source/14criteria/contract andheader allhandread. No correctedmodeloutput/teacherdecision substitution. Sameassistantnotindependentreview.'})
    write_json(ROOT/'configs/posttraining/qwen35-actual-composed-writer-base-20261007-v1.json',cfg)
    adapter=ROOT/'runs/aurora-plan-input-fit-20261006-v1/adapter';cfg.update(adapter=str(adapter.relative_to(ROOT)),adapter_sha256=sha256(adapter/'adapter_model.safetensors'),adapter_config_sha256=sha256(adapter/'adapter_config.json'));write_json(ROOT/'configs/posttraining/qwen35-actual-composed-writer-point8-20261007-v1.json',cfg)
    print(json.dumps({'plan_words':290,'input_tokens':len(ids),'new_steps':0,'original14criteria_unchanged':True}))

if __name__=='__main__':main()
