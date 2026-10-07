"""Fresh eight-target paired-Brazil application SFT:256 updates, five nonfitting monitors."""
import argparse
import importlib.metadata
import json
import math
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, sha256, write_json, write_jsonl
from run_aurora_qwen35_smoke import current_gpu, identity, verify_model, generate_controls

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode', choices=['fit'], required=True)
    p.add_argument('--config', type=Path, required=True); p.add_argument('--gpu-uuid', required=True)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--previous-inspected-run', type=Path)
    a = p.parse_args(); os.chdir(ROOT); config = json.loads(a.config.read_text())
    if a.mode != 'fit' or config['dpo_loss_types'] != ['sft'] or config['dpo_loss_weights'] != [1.0]:
        raise ValueError('This version is only the matched chosen-only SFT fit')
    preparation = json.loads((ROOT/config['preparation']).read_text())
    if preparation['config_sha256'] != sha256(a.config) or not preparation['all_selected_texts_read_complete']:
        raise ValueError('Current hand inspection must bind the new configuration')
    comparison = ROOT/config['comparison_run']
    comparison_run = json.loads((comparison/'run.json').read_text())
    comparison_review = json.loads((comparison/'inspection.json').read_text())
    if comparison_run['status'] != 'completed' or not comparison_review['all_outputs_read_complete']:
        raise ValueError('Previous application checkpoint must be complete and inspected before this fresh fit')
    if comparison_review['transcript_sha256'] != sha256(comparison/'transcript.jsonl'):
        raise ValueError('Inspected warm chosen-only output changed')
    if a.output.exists() or os.environ.get('SLURM_JOB_ID') or os.environ.get('CUDA_VISIBLE_DEVICES') != a.gpu_uuid:
        raise ValueError('Fresh explicit single-GPU Aurora run required')
    pack = ROOT / config['pack']; manifest = json.loads((pack / 'manifest.json').read_text())
    for filename, expected in manifest['files_sha256'].items():
        if sha256(pack / filename) != expected: raise ValueError('Frozen pack changed: ' + filename)
    hand = json.loads((pack / 'manual-inspection.json').read_text())
    if hand['manifest_sha256'] != sha256(pack / 'manifest.json') or not hand['all_selected_texts_read_complete']:
        raise ValueError('Full selected-data inspection must bind frozen pack')
    early_cases = list(read_jsonl(pack/'cases.jsonl'))
    if len(early_cases) != config['eval_cases'] or any(not {'id','country_iso3','prompt','input_ids'} <= set(c) for c in early_cases):
        raise ValueError('Complete generation metadata required before GPU loading')
    if a.previous_inspected_run:
        previous = json.loads((a.previous_inspected_run / 'inspection.json').read_text())
        if not previous['all_outputs_read_complete'] or previous['transcript_sha256'] != sha256(a.previous_inspected_run / 'transcript.jsonl'):
            raise ValueError('Inspect previous complete output before launch')
    gpu = current_gpu(a.gpu_uuid); a.output.mkdir(parents=True)
    sources = [Path(__file__), ROOT/'scripts/run_aurora_qwen35_smoke.py', ROOT/'src/country_persona/preference_checks.py',
               ROOT/'src/country_persona/training_checks.py', ROOT/'src/country_persona/io.py']
    record = {'status':'initializing','mode':a.mode,'identity':identity(),'gpu':gpu,'config':config,'config_sha256':sha256(a.config),
        'run_directory':str(a.output.resolve()),'pack_manifest_sha256':sha256(pack/'manifest.json'),
        'manual_inspection_sha256':sha256(pack/'manual-inspection.json'),'created_at':datetime.now(timezone.utc).isoformat(),
        'source_code_sha256':{str(s.relative_to(ROOT)):sha256(s) for s in sources},'optimizer_steps':0,
        'scope':manifest['source_scope'],'independent_review_complete':False}
    if a.previous_inspected_run: record['previous_inspected_run']={'path':str(a.previous_inspected_run),'inspection_sha256':sha256(a.previous_inspected_run/'inspection.json')}
    write_json(a.output/'launch.json',record)
    record['preparation_sha256'] = sha256(ROOT/config['preparation'])
    record['previous_inspected_checkpoint'] = {
        'path':str(comparison.relative_to(ROOT)), 'run_sha256':sha256(comparison/'run.json'),
        'transcript_sha256':sha256(comparison/'transcript.jsonl'), 'inspection_sha256':sha256(comparison/'inspection.json')}
    for s in sources: shutil.copy2(s,a.output/s.name)
    try:
        import torch
        from transformers import AutoTokenizer, Qwen3_5ForCausalLM
        from peft import LoraConfig, get_peft_model, get_peft_model_state_dict
        from country_persona.preference_checks import audit_preference_masks, use_torch_preference_logprobs
        from country_persona.training_checks import (OptimizationAudit,adapter_snapshot,check_adapter_update,
            validate_rank_checks,verify_saved_adapter,tensor_state_digest)
        record['versions']={k:importlib.metadata.version(k) for k in config['runtime_pins']}
        if record['versions'] != config['runtime_pins'] or torch.cuda.device_count()!=1 or not torch.cuda.is_bf16_supported():
            raise ValueError('Require exact runtime and one BF16 GPU')
        torch.cuda.set_device(0); record['model_verification']=verify_model(config)
        tok=AutoTokenizer.from_pretrained(config['model_path'],local_files_only=True)
        cases=list(read_jsonl(pack/'cases.jsonl')); pairs=list(read_jsonl(pack/'pairs.jsonl')); audits=list(read_jsonl(pack/'pair-audit.jsonl'))
        for c in cases:
            ids=tok.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,**config['chat_template_kwargs'])
            if ids!=c['input_ids'] or len(ids)+config['generation_max_new_tokens']>config['max_length']:
                raise ValueError('Frozen input differs or would truncate')
        if len(pairs)!=config['training_examples'] or len(audits)!=len(pairs) or len(cases)!=config['eval_cases']: raise ValueError('Frozen eight-pair/thirteen-case metadata required')
        if len(pairs)!=8 or len(cases)!=13 or config['max_steps']!=256:raise ValueError('Bounded inspected scope differs')
        torch.manual_seed(config['seed'])
        model,loading=Qwen3_5ForCausalLM.from_pretrained(config['model_path'],local_files_only=True,dtype=torch.bfloat16,
            attn_implementation='sdpa',output_loading_info=True)
        loading={k:sorted(v) if isinstance(v,set) else v for k,v in loading.items()}
        if loading['missing_keys'] or loading['mismatched_keys'] or loading['error_msgs']: raise ValueError('Incomplete text weights')
        record['text_model_loading']=loading; model.to('cuda:0')
        template=ROOT/config['lora_config_template']
        if sha256(template)!=config['lora_config_template_sha256']:raise ValueError('LoRA configuration template changed')
        lora=LoraConfig.from_pretrained(str(template.parent))
        if (lora.r,lora.lora_alpha,lora.bias,lora.modules_to_save,lora.init_lora_weights)!=(8,16,'none',None,True):
            raise ValueError('Unexpected fresh LoRA architecture or initialization')
        model.eval();initial_probe=torch.tensor([cases[0]['input_ids'][:32]],device='cuda:0')
        with torch.no_grad():base_probe=model(initial_probe,use_cache=False).logits.detach().clone()
        lora.inference_mode=False;model=get_peft_model(model,lora);model.eval()
        initial_state=adapter_snapshot(model)
        b=[v for k,v in initial_state.items() if 'lora_B' in k]
        if not b or not all(bool((v==0).all()) for v in b):raise ValueError('Fresh LoRA is not zero effect')
        with torch.no_grad():new_probe=model(initial_probe,use_cache=False).logits.detach()
        if not torch.equal(base_probe,new_probe):raise ValueError('Zero-effect adapter differs from base logits')
        record['initialization_checks']={'mode':config['initialization'],'lora_config_template_sha256':sha256(template),
            'zero_B_matrices':len(b),'all_B_tensors_zero':True,'adapter_tensors':len(initial_state),
            'initial_adapter_digest':tensor_state_digest(initial_state),'probe_tokens':32,'base_initial_adapter_logits_exact':True,
            'probe_maximum_logit_difference':float((base_probe-new_probe).abs().max()),'loaded_trained_adapter':False}
        model.save_pretrained(str(a.output/'initial-adapter'),selected_adapters=['default'])
        record['initial_adapter_files_sha256']={p.name:sha256(p) for p in (a.output/'initial-adapter').iterdir() if p.is_file()}
        del initial_state,b,base_probe,new_probe,initial_probe
        if a.mode=='fit':
            baseline=ROOT/config['baseline_run']; old=json.loads((baseline/'run.json').read_text()); old_review=json.loads((baseline/'inspection.json').read_text())
            if old['status']!='completed_cpu_replay' or old['mode']!='base' or not old_review['all_outputs_read_complete'] or old_review['transcript_sha256']!=sha256(baseline/'transcript.jsonl'):
                raise ValueError('Matching actual base baseline must be inspected')
            for k in ('versions',):
                if old[k]!=record[k]: raise ValueError('Fit/parent differs: '+k)
            if old['source_gpu_names'] != [gpu['name']]: raise ValueError('Actual source-call GPU types differ')
            record['baseline_inspection_sha256']=sha256(baseline/'inspection.json')
            if old['generation_helper_sha256']!=record['source_code_sha256']['scripts/run_aurora_qwen35_smoke.py']:
                raise ValueError('Replay/inference helper changed')
            before=list(read_jsonl(baseline/'transcript.jsonl'))
            for link in old['source_links']:
                origin=ROOT/link['run']
                for key in ['run','transcript','inspection']:
                    file=key+'.jsonl' if key=='transcript' else key+'.json'
                    if sha256(origin/file)!=link[key+'_sha256']:raise ValueError('Actual replay source changed')
                source=json.loads((origin/'run.json').read_text())
                if source['mode']!='base' or source['status']!='completed' or source['gpu']['name']!=gpu['name']:
                    raise ValueError('Replay does not bind actual matching GPU base calls')
            if [r['input_ids'] for r in before]!=[c['input_ids'] for c in cases]:raise ValueError('Actual baseline inputs differ')
            for key in ('model','revision','seed','max_length','generation_max_new_tokens','chat_template_kwargs'):
                if old['config'][key]!=config[key]:raise ValueError('Baseline protocol differs')
            baseline_pack=ROOT/old['config']['pack']
            if old['pack_manifest_sha256']!=sha256(baseline_pack/'manifest.json'):raise ValueError('Baseline frozen pack differs')
            if sha256(baseline_pack/'criteria.json')!=sha256(pack/'criteria.json'):raise ValueError('Frozen criteria differ')
            from datasets import Dataset
            from trl import DPOConfig,DPOTrainer
            record['logprob_backend']=use_torch_preference_logprobs()
            model.config.use_cache=False;model.enable_input_require_grads()
            settings=DPOConfig(output_dir=str(a.output/'adapter'),max_length=config['max_length'],max_steps=config['max_steps'],
                per_device_train_batch_size=1,gradient_accumulation_steps=config['gradient_accumulation_steps'],
                learning_rate=config['learning_rate'],warmup_steps=0,bf16=True,fp16=False,gradient_checkpointing=True,
                gradient_checkpointing_kwargs={'use_reentrant':False},seed=config['seed'],report_to='none',save_strategy='no',
                logging_steps=1,optim='adamw_torch',beta=config['dpo_beta'],loss_type=config['dpo_loss_types'],
                loss_weights=config['dpo_loss_weights'],precompute_ref_log_probs=True,disable_dropout=config['disable_dropout'])
            class Measured(DPOTrainer):
                processed_tokens=0;target_tokens=0;microbatches=0
                pair_presentations={audit['id']:0 for audit in audits}
                def training_step(self,model,inputs,num_items_in_batch=None):
                    matches=[audit['id'] for audit in audits if inputs['input_ids'][0,:len(audit['prompt_ids'])].tolist()==audit['prompt_ids']]
                    if len(matches)!=1:raise ValueError('Cannot identify actual training pair')
                    self.pair_presentations[matches[0]]+=1
                    self.processed_tokens+=int(inputs['attention_mask'].sum());self.target_tokens+=int(inputs['completion_mask'].sum());self.microbatches+=1
                    loss=super().training_step(model,inputs,num_items_in_batch)
                    if not torch.isfinite(loss):raise FloatingPointError('Nonfinite preference microbatch')
                    return loss
            callback=OptimizationAudit();setup=time.perf_counter()
            trainer=Measured(model=model,args=settings,train_dataset=Dataset.from_list(pairs),processing_class=tok,callbacks=[callback])
            record['reference_setup_seconds']=time.perf_counter()-setup
            record['mask_audit']=audit_preference_masks(trainer.train_dataset,trainer.data_collator,audits)
            trainer.model.set_adapter('default')
            for n,param in trainer.model.named_parameters():
                if '.ref.' in n:param.requires_grad_(False)
            def reference_digest():
                return tensor_state_digest({k:v.detach().cpu().clone() for k,v in get_peft_model_state_dict(trainer.model,adapter_name='ref').items()})
            reference_before=reference_digest()
            if reference_before!=tensor_state_digest(adapter_snapshot(trainer.model)): raise ValueError('Reference is not an exact frozen initial adapter copy')
            refs=[]
            for audit,row in zip(audits,trainer.train_dataset):
                ref={k:row[k] for k in ('ref_chosen_logps','ref_rejected_logps')}
                if not all(math.isfinite(v) for v in ref.values()):raise FloatingPointError('Nonfinite reference probabilities')
                refs.append({'id':audit['id'],**ref})
            write_json(a.output/'reference-logps.json',refs)
            # Check the pinned trainer's actual loss on the real masked pair.
            # No optimizer/backward occurs here; deterministic dropout is disabled.
            trainer.model.eval(); guards=[]
            actual_types=list(trainer.loss_types); actual_weights=list(trainer.loss_weights)
            with torch.no_grad():
                for audit,row in zip(audits,trainer.train_dataset):
                    batch=trainer._prepare_inputs(trainer.data_collator([row]));losses={}
                    for label,types,weights in [('dpo',['sigmoid'],[1.]),('chosen_nll',['sft'],[1.]),('combined',actual_types,actual_weights)]:
                        trainer.loss_types=types;trainer.loss_weights=weights
                        losses[label]=float(trainer.compute_loss(trainer.model,batch))
                    components={'sigmoid':losses['dpo'],'sft':losses['chosen_nll']}
                    expected=sum(components[t]*w for t,w in zip(actual_types,actual_weights,strict=True))
                    if abs(losses['combined']-expected)>1e-4:raise ValueError('Real combined loss differs')
                    guards.append({'id':audit['id'],'component_losses':losses,'weighted_sum':expected,'absolute_difference':abs(losses['combined']-expected)})
            trainer.loss_types=actual_types;trainer.loss_weights=actual_weights
            record['actual_objective_guard']={'pairs':guards,'real_pair_native_masks':True,'optimizer_steps':0,'loss_types':actual_types,'loss_weights':actual_weights}
            # Differentiate the native configured loss with respect to actual
            # model logits. Rejected rows and non-completion positions must have
            # zero loss gradient; this makes no backward to model parameters.
            # Trainer enables checkpointing only when train() starts. Enable
            # its identical settings now; eval-mode full graphs exceed memory.
            trainer.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs=settings.gradient_checkpointing_kwargs)
            trainer.model.train()
            gradient_guards=[]
            for audit,row in zip(audits,trainer.train_dataset):
                batch=trainer._prepare_inputs(trainer.data_collator([row]))
                with torch.enable_grad():
                    loss,output=trainer.compute_loss(trainer.model,batch,return_outputs=True)
                    grad=torch.autograd.grad(loss,output.logits)[0]
                active=grad.abs().sum(dim=-1)>0
                allowed=torch.zeros_like(active,dtype=torch.bool)
                allowed[0,:-1]=batch['completion_mask'][0,1:].bool()
                if not bool(active[0].any()) or bool((active & ~allowed).any()):
                    raise ValueError('Native chosen-only loss has missing chosen or nonchosen logit gradient')
                gradient_guards.append({'id':audit['id'],'rejected_logit_gradient_zero':not bool(active[1:].any()),
                    'prompt_padding_and_final_logit_gradient_zero':not bool((active & ~allowed).any()),
                    'chosen_completion_logit_gradient_nonzero':bool(active[0].any()),
                    'active_chosen_prediction_positions':int(active[0].sum()),'loss':float(loss.detach()),
                    'parameter_gradients_not_accumulated':all(p.grad is None for p in trainer.model.parameters())})
                if not gradient_guards[-1]['parameter_gradients_not_accumulated']:
                    raise ValueError('Objective-only gradient guard accumulated model gradients')
                del loss,output,grad,active,allowed,batch
            record['actual_objective_guard']['native_logit_gradient_checks']=gradient_guards
            record['actual_objective_guard']['gradient_guard_uses_training_checkpointing']=True
            record['method']={'loss':'chosen-token mean NLL only; rejected/reference forward retained for matched batching','beta':settings.beta,'loss_weights':actual_weights,
                'reference':'cached exact copy of saved fresh zero-effect adapter on pinned base; diagnostics only','reference_tensor_digest_before':reference_before,
                'dropout_disabled':config['disable_dropout'],'additional_approximate_kl':False,'introspection':False,'optimizer_state_resumed':False}
            record['method']['preference_gradient_enabled']=False
            record['method']['negative_and_reference_compute_retained']=True
            # _compute_loss also appends metrics in eval mode. Keep the component
            # probes out of subsequent fitted-pair reporting; they made no updates.
            for values in trainer._metrics.values():
                values.clear()
            record['status']='training_running';write_json(a.output/'run.json',record)
            torch.cuda.reset_peak_memory_stats(); started=time.perf_counter(); result=trainer.train();torch.cuda.synchronize()
            checks={'rank':0,'steps':trainer.state.global_step,'training_loss':result.training_loss,'actual_sequence_tokens':trainer.processed_tokens,
                'actual_target_tokens':trainer.target_tokens,'microbatches':trainer.microbatches,'gradient_checks':len(callback.gradients),
                'gradient_trace':callback.gradients,'pair_presentations':trainer.pair_presentations,**check_adapter_update(callback.initial,adapter_snapshot(trainer.model))}
            if trainer.pair_presentations!={audit['id']:32 for audit in audits}:raise ValueError('Actual pair exposure differs')
            record['optimization_checks']=validate_rank_checks([checks],1,config['max_steps']);record['optimizer_steps']=trainer.state.global_step
            record['training_seconds']=time.perf_counter()-started;record['peak_allocated_gpu_gib']=torch.cuda.max_memory_allocated()/2**30
            record['method']['reference_tensor_digest_after']=reference_digest()
            if reference_digest()!=reference_before:raise ValueError('Frozen reference changed during optimization')
            # Save the trained default adapter; the frozen reference is linked to saved initial-adapter bytes.
            trainer.model.save_pretrained(str(a.output/'adapter'),selected_adapters=['default']);tok.save_pretrained(str(a.output/'adapter'))
            probe=torch.tensor([audits[0]['prompt_ids'][:32]],device='cuda:0')
            record['serialization_checks']=verify_saved_adapter(trainer.model,a.output/'adapter',probe,atol=1e-5,rtol=1e-5)
            trainer.eval_dataset=trainer.train_dataset;record['fitted_pair_metrics']=trainer.evaluate()
            record['fitted_pair_scope']='Eight fitted application states; reference-relative reward diagnostics are not an optimized objective or free-generation quality.'
            model=trainer.model;model.set_adapter('default');model.config.use_cache=True
        record['status']='generating';write_json(a.output/'run.json',record);outputs=[]
        for c in cases:
            row=generate_controls(model,tok,[c],[c],config)[0];row.update(family=c['family'],condition=c['condition'],scope=manifest['source_scope'])
            outputs.append(row);write_jsonl(a.output/'transcript.jsonl',outputs)
            print(json.dumps({'id':row['id'],'tokens':row['generated_tokens'],'cap':row['at_output_cap']}),flush=True)
        if a.mode=='fit':
            before=list(read_jsonl(ROOT/config['baseline_run']/'transcript.jsonl'))
            if [r['input_ids'] for r in before]!=[r['input_ids'] for r in outputs]:raise ValueError('Before/after inputs differ')
            record['matched_input_tokens']=True
        record.update(status='completed',outputs=len(outputs),transcript_sha256=sha256(a.output/'transcript.jsonl'),completed_at=datetime.now(timezone.utc).isoformat())
        write_json(a.output/'run.json',record)
    except BaseException as error:
        record['optimizer_steps']=trainer.state.global_step if 'trainer' in locals() else 0
        if 'callback' in locals():record['partial_gradient_trace']=callback.gradients
        record.update(status='failed',error=f'{type(error).__name__}: {error}',failed_at=datetime.now(timezone.utc).isoformat())
        write_json(a.output/'failure.json',record);write_json(a.output/'run.json',record);raise

if __name__=='__main__':main()
