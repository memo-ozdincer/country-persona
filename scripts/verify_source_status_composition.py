"""Replay native execution and annotated source/application/writer composition artifacts."""
import json,hashlib,sys,re
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,digest,write_json
from verify_two_context_country import exited

NAMES=['aurora-source-status-base-20261007-v1','aurora-source-status-oldone64-20261007-v1','aurora-source-status-oldtwo64-20261007-v1','aurora-source-status-fit-20261007-v2','aurora-source-status-application-20261007-v1','aurora-source-status-application-block-base-20261007-v1','aurora-source-status-application-block-base-20261007-v2','aurora-minimal-application-base-20261007-v1','aurora-minimal-application-fit-20261007-v1','aurora-actual-composed-writer-base-20261007-v1','aurora-actual-composed-writer-point8-20261007-v1']

def main():
    cfg=json.loads((ROOT/'configs/posttraining/qwen35-source-status-fit-20261007-v2.json').read_text())
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(ROOT/'runs/aurora-source-status-fit-20261007-v2/adapter',local_files_only=True)
    summaries,resources,fits={},[],{};total,caps,steps=0,0,0
    for name in NAMES:
        d=ROOT/'runs'/name;r=json.loads((d/'run.json').read_text());i=json.loads((d/'inspection.json').read_text());pack=ROOT/r['config']['pack'];m=json.loads((pack/'manifest.json').read_text());h=json.loads((pack/'manual-inspection.json').read_text());cs=list(read_jsonl(pack/'cases.jsonl'));rows=list(read_jsonl(d/'transcript.jsonl'));crit=json.loads((pack/'criteria.json').read_text())
        assert r['status']=='completed' and exited(r['identity']) and i['all_outputs_read_complete']
        assert r['pack_manifest_sha256']==h['manifest_sha256']==sha256(pack/'manifest.json') and h['all_selected_texts_read_complete']
        for f,x in m['files_sha256'].items():assert sha256(pack/f)==x
        assert r['transcript_sha256']==i['transcript_sha256']==sha256(d/'transcript.jsonl') and i['manual_annotations_sha256']==sha256(d/'manual-annotations.json') and i['criteria_sha256']==sha256(pack/'criteria.json')
        assert r['versions']==cfg['runtime_pins'] and r['gpu']['name']=='NVIDIA RTX PRO 6000 Blackwell Server Edition'
        for key in ['model','revision','seed','max_length','generation_max_new_tokens','chat_template_kwargs']:assert r['config'][key]==cfg[key]
        for f,x in r['source_code_sha256'].items():assert sha256(d/Path(f).name)==x
        assert r['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py']==sha256(ROOT/'scripts/run_aurora_qwen35_smoke.py')
        prev=r.get('previous_inspected_run')
        if prev:assert prev['inspection_sha256']==sha256(ROOT/prev.get('run',prev.get('path'))/'inspection.json')
        assert len(cs)==len(rows)==len(i['reviews']);summaries[name]={}
        for c,row,v in zip(cs,rows,i['reviews'],strict=True):
            assert c['id']==row['id']==v['id'] and c['input_ids']==row['input_ids']
            assert tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)==row['input_ids']
            assert tok.decode(row['output_ids'],skip_special_tokens=True)==row['output'] and hashlib.sha256(row['output'].encode()).hexdigest()==v['output_sha256']
            assert v['words']==len(row['output'].split()) and v['all_output_read_complete']
            units=crit['source_units'][c['family']];units=units[c['country_iso3']] if c['country_iso3'] in units else units
            expected={**units,**crit['common_units']};assert set(v['ratings'])==set(expected) and set(v['universal_checks'])==set(crit['universal_checks'])
            counts=dict(Counter(x['status'] for x in v['ratings'].values()));assert counts==v['content_counts']
            allmet=all(x['status']=='met' for x in list(v['ratings'].values())+list(v['universal_checks'].values()))
            limit=r['config'].get('task_max_words',210);ordinary=v.get('ordinary_word_separation',v.get('presentation',{}).get('ordinary_word_separation'))
            scope='full14' if len(expected)==14 else 'source8' if len(expected)==8 else 'application6';assert scope in ['full14','source8','application6']
            shape=v['presentation']['three_requested_sections'] if scope=='full14' else v.get('one_documentary_section',True) if scope=='source8' else 'Analytical decisions' in row['output'] and 'Authority' in row['output']
            passed=allmet and v['words']<=limit and ordinary and shape and not row['at_output_cap']
            summaries[name][c['id']]={'content':counts,'guards':dict(Counter(x['status'] for x in v['universal_checks'].values())),'words':v['words'],'task_max_words':limit,'task_pass':bool(passed),'scope':scope,'capped':row['at_output_cap']}
            total+=1;caps+=int(row['at_output_cap'])
        resources.append({'run':str(d.relative_to(ROOT)),'identity':r['identity'],'gpu':r['gpu'],'exited':True})
        if r['mode']=='fit':
            pairs=list(read_jsonl(pack/'pairs.jsonl'));audits=list(read_jsonl(pack/'pair-audit.jsonl'));assert len(pairs)==len(audits)==r['config']['training_examples'];presentations=r['optimizer_steps']//len(pairs);checks=r['optimization_checks']['rank_checks'][0];mask=r['mask_audit'];init=r['initialization_checks']
            assert checks['steps']==checks['microbatches']==checks['gradient_checks']==r['optimizer_steps']==r['config']['max_steps'] and checks['pair_presentations']=={a['id']:presentations for a in audits}
            assert checks['actual_sequence_tokens']==presentations*mask['sequence_tokens_once'] and checks['actual_target_tokens']==presentations*(mask['chosen_tokens_once']+mask['rejected_tokens_once'])
            assert init['all_B_tensors_zero'] and init['base_initial_adapter_logits_exact'] and not init['loaded_trained_adapter'] and r['method']['reference_tensor_digest_before']==r['method']['reference_tensor_digest_after']==init['initial_adapter_digest']
            assert r['actual_objective_guard']['loss_types']==['sft'] and not r['method']['preference_gradient_enabled'] and len(r['actual_objective_guard']['native_logit_gradient_checks'])==len(pairs)
            for g in r['actual_objective_guard']['native_logit_gradient_checks']:assert all(g[k] for k in ['rejected_logit_gradient_zero','prompt_padding_and_final_logit_gradient_zero','chosen_completion_logit_gradient_nonzero','parameter_gradients_not_accumulated'])
            for f,x in r['serialization_checks']['files_sha256'].items():assert sha256(d/'adapter'/f)==x
            assert r['serialization_checks']['saved_tensors_equal'] and r['serialization_checks']['reload_verified_after_state_perturbation']
            before=list(read_jsonl(ROOT/r['config']['baseline_run']/'transcript.jsonl'));assert [x['input_ids'] for x in before]==[x['input_ids'] for x in rows]
            for index,(pair,audit) in enumerate(zip(pairs,audits,strict=True)):
                assert digest(pair)==audit['pair_sha256'] and pair['prompt']==cs[index]['prompt'] and pair['rejected'][0]['content']==before[index]['output']
                for part in ['chosen','rejected']:
                    ids=tok.apply_chat_template(pair['prompt']+pair[part],tokenize=True,return_dict=False,enable_thinking=False);assert ids==audit['prompt_ids']+audit[part+'_ids']
            fits[name]={'steps':r['optimizer_steps'],'training_seconds':r['training_seconds'],'peak_gib':r['peak_allocated_gpu_gib'],'actual_sequence_tokens':checks['actual_sequence_tokens'],'actual_both_completion_tokens':checks['actual_target_tokens'],'actual_chosen_supervised_tokens':presentations*mask['chosen_tokens_once'],'presentations':checks['pair_presentations'],'initial_digest':init['initial_adapter_digest']};steps+=r['optimizer_steps']
        else:assert r['optimizer_steps']==0
    assert total==19 and steps==96
    raw=ROOT/'data/raw/source-status-grounding-20261007-v1';proof=json.loads((raw/'source-proof.json').read_text());s=json.loads((raw/'statement.json').read_text());text=(raw/'record-9694.txt').read_text()
    assert sha256(raw/'record-9694.pdf')==proof['pdf_sha256'] and sha256(raw/'statement.json')==proof['statement_sha256'] and sha256(raw/'columns.json')==proof['columns_sha256']
    assert text[s['start']:s['end']].rstrip()==s['raw_text'] and proof['whole_selected_speech_read'] and proof['selected_pdf_pages_viewed']==[1,16,17] and all(v['equal'] for v in json.loads((raw/'columns.json').read_text())['coverage'])
    finalpack=ROOT/'data/prepared/source-status-fit-20261007-v2';target=json.loads((finalpack/'preferred-targets.json').read_text());source=json.loads((finalpack/'sources.json').read_text());cs=list(read_jsonl(finalpack/'cases.jsonl'));old=list(read_jsonl(ROOT/'data/prepared/extraction-diversity-20261007-v1/cases.jsonl'));assert [x['input_ids'] for x in cs[:3]]==[x['input_ids'] for x in old]
    for c in cs[:2]:
        for q in re.findall(r'"([^"]+)"',target['targets'][c['id']]):assert q in source[c['family']]['FRA']['text']
    composed=ROOT/'data/prepared/actual-composed-writer-20261007-v1';plan=json.loads((composed/'actual-plan.json').read_text());parts=[]
    for link in plan['components']:
        d=ROOT/link['run'];row=next(v for v in read_jsonl(d/'transcript.jsonl') if v['id']==link['id']);assert digest(row)==link['row_digest'];parts.append(row['output'])
        for k in ['run','transcript','inspection']:assert sha256(d/(k+'.jsonl' if k=='transcript' else k+'.json'))==link[k+'_sha256']
    assert plan['plan']=='\n\n'.join(parts) and len(plan['plan'].split())==plan['words']==290
    assert sha256(composed/'criteria.json')==sha256(ROOT/'data/prepared/actual-compact-planner-checked-20261007-v1/criteria.json')
    wbase=list(read_jsonl(ROOT/'runs/aurora-actual-composed-writer-base-20261007-v1/transcript.jsonl'))[0];wfit=list(read_jsonl(ROOT/'runs/aurora-actual-composed-writer-point8-20261007-v1/transcript.jsonl'))[0];assert wbase['input_ids']==wfit['input_ids']
    wf=json.loads((ROOT/'runs/aurora-actual-composed-writer-point8-20261007-v1/run.json').read_text());assert wf['loaded_adapter_sha256']==sha256(ROOT/'runs/aurora-plan-input-fit-20261006-v1/adapter/adapter_model.safetensors')
    receipt={'status':'pass','verified_at':datetime.now(timezone.utc).isoformat(),'summaries':summaries,'resources':resources,'all_eleven_owned_gpu_identities_exited':True,'new_model_outputs':total,'uncapped':total-caps,'capped':caps,'all_outputs_hand_read':True,'new_optimizer_steps':steps,'cumulative_qwen35_steps':2910,'reference_qwen25_steps':582,'fit_checks':fits,'actual_composed_plan_words':290,'actual_components_unedited':True,'original14_endpoint_criteria_unchanged':True,'independent_review_complete':False,'scope':'Same-assistant adaptive development, knownfittedsource/application/fixedwriter composition; notsealedOOD/persona/nativeprediction/autonomousmultiagent gain. Source/report/commitment ambiguity disclosed.'}
    write_json(ROOT/'reports/source-status-composition-checkpoint-20261007-v1.json',receipt);print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
