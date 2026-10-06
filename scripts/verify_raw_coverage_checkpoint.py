"""Replay unchanged targets, real control provenance, two-pair fitting and six reviews."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import digest,read_jsonl,sha256,write_json

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    pack=ROOT/'data/prepared/raw-coverage-20261006-v1';m=json.loads((pack/'manifest.json').read_text());hand=json.loads((pack/'manual-inspection.json').read_text())
    for filename,h in m['files_sha256'].items():assert sha256(pack/filename)==h
    assert hand['all_selected_texts_read_complete'] and hand['manifest_sha256']==sha256(pack/'manifest.json')
    pairs=list(read_jsonl(pack/'pairs.jsonl'));audits=list(read_jsonl(pack/'pair-audit.jsonl'));cases=list(read_jsonl(pack/'cases.jsonl'));criteria=json.loads((pack/'criteria.json').read_text())
    assert len(pairs)==len(audits)==2 and len(cases)==6 and pairs[0]['chosen']==pairs[1]['chosen']
    proof=json.loads((pack/'pair-provenance.json').read_text());assert sha256(ROOT/proof['card_pair_original_file'])==proof['original_file_sha256']
    assert pairs[0]==list(read_jsonl(ROOT/proof['card_pair_original_file']))[0] and digest(pairs[0])==proof['card_pair_sha256']
    negative=proof['raw_negative'];neg=ROOT/negative['run'];assert sha256(neg/'transcript.jsonl')==negative['transcript_sha256'] and sha256(neg/'inspection.json')==negative['inspection_sha256']
    assert pairs[1]['rejected'][0]['content']==next(r['output'] for r in read_jsonl(neg/'transcript.jsonl') if r['id']==negative['case_id'])
    sources={}
    for family,filename,rawdir,recordfile in [('wps','wps-statements.json','data/raw/source-application-grounding-20261003-v1','record-8514.txt'),('mali','mali-statements.json','data/raw/coverage-objective-grounding-20261003-v1','record-9365.txt')]:
        sources[family]=json.loads((pack/filename).read_text());doc=(ROOT/rawdir/recordfile).read_text()
        for s in sources[family].values():assert doc[s['start']:s['end']].strip()==s['text'] and digest(s['text'])==s['text_digest']
        pr=json.loads((pack/('source-proof.json' if family=='wps' else 'mali-source-proof.json')).read_text())
        hashes=pr['wps_raw_files_sha256'] if family=='wps' else pr['files_sha256']
        for name,h in hashes.items():assert sha256(ROOT/rawdir/name)==h
    from transformers import AutoTokenizer
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-raw-coverage-20261006-v1.json').read_text());tok=AutoTokenizer.from_pretrained(ROOT/cfg['starting_adapter'],local_files_only=True)
    for i,(pair,audit) in enumerate(zip(pairs,audits)):
        assert pair['prompt']==cases[i]['prompt'] and digest(pair)==audit['pair_sha256']
        prefix=tok.apply_chat_template(pair['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
        assert prefix==audit['prompt_ids']
        for k in ('chosen','rejected'):
            full=tok.apply_chat_template(pair['prompt']+pair[k],tokenize=True,return_dict=False,enable_thinking=False)
            assert full[:len(prefix)]==prefix and full[len(prefix):]==audit[k+'_ids'] and len(full)<=8192
    assert (pack/'selected-card.txt').read_text() not in pairs[1]['prompt'][1]['content']
    runs={};outputs={};summary={}
    for arm in ('base','parent','fit'):
        d=ROOT/('runs/aurora-raw-coverage-'+arm+('-replay' if arm!='fit' else '')+'-20261006-v1');run=json.loads((d/'run.json').read_text());inspection=json.loads((d/'inspection.json').read_text());rows=list(read_jsonl(d/'transcript.jsonl'))
        assert len(rows)==len(inspection['reviews'])==6 and inspection['all_outputs_read_complete']
        assert run['transcript_sha256']==inspection['transcript_sha256']==sha256(d/'transcript.jsonl') and inspection['criteria_sha256']==sha256(pack/'criteria.json')
        assert run['pack_manifest_sha256']==sha256(pack/'manifest.json')
        for source,h in run['source_code_sha256'].items():assert sha256(d/Path(source).name)==h
        if arm!='fit':
            assert run['status']=='completed_cpu_replay' and run['optimizer_steps']==run['new_model_generations']==0 and run['original_actual_generations']==6
            assert len(run['source_links'])==6 and run['generation_helper_sha256']==sha256(ROOT/'scripts/run_aurora_qwen35_smoke.py')
            for link,row in zip(run['source_links'],rows):
                origin=ROOT/link['run'];original=json.loads((origin/'run.json').read_text())
                for k in ('run','transcript','inspection'):assert sha256(origin/(k+('.jsonl' if k=='transcript' else '.json')))==link[k+'_sha256']
                actual=next(r for r in read_jsonl(origin/'transcript.jsonl') if r['id']==row['id'])
                assert row['input_ids']==actual['input_ids'] and row['output_ids']==actual['output_ids'] and row['output']==actual['output'] and original['identity']==link['actual_identity']
                assert original['versions']==cfg['runtime_pins'] and original['gpu']['name']==run['gpu']['name']
                if arm=='parent':
                    loaded=original['serialization_checks']['files_sha256']['adapter_model.safetensors'] if original['mode']=='fit' else original['loaded_adapter_sha256']
                    assert loaded==cfg['starting_adapter_sha256']
                else:assert original['mode']=='base'
        else:assert run['status']=='completed' and run['optimizer_steps']==64
        results={}
        for case,row,review in zip(cases,rows,inspection['reviews']):
            assert case['id']==row['id']==review['id'] and review['all_output_read_complete']
            ids=tok.apply_chat_template(case['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
            assert ids==case['input_ids']==row['input_ids'] and len(ids)+2048<=8192 and tok.decode(row['output_ids'],skip_special_tokens=True)==row['output']
            assert hashlib.sha256(row['output'].encode()).hexdigest()==review['output_sha256']
            for s in sources[case['family']].values():assert s['text'] in case['prompt'][1]['content']
            expected={co+':'+k for co in ('FRA','GBR') for k,_ in criteria['wps']['common']+criteria['wps']['specific'][co]} if case['family']=='wps' else {u['id'] for u in criteria['mali']}
            assert set(review['ratings'])==expected and set(review['universal_checks'])==set(criteria['universal_checks'])
            assert set(review['synthesis_checks'])==(set(criteria['synthesis_checks']) if case['family']=='wps' else set())
            values=[*review['ratings'].values(),*review['universal_checks'].values(),*review['synthesis_checks'].values()]
            assert all(v['status'] in ('met','unmet','unratable') and v['reason'].strip() for v in values)
            results[case['id']]={'met':sum(v['status']=='met' for v in review['ratings'].values()),'unratable':sum(v['status']=='unratable' for v in review['ratings'].values()),'units':len(expected),
                'source_pass':not row['at_output_cap'] and not review.get('additional_source_fidelity_observations') and all(v['status']=='met' for v in values),'words':len(row['output'].split()),'at_cap':row['at_output_cap']}
        runs[arm]=run;outputs[arm]=rows;summary[arm]=results
    fit=runs['fit'];assert fit['config_sha256']==sha256(ROOT/'configs/posttraining/qwen35-raw-coverage-20261006-v1.json')
    for arm in ('base','parent'):
        assert [r['input_ids'] for r in outputs[arm]]==[r['input_ids'] for r in outputs['fit']] and runs[arm]['versions']==fit['versions']
        assert runs[arm]['gpu']['name']==fit['gpu']['name']=='NVIDIA RTX PRO 6000 Blackwell Server Edition'
    checks=fit['optimization_checks']['rank_checks'][0];mask=fit['mask_audit']
    assert checks['steps']==checks['microbatches']==checks['gradient_checks']==64 and checks['pair_presentations']=={'card':32,'raw':32}
    assert checks['actual_sequence_tokens']==32*mask['sequence_tokens_once'] and checks['actual_target_tokens']==32*(mask['chosen_tokens_once']+mask['rejected_tokens_once'])
    assert mask['actual_trainer_token_ids_and_masks_checked'] and checks['all_adapter_tensors_finite'] and checks['changed_adapter_tensors']>0
    assert fit['method']['reference_tensor_digest_before']==fit['method']['reference_tensor_digest_after']==checks['initial_adapter_digest']
    assert len(fit['actual_objective_guard']['pairs'])==2 and all(p['absolute_difference']<1e-4 for p in fit['actual_objective_guard']['pairs'])
    assert sha256(ROOT/cfg['starting_adapter']/'adapter_config.json')==cfg['starting_adapter_config_sha256']
    assert fit['serialization_checks']['saved_tensors_equal'] and fit['serialization_checks']['reload_verified_after_state_perturbation']
    for name,h in fit['serialization_checks']['files_sha256'].items():assert sha256(ROOT/'runs/aurora-raw-coverage-fit-20261006-v1/adapter'/name)==h
    result={'status':'two_input_formats_same_target_actual_controls_masks_reference_steps_saved_weights_and_reviews_replayed',
        'new_public_model_generations':6,'control_outputs_replayed':12,'new_optimizer_steps':64,'new_branch_steps':256,'cumulative_aurora_qwen35_steps':510,'reference_qwen25_steps':582,
        'summary':summary,'actual_pair_presentations':checks['pair_presentations'],'actual_sequence_tokens':checks['actual_sequence_tokens'],'actual_preference_completion_tokens':checks['actual_target_tokens'],
        'training_seconds':fit['training_seconds'],'scope':m['source_scope'],'comparison_scope':m['comparison_scope'],'independent_review_complete':False}
    write_json(a.output,result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
