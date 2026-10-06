"""Replay source spans, matched tokens, real optimization and stored annotations."""
import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import digest,read_jsonl,sha256,write_json

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    pack=ROOT/'data/prepared/factual-anchor-20261006-v1';m=json.loads((pack/'manifest.json').read_text())
    for name,h in m['files_sha256'].items():assert sha256(pack/name)==h
    hand=json.loads((pack/'manual-inspection.json').read_text());assert hand['all_selected_texts_read_complete'] and hand['manifest_sha256']==sha256(pack/'manifest.json')
    proof=json.loads((pack/'mali-source-proof.json').read_text());raw=ROOT/proof['raw_directory']
    for name,h in proof['files_sha256'].items():assert sha256(raw/name)==h
    wps_proof=json.loads((pack/'source-proof.json').read_text());wps_raw=ROOT/'data/raw/source-application-grounding-20261003-v1'
    for name,h in wps_proof['wps_raw_files_sha256'].items():assert sha256(wps_raw/name)==h
    sources={}
    for family,sourcefile,rawdir,recordfile in [('wps','wps-statements.json',wps_raw,'record-8514.txt'),('mali','mali-statements.json',raw,'record-9365.txt')]:
        sources[family]=json.loads((pack/sourcefile).read_text());doc=(rawdir/recordfile).read_text()
        for s in sources[family].values():assert doc[s['start']:s['end']].strip()==s['text'] and digest(s['text'])==s['text_digest']
    pair=list(read_jsonl(pack/'pairs.jsonl'))[0];audit=list(read_jsonl(pack/'pair-audit.jsonl'))[0]
    assert digest(pair)==audit['pair_sha256'] and pair['chat_template_kwargs']=={'enable_thinking':False}
    target=json.loads((pack/'target-audit.json').read_text());binding=target['negative_provenance'];neg=ROOT/binding['run']
    assert sha256(neg/'transcript.jsonl')==binding['transcript_sha256'] and sha256(neg/'inspection.json')==binding['inspection_sha256']
    assert pair['rejected'][0]['content']==list(read_jsonl(neg/'transcript.jsonl'))[0]['output']
    assert pair['chosen'][0]['content']==target['preferred_text'] and len(target['preferred_text'].split())==target['words']<=300
    cases=list(read_jsonl(pack/'cases.jsonl'));criteria=json.loads((pack/'criteria.json').read_text());assert len(cases)==5
    from transformers import AutoTokenizer
    parent=ROOT/'runs/aurora-synthesis-rehearsal-fit-20261006-v1/adapter';tok=AutoTokenizer.from_pretrained(parent,local_files_only=True)
    original_parent_lock=json.loads((ROOT/'data/prepared/country-source-bridge-20261006-v1/manifest.json').read_text())
    assert sha256(parent/'adapter_config.json')==original_parent_lock['adapter_config_sha256']
    ids=tok.apply_chat_template(pair['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
    assert ids==audit['prompt_ids']==cases[0]['input_ids'] and pair['prompt']==cases[0]['prompt']
    for k in ('chosen','rejected'):
        full=tok.apply_chat_template(pair['prompt']+pair[k],tokenize=True,return_dict=False,enable_thinking=False)
        assert full[:len(ids)]==ids and full[len(ids):]==audit[k+'_ids']
    runs={};outputs={};summary={}
    for arm in ('base','parent','fit'):
        d=ROOT/('runs/aurora-factual-anchor-'+arm+'-20261006-v1');r=json.loads((d/'run.json').read_text());review=json.loads((d/'inspection.json').read_text())
        rows=list(read_jsonl(d/'transcript.jsonl'));assert r['status']=='completed' and len(rows)==len(cases)==len(review['reviews'])
        assert review['all_outputs_read_complete'] and r['transcript_sha256']==review['transcript_sha256']==sha256(d/'transcript.jsonl')
        assert review['criteria_sha256']==sha256(pack/'criteria.json') and r['pack_manifest_sha256']==sha256(pack/'manifest.json')
        assert sha256(ROOT/('configs/posttraining/qwen35-factual-anchor-20261006-v1.json'))==r['config_sha256']
        for source,h in r['source_code_sha256'].items():assert sha256(d/Path(source).name)==h
        if arm!='base':assert r['loaded_adapter_sha256']==sha256(parent/'adapter_model.safetensors')
        results={}
        for c,row,v in zip(cases,rows,review['reviews']):
            assert c['id']==row['id']==v['id'] and v['all_output_read_complete']
            assert hashlib.sha256(row['output'].encode()).hexdigest()==v['output_sha256']
            assert row['input_ids']==c['input_ids']==tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
            assert row['input_ids_digest']==digest(row['input_ids']) and tok.decode(row['output_ids'],skip_special_tokens=True)==row['output']
            assert len(row['input_ids'])+r['config']['generation_max_new_tokens']<=r['config']['max_length']
            for s in sources[c['family']].values():assert s['text'] in c['prompt'][1]['content']
            unitkeys={country+':'+k for country in ('FRA','GBR') for k,_ in criteria['wps']['common']+criteria['wps']['specific'][country]} if c['family']=='wps' else {u['id'] for u in criteria['mali']}
            assert set(v['ratings'])==unitkeys and set(v['universal_checks'])==set(criteria['universal_checks'])
            assert set(v['synthesis_checks'])==(set(criteria['synthesis_checks']) if c['family']=='wps' else set())
            allchecks=[*v['ratings'].values(),*v['universal_checks'].values(),*v['synthesis_checks'].values()]
            assert all(x['status'] in {'met','unmet','unratable'} and x['reason'].strip() for x in allchecks)
            results[c['id']]={'met':sum(x['status']=='met' for x in v['ratings'].values()),'unratable':sum(x['status']=='unratable' for x in v['ratings'].values()),'units':len(unitkeys),
                'source_pass':not row['at_output_cap'] and not v.get('additional_source_fidelity_observations') and all(x['status']=='met' for x in allchecks),
                'words':len(row['output'].split()),'at_cap':row['at_output_cap']}
        runs[arm]=r;outputs[arm]=rows;summary[arm]=results
    for arm in ('parent','fit'):
        for k in ('versions','source_code_sha256','gpu'):assert (runs[arm][k] if k!='gpu' else runs[arm][k]['name'])==(runs['base'][k] if k!='gpu' else runs['base'][k]['name'])
        assert [r['input_ids'] for r in outputs[arm]]==[r['input_ids'] for r in outputs['base']]
    fit=runs['fit'];mask=fit['mask_audit'];checks=fit['optimization_checks']['rank_checks'][0]
    assert fit['optimizer_steps']==checks['steps']==checks['gradient_checks']==checks['microbatches']==32 and checks['changed_adapter_tensors']>0
    assert checks['actual_sequence_tokens']==32*mask['sequence_tokens_once'] and checks['actual_target_tokens']==32*(mask['chosen_tokens_once']+mask['rejected_tokens_once'])
    assert mask['actual_trainer_token_ids_and_masks_checked'] and mask['prompt_and_padding_excluded'] and fit['matched_input_tokens']
    method=fit['method'];assert method['reference_tensor_digest_before']==method['reference_tensor_digest_after']==checks['initial_adapter_digest']
    guard=fit['actual_objective_guard'];assert guard['loss_types']==['sigmoid','sft'] and guard['loss_weights']==[1.,1.] and guard['absolute_difference']<1e-4
    assert guard['real_pair_native_masks'] and guard['optimizer_steps']==0 and not method['additional_approximate_kl'] and not method['introspection']
    for name,h in fit['serialization_checks']['files_sha256'].items():assert sha256(ROOT/'runs/aurora-factual-anchor-fit-20261006-v1/adapter'/name)==h
    assert fit['serialization_checks']['reload_verified_after_state_perturbation'] and fit['serialization_checks']['saved_tensors_equal']
    assert datetime.fromisoformat(m['created_at'])<datetime.fromisoformat(fit['created_at'])
    clean_dir=ROOT/'runs/aurora-factual-anchor-pair-metrics-20261006-v1';clean=json.loads((clean_dir/'run.json').read_text())
    assert clean['status']=='clean_single_fitted_pair_metrics_replayed' and clean['optimizer_steps']==0 and clean['new_public_model_generations']==0
    assert clean['fit_run_sha256']==sha256(ROOT/'runs/aurora-factual-anchor-fit-20261006-v1/run.json') and clean['reference_matches_original']
    assert clean['loaded_tensor_digest']==checks['final_adapter_digest'] and clean['loaded_saved_adapter_sha256']==sha256(ROOT/'runs/aurora-factual-anchor-fit-20261006-v1/adapter/adapter_model.safetensors')
    for source,h in clean['source_code_sha256'].items():assert sha256(clean_dir/Path(source).name)==h
    assert clean['versions']==runs['base']['versions'] and clean['gpu']['name']==runs['base']['gpu']['name']
    result={'status':'one_pair_sources_tokens_reference_objective_steps_saved_weights_and_stored_annotations_replayed',
        'new_model_answers':15,'new_optimizer_steps':32,'cumulative_aurora_qwen35_steps':446,'selected_new_branch_steps':192,'reference_qwen25_steps':582,
        'summary':summary,'training_seconds':fit['training_seconds'],'actual_sequence_tokens':checks['actual_sequence_tokens'],'actual_preference_completion_tokens':checks['actual_target_tokens'],
        'independent_review_complete':False,'scope':m['source_scope'],'clean_cold_fitted_pair_metrics_verified':True,
        'objective_isolation':'This initial anchored trial does not isolate DPO benefit over matched chosen-only SFT.'}
    write_json(a.output,result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
