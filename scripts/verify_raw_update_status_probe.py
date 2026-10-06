"""Replay direct-status controls without replacing full-memo grades."""
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
    tok=AutoTokenizer.from_pretrained(ROOT/'runs/aurora-raw-coverage-fit-20261006-v1/adapter',local_files_only=True);summary={};rows={};runs={};packs={}
    for arm in ('parent','new'):
        pack=ROOT/('data/prepared/raw-update-status-20261006-'+('v1-parent' if arm=='parent' else 'v1'));m=json.loads((pack/'manifest.json').read_text());c=list(read_jsonl(pack/'cases.jsonl'))[0]
        for name,h in m['files_sha256'].items():assert sha256(pack/name)==h
        hand=json.loads((pack/'manual-inspection.json').read_text());assert hand['all_selected_texts_read_complete'] and hand['manifest_sha256']==sha256(pack/'manifest.json')
        d=ROOT/('runs/aurora-raw-update-status-'+arm+'-20261006-v1');r=json.loads((d/'run.json').read_text());row=list(read_jsonl(d/'transcript.jsonl'))[0];i=json.loads((d/'inspection.json').read_text());v=i['reviews'][0]
        assert not m['training_authorized_for_this_pack'] and r['status']=='completed' and r['optimizer_steps']==0 and i['all_outputs_read_complete'] and i['all_reasoning_read_complete']
        assert i['transcript_sha256']==r['transcript_sha256']==sha256(d/'transcript.jsonl') and i['criteria_sha256']==sha256(pack/'criteria.json')
        assert row['id']==c['id']==v['id'] and v['all_output_read_complete'] and hashlib.sha256(row['output'].encode()).hexdigest()==v['output_sha256']
        assert row['input_ids']==tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False) and tok.decode(row['output_ids'],skip_special_tokens=True)==row['output']
        assert r['loaded_adapter_sha256']==m['adapter_sha256']==sha256(ROOT/m['adapter']/'adapter_model.safetensors') and not row['at_output_cap']
        for source,h in r['source_code_sha256'].items():assert sha256(d/Path(source).name)==h
        assert set(v['ratings'])==set(json.loads((pack/'criteria.json').read_text())['units']) and all(x['status'] in ['met','unmet','unratable'] for x in v['ratings'].values())
        summary[arm]={'core_status_units_met':sum(x['status']=='met' for x in v['ratings'].values()),'units':4,'words':len(row['output'].split()),'within100words':len(row['output'].split())<=100,'additional_wording_observations':v['additional_source_observations']}
        rows[arm]=row;runs[arm]=r;packs[arm]=pack
    assert rows['parent']['input_ids']==rows['new']['input_ids']
    for k in ('versions','source_code_sha256'):assert runs['parent'][k]==runs['new'][k]
    assert runs['parent']['gpu']['name']==runs['new']['gpu']['name']=='NVIDIA RTX PRO 6000 Blackwell Server Edition'
    for name in ('cases.jsonl','criteria.json','wps-statements.json','source-proof.json'):assert sha256(packs['parent']/name)==sha256(packs['new']/name)
    result={'status':'two_matched_direct_status_outputs_and_stored_core_annotations_replayed','new_public_generations':2,'new_optimizer_steps':0,'summary':summary,
        'scope':'Easier four-status diagnostic selected after full-memo ambiguity; no replacement of original grades or broad persona/task/OOD gain.',
        'interpretation':'Both models can identify current care/gate removal and historical/authority boundaries directly. Full-memo failure concerns missing requested recognition/trade-off; it alone does not prove lack of current-state understanding.',
        'independent_review_complete':False};write_json(a.output,result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
