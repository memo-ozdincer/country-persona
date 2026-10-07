"""Replay native training, frozen sources/inputs, full-output reviews and ownership."""
import hashlib,json,sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,digest,write_json
from verify_two_context_country import exited

def main():
    names=['aurora-extraction-diversity-base-20261007-v1','aurora-extraction-diversity-monitor-old64-20261007-v1','aurora-extraction-diversity-fit-20261007-v1','aurora-extraction-diversity-fit64-20261007-v1']
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-extraction-diversity-fit-20261007-v1.json').read_text())
    fitdir=ROOT/'runs'/names[2]
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(fitdir/'adapter',local_files_only=True)
    summaries,resources={},[];total=0;caps=0
    for name in names:
        d=ROOT/'runs'/name;r=json.loads((d/'run.json').read_text());i=json.loads((d/'inspection.json').read_text());pack=ROOT/r['config']['pack'];m=json.loads((pack/'manifest.json').read_text());h=json.loads((pack/'manual-inspection.json').read_text());cases=list(read_jsonl(pack/'cases.jsonl'));rows=list(read_jsonl(d/'transcript.jsonl'));crit=json.loads((pack/'criteria.json').read_text());sources=json.loads((pack/'sources.json').read_text())
        assert r['status']=='completed' and exited(r['identity']) and i['all_outputs_read_complete']
        assert r['transcript_sha256']==i['transcript_sha256']==sha256(d/'transcript.jsonl')
        assert r['pack_manifest_sha256']==h['manifest_sha256']==sha256(pack/'manifest.json') and h['all_selected_texts_read_complete']
        for f,v in m['files_sha256'].items():assert sha256(pack/f)==v
        assert i['manual_annotations_sha256']==sha256(d/'manual-annotations.json') and i['criteria_sha256']==sha256(pack/'criteria.json')
        assert r['versions']==cfg['runtime_pins'] and r['gpu']['name']=='NVIDIA RTX PRO 6000 Blackwell Server Edition'
        for k in ['model','revision','seed','max_length','generation_max_new_tokens','chat_template_kwargs']:assert r['config'][k]==cfg[k]
        for f,v in r['source_code_sha256'].items():assert sha256(d/Path(f).name)==v
        assert r['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py']==sha256(ROOT/'scripts/run_aurora_qwen35_smoke.py')
        previous=r.get('previous_inspected_run')
        if previous:
            prior=ROOT/previous.get('run',previous.get('path'));assert previous['inspection_sha256']==sha256(prior/'inspection.json')
        assert len(rows)==len(cases)==len(i['reviews']);summaries[name]={}
        for c,row,v in zip(cases,rows,i['reviews'],strict=True):
            assert c['id']==row['id']==v['id'] and c['input_ids']==row['input_ids']
            assert sources[c['family']][c['country_iso3']]['text'] in c['prompt'][1]['content']
            assert tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)==row['input_ids']
            assert tok.decode(row['output_ids'],skip_special_tokens=True)==row['output'] and v['output_sha256']==hashlib.sha256(row['output'].encode()).hexdigest()
            assert v['all_output_read_complete'] and v['words']==len(row['output'].split()) 
            required=crit['source_units'][c['family']]['FRA'];assert not crit['common_units'] and set(v['ratings'])==set(required) and set(v['universal_checks'])==set(crit['universal_checks'])
            counts=dict(Counter(x['status'] for x in v['ratings'].values()));assert counts==v['content_counts']
            full=all(x['status']=='met' for x in list(v['ratings'].values())+list(v['universal_checks'].values()));passed=full and v['words']<=210 and v['ordinary_word_separation'] and v['one_documentary_section'] and not row['at_output_cap']
            assert passed==v['source_only_task_pass']
            summaries[name][c['id']]={'content':counts,'universal':dict(Counter(x['status'] for x in v['universal_checks'].values())),'words':v['words'],'task_pass':passed,'capped':row['at_output_cap']};total+=1;caps+=int(row['at_output_cap'])
        resources.append({'run':str(d.relative_to(ROOT)),'identity':r['identity'],'gpu':r['gpu'],'exited':True})
    r=json.loads((fitdir/'run.json').read_text());pack=ROOT/r['config']['pack'];a=list(read_jsonl(pack/'pair-audit.jsonl'));pairs=list(read_jsonl(pack/'pairs.jsonl'));assert len(a)==len(pairs)==2
    checks=r['optimization_checks']['rank_checks'][0];mask=r['mask_audit'];init=r['initialization_checks']
    assert r['optimizer_steps']==checks['steps']==checks['microbatches']==checks['gradient_checks']==128 and checks['pair_presentations']=={x['id']:64 for x in a}
    assert checks['actual_sequence_tokens']==64*mask['sequence_tokens_once'] and checks['actual_target_tokens']==64*(mask['chosen_tokens_once']+mask['rejected_tokens_once'])
    assert init['all_B_tensors_zero'] and init['base_initial_adapter_logits_exact'] and not init['loaded_trained_adapter']
    oldfit=json.loads((ROOT/'runs/aurora-source-extraction-fit64-20261007-v1/run.json').read_text());assert init['initial_adapter_digest']==oldfit['initialization_checks']['initial_adapter_digest']
    assert r['method']['reference_tensor_digest_before']==r['method']['reference_tensor_digest_after']==init['initial_adapter_digest'] and not r['method']['preference_gradient_enabled']
    assert r['actual_objective_guard']['loss_types']==['sft'] and len(r['actual_objective_guard']['native_logit_gradient_checks'])==2
    for g in r['actual_objective_guard']['native_logit_gradient_checks']:assert all(g[k] for k in ['rejected_logit_gradient_zero','prompt_padding_and_final_logit_gradient_zero','chosen_completion_logit_gradient_nonzero','parameter_gradients_not_accumulated'])
    for f,v in r['serialization_checks']['files_sha256'].items():assert sha256(fitdir/'adapter'/f)==v
    assert r['serialization_checks']['saved_tensors_equal'] and r['serialization_checks']['reload_verified_after_state_perturbation']
    before=list(read_jsonl(ROOT/r['config']['baseline_run']/'transcript.jsonl'));after=list(read_jsonl(fitdir/'transcript.jsonl'));assert [v['input_ids'] for v in before]==[v['input_ids'] for v in after]
    for index,(pair,audit,row) in enumerate(zip(pairs,a,before[:2],strict=True)):
        assert pair['prompt']==list(read_jsonl(pack/'cases.jsonl'))[index]['prompt']
        assert pair['rejected'][0]['content']==row['output'] and digest(pair)==audit['pair_sha256']
        for part in ['chosen','rejected']:
            full=tok.apply_chat_template(pair['prompt']+pair[part],tokenize=True,return_dict=False,enable_thinking=False);assert full==audit['prompt_ids']+audit[part+'_ids']
    original=list(read_jsonl(ROOT/'data/prepared/source-extraction-fit-20261007-v1/pairs.jsonl'))[0];assert pairs[0]['prompt']==original['prompt'] and pairs[0]['chosen']==original['chosen']
    expected=json.loads((ROOT/'data/prepared/compact-france-20261007-v1/checked-plan.json').read_text())['plan'].split('\n\n')[0];assert pairs[1]['chosen'][0]['content']==expected
    held=list(read_jsonl(pack/'cases.jsonl'))[2];assert all(p['prompt']!=held['prompt'] and 'S/PV.9687' not in json.dumps(p) for p in pairs)
    base_pack=ROOT/'data/prepared/extraction-diversity-20261007-v1';assert sha256(base_pack/'criteria.json')==sha256(pack/'criteria.json')
    raw=ROOT/'data/raw/extraction-diversity-gaza-grounding-20261007-v1';proof=json.loads((raw/'source-proof.json').read_text());s=json.loads((raw/'statement.json').read_text());doc=(raw/'record-9687.txt').read_text()
    assert proof['pdf_sha256']==sha256(raw/'record-9687.pdf') and proof['selected_source_sha256']==sha256(raw/'statement.json') and doc[s['start']:s['end']].rstrip()==s['raw_text']
    assert proof['whole_selected_national_speech_read'] and proof['cover_and_pages_24_25_viewed'] and all(x['equal'] for x in json.loads((raw/'columns.json').read_text())['coverage'])
    lowerdir=ROOT/'runs'/names[3];lower=json.loads((lowerdir/'run.json').read_text());lc=lower['optimization_checks']['rank_checks'][0]
    assert lower['optimizer_steps']==lc['steps']==lc['microbatches']==lc['gradient_checks']==64 and lc['pair_presentations']=={x['id']:32 for x in a}
    assert lc['actual_sequence_tokens']==32*mask['sequence_tokens_once'] and lc['actual_target_tokens']==32*(mask['chosen_tokens_once']+mask['rejected_tokens_once'])
    assert lower['pack_manifest_sha256']==r['pack_manifest_sha256'] and lower['initialization_checks']['initial_adapter_digest']==init['initial_adapter_digest']
    assert lower['initialization_checks']['all_B_tensors_zero'] and lower['initialization_checks']['base_initial_adapter_logits_exact'] and not lower['initialization_checks']['loaded_trained_adapter']
    assert lower['method']['reference_tensor_digest_before']==lower['method']['reference_tensor_digest_after']==init['initial_adapter_digest'] and not lower['method']['preference_gradient_enabled']
    assert lower['actual_objective_guard']['loss_types']==['sft'] and len(lower['actual_objective_guard']['native_logit_gradient_checks'])==2
    for g in lower['actual_objective_guard']['native_logit_gradient_checks']:assert all(g[k] for k in ['rejected_logit_gradient_zero','prompt_padding_and_final_logit_gradient_zero','chosen_completion_logit_gradient_nonzero','parameter_gradients_not_accumulated'])
    for f,v in lower['serialization_checks']['files_sha256'].items():assert sha256(lowerdir/'adapter'/f)==v
    assert lower['serialization_checks']['saved_tensors_equal'] and lower['serialization_checks']['reload_verified_after_state_perturbation']
    lowerrows=list(read_jsonl(lowerdir/'transcript.jsonl'));assert [v['input_ids'] for v in lowerrows]==[v['input_ids'] for v in before]
    assert total==10 and caps==1
    receipt={'status':'pass','verified_at':datetime.now(timezone.utc).isoformat(),'summaries':summaries,'resources':resources,'all_four_owned_gpu_identities_exited':True,'new_model_outputs':total,'all_outputs_hand_read':True,'uncapped':total-caps,'capped':caps,'new_optimizer_steps':192,'cumulative_qwen35_steps':2814,'reference_qwen25_steps':582,'training_seconds':r['training_seconds'],'peak_allocated_gpu_gib':r['peak_allocated_gpu_gib'],'native_training_checks':{'initial_digest':init['initial_adapter_digest'],'actual_sequence_tokens':checks['actual_sequence_tokens'],'actual_both_completion_tokens':checks['actual_target_tokens'],'actual_chosen_supervised_tokens':64*mask['chosen_tokens_once'],'presentations':checks['pair_presentations']},'independent_review_complete':False,'scope':'Two-source extraction fitting and one same-genre/new-source monitor; source-only8unit task, full14unit application/persona/multiagent claims unproved. Totalbudget doubled versusone-source64.','lower_exposure_training_seconds':lower['training_seconds'],'lower_exposure_peak_allocated_gpu_gib':lower['peak_allocated_gpu_gib'],'next_decision':json.loads((lowerdir/'inspection.json').read_text())['decision']}
    write_json(ROOT/'reports/extraction-diversity-checkpoint-20261007-v1.json',receipt);print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
