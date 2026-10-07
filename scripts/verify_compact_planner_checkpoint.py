"""Replay twelve read outputs, one-target32/64 native fits and selected primary source."""
import hashlib,json,sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,digest,write_json
from verify_two_context_country import exited

def main():
    names=['aurora-compact-france-base-20261007-v1','aurora-compact-france-point8-20261007-v1','aurora-actual-compact-planner-20261007-v1',
        'aurora-actual-compact-checked-base-20261007-v1','aurora-actual-compact-checked-point8-20261007-v1','aurora-source-only-compact-probe-20261007-v1',
        'aurora-source-extraction-base-20261007-v1','aurora-source-extraction-fit-20261007-v1','aurora-source-extraction-fit64-20261007-v1']
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-source-extraction-20261007-v1.json').read_text())
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['model_path'],local_files_only=True)
    summaries,resources,fit_checks={},[],{};total,tokens,caps,seconds=0,0,0,0
    for name in names:
        d=ROOT/'runs'/name;r=json.loads((d/'run.json').read_text());i=json.loads((d/'inspection.json').read_text());pack=ROOT/r['config']['pack'];m=json.loads((pack/'manifest.json').read_text());h=json.loads((pack/'manual-inspection.json').read_text());cases=list(read_jsonl(pack/'cases.jsonl'));rows=list(read_jsonl(d/'transcript.jsonl'));crit=json.loads((pack/'criteria.json').read_text())
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
            prior=ROOT/previous.get('run',previous.get('path'));matches=[v for v in [prior/'inspection.json',prior/'initial-inspection.json'] if v.exists() and sha256(v)==previous['inspection_sha256']]
            assert len(matches)==1 or len(matches)==2 and matches[0].read_bytes()==matches[1].read_bytes()
        assert len(rows)==len(cases)==len(i['reviews']);summaries[name]={}
        for c,row,v in zip(cases,rows,i['reviews'],strict=True):
            assert c['id']==row['id']==v['id'] and c['input_ids']==row['input_ids']
            assert tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)==row['input_ids']
            assert tok.decode(row['output_ids'],skip_special_tokens=True)==row['output'] and v['output_sha256']==hashlib.sha256(row['output'].encode()).hexdigest()
            assert v['all_output_read_complete'] and v['words']==len(row['output'].split())
            required=crit['source_units'][c['family']]['FRA'];assert set(v['ratings'])==set(required)|set(crit['common_units'])
            counts=dict(Counter(x['status'] for x in v['ratings'].values()));assert counts==v['content_counts']
            allmet=all(x['status']=='met' for x in list(v['ratings'].values())+list(v['universal_checks'].values()))
            source_only=not crit['common_units'];limit=210 if source_only else 280 if name=='aurora-actual-compact-planner-20261007-v1' else 300
            taskpass=allmet and v['words']<=limit and v['presentation']['ordinary_word_separation'] and not row['at_output_cap'] and (source_only or v['presentation']['three_requested_sections'])
            summaries[name][c['id']]={'content':counts,'source':dict(Counter(x['status'] for k,x in v['ratings'].items() if k.startswith('S'))),'universal':dict(Counter(x['status'] for x in v['universal_checks'].values())),'words':v['words'],'task_max_words':limit,'task_pass':taskpass,'scope':'source-only8units' if source_only else 'full14unitplanning_orwriting'}
            total+=1;tokens+=row['generated_tokens'];caps+=int(row['at_output_cap']);seconds+=row['generation_seconds']
        if r['mode']=='fit':
            steps=r['config']['max_steps'];a=list(read_jsonl(pack/'pair-audit.jsonl'));pairs=list(read_jsonl(pack/'pairs.jsonl'));assert len(a)==len(pairs)==1
            checks=r['optimization_checks']['rank_checks'][0];mask=r['mask_audit'];init=r['initialization_checks']
            assert r['optimizer_steps']==checks['steps']==checks['microbatches']==checks['gradient_checks']==steps
            assert checks['pair_presentations']=={a[0]['id']:steps} and checks['actual_sequence_tokens']==steps*mask['sequence_tokens_once']
            assert checks['actual_target_tokens']==steps*(mask['chosen_tokens_once']+mask['rejected_tokens_once'])
            assert init['all_B_tensors_zero'] and init['base_initial_adapter_logits_exact'] and not init['loaded_trained_adapter']
            assert r['method']['reference_tensor_digest_before']==r['method']['reference_tensor_digest_after']==init['initial_adapter_digest']
            assert r['actual_objective_guard']['loss_types']==['sft'] and not r['method']['preference_gradient_enabled']
            for g in r['actual_objective_guard']['native_logit_gradient_checks']:assert all(g[k] for k in ['rejected_logit_gradient_zero','prompt_padding_and_final_logit_gradient_zero','chosen_completion_logit_gradient_nonzero','parameter_gradients_not_accumulated'])
            for f,v in r['serialization_checks']['files_sha256'].items():assert sha256(d/'adapter'/f)==v
            assert r['serialization_checks']['saved_tensors_equal'] and r['serialization_checks']['reload_verified_after_state_perturbation']
            before=list(read_jsonl(ROOT/r['config']['baseline_run']/'transcript.jsonl'));assert [v['input_ids'] for v in before]==[v['input_ids'] for v in rows]
            for pair,audit in zip(pairs,a,strict=True):
                for part in ['chosen','rejected']:
                    full=tok.apply_chat_template(pair['prompt']+pair[part],tokenize=True,return_dict=False,enable_thinking=False)
                    assert full[:len(audit['prompt_ids'])]==audit['prompt_ids'] and full[len(audit['prompt_ids']):]==audit[part+'_ids']
            assert pairs[0]['rejected'][0]['content']==before[0]['output']
            fit_checks[str(steps)]={'initial_digest':init['initial_adapter_digest'],'training_seconds':r['training_seconds'],'peak_gib':r['peak_allocated_gpu_gib'],'actual_sequence_tokens':checks['actual_sequence_tokens'],'actual_both_completion_tokens':checks['actual_target_tokens'],'actual_chosen_supervised_tokens':steps*mask['chosen_tokens_once']}
        else:assert r['optimizer_steps']==0
        resources.append({'run':str(d.relative_to(ROOT)),'identity':r['identity'],'gpu':r['gpu'],'exited':True})
    assert total==12 and fit_checks['32']['initial_digest']==fit_checks['64']['initial_digest']
    raw=ROOT/'data/raw/compact-planner-ukraine-grounding-20261007-v1';proof=json.loads((raw/'source-proof.json').read_text());source=json.loads((raw/'statement.json').read_text());doc=(raw/'record-9693.txt').read_text()
    assert proof['pdf_sha256']==sha256(raw/'record-9693.pdf') and proof['statement_sha256']==sha256(raw/'statement.json') and proof['columns_sha256']==sha256(raw/'columns.json')
    assert doc[source['start']:source['end']]==source['raw_text'] and digest(doc)==proof['document_text_digest'] and proof['selected_pdf_pages_viewed']==[1,13] and proof['source_hand_read_complete']
    receipt={'status':'pass','verified_at':datetime.now(timezone.utc).isoformat(),'summaries':summaries,'fit_checks':fit_checks,'resources':resources,'new_model_outputs':total,'new_optimizer_steps':96,'cumulative_qwen35_steps':2622,'reference_qwen25_steps':582,'uncapped':total-caps,'capped':caps,'all_outputs_hand_read':True,'all_nine_owned_gpu_identities_exited':True,'generated_tokens':tokens,'generation_seconds':seconds,'independent_review_complete':False,'scope':'Three checked-plan writer cases work; rawsourceplanning/extraction remains deficient. Same-assistant development, no nativeprediction/persona/multiagent/strongOOD gain.','next_decision':json.loads((ROOT/'runs/aurora-source-extraction-fit64-20261007-v1/inspection.json').read_text())['decision']}
    write_json(ROOT/'reports/compact-planner-checkpoint-20261007-v1.json',receipt)
    print(json.dumps({'status':'pass','new_outputs':total,'updates':96,'fit_checks':fit_checks,'summaries':summaries},indent=2))

if __name__=='__main__':main()
