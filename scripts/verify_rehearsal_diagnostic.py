"""Replay two inspected saved-weight probes; distinguish source coverage from format."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,write_json

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    pack=ROOT/'data/prepared/rehearsal-diagnostic-20261006-v1';manifest=json.loads((pack/'manifest.json').read_text())
    for name,expected in manifest['files_sha256'].items():assert sha256(pack/name)==expected
    assert not manifest['training_authorized_for_this_pack']
    assert sha256(ROOT/'runs/aurora-synthesis-rehearsal-fit-20261006-v1/inspection.json')==manifest['selection_inspection_sha256']
    cases=list(read_jsonl(pack/'cases.jsonl'));criteria=json.loads((pack/'criteria.json').read_text())
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(ROOT/'runs/aurora-synthesis-rehearsal-fit-20261006-v1/adapter',local_files_only=True)
    summaries={};traces={};runs={}
    for arm in ('parent','fit'):
        directory=ROOT/('runs/aurora-rehearsal-diagnostic-'+arm+'-20261006-v1')
        run=json.loads((directory/'run.json').read_text());review=json.loads((directory/'inspection.json').read_text())
        outputs=list(read_jsonl(directory/'transcript.jsonl'))
        assert run['status']=='completed' and run['mode']=='adapter' and len(outputs)==len(review['reviews'])==2 and review['all_outputs_read_complete']
        assert sha256(directory/'transcript.jsonl')==run['transcript_sha256']==review['transcript_sha256']
        assert sha256(pack/'manifest.json')==run['pack_manifest_sha256'] and sha256(pack/'criteria.json')==review['criteria_sha256']
        adapter=(ROOT/'runs/aurora-minimal-country-fit-20261005-v4/adapter' if arm=='parent' else ROOT/'runs/aurora-synthesis-rehearsal-fit-20261006-v1/adapter')
        assert sha256(adapter/'adapter_model.safetensors')==run['loaded_adapter_sha256']
        for path,expected in run['source_code_sha256'].items():assert sha256(directory/Path(path).name)==expected
        summary={}
        for case,output,rating in zip(cases,outputs,review['reviews']):
            assert case['id']==output['id']==rating['id'] and rating['all_output_read_complete']
            assert hashlib.sha256(output['output'].encode()).hexdigest()==rating['output_sha256']
            ids=tokenizer.apply_chat_template(case['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,**run['config']['chat_template_kwargs'])
            assert ids==output['input_ids'] and tokenizer.decode(output['output_ids'],skip_special_tokens=True)==output['output']
            expected=(set(criteria['wps_direct']) if case['family']=='wps_direct' else {c+':'+u['id'] for c,r in criteria['ukraine']['national_policy_rubrics'].items() for u in r['criteria']})
            assert set(rating['ratings'])==expected
            values=[*rating['ratings'].values(),*rating.get('universal_checks',{}).values(),*rating.get('synthesis_checks',{}).values()]
            assert all(v['status'] in {'met','unmet','unratable'} and v['reason'].strip() for v in values)
            summary[case['id']]={'met':sum(v['status']=='met' for v in rating['ratings'].values()),'unratable':sum(v['status']=='unratable' for v in rating['ratings'].values()),
                                'units':len(expected),'source_criteria_pass':not output['at_output_cap'] and all(v['status']=='met' for v in values),'words':len(output['output'].split()),'at_output_cap':output['at_output_cap'],
                                'format_observation':rating.get('format_observation',{})}
        summaries[arm]=summary;traces[arm]=outputs;runs[arm]=run
    assert [r['input_ids'] for r in traces['parent']]==[r['input_ids'] for r in traces['fit']]
    for key in ('source_code_sha256','versions'):assert runs['parent'][key]==runs['fit'][key]
    assert runs['parent']['gpu']['name']==runs['fit']['gpu']['name']=='NVIDIA RTX PRO 6000 Blackwell Server Edition'
    result={'status':'saved_weight_diagnostic_tokens_and_stored_annotations_replayed','new_model_answers':4,'new_optimizer_steps':0,'summary':summaries,
            'new_fit_cold_saved_adapter_sha256':runs['fit']['loaded_adapter_sha256'],'actual_input_output_tokens_replayed':True,
            'scope':'Same sources/minimal prompt variation and one full UK source. Parent/new saved weights only; no unadapted base arm or new fitting. Source criteria pass does not establish80word/2–3sentence compliance or persona/multi-agent improvement.'}
    write_json(args.output,result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
