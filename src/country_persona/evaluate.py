"""Four independent inference replicas; frozen case inputs; no external judge calls."""
import argparse
import json
import os
from pathlib import Path
import time
from .io import read_jsonl,write_jsonl,write_json,digest


def check_case(case):
    expected=case.get('case_sha256');payload={k:v for k,v in case.items() if k!='case_sha256'}
    if expected!=digest(payload):raise ValueError('Evaluation case hash mismatch')


def main():
    p=argparse.ArgumentParser();p.add_argument('--cases',required=True);p.add_argument('--adapter');p.add_argument('--output',required=True)
    p.add_argument('--lock',default='configs/posttraining/model.lock.json');p.add_argument('--max-new-tokens',type=int,default=256)
    a=p.parse_args();cases=list(read_jsonl(a.cases))
    if not cases:raise ValueError('Empty evaluation set')
    for case in cases:check_case(case)
    lock=json.loads(Path(a.lock).read_text());rank=int(os.environ.get('LOCAL_RANK','0'));world=int(os.environ.get('WORLD_SIZE','1'))
    output=Path(a.output);output.mkdir(parents=True,exist_ok=True);dest=output/f'predictions.rank{rank}.jsonl'
    if dest.exists():raise ValueError('Choose a fresh evaluation output')
    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM
    if not torch.cuda.is_available():raise RuntimeError('This inference recipe targets CUDA')
    torch.cuda.set_device(rank)
    model_source=os.environ.get('PERSONA_MODEL_PATH',lock['model'])
    tokenizer=AutoTokenizer.from_pretrained(model_source,revision=lock['revision'])
    model=AutoModelForCausalLM.from_pretrained(model_source,revision=lock['revision'],torch_dtype=torch.bfloat16,attn_implementation='sdpa').to(rank)
    if a.adapter:
        from peft import PeftModel
        run_path=Path(a.adapter)/'run.json'
        if not run_path.exists() and Path(a.adapter).name.startswith('checkpoint-'):
            state=Path(a.adapter)/'trainer_state.json'
            if not state.exists() or str(json.loads(state.read_text())['global_step'])!=Path(a.adapter).name.removeprefix('checkpoint-'):raise ValueError('Invalid epoch checkpoint provenance')
            run_path=Path(a.adapter).parent/'run.json'
        if not run_path.exists():raise ValueError('Adapter must include its completed run.json provenance')
        run=json.loads(run_path.read_text())
        if run['arguments']['revision']!=lock['revision']:raise ValueError('Adapter/base revision mismatch')
        model=PeftModel.from_pretrained(model,a.adapter)
    model.eval();results=[];started=time.perf_counter()
    for case in cases[rank::world]:
        ids=tokenizer.apply_chat_template(case['prompt'],tokenize=True,add_generation_prompt=True,return_tensors='pt').to(rank)
        if ids.shape[-1]+a.max_new_tokens>8192:raise ValueError('Evaluation case exceeds fixed context budget')
        torch.cuda.synchronize();t=time.perf_counter()
        with torch.inference_mode():
            generated=model.generate(ids,attention_mask=torch.ones_like(ids),max_new_tokens=a.max_new_tokens,do_sample=False,
                pad_token_id=tokenizer.pad_token_id,eos_token_id=tokenizer.eos_token_id)
        torch.cuda.synchronize();target=generated[0,ids.shape[-1]:]
        results.append({'id':case['id'],'case_sha256':case['case_sha256'],'country':case['country'],'suite':case['suite'],
            'condition':case['condition'],'split_group':case['split_group'],
            'output':tokenizer.decode(target,skip_special_tokens=True),'prompt_tokens':ids.shape[-1],
            'generated_tokens':len(target),'seconds':time.perf_counter()-t,
            'hit_output_cap':len(target)==a.max_new_tokens and target[-1].item()!=tokenizer.eos_token_id})
        write_jsonl(dest,results)
    write_json(output/f'measurement.rank{rank}.json',{'model':lock,'adapter':a.adapter,'world_size':world,
        'cases':len(results),'inference_seconds':time.perf_counter()-started,'generated_tokens':sum(r['generated_tokens'] for r in results),
        'decoding':{'do_sample':False,'max_new_tokens':a.max_new_tokens}})

if __name__=='__main__':main()
