"""Replay one legitimate-repair development scenario across three weights."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,write_json

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(ROOT/'runs/aurora-factual-anchor-fit-20261006-v1/adapter',local_files_only=True)
    summary={};outputs={};runs={};packs={}
    for arm in ('base','parent','new'):
        pack=ROOT/('data/prepared/factual-repair-20261006-'+('v1-parent' if arm=='parent' else 'v1'))
        m=json.loads((pack/'manifest.json').read_text());c=list(read_jsonl(pack/'cases.jsonl'))[0];criteria=json.loads((pack/'criteria.json').read_text())
        for filename,h in m['files_sha256'].items():assert sha256(pack/filename)==h
        hand=json.loads((pack/'manual-inspection.json').read_text());assert hand['all_selected_texts_read_complete'] and hand['manifest_sha256']==sha256(pack/'manifest.json')
        assert not m['training_authorized_for_this_pack']
        d=ROOT/('runs/aurora-factual-repair-'+arm+'-20261006-v1');run=json.loads((d/'run.json').read_text());inspection=json.loads((d/'inspection.json').read_text());row=list(read_jsonl(d/'transcript.jsonl'))[0];v=inspection['reviews'][0]
        assert run['status']=='completed' and run['optimizer_steps']==0 and inspection['all_outputs_read_complete'] and inspection['all_reasoning_read_complete']
        assert run['transcript_sha256']==inspection['transcript_sha256']==sha256(d/'transcript.jsonl') and inspection['criteria_sha256']==sha256(pack/'criteria.json')
        assert row['id']==c['id']==v['id'] and v['all_output_read_complete'] and hashlib.sha256(row['output'].encode()).hexdigest()==v['output_sha256']
        ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
        assert row['input_ids']==ids and len(ids)+2048<=8192 and row['protocol_status']=='public_answer' and not row['reasoning_ids']
        assert tok.decode(row['public_ids'],skip_special_tokens=True)==row['output']
        if arm!='base':assert run['loaded_adapter_sha256']==m['adapter_sha256']==sha256(ROOT/m['adapter']/'adapter_model.safetensors')
        for source,h in run['source_code_sha256'].items():assert sha256(d/Path(source).name)==h
        assert set(v['ratings'])=={co+':'+k for co in ('FRA','GBR') for k,_ in criteria['wps']['common']+criteria['wps']['specific'][co]}
        assert set(v['universal_checks'])==set(criteria['universal_checks']) and set(v['synthesis_checks'])==set(criteria['synthesis_checks'])
        checks=[*v['ratings'].values(),*v['universal_checks'].values(),*v['synthesis_checks'].values()]
        assert all(x['status'] in ('met','unmet','unratable') and x['reason'].strip() for x in checks)
        summary[arm]={'met':sum(x['status']=='met' for x in v['ratings'].values()),'unratable':sum(x['status']=='unratable' for x in v['ratings'].values()),'units':24,
            'current_repair_recognized':all(v['ratings'][co+':H5']['status']=='met' for co in ('FRA','GBR')),
            'source_pass':not row['at_output_cap'] and not v.get('additional_source_fidelity_observations') and all(x['status']=='met' for x in checks),
            'words':len(row['output'].split()),'within_word_limit':len(row['output'].split())<=300,'at_cap':row['at_output_cap']}
        outputs[arm]=row;runs[arm]=run;packs[arm]=pack
    for arm in ('parent','new'):
        assert outputs[arm]['input_ids']==outputs['base']['input_ids']
        for k in ('versions','source_code_sha256'):assert runs[arm][k]==runs['base'][k]
        assert runs[arm]['gpu']['name']==runs['base']['gpu']['name']=='NVIDIA RTX PRO 6000 Blackwell Server Edition'
        for name in ('cases.jsonl','criteria.json','wps-statements.json','source-proof.json'):assert sha256(packs[arm]/name)==sha256(packs['base']/name)
    result={'status':'three_matched_saved_weight_legitimate_repair_outputs_and_stored_annotations_replayed','new_model_generations':3,'new_optimizer_steps':0,
        'summary':summary,'scope':'Same-exposed-event post-fit development challenge; correct current repair is distinct from historical language omissions, no new national statement/vote label.',
        'independent_review_complete':False}
    write_json(a.output,result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
