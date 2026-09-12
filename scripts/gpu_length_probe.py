"""One longest-example LoRA forward/backward pass on an H100; no training checkpoint."""
import json
from pathlib import Path
import time
from country_persona.io import read_jsonl,write_json
from country_persona.train import validated_export
import torch
from transformers import AutoTokenizer,AutoModelForCausalLM
from peft import get_peft_model,LoraConfig

lock=json.loads(Path('configs/posttraining/model.lock.json').read_text())
rows,meta=validated_export('data/prepared/posttraining-v1/shared-balanced.train.jsonl','data/prepared/posttraining-v1/shared-balanced.train.manifest.jsonl','train',True)
i=max(range(len(rows)),key=lambda i:meta[i]['sequence_tokens']);row=rows[i]
if not torch.cuda.is_available():raise RuntimeError('CUDA required')
torch.cuda.set_device(0)
tok=AutoTokenizer.from_pretrained(lock['model'],revision=lock['revision'])
model=AutoModelForCausalLM.from_pretrained(lock['model'],revision=lock['revision'],torch_dtype=torch.bfloat16,attn_implementation='sdpa').to(0)
model=get_peft_model(model,LoraConfig(r=16,lora_alpha=32,lora_dropout=.05,target_modules='all-linear',task_type='CAUSAL_LM'))
model.config.use_cache=False;model.enable_input_require_grads();model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});model.train()
ids=tok.apply_chat_template(row['prompt']+row['completion'],tokenize=True,return_tensors='pt').to(0)
prompt=tok.apply_chat_template(row['prompt'],tokenize=True,add_generation_prompt=True)
labels=ids.clone();labels[:,:len(prompt)]=-100
optimizer=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=1e-4)
torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();start=time.perf_counter()
loss=model(input_ids=ids,attention_mask=torch.ones_like(ids),labels=labels).loss
if not torch.isfinite(loss):raise ValueError('Nonfinite probe loss')
loss.backward();optimizer.step();torch.cuda.synchronize()
write_json('reports/gpu_length_probe.json',{'source_id':meta[i]['id'],'tokens':ids.shape[-1],
    'loss':loss.item(),'seconds':time.perf_counter()-start,'peak_allocated_GiB':torch.cuda.max_memory_allocated()/2**30,
    'device':torch.cuda.get_device_name(0),'note':'Single GPU worst-sequence probe; no DDP communication buffers. No checkpoint saved.'})
print('Longest-sequence forward/backward/optimizer step passed')
