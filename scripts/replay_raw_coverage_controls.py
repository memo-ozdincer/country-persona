"""Explicit CPU token replays of six existing actual outputs per control arm."""
import copy
import json
import sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,write_json,write_jsonl

def main():
    from transformers import AutoTokenizer
    pack=ROOT/'data/prepared/raw-coverage-20261006-v1';m=json.loads((pack/'manifest.json').read_text());cases=list(read_jsonl(pack/'cases.jsonl'))
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-raw-coverage-20261006-v1.json').read_text());tok=AutoTokenizer.from_pretrained(ROOT/cfg['starting_adapter'],local_files_only=True)
    for name,h in m['files_sha256'].items():assert sha256(pack/name)==h
    for arm,first,last in [('base','aurora-factual-anchor-base-20261006-v1','aurora-factual-repair-base-20261006-v1'),
                           ('parent','aurora-factual-anchor-fit-20261006-v1','aurora-factual-repair-new-20261006-v1')]:
        out=ROOT/('runs/aurora-raw-coverage-'+arm+'-replay-20261006-v1')
        if out.exists():raise ValueError('Fresh control replay required')
        out.mkdir();outputs=[];ratings=[];links=[];versions=None;gpu_name=None;helper=None
        for i,c in enumerate(cases):
            origin=ROOT/'runs'/(first if i<5 else last);run=json.loads((origin/'run.json').read_text());review=json.loads((origin/'inspection.json').read_text())
            assert run['status']=='completed' and review['all_outputs_read_complete'] and review['transcript_sha256']==run['transcript_sha256']==sha256(origin/'transcript.jsonl')
            source=next(r for r in read_jsonl(origin/'transcript.jsonl') if r['id']==c['id']);rating=next(v for v in review['reviews'] if v['id']==c['id'])
            if arm=='parent':
                actual=run['serialization_checks']['files_sha256']['adapter_model.safetensors'] if i<5 else run['loaded_adapter_sha256']
                assert actual==cfg['starting_adapter_sha256']==sha256(ROOT/cfg['starting_adapter']/'adapter_model.safetensors')
            else:assert run['mode']=='base'
            for k in ('model','revision','generation_max_new_tokens','max_length','chat_template_kwargs'):assert run['config'][k]==cfg[k]
            h=run['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py'];assert h==sha256(ROOT/'scripts/run_aurora_qwen35_smoke.py')
            if versions is None:versions=run['versions'];gpu_name=run['gpu']['name'];helper=h
            assert versions==run['versions']==cfg['runtime_pins'] and gpu_name==run['gpu']['name']=='NVIDIA RTX PRO 6000 Blackwell Server Edition'
            ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
            assert ids==c['input_ids']==source['input_ids'] and tok.decode(source['output_ids'],skip_special_tokens=True)==source['output']
            outputs.append({**source,'family':c['family'],'condition':c['condition'],'scope':m['source_scope'],'replay_only_no_new_generation':True})
            ratings.append(copy.deepcopy(rating));links.append({'case_id':c['id'],'run':str(origin.relative_to(ROOT)),
                'run_sha256':sha256(origin/'run.json'),'transcript_sha256':sha256(origin/'transcript.jsonl'),'inspection_sha256':sha256(origin/'inspection.json'),
                'actual_identity':run['identity'],'actual_gpu':run['gpu'],'source_code_sha256':run['source_code_sha256']})
        write_jsonl(out/'transcript.jsonl',outputs)
        record={'status':'completed_cpu_replay','mode':arm,'protocol':'explicit_cpu_token_replay_of_actual_model_outputs','created_at':datetime.now(timezone.utc).isoformat(),
            'config':cfg,'pack_manifest_sha256':sha256(pack/'manifest.json'),'generation_helper_sha256':helper,'versions':versions,'gpu':{'name':gpu_name},
            'optimizer_steps':0,'new_model_generations':0,'original_actual_generations':6,'source_links':links,'transcript_sha256':sha256(out/'transcript.jsonl'),
            'source_code_sha256':{str(Path(__file__).relative_to(ROOT)):sha256(Path(__file__))}}
        if arm=='parent':record['loaded_adapter_sha256']=cfg['starting_adapter_sha256']
        (out/Path(__file__).name).write_bytes(Path(__file__).read_bytes());write_json(out/'run.json',record)
        write_json(out/'stored-annotations.json',{'reviews':ratings,'criteria_sha256':sha256(pack/'criteria.json'),'scope':'Original annotations preserved. Complete outputs must be reread before binding a fresh inspection.'})
        print(json.dumps({'arm':arm,'new_gpu_generations':0,'actual_outputs_replayed':6,'all_input_output_ids_replayed':True}))

if __name__=='__main__':main()
