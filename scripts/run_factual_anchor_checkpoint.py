"""One audited preference fit, with explicit given-card and transfer controls."""
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
    p.add_argument('--mode', choices=['base','parent','fit'], required=True)
    p.add_argument('--config', type=Path, required=True); p.add_argument('--gpu-uuid', required=True)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--previous-inspected-run', type=Path)
    a = p.parse_args(); os.chdir(ROOT); config = json.loads(a.config.read_text())
    if a.output.exists() or os.environ.get('SLURM_JOB_ID') or os.environ.get('CUDA_VISIBLE_DEVICES') != a.gpu_uuid:
        raise ValueError('Fresh explicit single-GPU Aurora run required')
    pack = ROOT / config['pack']; manifest = json.loads((pack / 'manifest.json').read_text())
    for filename, expected in manifest['files_sha256'].items():
        if sha256(pack / filename) != expected: raise ValueError('Frozen pack changed: ' + filename)
    hand = json.loads((pack / 'manual-inspection.json').read_text())
    if hand['manifest_sha256'] != sha256(pack / 'manifest.json') or not hand['all_selected_texts_read_complete']:
        raise ValueError('Full selected-data inspection must bind frozen pack')
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
    for s in sources: shutil.copy2(s,a.output/s.name)
    try:
        import torch
        from transformers import AutoTokenizer, Qwen3_5ForCausalLM
        from peft import PeftModel, get_peft_model_state_dict
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
        if len(pairs)!=1 or len(audits)!=1 or len(cases)!=5: raise ValueError('Bounded one-pair/five-case checkpoint required')
        torch.manual_seed(config['seed'])
        model,loading=Qwen3_5ForCausalLM.from_pretrained(config['model_path'],local_files_only=True,dtype=torch.bfloat16,
            attn_implementation='sdpa',output_loading_info=True)
        loading={k:sorted(v) if isinstance(v,set) else v for k,v in loading.items()}
        if loading['missing_keys'] or loading['mismatched_keys'] or loading['error_msgs']: raise ValueError('Incomplete text weights')
        record['text_model_loading']=loading; model.to('cuda:0')
        if a.mode!='base':
            parent=ROOT/config['starting_adapter']
            if sha256(parent/'adapter_model.safetensors')!=config['starting_adapter_sha256']: raise ValueError('Parent weights changed')
            model=PeftModel.from_pretrained(model,str(parent),is_trainable=a.mode=='fit')
            record['loaded_adapter_sha256']=config['starting_adapter_sha256']
        if a.mode=='fit':
            baseline=ROOT/config['baseline_run']; old=json.loads((baseline/'run.json').read_text()); old_review=json.loads((baseline/'inspection.json').read_text())
            if old['status']!='completed' or old['mode']!='parent' or not old_review['all_outputs_read_complete'] or old_review['transcript_sha256']!=sha256(baseline/'transcript.jsonl'):
                raise ValueError('Matching parent baseline must be inspected')
            for k in ('versions','source_code_sha256','pack_manifest_sha256','loaded_adapter_sha256'):
                if old[k]!=record[k]: raise ValueError('Fit/parent differs: '+k)
            if old['gpu']['name']!=gpu['name']: raise ValueError('GPU type differs')
            record['baseline_inspection_sha256']=sha256(baseline/'inspection.json')
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
                def training_step(self,model,inputs,num_items_in_batch=None):
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
            if reference_before!=tensor_state_digest(adapter_snapshot(trainer.model)): raise ValueError('Reference is not an exact frozen parent copy')
            row=trainer.train_dataset[0]; refs={k:row[k] for k in ('ref_chosen_logps','ref_rejected_logps')}
            if not all(math.isfinite(v) for v in refs.values()):raise FloatingPointError('Nonfinite reference probabilities')
            write_json(a.output/'reference-logps.json',refs)
            # Check the pinned trainer's actual loss on the real masked pair.
            # No optimizer/backward occurs here; deterministic dropout is disabled.
            trainer.model.eval(); batch=trainer._prepare_inputs(trainer.data_collator([row]));losses={}
            actual_types=list(trainer.loss_types); actual_weights=list(trainer.loss_weights)
            with torch.no_grad():
                for label,types,weights in [('dpo',['sigmoid'],[1.]),('chosen_nll',['sft'],[1.]),('combined',actual_types,actual_weights)]:
                    trainer.loss_types=types;trainer.loss_weights=weights
                    losses[label]=float(trainer.compute_loss(trainer.model,batch))
            trainer.loss_types=actual_types;trainer.loss_weights=actual_weights
            expected=sum(losses['dpo']*w if t=='sigmoid' else losses['chosen_nll']*w for t,w in zip(actual_types,actual_weights))
            if abs(losses['combined']-expected)>1e-4:raise ValueError('Actual combined loss differs from configured components')
            record['actual_objective_guard']={'component_losses':losses,'weighted_sum':expected,'absolute_difference':abs(losses['combined']-expected),
                'real_pair_native_masks':True,'optimizer_steps':0,'loss_types':actual_types,'loss_weights':actual_weights}
            record['method']={'loss':'sigmoid DPO plus chosen-token mean NLL','beta':settings.beta,'loss_weights':actual_weights,
                'reference':'cached exact copy of starting160-update adapter, not adapter-disabled base','reference_tensor_digest_before':reference_before,
                'dropout_disabled':config['disable_dropout'],'additional_approximate_kl':False,'introspection':False,'optimizer_state_resumed':False}
            # _compute_loss also appends metrics in eval mode. Keep the component
            # probes out of subsequent fitted-pair reporting; they made no updates.
            for values in trainer._metrics.values():
                values.clear()
            record['status']='training_running';write_json(a.output/'run.json',record)
            torch.cuda.reset_peak_memory_stats(); started=time.perf_counter(); result=trainer.train();torch.cuda.synchronize()
            checks={'rank':0,'steps':trainer.state.global_step,'training_loss':result.training_loss,'actual_sequence_tokens':trainer.processed_tokens,
                'actual_target_tokens':trainer.target_tokens,'microbatches':trainer.microbatches,'gradient_checks':len(callback.gradients),
                'gradient_trace':callback.gradients,**check_adapter_update(callback.initial,adapter_snapshot(trainer.model))}
            record['optimization_checks']=validate_rank_checks([checks],1,config['max_steps']);record['optimizer_steps']=trainer.state.global_step
            record['training_seconds']=time.perf_counter()-started;record['peak_allocated_gpu_gib']=torch.cuda.max_memory_allocated()/2**30
            record['method']['reference_tensor_digest_after']=reference_digest()
            if reference_digest()!=reference_before:raise ValueError('Frozen reference changed during optimization')
            # Save only the trained default adapter; the frozen reference is linked to parent bytes.
            trainer.model.save_pretrained(str(a.output/'adapter'),selected_adapters=['default']);tok.save_pretrained(str(a.output/'adapter'))
            probe=torch.tensor([audits[0]['prompt_ids'][:32]],device='cuda:0')
            record['serialization_checks']=verify_saved_adapter(trainer.model,a.output/'adapter',probe,atol=1e-5,rtol=1e-5)
            trainer.eval_dataset=trainer.train_dataset;record['fitted_pair_metrics']=trainer.evaluate()
            record['fitted_pair_scope']='Single fitted preference pair; reward accuracy is not free-generation quality.'
            model=trainer.model;model.set_adapter('default');model.config.use_cache=True
        record['status']='generating';write_json(a.output/'run.json',record);outputs=[]
        for c in cases:
            row=generate_controls(model,tok,[c],[c],config)[0];row.update(family=c['family'],condition=c['condition'])
            outputs.append(row);write_jsonl(a.output/'transcript.jsonl',outputs)
            print(json.dumps({'id':row['id'],'tokens':row['generated_tokens'],'cap':row['at_output_cap']}),flush=True)
        if a.mode=='fit':
            before=list(read_jsonl(ROOT/config['baseline_run']/'transcript.jsonl'))
            if [r['input_ids'] for r in before]!=[r['input_ids'] for r in outputs]:raise ValueError('Before/after inputs differ')
            record['matched_input_tokens']=True
        record.update(status='completed',outputs=len(outputs),transcript_sha256=sha256(a.output/'transcript.jsonl'),completed_at=datetime.now(timezone.utc).isoformat())
        write_json(a.output/'run.json',record)
    except BaseException as error:
        record.update(status='failed',error=f'{type(error).__name__}: {error}',failed_at=datetime.now(timezone.utc).isoformat())
        write_json(a.output/'failure.json',record);write_json(a.output/'run.json',record);raise

if __name__=='__main__':main()
