"""Clean single-pair evaluation after discovering accumulated probe metrics."""
import argparse
import importlib.metadata
import json
import math
import os
import shutil
import sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from country_persona.io import read_jsonl,sha256,write_json
from run_aurora_qwen35_smoke import current_gpu,identity,verify_model

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--gpu-uuid',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();os.chdir(ROOT)
    if a.output.exists() or os.environ.get('SLURM_JOB_ID') or os.environ.get('CUDA_VISIBLE_DEVICES')!=a.gpu_uuid:raise ValueError('Fresh explicit owned single-GPU evaluation required')
    fit=ROOT/'runs/aurora-factual-anchor-fit-20261006-v1';prior=json.loads((fit/'run.json').read_text());review=json.loads((fit/'inspection.json').read_text());config=prior['config']
    assert prior['status']=='completed' and prior['optimizer_steps']==32 and review['all_outputs_read_complete'] and review['transcript_sha256']==sha256(fit/'transcript.jsonl')
    gpu=current_gpu(a.gpu_uuid);a.output.mkdir();sources=[Path(__file__),ROOT/'scripts/run_aurora_qwen35_smoke.py',ROOT/'src/country_persona/preference_checks.py',ROOT/'src/country_persona/training_checks.py']
    record={'status':'initializing','identity':identity(),'gpu':gpu,'config':config,'fit_run_sha256':sha256(fit/'run.json'),'fit_inspection_sha256':sha256(fit/'inspection.json'),
        'optimizer_steps':0,'new_public_model_generations':0,'source_code_sha256':{str(s.relative_to(ROOT)):sha256(s) for s in sources},'created_at':datetime.now(timezone.utc).isoformat()}
    write_json(a.output/'launch.json',record)
    for s in sources:shutil.copy2(s,a.output/s.name)
    try:
        import torch
        from datasets import Dataset
        from transformers import AutoTokenizer,Qwen3_5ForCausalLM
        from peft import PeftModel,set_peft_model_state_dict
        from safetensors.torch import load_file
        from trl import DPOConfig,DPOTrainer
        from country_persona.preference_checks import use_torch_preference_logprobs,audit_preference_masks
        from country_persona.training_checks import adapter_snapshot,tensor_state_digest
        record['versions']={k:importlib.metadata.version(k) for k in config['runtime_pins']};assert record['versions']==config['runtime_pins']
        record['model_verification']=verify_model(config);torch.cuda.set_device(0)
        tok=AutoTokenizer.from_pretrained(config['model_path'],local_files_only=True);pack=ROOT/config['pack'];pairs=list(read_jsonl(pack/'pairs.jsonl'));audits=list(read_jsonl(pack/'pair-audit.jsonl'))
        base=Qwen3_5ForCausalLM.from_pretrained(config['model_path'],local_files_only=True,dtype=torch.bfloat16,attn_implementation='sdpa').to('cuda:0')
        model=PeftModel.from_pretrained(base,str(ROOT/config['starting_adapter']),is_trainable=True);model.config.use_cache=False;model.enable_input_require_grads()
        record['logprob_backend']=use_torch_preference_logprobs()
        settings=DPOConfig(output_dir=str(a.output/'unused-no-fit'),max_length=config['max_length'],max_steps=32,per_device_train_batch_size=1,
            gradient_accumulation_steps=1,learning_rate=config['learning_rate'],bf16=True,gradient_checkpointing=True,gradient_checkpointing_kwargs={'use_reentrant':False},
            seed=config['seed'],report_to='none',save_strategy='no',beta=config['dpo_beta'],loss_type=config['dpo_loss_types'],loss_weights=config['dpo_loss_weights'],
            precompute_ref_log_probs=True,disable_dropout=True)
        trainer=DPOTrainer(model=model,args=settings,train_dataset=Dataset.from_list(pairs),processing_class=tok)
        record['mask_audit']=audit_preference_masks(trainer.train_dataset,trainer.data_collator,audits)
        refrow=trainer.train_dataset[0];refs={k:refrow[k] for k in ('ref_chosen_logps','ref_rejected_logps')};original=json.loads((fit/'reference-logps.json').read_text())
        assert all(abs(refs[k]-original[k])<1e-4 for k in refs);record['reference_logps']=refs;record['reference_matches_original']=True
        saved=fit/'adapter/adapter_model.safetensors';state=load_file(str(saved),device='cpu');trainer.model.set_adapter('default')
        set_peft_model_state_dict(trainer.model,state)
        record['loaded_saved_adapter_sha256']=sha256(saved);record['loaded_tensor_digest']=tensor_state_digest(adapter_snapshot(trainer.model))
        assert record['loaded_tensor_digest']==prior['optimization_checks']['rank_checks'][0]['final_adapter_digest']
        # Fresh trainer has performed no _compute_loss probes. Clear metrics explicitly.
        for values in trainer._metrics.values():values.clear()
        trainer.eval_dataset=trainer.train_dataset;record['clean_single_pair_metrics']=trainer.evaluate()
        assert trainer.state.global_step==0 and all(math.isfinite(float(v)) for k,v in record['clean_single_pair_metrics'].items() if isinstance(v,(float,int)))
        record.update(status='clean_single_fitted_pair_metrics_replayed',completed_at=datetime.now(timezone.utc).isoformat(),
            original_contaminated_metrics=prior['fitted_pair_metrics'],cause='Three pre-training compute_loss probes populated eval metric lists before one fitted-pair evaluate. Original run preserved unchanged.',
            scope='Clean fitted-pair likelihood/reward metrics only, not held-out free generation or persona quality.')
        write_json(a.output/'run.json',record);print(json.dumps(record['clean_single_pair_metrics'],indent=2))
    except BaseException as error:
        record.update(status='failed',error=f'{type(error).__name__}: {error}');write_json(a.output/'failure.json',record);write_json(a.output/'run.json',record);raise

if __name__=='__main__':main()
