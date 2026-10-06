"""Replay unchanged positives/artificial one-clause negatives,12cases,4arms and native DPO+NLL evidence."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import digest,read_jsonl,sha256,write_json

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    pack=ROOT/'data/prepared/conditional-india-fit-20261006-v2';m=json.loads((pack/'manifest.json').read_text());hand=json.loads((pack/'manual-inspection.json').read_text())
    for filename,h in m['files_sha256'].items():assert sha256(pack/filename)==h
    assert hand['all_selected_texts_read_complete'] and hand['manifest_sha256']==sha256(pack/'manifest.json')
    pairs=list(read_jsonl(pack/'pairs.jsonl'));audits=list(read_jsonl(pack/'pair-audit.jsonl'));cases=list(read_jsonl(pack/'cases.jsonl'));criteria=json.loads((pack/'criteria.json').read_text())
    assert len(pairs)==len(audits)==6 and len(cases)==17 and pairs[0]['chosen']==pairs[1]['chosen']
    proof=json.loads((pack/'data-provenance.json').read_text());old=ROOT/proof['old_pack'];recent=ROOT/proof['recent_pack']
    assert sha256(old/'manifest.json')==proof['old_manifest_sha256'] and sha256(old/'pairs.jsonl')==proof['old_pairs_sha256']
    assert pairs[:4]==list(read_jsonl(old/'pairs.jsonl'))
    assert sha256(recent/'cases.jsonl')==proof['recent_cases_sha256']
    for actual,original in zip(cases[:12],read_jsonl(recent/'cases.jsonl'),strict=True):
        normalized=dict(actual)
        if 'input_ids_digest' not in original:
            assert normalized.pop('input_ids_digest')==digest(original['input_ids'])
        assert normalized==original
    assert sha256(recent/'criteria.json')==proof['recent_criteria_sha256']
    original_criteria=json.loads((recent/'criteria.json').read_text())
    for key,value in original_criteria.items():
        if key=='case_overrides':
            for id,v in value.items():assert criteria[key][id]==v
        else:assert criteria[key]==value
    assert criteria['case_overrides']['sanctions-ind-authority-raw']==criteria['case_overrides']['sanctions-ind-authority-plan']
    assert len(cases[-4:])==4 and all(c['family']=='haiti' for c in cases[-4:])
    negatives=json.loads((pack/'actual-negative-provenance.json').read_text());assert negatives['all_new_negatives_actual_parent_outputs'] and not negatives['negative_gradient_enabled']
    for link in negatives['links']:
        origin=ROOT/link['run'];actual=json.loads((origin/'run.json').read_text())
        for name in ('run','transcript','inspection'):assert sha256(origin/(name+('.jsonl' if name=='transcript' else '.json')))==link[name+'_sha256']
        row=next(r for r in read_jsonl(origin/'transcript.jsonl') if r['id']==link['id'])
        assert pairs[link['pair_index']]['rejected'][0]['content']==row['output']
        case=next(c for c in cases if c['id']==link['id']);assert row['input_ids']==case['input_ids'] and actual['identity']==link['actual_identity']
    epack=ROOT/'data/prepared/conditional-india-eval-20261006-v2';em=json.loads((epack/'manifest.json').read_text());eh=json.loads((epack/'manual-inspection.json').read_text())
    assert not em['training_authorized_for_this_pack'] and eh['all_selected_texts_read_complete'] and eh['manifest_sha256']==sha256(epack/'manifest.json')
    for name,h in em['files_sha256'].items():assert sha256(epack/name)==h
    assert list(read_jsonl(epack/'cases.jsonl'))==cases[12:] and sha256(epack/'criteria.json')==sha256(pack/'criteria.json')
    sources={}
    for family,filename,rawdir,recordfile in [('wps','wps-statements.json','data/raw/source-application-grounding-20261003-v1','record-8514.txt'),('mali','mali-statements.json','data/raw/coverage-objective-grounding-20261003-v1','record-9365.txt'),('sanctions','sanctions-statements.json','data/raw/source-plan-grounding-20261002-v1','record-9214.txt')]:
        sources[family]=json.loads((pack/filename).read_text());doc=(ROOT/rawdir/recordfile).read_text()
        for s in sources[family].values():assert doc[s['start']:s['end']].strip()==s['text'] and digest(s['text'])==s['text_digest']
        pr=json.loads((pack/({'wps':'source-proof.json','mali':'mali-source-proof.json','sanctions':'sanctions-source-proof.json'}[family])).read_text())
        hashes=pr['wps_raw_files_sha256'] if family=='wps' else pr['files_sha256']
        for name,h in hashes.items():assert sha256(ROOT/rawdir/name)==h
    import re
    sources['haiti']=json.loads((pack/'haiti-statements.json').read_text());hr=ROOT/'data/raw/conditional-india-haiti-grounding-20261006-v1';ht=(hr/'record-9430.txt').read_text()
    for v in sources['haiti'].values():
        assert ht[v['start']:v['end']].strip()==v['raw_text'] and digest(v['raw_text'])==v['raw_text_digest']
        assert re.sub('\u00ad\\s*','',v['raw_text'])==v['text'] and digest(v['text'])==v['text_digest']
    hp=json.loads((pack/'haiti-source-proof.json').read_text())
    for name,h in hp['files_sha256'].items():assert sha256(hr/name)==h
    assert json.loads((hr/'source-hand-inspection.json').read_text())['all_selected_sources_read_complete']
    from transformers import AutoTokenizer
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-conditional-india-20261006-v2.json').read_text());tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True)
    for i,(pair,audit) in enumerate(zip(pairs,audits)):
        assert pair['prompt']==cases[[0,1,5,3,9,12][i]]['prompt'] and digest(pair)==audit['pair_sha256']
        prefix=tok.apply_chat_template(pair['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
        assert prefix==audit['prompt_ids']
        for k in ('chosen','rejected'):
            full=tok.apply_chat_template(pair['prompt']+pair[k],tokenize=True,return_dict=False,enable_thinking=False)
            assert full[:len(prefix)]==prefix and full[len(prefix):]==audit[k+'_ids'] and len(full)<=8192
    assert all((pack/'selected-card.txt').read_text() not in pair['prompt'][1]['content'] for pair in pairs[1:])
    runs={};outputs={};summary={}
    for arm in ('base','parent','chosen','fit'):
        d=ROOT/({'base':'runs/aurora-conditional-india-base-replay-20261006-v2','parent':'runs/aurora-conditional-india-parent-replay-20261006-v2','chosen':'runs/aurora-conditional-india-chosen-replay-20261006-v2','fit':'runs/aurora-conditional-india-fit-20261006-v2'}[arm]);run=json.loads((d/'run.json').read_text());inspection=json.loads((d/'inspection.json').read_text());rows=list(read_jsonl(d/'transcript.jsonl'))
        assert len(rows)==len(inspection['reviews'])==17 and inspection['all_outputs_read_complete']
        assert run['transcript_sha256']==inspection['transcript_sha256']==sha256(d/'transcript.jsonl') and inspection['criteria_sha256']==sha256(pack/'criteria.json')
        assert run['pack_manifest_sha256']==sha256(pack/'manifest.json')
        for source,h in run['source_code_sha256'].items():assert sha256(d/Path(source).name)==h
        if arm in ('base','parent','chosen'):
            assert run['status']=='completed_cpu_replay' and run['optimizer_steps']==run['new_model_generations']==0 and run['original_actual_generations']==17
            assert len(run['source_links'])==17 and run['generation_helper_sha256']==sha256(ROOT/'scripts/run_aurora_qwen35_smoke.py')
            for link,row,review in zip(run['source_links'],rows,inspection['reviews'],strict=True):
                origin=ROOT/link['run'];original=json.loads((origin/'run.json').read_text())
                for k in ('run','transcript','inspection'):assert sha256(origin/(k+('.jsonl' if k=='transcript' else '.json')))==link[k+'_sha256']
                actual=next(r for r in read_jsonl(origin/'transcript.jsonl') if r['id']==row['id'])
                actual_review=next(v for v in json.loads((origin/'inspection.json').read_text())['reviews'] if v['id']==row['id'])
                if 'partial_state_ratings' not in actual_review and 'partial_state_ratings' in review:
                    assert review['partial_state_ratings']=={}
                    actual_review['partial_state_ratings']={}
                assert review==actual_review
                assert row['input_ids']==actual['input_ids'] and row['output_ids']==actual['output_ids'] and row['output']==actual['output'] and original['identity']==link['actual_identity']
                assert original['versions']==cfg['runtime_pins'] and original['gpu']['name']==run['gpu']['name']
                for k in ('model','revision','generation_max_new_tokens','max_length','chat_template_kwargs'):assert original['config'][k]==cfg[k]
                assert original['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py']==run['generation_helper_sha256']
                if arm=='base':assert original['mode']=='base'
                else:
                    actual_weight=original['serialization_checks']['files_sha256']['adapter_model.safetensors'] if original['mode']=='fit' else original['loaded_adapter_sha256']
                    expected_weight=cfg['starting_adapter_sha256'] if arm=='parent' else json.loads((ROOT/cfg['comparison_chosen_run']/'run.json').read_text())['serialization_checks']['files_sha256']['adapter_model.safetensors']
                    assert actual_weight==expected_weight
        else:assert run['status']=='completed' and run['optimizer_steps']==192
        results={}
        for case,row,review in zip(cases,rows,inspection['reviews']):
            assert case['id']==row['id']==review['id'] and review['all_output_read_complete']
            ids=tok.apply_chat_template(case['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
            assert ids==case['input_ids']==row['input_ids'] and len(ids)+2048<=8192 and tok.decode(row['output_ids'],skip_special_tokens=True)==row['output']
            assert hashlib.sha256(row['output'].encode()).hexdigest()==review['output_sha256']
            for s in sources[case['family']].values():assert s['text'] in case['prompt'][1]['content']
            expected=({co+':'+k for co in ('FRA','GBR') for k,_ in criteria['wps']['common']+criteria['wps']['specific'][co]} if case['family']=='wps' else {u['id'] for u in criteria['mali']} if case['family']=='mali' else set(criteria[case['family']]['source_units'][case['country_iso3']])|set(criteria[case['family']]['common_units']))
            assert set(review['ratings'])==expected and set(review['universal_checks'])==set(criteria['universal_checks'])
            assert set(review['synthesis_checks'])==(set(criteria['synthesis_checks']) if case['family']=='wps' else set())
            values=[*review['ratings'].values(),*review['universal_checks'].values(),*review['synthesis_checks'].values()]
            assert all(v['status'] in ('met','unmet','unratable') and v['reason'].strip() for v in values)
            partial=review.get('partial_state_ratings',{})
            assert set(partial)==(set(criteria['partial_state_units']) if case['id']=='wps-partial-repair' else set())
            assert all(v['status'] in ('met','unmet','unratable') and v['reason'].strip() for v in partial.values())
            results[case['id']]={'met':sum(v['status']=='met' for v in review['ratings'].values()),'unratable':sum(v['status']=='unratable' for v in review['ratings'].values()),'units':len(expected),
                'source_pass':not row['at_output_cap'] and (case['family'] not in ('sanctions','haiti') or len(row['output'].split())<=300) and not review.get('additional_source_fidelity_observations') and all(v['status']=='met' for v in [*values,*partial.values()]),'words':len(row['output'].split()),'at_cap':row['at_output_cap'], 'partial_state_met':sum(v['status']=='met' for v in partial.values()),'partial_state_unratable':sum(v['status']=='unratable' for v in partial.values()),'partial_state_units':len(partial)}
        runs[arm]=run;outputs[arm]=rows;summary[arm]=results
    fit=runs['fit'];assert fit['config_sha256']==sha256(ROOT/'configs/posttraining/qwen35-conditional-india-20261006-v2.json')
    for arm in ('base','parent','chosen'):
        assert [r['input_ids'] for r in outputs[arm]]==[r['input_ids'] for r in outputs['fit']] and runs[arm]['versions']==fit['versions']
        assert runs[arm]['gpu']['name']==fit['gpu']['name']=='NVIDIA RTX PRO 6000 Blackwell Server Edition'
    checks=fit['optimization_checks']['rank_checks'][0];mask=fit['mask_audit']
    assert checks['steps']==checks['microbatches']==checks['gradient_checks']==192 and checks['pair_presentations']=={'card':32,'raw':32,'repair':32,'mali':32,'india_absent':32,'india_known':32}
    assert checks['actual_sequence_tokens']==32*mask['sequence_tokens_once'] and checks['actual_target_tokens']==32*(mask['chosen_tokens_once']+mask['rejected_tokens_once'])
    assert mask['actual_trainer_token_ids_and_masks_checked'] and checks['all_adapter_tensors_finite'] and checks['changed_adapter_tensors']>0
    assert fit['method']['reference_tensor_digest_before']==fit['method']['reference_tensor_digest_after']==checks['initial_adapter_digest']
    assert len(fit['actual_objective_guard']['pairs'])==len(pairs) and all(p['absolute_difference']<1e-4 for p in fit['actual_objective_guard']['pairs'])
    assert sha256(ROOT/cfg['starting_adapter']/'adapter_model.safetensors')==cfg['starting_adapter_sha256'] and sha256(ROOT/cfg['starting_adapter']/'adapter_config.json')==cfg['starting_adapter_config_sha256']
    assert fit['serialization_checks']['saved_tensors_equal'] and fit['serialization_checks']['reload_verified_after_state_perturbation']
    for name,h in fit['serialization_checks']['files_sha256'].items():assert sha256(ROOT/'runs/aurora-conditional-india-fit-20261006-v2/adapter'/name)==h
    assert fit['method']['preference_gradient_enabled'] is False and fit['method']['negative_and_reference_compute_retained']
    objective=fit['actual_objective_guard']
    assert objective['loss_types']==['sft'] and objective['loss_weights']==[1.0]
    assert all(abs(p['component_losses']['combined']-p['component_losses']['chosen_nll'])<1e-4 for p in objective['pairs'])
    assert len(objective['native_logit_gradient_checks'])==6
    for g in objective['native_logit_gradient_checks']:
        assert g['rejected_logit_gradient_zero'] and g['prompt_padding_and_final_logit_gradient_zero']
        assert g['chosen_completion_logit_gradient_nonzero'] and g['parameter_gradients_not_accumulated']
    preparation=ROOT/cfg['preparation'];prep=json.loads(preparation.read_text())
    assert sha256(preparation)==fit['preparation_sha256'] and prep['all_selected_texts_read_complete']
    assert prep['config_sha256']==fit['config_sha256'] and prep['pack_manifest_sha256']==fit['pack_manifest_sha256']
    for key in ('run','transcript','inspection'):
        fn=key+('.jsonl' if key=='transcript' else '.json')
        assert sha256(ROOT/cfg['comparison_run']/fn)==fit['fresh_parent_comparison'][key+'_sha256']
    parent_actual=json.loads((ROOT/cfg['comparison_run']/'run.json').read_text())
    assert parent_actual['serialization_checks']['files_sha256']['adapter_model.safetensors']==cfg['starting_adapter_sha256']
    assert cfg['parent_steps']==96
    result={'status':'two_source_complete_raw_india_states_rehearsal_haiti_masks_reference_updates_weights_four_arm_controls_reviews_replayed',
        'new_public_model_generations':32,'new_control_generations':15,'new_fit_generations':17,'original_control_outputs_reused':36,'new_optimizer_steps':192,'new_branch_steps':288,'cumulative_aurora_qwen35_steps':1246,'reference_qwen25_steps':582,
        'summary':summary,'actual_pair_presentations':checks['pair_presentations'],'actual_sequence_tokens':checks['actual_sequence_tokens'],'actual_preference_completion_tokens':checks['actual_target_tokens'],
        'training_seconds':fit['training_seconds'],'scope':m['source_scope'],'comparison_scope':'New2source-complete raw India positives plus unchanged4rehearsal, chosen-onlyfresh96/192updates/32presentations each. Data/dose/order/padding coupled. NewHaiti family frozen before calls/fit, acquired corpus/pretraining unknown; not isolated data effect, sealed OOD or persona gain.','independent_review_complete':False}
    write_json(a.output,result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
