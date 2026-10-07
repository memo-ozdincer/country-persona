"""Combine inspected native fits with actual two-clause quote/status controls."""
import json,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,write_json
from verify_two_context_country import exited
from verify_extraction_diversity import main as verify_fits

def main():
    verify_fits();r=json.loads((ROOT/'reports/extraction-diversity-checkpoint-20261007-v1.json').read_text());summaries,resources={},[];inputs=[]
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(ROOT/'runs/aurora-extraction-diversity-fit64-20261007-v1/adapter',local_files_only=True)
    for name in ['aurora-modal-status-base-20261007-v1','aurora-modal-status-fit64-20261007-v1']:
        d=ROOT/'runs'/name;run=json.loads((d/'run.json').read_text());i=json.loads((d/'inspection.json').read_text());pack=ROOT/run['config']['pack'];m=json.loads((pack/'manifest.json').read_text());h=json.loads((pack/'manual-inspection.json').read_text());c=list(read_jsonl(pack/'cases.jsonl'))[0];row=list(read_jsonl(d/'transcript.jsonl'))[0];v=i['reviews'][0]
        assert run['status']=='completed' and run['optimizer_steps']==0 and exited(run['identity']) and i['all_outputs_read_complete']
        assert run['pack_manifest_sha256']==h['manifest_sha256']==sha256(pack/'manifest.json') and h['all_selected_texts_read_complete'] and not m['training_authorized_for_this_pack']
        for f,x in m['files_sha256'].items():assert sha256(pack/f)==x
        assert run['transcript_sha256']==i['transcript_sha256']==sha256(d/'transcript.jsonl') and i['manual_annotations_sha256']==sha256(d/'manual-annotations.json') and i['criteria_sha256']==sha256(pack/'criteria.json')
        assert row['id']==c['id']==v['id'] and row['input_ids']==c['input_ids'] and tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)==row['input_ids']
        assert tok.decode(row['output_ids'],skip_special_tokens=True)==row['output'] and v['output_sha256']==hashlib.sha256(row['output'].encode()).hexdigest() and not row['at_output_cap']
        assert run['gpu']['name']=='NVIDIA RTX PRO 6000 Blackwell Server Edition'
        fit_config=json.loads((ROOT/'configs/posttraining/qwen35-extraction-diversity-fit64-20261007-v1.json').read_text())
        for key in ['model','revision','seed','max_length','generation_max_new_tokens','chat_template_kwargs']:
            assert run['config'][key]==fit_config[key]
        assert set(v['ratings'])=={'S1','S2','S3','S4'} and v['task_max_words']==100 and v['words']==len(row['output'].split())<=100
        quote1='The resolutions adopted by the Council must finally be implemented.';quote2='The Council should be able to unanimously call for de-escalation.'
        source=json.loads((pack/'sources.json').read_text())['gaza24']['FRA']['text'];assert all(q in source and q in row['output'] for q in [quote1,quote2])
        for f,x in run['source_code_sha256'].items():assert sha256(d/Path(f).name)==x
        previous=run['previous_inspected_run'];assert previous['inspection_sha256']==sha256(ROOT/previous['run']/'inspection.json')
        assert run['versions']==json.loads((ROOT/'configs/posttraining/qwen35-extraction-diversity-fit64-20261007-v1.json').read_text())['runtime_pins']
        if run['mode']=='adapter':assert run['loaded_adapter_sha256']==sha256(ROOT/'runs/aurora-extraction-diversity-fit64-20261007-v1/adapter/adapter_model.safetensors')
        summaries[name]={k:v[k] for k in ['content_counts','words','source_only_task_pass']};summaries[name]['scope']='four-unit/two-clause diagnostic,100words; classlabel mismatch retained, not8compound summary'
        resources.append({'run':str(d.relative_to(ROOT)),'identity':run['identity'],'gpu':run['gpu'],'exited':True});inputs.append(row['input_ids'])
    assert inputs[0]==inputs[1]
    r.update(verified_at=datetime.now(timezone.utc).isoformat(),modal_summaries=summaries,resources=r['resources']+resources,all_six_owned_gpu_identities_exited=True,new_model_outputs=12,uncapped=11,capped=1,modal_control_input_tokens_identical=True,next_decision=json.loads((ROOT/'runs/aurora-modal-status-fit64-20261007-v1/inspection.json').read_text())['decision'])
    write_json(ROOT/'reports/extraction-diversity-combined-20261007-v1.json',r);print(json.dumps({'status':'pass','new_outputs':12,'uncapped':11,'capped':1,'new_optimizer_steps':192,'modal_summaries':summaries},indent=2))

if __name__=='__main__':main()
