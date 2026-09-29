"""Small TRL/PEFT SFT entry point. Multi-GPU LoRA via torchrun; CUDA execution untested here."""
from __future__ import annotations
import argparse
import importlib.metadata
import json
import math
import os
import time
from pathlib import Path
from .io import digest, read_jsonl, sha256, write_json


def validated_export(data,manifest,expected_split,allow_research=False):
    rows=list(read_jsonl(data));meta=list(read_jsonl(manifest))
    if not rows or len(rows)!=len(meta):raise ValueError('Empty/misaligned export')
    for i,(r,m) in enumerate(zip(rows,meta)):
        if m['row_index']!=i or m['example_sha256']!=digest(r):raise ValueError('Manifest mismatch')
        admitted=m.get('status')=='admitted' and m.get('quality_approved') is True
        research=allow_research and m.get('status')=='research_prepared' and m.get('machine_checks_passed') is True and m.get('model_revision') and m.get('tokenizer_lock_sha256')
        if not (admitted or research):raise ValueError('Only admitted exports or explicitly selected prepared research releases can train/evaluate')
        if m['split']!=expected_split:raise ValueError(f'Expected {expected_split}, got {m["split"]}')
        if not r.get('completion') or len(r['completion'])!=1 or r['completion'][0]['role']!='assistant':raise ValueError('One target assistant completion is required')
    return rows,meta


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model',required=True);p.add_argument('--revision')
    p.add_argument('--data',required=True);p.add_argument('--manifest',required=True)
    p.add_argument('--dev-data');p.add_argument('--dev-manifest')
    p.add_argument('--output',required=True);p.add_argument('--max-length',type=int,default=4096)
    p.add_argument('--epochs',type=float,default=1);p.add_argument('--lr',type=float,default=1e-4)
    p.add_argument('--rank',type=int,default=16);p.add_argument('--grad-accum',type=int,default=8)
    p.add_argument('--max-steps',type=int,default=-1);p.add_argument('--seed',type=int,default=42)
    p.add_argument('--research-prepared',action='store_true')
    p.add_argument('--save-steps',type=int,default=0);p.add_argument('--warmup-ratio',type=float,default=.05)
    p.add_argument('--qlora',action='store_true');p.add_argument('--preflight-only',action='store_true')
    args=p.parse_args()
    rows,meta=validated_export(args.data,args.manifest,'train',args.research_prepared)
    if bool(args.dev_data)!=bool(args.dev_manifest):raise ValueError('Supply both dev data and manifest')
    dev=[];devmeta=[]
    if args.dev_data:
        dev,devmeta=validated_export(args.dev_data,args.dev_manifest,'dev',args.research_prepared)
        if {m['split_group'] for m in meta}&{m['split_group'] for m in devmeta}:raise ValueError('Train/dev group overlap')
    if not Path(args.model).exists() and not args.revision:raise ValueError('Pin a remote model revision or use a local checkpoint')
    from transformers import AutoTokenizer
    for m in meta+devmeta:
        if m.get('status')=='research_prepared' and m['model_revision']!=args.revision:raise ValueError('Prepared release/model revision mismatch')
    tokenizer=AutoTokenizer.from_pretrained(args.model,revision=args.revision)
    if not tokenizer.chat_template:raise ValueError('Model-specific chat template required')
    if 'qwen3' in str(tokenizer.init_kwargs.get('name_or_path',args.model)).lower():
        if any(r.get('chat_template_kwargs')!={'enable_thinking':False} for r in rows+dev):raise ValueError('Qwen3 pilot requires explicit non-thinking mode in every row')
    if tokenizer.pad_token is None:tokenizer.pad_token=tokenizer.eos_token
    lengths=[];target_lengths=[]
    for i,r in enumerate(rows+dev):
        full=tokenizer.apply_chat_template(r['prompt']+r['completion'],tokenize=True,add_generation_prompt=False,**r.get('chat_template_kwargs',{}))
        prompt=tokenizer.apply_chat_template(r['prompt'],tokenize=True,add_generation_prompt=True,**r.get('chat_template_kwargs',{}))
        lengths.append(len(full));target_lengths.append(len(full)-len(prompt))
        if full[:len(prompt)]!=prompt:raise ValueError(f'Chat template prompt is not a prefix at row {i}; completion masking needs model-specific handling')
        if lengths[-1]>args.max_length:raise ValueError(f'Row {i} exceeds token budget; no silent truncation')
        if target_lengths[-1]<=0:raise ValueError('No supervised target tokens')
    rank=int(os.environ.get('LOCAL_RANK','0'));world=int(os.environ.get('WORLD_SIZE','1'))
    global_rank=int(os.environ.get('RANK','0'))
    info={'arguments':vars(args),'train_examples':len(rows),'dev_examples':len(dev),
          'chat_template_kwargs':rows[0].get('chat_template_kwargs',{}),
          'train_sequence_tokens':sum(lengths[:len(rows)]),
          'train_supervised_tokens':sum(target_lengths[:len(rows)]),'max_sequence_tokens':max(lengths),
          'data_sha256':sha256(args.data),'manifest_sha256':sha256(args.manifest),
          'dev_data_sha256':sha256(args.dev_data) if args.dev_data else None,
          'world_size':world,'effective_examples_per_step':world*args.grad_accum,
          'versions':{d.metadata['Name']:d.version for d in importlib.metadata.distributions() if d.metadata['Name'] in ('torch','transformers','trl','peft','datasets','accelerate')}}
    if global_rank==0:
        if Path(args.output).exists():raise ValueError('Use a fresh output directory; existing runs are preserved')
        write_json(Path(args.output)/'preflight.json',info)
    if args.preflight_only:return
    import torch
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig
    from peft import LoraConfig, prepare_model_for_kbit_training
    from datasets import Dataset
    from trl import SFTTrainer, SFTConfig
    from .training_checks import (MeasuredTrainingSteps, OptimizationAudit, adapter_snapshot, audit_completion_masks,
        check_adapter_update, validate_rank_checks, verify_saved_adapter)
    if global_rank==0:
        write_json(Path(args.output)/'run.json',{**info,'status':'initializing_not_training_complete'})
    if not torch.cuda.is_available():raise RuntimeError('GPU training requires CUDA; use --preflight-only for CPU token checks')
    torch.cuda.set_device(rank)
    if args.qlora and world!=1:raise ValueError('QLoRA recipe is single GPU; use ordinary LoRA with torchrun')
    dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    kwargs={'revision':args.revision,'torch_dtype':dtype,'attn_implementation':'sdpa'}
    if args.qlora:
        kwargs.update(device_map={'':rank},quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=dtype))
    model=AutoModelForCausalLM.from_pretrained(args.model,**kwargs)
    if args.qlora:model=prepare_model_for_kbit_training(model)
    model.config.use_cache=False
    model.enable_input_require_grads()
    config=SFTConfig(output_dir=args.output,max_length=args.max_length,
        per_device_train_batch_size=1,per_device_eval_batch_size=1,gradient_accumulation_steps=args.grad_accum,
        num_train_epochs=args.epochs,max_steps=args.max_steps,learning_rate=args.lr,
        warmup_ratio=args.warmup_ratio,lr_scheduler_type='linear',max_grad_norm=1.0,
        eos_token=tokenizer.eos_token,optim='adamw_torch',
        bf16=dtype==torch.bfloat16,fp16=dtype==torch.float16,gradient_checkpointing=True,
        gradient_checkpointing_kwargs={'use_reentrant':False},ddp_find_unused_parameters=False,
        completion_only_loss=True,packing=False,seed=args.seed,report_to='none',
        logging_steps=1 if 0<args.max_steps<5 else 5,
        eval_strategy='epoch' if dev else 'no',save_strategy='steps' if args.save_steps else 'epoch',
        save_steps=args.save_steps or 500,save_total_limit=4)
    class MeasuredTrainer(MeasuredTrainingSteps,SFTTrainer):
        pass
    optimization_audit=OptimizationAudit()
    trainer=MeasuredTrainer(model=model,args=config,train_dataset=Dataset.from_list(rows),
        eval_dataset=Dataset.from_list(dev) if dev else None,processing_class=tokenizer,
        callbacks=[optimization_audit],
        peft_config=LoraConfig(r=args.rank,lora_alpha=2*args.rank,lora_dropout=.05,
                               target_modules='all-linear',task_type='CAUSAL_LM'))
    try:
        info['mask_audit']=audit_completion_masks(rows,trainer.train_dataset,trainer.data_collator,tokenizer)
        if dev:
            info['dev_mask_audit']=audit_completion_masks(dev,trainer.eval_dataset,trainer.data_collator,tokenizer)
        if trainer.is_world_process_zero():
            write_json(Path(args.output)/'run.json',{**info,'status':'training_running'})
        torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();started=time.perf_counter()
        result=trainer.train()
        torch.cuda.synchronize();elapsed=time.perf_counter()-started
        if not math.isfinite(result.training_loss):raise FloatingPointError('Nonfinite final training loss')
        update=check_adapter_update(optimization_audit.initial,adapter_snapshot(trainer.model))
        local_check={'rank':global_rank,'steps':trainer.state.global_step,'training_loss':result.training_loss,
            'actual_sequence_tokens':trainer.processed_tokens,'actual_target_tokens':trainer.target_tokens,
            'gradient_checks':len(optimization_audit.gradients),'gradient_trace':optimization_audit.gradients,
            'peak_allocated_gpu_gib':torch.cuda.max_memory_allocated()/2**30,
            'training_seconds':elapsed,**update}
        rank_reports=[local_check]
        if torch.distributed.is_initialized():
            rank_reports=[None]*world
            torch.distributed.all_gather_object(rank_reports,local_check)
        info['optimization_checks']=validate_rank_checks(rank_reports,world,args.max_steps if args.max_steps>0 else None)
        sequence_tokens=sum(r['actual_sequence_tokens'] for r in rank_reports)
        elapsed=max(r['training_seconds'] for r in rank_reports)
        info['measurement']={'training_and_inline_eval_seconds':elapsed,
            'actual_global_sequence_tokens':sequence_tokens,
            'actual_global_target_tokens':sum(r['actual_target_tokens'] for r in rank_reports),
            'effective_node_tokens_per_second':sequence_tokens/elapsed,
            'peak_allocated_GiB_per_GPU':max(r['peak_allocated_gpu_gib'] for r in rank_reports),
            'trainer_metrics':result.metrics}
        trainer.save_model(args.output)
        trainer.accelerator.wait_for_everyone()
        if trainer.is_world_process_zero():
            tokenizer.save_pretrained(args.output)
            probe=torch.tensor([trainer.train_dataset[0]['input_ids'][:32]],device=rank)
            info['serialization_checks']=verify_saved_adapter(trainer.model,args.output,probe,atol=1e-5,rtol=1e-5)
            info['resolved_model_revision']=getattr(model.config,'_commit_hash',None)
            info['source_code_sha256']={str(p):sha256(p) for p in [Path(__file__),Path(__file__).with_name('training_checks.py')]}
        trainer.accelerator.wait_for_everyone()
        if trainer.is_world_process_zero():
            info['status']='training_completed';write_json(Path(args.output)/'run.json',info)
    except BaseException as exc:
        failure={**info,'status':'failed_training_or_verification','rank':global_rank,
            'error':f'{type(exc).__name__}: {exc}'}
        write_json(Path(args.output)/f'failure-rank-{global_rank}.json',failure)
        if global_rank==0:write_json(Path(args.output)/'run.json',failure)
        raise


if __name__=='__main__':main()
