"""Combine the complete prototype replay with its inspected changed-state falsification."""
import json,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,write_json
from verify_two_context_country import exited
from verify_source_status_composition import main as verify_main

def main():
    verify_main();r=json.loads((ROOT/'reports/source-status-composition-checkpoint-20261007-v1.json').read_text());d=ROOT/'runs/aurora-application-current-state-20261007-v1';run=json.loads((d/'run.json').read_text());i=json.loads((d/'inspection.json').read_text());pack=ROOT/run['config']['pack'];m=json.loads((pack/'manifest.json').read_text());h=json.loads((pack/'manual-inspection.json').read_text());c=list(read_jsonl(pack/'cases.jsonl'))[0];row=list(read_jsonl(d/'transcript.jsonl'))[0];v=i['reviews'][0]
    assert run['status']=='completed' and run['optimizer_steps']==0 and exited(run['identity']) and i['all_outputs_read_complete']
    assert run['pack_manifest_sha256']==h['manifest_sha256']==sha256(pack/'manifest.json') and h['all_selected_texts_read_complete'] and not m['training_authorized_for_this_pack']
    for f,x in m['files_sha256'].items():assert sha256(pack/f)==x
    assert run['transcript_sha256']==i['transcript_sha256']==sha256(d/'transcript.jsonl') and i['manual_annotations_sha256']==sha256(d/'manual-annotations.json') and i['criteria_sha256']==sha256(pack/'criteria.json')
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-minimal-application-fit-20261007-v1.json').read_text());assert run['versions']==cfg['runtime_pins'] and run['gpu']['name']=='NVIDIA RTX PRO 6000 Blackwell Server Edition'
    for key in ['model','revision','seed','max_length','generation_max_new_tokens','chat_template_kwargs']:assert run['config'][key]==cfg[key]
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(ROOT/'runs/aurora-minimal-application-fit-20261007-v1/adapter',local_files_only=True)
    assert c['id']==row['id']==v['id'] and c['input_ids']==row['input_ids']==tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
    assert tok.decode(row['output_ids'],skip_special_tokens=True)==row['output'] and hashlib.sha256(row['output'].encode()).hexdigest()==v['output_sha256'] and v['words']==len(row['output'].split())==80 and not row['at_output_cap']
    assert run['loaded_adapter_sha256']==sha256(ROOT/'runs/aurora-minimal-application-fit-20261007-v1/adapter/adapter_model.safetensors')
    for f,x in run['source_code_sha256'].items():assert sha256(d/Path(f).name)==x
    prev=run['previous_inspected_run'];assert prev['inspection_sha256']==sha256(ROOT/prev['run']/'inspection.json')
    original=ROOT/'data/prepared/minimal-application-fit-20261007-v1';assert sha256(pack/'criteria.json')==sha256(original/'criteria.json')
    oldcase=list(read_jsonl(original/'cases.jsonl'))[0];prefix=oldcase['prompt'][1]['content'].split('CURRENT HYPOTHETICAL NOTE',1)[0];assert c['prompt'][1]['content'].startswith(prefix)
    assert v['content_counts']=={'unmet':2,'met':4} and set(v['ratings'])=={'A1','A2','A3','A4','A5','A6'}
    r.update(verified_at=datetime.now(timezone.utc).isoformat(),new_model_outputs=20,uncapped=20,capped=0,all_twelve_owned_gpu_identities_exited=True,changed_state_probe={'content':v['content_counts'],'words':80,'component_pass':False,'source_prefix_unchanged':True,'original_six_criteria_unchanged':True,'scope':'Familiar-source/untrained-repaired-note adaptive probe; removealreadyrepairedaidgate showsstate-sensitiveplanning notyetlearned.'})
    r['resources'].append({'run':str(d.relative_to(ROOT)),'identity':run['identity'],'gpu':run['gpu'],'exited':True});r['next_decision']='Keepworkingfamiliar14unitpipeline, fixedsource/writer. Beforecountry/topicexpansion, addpairedapplication supervision withsamefacts anddifferentcurrentproposalstates, preserveoriginal83wordtarget andfrozencriteria, freezeanotheruntrainedstatefirst. No nextfit/queue/sweep prepared. Independentsemanticreview/nativeprediction/persona/autonomousmultiagent/strongOOD stillpending.'
    write_json(ROOT/'reports/source-status-composition-combined-20261007-v1.json',r);print(json.dumps({'status':'pass','new_outputs':20,'steps':96,'full14_point8':r['summaries']['aurora-actual-composed-writer-point8-20261007-v1'],'changed_state_probe':r['changed_state_probe']},indent=2))

if __name__=='__main__':main()
