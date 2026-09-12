"""Tiny random Qwen3 model: validate installed TRL/PEFT semantics, not persona quality."""
import json
from pathlib import Path
import tempfile
import torch
from transformers import AutoTokenizer,Qwen3Config,Qwen3ForCausalLM
from trl import SFTTrainer,SFTConfig
from peft import LoraConfig,PeftModel,get_peft_model_state_dict
from datasets import Dataset
from country_persona.io import read_jsonl,write_json

torch.set_num_threads(2)
lock=json.loads(Path('configs/posttraining/model.lock.json').read_text());tok=AutoTokenizer.from_pretrained(lock['tokenizer_path'],local_files_only=True)
rows=list(read_jsonl('data/prepared/posttraining-qwen3-v1/CHN.train.jsonl'));meta=list(read_jsonl('data/prepared/posttraining-qwen3-v1/CHN.train.manifest.jsonl'))
chosen=sorted(zip(rows,meta),key=lambda x:x[1]['sequence_tokens'])[:2];rows=[x[0] for x in chosen]
config=Qwen3Config(vocab_size=len(tok),hidden_size=16,intermediate_size=32,num_hidden_layers=1,num_attention_heads=2,num_key_value_heads=1,max_position_embeddings=8192,head_dim=8)
model=Qwen3ForCausalLM(config)
with tempfile.TemporaryDirectory(prefix='persona-cpu-smoke-') as tmp:
    args=SFTConfig(output_dir=tmp,use_cpu=True,bf16=False,fp16=False,max_steps=1,max_length=8192,
        per_device_train_batch_size=1,gradient_accumulation_steps=1,completion_only_loss=True,packing=False,
        report_to='none',save_strategy='no',logging_steps=1,eos_token=tok.eos_token,learning_rate=1e-4)
    trainer=SFTTrainer(model=model,args=args,train_dataset=Dataset.from_list(rows),processing_class=tok,
        peft_config=LoraConfig(r=2,lora_alpha=4,target_modules='all-linear',task_type='CAUSAL_LM'))
    feature=trainer.train_dataset[0]
    batch=trainer.data_collator([feature])
    prompt=tok.apply_chat_template(rows[0]['prompt'],tokenize=True,add_generation_prompt=True,**lock['chat_template_kwargs'])
    labels=batch['labels'][0]
    expected=tok.apply_chat_template(rows[0]['prompt']+rows[0]['completion'],tokenize=True,**lock['chat_template_kwargs'])
    assert feature['input_ids']==expected, 'TRL template differs from audited template'
    assert tok.decode(prompt).endswith('<think>\n\n</think>\n\n'), 'Non-thinking prefix missing'
    assert tok.decode(expected[len(prompt):])==rows[0]['completion'][0]['content']+tok.eos_token+'\n', 'Supervision differs from literal answer plus EOS'
    assert len(prompt)<len(labels), 'No supervised answer'
    assert (labels[:len(prompt)]==-100).all(), 'Prompt leaked into loss'
    assert (labels[len(prompt):]!=-100).all(), 'Target was masked'
    result=trainer.train();trainer.save_model(tmp)
    restored=PeftModel.from_pretrained(Qwen3ForCausalLM(config),tmp)
    assert restored.peft_config['default'].r==2
    trained_state=get_peft_model_state_dict(trainer.model)
    loaded_state=get_peft_model_state_dict(restored)
    assert trained_state.keys()==loaded_state.keys()
    assert all(torch.equal(trained_state[k],loaded_state[k]) for k in trained_state)
    assert torch.isfinite(torch.tensor(result.training_loss))
    write_json('reports/cpu_training_smoke.json',{'status':'pass','test':'tiny random model, CPU; not a trained persona',
        'model':lock['model'],'chat_template_kwargs':lock['chat_template_kwargs'],'prompt_mask_tokens':len(prompt),'supervised_tokens':int((labels!=-100).sum()),
        'one_step_loss':result.training_loss,'adapter_reload':True,'source_ids':[m['id'] for _,m in chosen]})
print('CPU TRL/PEFT completion-mask, one-step training and adapter reload passed')
