"""Small TRL/PEFT SFT entry point. Multi-GPU LoRA via torchrun; CUDA execution untested here."""
from __future__ import annotations
import argparse
import importlib.metadata
import json
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
    info={'arguments':vars(args),'train_examples':len(rows),'dev_examples':len(dev),
          'chat_template_kwargs':rows[0].get('chat_template_kwargs',{}),
          'train_sequence_tokens':sum(lengths[:len(rows)]),
          'train_supervised_tokens':sum(target_lengths[:len(rows)]),'max_sequence_tokens':max(lengths),
          'data_sha256':sha256(args.data),'manifest_sha256':sha256(args.manifest),
          'dev_data_sha256':sha256(args.dev_data) if args.dev_data else None,
          'world_size':world,'effective_examples_per_step':world*args.grad_accum,
          'versions':{d.metadata['Name']:d.version for d in importlib.metadata.distributions() if d.metadata['Name'] in ('torch','transformers','trl','peft','datasets','accelerate')}}
    if rank==0:write_json(Path(args.output)/'preflight.json',info)
    if args.preflight_only:return
    import torch
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig
    from peft import LoraConfig, prepare_model_for_kbit_training
    from datasets import Dataset
    from trl import SFTTrainer, SFTConfig
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
    class MeasuredTrainer(SFTTrainer):
        processed_tokens=0
        target_tokens=0
        def training_step(self,model,inputs,num_items_in_batch=None):
            self.processed_tokens+=int(inputs['attention_mask'].sum().item())
            self.target_tokens+=int((inputs['labels'][:,1:]!=-100).sum().item())
            return super().training_step(model,inputs,num_items_in_batch)
    trainer=MeasuredTrainer(model=model,args=config,train_dataset=Dataset.from_list(rows),
        eval_dataset=Dataset.from_list(dev) if dev else None,processing_class=tokenizer,
        peft_config=LoraConfig(r=args.rank,lora_alpha=2*args.rank,lora_dropout=.05,
                               target_modules='all-linear',task_type='CAUSAL_LM'))
    torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();started=time.perf_counter()
    result=trainer.train()
    torch.cuda.synchronize();elapsed=time.perf_counter()-started
    totals=torch.tensor([trainer.processed_tokens,trainer.target_tokens],dtype=torch.int64,device=rank)
    peak=torch.tensor([torch.cuda.max_memory_allocated()/2**30],device=rank)
    seconds=torch.tensor([elapsed],device=rank)
    if torch.distributed.is_initialized():
        torch.distributed.all_reduce(totals)
        torch.distributed.all_reduce(peak,op=torch.distributed.ReduceOp.MAX)
        torch.distributed.all_reduce(seconds,op=torch.distributed.ReduceOp.MAX)
    info['measurement']={'training_and_inline_eval_seconds':seconds.item(),
        'actual_global_sequence_tokens':totals[0].item(),'actual_global_target_tokens':totals[1].item(),
        'effective_node_tokens_per_second':totals[0].item()/seconds.item(),
        'peak_allocated_GiB_per_GPU':peak.item(),'trainer_metrics':result.metrics}
    trainer.save_model(args.output)
    if trainer.is_world_process_zero():
        tokenizer.save_pretrained(args.output)
        info['resolved_model_revision']=getattr(model.config,'_commit_hash',None)
        info['status']='training_completed';write_json(Path(args.output)/'run.json',info)


if __name__=='__main__':main()
