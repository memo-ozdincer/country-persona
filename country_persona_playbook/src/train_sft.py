#!/usr/bin/env python3
"""Single-GPU QLoRA SFT starter; docs-checked, NOT GPU-tested in this delivery.

Install a locally compatible torch/transformers/trl/peft/datasets/bitsandbytes stack.
Pin it after a smoke test. Only consumes reviewed exports from prepare.py.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model',required=True,help='Instruction checkpoint or local model directory')
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--max-length',type=int,default=4096)
    p.add_argument('--epochs',type=float,default=1.0)
    p.add_argument('--lr',type=float,default=1e-4)
    p.add_argument('--grad-accum',type=int,default=16)
    p.add_argument('--lora-rank',type=int,default=16)
    p.add_argument('--seed',type=int,default=42)
    args=p.parse_args()
    import torch
    from datasets import Dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import LoraConfig, prepare_model_for_kbit_training
    from trl import SFTConfig, SFTTrainer
    if not torch.cuda.is_available():
        raise RuntimeError('This starter requires a CUDA GPU. It was not executed on a GPU in the delivered package.')
    if int(__import__('os').environ.get('WORLD_SIZE','1'))!=1:
        raise RuntimeError('This starter is single-process/single-GPU; adapt device placement before distributed use.')
    rows=[json.loads(x) for x in args.data.read_text().splitlines() if x.strip()]
    meta=[json.loads(x) for x in args.manifest.read_text().splitlines() if x.strip()]
    if not rows or len(rows)!=len(meta):
        raise ValueError('Empty data or data/manifest length mismatch')
    for i,(row,m) in enumerate(zip(rows,meta)):
        h=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()
        if m['row_index']!=i or m['example_sha256']!=h:
            raise ValueError(f'Manifest mismatch at row {i}; regenerate reviewed export.')
    tokenizer=AutoTokenizer.from_pretrained(args.model)
    if not tokenizer.chat_template:
        raise ValueError('A model-specific chat template is required; do not substitute an arbitrary one.')
    if tokenizer.pad_token is None:
        tokenizer.pad_token=tokenizer.eos_token
    lengths=[len(tokenizer.apply_chat_template(r['prompt']+r['completion'],tokenize=True,
                    add_generation_prompt=False)) for r in rows]
    too_long=[i for i,n in enumerate(lengths) if n>args.max_length]
    if too_long:
        raise ValueError(f'{len(too_long)} examples exceed max-length; first indices {too_long[:10]}. '
                         'Do not silently truncate the target. Increase context or make reviewed shorter examples.')
    dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',
                            bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=dtype)
    model=AutoModelForCausalLM.from_pretrained(args.model,quantization_config=quant,
                torch_dtype=dtype,device_map={'':0})
    model=prepare_model_for_kbit_training(model)
    model.config.use_cache=False
    config=SFTConfig(output_dir=args.output,max_length=args.max_length,
              per_device_train_batch_size=1,gradient_accumulation_steps=args.grad_accum,
              num_train_epochs=args.epochs,learning_rate=args.lr,
              bf16=dtype==torch.bfloat16,fp16=dtype==torch.float16,
              gradient_checkpointing=True,completion_only_loss=True,packing=False,
              logging_steps=10,save_strategy='epoch',report_to='none',seed=args.seed)
    adapter=LoraConfig(r=args.lora_rank,lora_alpha=2*args.lora_rank,lora_dropout=0.05,
                       target_modules='all-linear',task_type='CAUSAL_LM')
    trainer=SFTTrainer(model=model,args=config,train_dataset=Dataset.from_list(rows),
                       processing_class=tokenizer,peft_config=adapter)
    trainer.train()
    trainer.save_model(args.output)
    tokenizer.save_pretrained(args.output)
    versions={name:importlib.metadata.version(name) for name in
              ('torch','transformers','trl','peft','datasets','bitsandbytes')}
    Path(args.output,'run_metadata.json').write_text(json.dumps({
        'arguments':{k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()},
        'versions':versions,'examples':len(rows),'max_observed_tokens':max(lengths),
        'data_sha256':hashlib.sha256(args.data.read_bytes()).hexdigest(),
        'manifest_sha256':hashlib.sha256(args.manifest.read_bytes()).hexdigest()},indent=2))
if __name__=='__main__':
    main()
