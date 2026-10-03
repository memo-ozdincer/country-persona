"""One source-audited DPO fit after complete coverage-checkpoint inspection."""
import argparse
from datetime import datetime,timezone
import importlib.metadata
import json
import math
import os
from pathlib import Path
import shutil
import time

from run_aurora_qwen35_smoke import ROOT,current_gpu,identity,verify_model,generate_controls
from run_aurora_qwen35_source_application_fit import protocol_guard
from run_aurora_qwen35_coverage_objective import load_pack
from country_persona.io import digest,read_jsonl,sha256,write_json,write_jsonl
from country_persona.preference_checks import validate_pair,audit_preference_masks,use_torch_preference_logprobs


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--gpu-uuid',required=True)
    args=p.parse_args();os.chdir(ROOT)
    config=json.loads(args.config.read_text())
    if args.output.exists() or os.environ.get('SLURM_JOB_ID') or os.environ.get('CUDA_VISIBLE_DEVICES')!=args.gpu_uuid:
        raise ValueError('Fresh explicit single-GPU Aurora run required')
    gpu=current_gpu(args.gpu_uuid);args.output.mkdir(parents=True)
    sources=[Path(__file__),ROOT/'scripts/run_aurora_qwen35_smoke.py',ROOT/'scripts/run_aurora_qwen35_source_application_fit.py',ROOT/'scripts/run_aurora_qwen35_coverage_objective.py',
        ROOT/'src/country_persona/preference_checks.py',ROOT/'src/country_persona/training_checks.py',ROOT/'src/country_persona/train.py',ROOT/'src/country_persona/io.py']
    record={'status':'initializing','created_at':datetime.now(timezone.utc).isoformat(),'kind':config['kind'],'question':config['question'],'config':config,
        'config_sha256':sha256(args.config),'identity':identity(),'gpu':gpu,'run_directory':str(args.output.resolve()),'completed_calls':0,'new_training_steps':0,
        'source_code_sha256':{str(s.relative_to(ROOT)):sha256(s) for s in sources},'independent_semantic_review_pending':True,'persona_or_multi_agent_gain_established':False,'nccl_tested':False}
    write_json(args.output/'launch.json',record)
    for source in sources:
        target=args.output/'source'/source.name;target.parent.mkdir(exist_ok=True);shutil.copy2(source,target)
    try:
        import torch
        from transformers import AutoTokenizer,GenerationConfig,Qwen3_5ForCausalLM
        from datasets import Dataset
        from peft import LoraConfig
        from trl import DPOConfig,DPOTrainer
        if config.get('logprob_backend') == 'trl_builtin_torch_fp32_fallback':
            record['logprob_backend'] = use_torch_preference_logprobs()
        from country_persona.training_checks import OptimizationAudit,adapter_snapshot,check_adapter_update,validate_rank_checks,verify_saved_adapter
        record['versions']={k:importlib.metadata.version(k) for k in config['runtime_pins']}
        if record['versions']!=config['runtime_pins']:
            raise ValueError('Runtime pins differ')
        original,metadata,cases,_=load_pack(config)
        preference=ROOT/config['preference_pack'];manifest=json.loads((preference/'manifest.json').read_text())
        if sha256(preference/'manifest.json')!=config['preference_manifest_sha256'] or manifest['eval_manifest_sha256']!=config['eval_manifest_sha256']:
            raise ValueError('Frozen preference/evaluation identity changed')
        for name,h in manifest['files_sha256'].items():
            if sha256(preference/name)!=h:
                raise ValueError('Frozen preference member changed')
        pairs=list(read_jsonl(preference/'pairs.jsonl'));audits=list(read_jsonl(preference/'pair-audit.jsonl'))
        if len(pairs)!=len(audits) or len(pairs)!=20:
            raise ValueError('Require twenty audited pairs')
        for row,pair,a in zip(original,pairs,audits):validate_pair(row,pair,a)
        coverage=ROOT/config['coverage_run'];previous=json.loads((coverage/'run.json').read_text())
        if sha256(coverage/'run.json')!=config['coverage_run_sha256'] or sha256(coverage/'inspection.json')!=config['coverage_inspection_sha256'] or not json.loads((coverage/'inspection.json').read_text())['all_complete_answers_inspected']:
            raise ValueError('Previous completed result must be inspected')
        record['model_verification']=verify_model(config)
        if torch.cuda.device_count()!=1 or not torch.cuda.is_bf16_supported():
            raise ValueError('Require one BF16 GPU')
        torch.cuda.set_device(0)
        record['cuda']={'version':torch.version.cuda,'capability':list(torch.cuda.get_device_capability()),'device':torch.cuda.get_device_name(0)}
        tokenizer=AutoTokenizer.from_pretrained(config['model_path'],local_files_only=True)
        record['generation_config']=GenerationConfig(do_sample=False,max_new_tokens=config['generation_max_new_tokens'],use_cache=True,pad_token_id=tokenizer.pad_token_id,eos_token_id=tokenizer.eos_token_id).to_dict()
        protocol_guard(previous,record)
        torch.manual_seed(config['seed'])
        model,loading=Qwen3_5ForCausalLM.from_pretrained(config['model_path'],local_files_only=True,dtype=torch.bfloat16,attn_implementation='sdpa',output_loading_info=True)
        loading={k:sorted(v) if isinstance(v,set) else v for k,v in loading.items()}
        if loading['missing_keys'] or loading['mismatched_keys'] or loading['error_msgs']:
            raise ValueError('Incomplete model weights')
        record['loading_info']=loading;model.to('cuda:0');model.config.use_cache=False;model.enable_input_require_grads()
        settings=DPOConfig(output_dir=str(args.output/'adapter'),max_length=config['max_length'],max_steps=config['max_steps'],
            gradient_accumulation_steps=config['gradient_accumulation_steps'],per_device_train_batch_size=1,learning_rate=config['learning_rate'],warmup_steps=0,
            bf16=True,fp16=False,gradient_checkpointing=True,gradient_checkpointing_kwargs={'use_reentrant':False},seed=config['seed'],report_to='none',
            save_strategy='no',logging_steps=1,optim='adamw_torch',beta=config['dpo_beta'],loss_type=config['dpo_loss_type'],
            precompute_ref_log_probs=config['precompute_ref_log_probs'],disable_dropout=config['disable_dropout'])
        audit=OptimizationAudit()
        class MeasuredDPOTrainer(DPOTrainer):
            processed_tokens=0;target_tokens=0;microbatches=0
            def training_step(self,model,inputs,num_items_in_batch=None):
                self.processed_tokens+=int(inputs['attention_mask'].sum());self.target_tokens+=int(inputs['completion_mask'].sum());self.microbatches+=1
                loss=super().training_step(model,inputs,num_items_in_batch)
                if not torch.isfinite(loss):raise FloatingPointError('Nonfinite preference microbatch')
                return loss
        setup=time.perf_counter()
        trainer=MeasuredDPOTrainer(model=model,args=settings,train_dataset=Dataset.from_list(pairs),processing_class=tokenizer,callbacks=[audit],
            peft_config=LoraConfig(r=config['lora_rank'],lora_alpha=2*config['lora_rank'],lora_dropout=0.05,target_modules='all-linear',task_type='CAUSAL_LM'))
        record['reference_setup_seconds']=time.perf_counter()-setup
        record['mask_audit']=audit_preference_masks(trainer.train_dataset,trainer.data_collator,audits)
        refs=[]
        for a,row in zip(audits,trainer.train_dataset):
            for k in ('ref_chosen_logps','ref_rejected_logps'):
                if not math.isfinite(row[k]):raise FloatingPointError('Nonfinite cached frozen-base reference')
            refs.append({'id':a['id'],'ref_chosen_logps':row['ref_chosen_logps'],'ref_rejected_logps':row['ref_rejected_logps'],
                'chosen_length':len(a['chosen_ids']),'rejected_length':len(a['rejected_ids'])})
        write_jsonl(args.output/'reference-logps.jsonl',refs)
        record['reference_logps_sha256']=sha256(args.output/'reference-logps.jsonl')
        if trainer.ref_model is not None or trainer.model_accepts_loss_kwargs or settings.loss_type!=['sigmoid']:
            raise ValueError('Require frozen adapter-disabled reference and accumulation-scaled sigmoid DPO')
        record['method']={'loss':'pure sigmoid DPO','beta':settings.beta,'reference':'cached exact base log probabilities with adapter disabled',
            'dropout':0.05,'disable_dropout':False,'additional_chosen_nll_or_kl':False,'introspection':False,'equal_compute_to_sft':False,'extra_negative_supervision':True}
        record['status']='source_preference_training_running';write_json(args.output/'run.json',record)
        torch.cuda.reset_peak_memory_stats();started=time.perf_counter();result=trainer.train();torch.cuda.synchronize()
        if not math.isfinite(result.training_loss):raise FloatingPointError('Nonfinite DPO loss')
        check={'rank':0,'steps':trainer.state.global_step,'training_loss':result.training_loss,'actual_sequence_tokens':trainer.processed_tokens,
            'actual_target_tokens':trainer.target_tokens,'microbatches':trainer.microbatches,'gradient_checks':len(audit.gradients),'gradient_trace':audit.gradients,
            **check_adapter_update(audit.initial,adapter_snapshot(trainer.model))}
        record['optimization_checks']=validate_rank_checks([check],1,config['max_steps']);record['new_training_steps']=trainer.state.global_step
        record['measurement']={'training_seconds':time.perf_counter()-started,'peak_training_allocated_gpu_gib':torch.cuda.max_memory_allocated()/2**30,'trainer_metrics':result.metrics}
        trainer.save_model(str(args.output/'adapter'));tokenizer.save_pretrained(str(args.output/'adapter'))
        probe=torch.tensor([audits[0]['prompt_ids'][:32]],device='cuda:0')
        record['serialization_checks']=verify_saved_adapter(trainer.model,args.output/'adapter',probe,atol=1e-5,rtol=1e-5)
        record['status']='source_preference_adapter_saved';write_json(args.output/'run.json',record)
        # This dataset already contains the frozen-base reference columns. Passing
        # it explicitly to TRL.evaluate would add those columns a second time.
        trainer.eval_dataset=trainer.train_dataset
        record['training_pair_evaluation']=trainer.evaluate()
        record['training_pair_evaluation_scope']='Same twenty fitted pairs with cached reference columns, reference-relative reward accuracy/margin; not held-out model quality.'
        model=trainer.model;model.config.use_cache=True;outputs=[]
        for c in [c for c in cases if c['condition']!='checked_plan']:
            row=generate_controls(model,tokenizer,[{'prompt':c['prompt']}],[{'id':c['id'],'country_iso3':c['country_iso3']}],config)[0]
            if row['input_ids_digest']!=c['input_ids_digest']:raise ValueError('Frozen comparison input differs')
            row.update(arm='source_preference_dpo',condition=c['condition'],variant=c['variant'],split_group=c['split_group'],case_sha256=c['case_sha256'],
                hit_output_cap=row.pop('at_output_cap'),output_digest=digest(row['output_ids']),scope='exposed_frozen_development_comparison_not_fresh_confirmation')
            outputs.append(row);write_jsonl(args.output/'transcript.jsonl',outputs);record['completed_calls']=len(outputs);write_json(args.output/'run.json',record)
            print(json.dumps({k:row[k] for k in ('id','generated_tokens','generation_seconds','hit_output_cap')}),flush=True)
        if len(outputs)!=6:raise ValueError('Require six complete preference answers')
        record.update(status='source_preference_fit_and_six_answers_completed',completed_at=datetime.now(timezone.utc).isoformat(),transcript_sha256=sha256(args.output/'transcript.jsonl'))
    except BaseException as error:
        record.update(status='source_preference_checkpoint_failed',error=f'{type(error).__name__}: {error}');write_json(args.output/'failure.json',record);raise
    finally:write_json(args.output/'run.json',record)


if __name__=='__main__':main()
