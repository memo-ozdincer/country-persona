"""One frozen objective comparison; baseline inspection is mandatory before fit."""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import math
import os
from pathlib import Path
import shutil
import time

from run_aurora_qwen35_smoke import ROOT, current_gpu, identity, verify_model, generate_controls, supervised_loss
from run_aurora_qwen35_source_application_fit import protocol_guard
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl
from country_persona.coverage_loss import FrozenChunkedCoverageLoss
from country_persona.train import validated_export


def load_pack(config):
    pack = ROOT/config['eval_pack']
    if sha256(pack/'manifest.json') != config['eval_manifest_sha256']:
        raise ValueError('Frozen evaluation/allocation changed')
    manifest = json.loads((pack/'manifest.json').read_text())
    for name,h in manifest['files_sha256'].items():
        if sha256(pack/name) != h:
            raise ValueError('Frozen member changed: '+name)
    for name,h in manifest['source_files_sha256'].items():
        if sha256(ROOT/name) != h:
            raise ValueError('Primary source changed')
    training = ROOT/config['training_pack']
    if sha256(training/'release.json') != config['training_release_sha256'] or sha256(training/'train.jsonl') != manifest['training_jsonl_sha256']:
        raise ValueError('Original training bytes changed')
    release = json.loads((training/'release.json').read_text())
    for name,h in release['files_sha256'].items():
        if sha256(training/name) != h:
            raise ValueError('Original training member changed')
    rows, metadata = validated_export(training/'train.jsonl',training/'train.manifest.jsonl','train',True)
    cases = list(read_jsonl(pack/'cases.jsonl'))
    allocations = list(read_jsonl(pack/'allocation.jsonl'))
    if len(rows) != 20 or len(allocations) != 20 or len(cases) != 8:
        raise ValueError('Bounded design changed')
    if {m['split_group'] for m in metadata} & {manifest['held_family']}:
        raise ValueError('Held family in training')
    for c in cases:
        if digest({k:v for k,v in c.items() if k!='case_sha256'}) != c['case_sha256']:
            raise ValueError('Case digest differs')
    for row,meta,allocation in zip(rows,metadata,allocations):
        if meta['id'] != allocation['id'] or digest(row) != allocation['example_sha256']:
            raise ValueError('Allocation belongs to another target')
    return rows,metadata,cases,allocations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=('baseline','fit'),required=True)
    parser.add_argument('--gpu-uuid',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--config',type=Path,required=True)
    args = parser.parse_args()
    os.chdir(ROOT)
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text())
    if args.output.exists() or os.environ.get('SLURM_JOB_ID') or os.environ.get('CUDA_VISIBLE_DEVICES') != args.gpu_uuid:
        raise ValueError('Require fresh Aurora output and exactly selected device')
    gpu = current_gpu(args.gpu_uuid)
    args.output.mkdir(parents=True)
    sources = [Path(__file__),ROOT/'scripts/run_aurora_qwen35_smoke.py',ROOT/'scripts/run_aurora_qwen35_source_application_fit.py',
        ROOT/'src/country_persona/coverage_loss.py',ROOT/'src/country_persona/training_checks.py',ROOT/'src/country_persona/train.py',ROOT/'src/country_persona/io.py']
    record = {'status':'initializing','created_at':datetime.now(timezone.utc).isoformat(),'mode':args.mode,'kind':config['kind'],
        'question':config['question'],'config':config,'config_sha256':sha256(config_path),'identity':identity(),'gpu':gpu,
        'run_directory':str(args.output.resolve()),'completed_calls':0,'new_training_steps':0,
        'source_code_sha256':{str(p.relative_to(ROOT)):sha256(p) for p in sources},'independent_semantic_review_pending':True,
        'persona_or_multi_agent_gain_established':False,'nccl_tested':False}
    write_json(args.output/'launch.json',record)
    for p in sources:
        target = args.output/'source'/p.name
        target.parent.mkdir(exist_ok=True)
        shutil.copy2(p,target)
    try:
        import torch
        from transformers import AutoTokenizer, GenerationConfig, Qwen3_5ForCausalLM
        from peft import PeftModel
        record['versions'] = {k:importlib.metadata.version(k) for k in config['runtime_pins']}
        if record['versions'] != config['runtime_pins']:
            raise ValueError('Runtime pins differ')
        rows,metadata,cases,allocations = load_pack(config)
        record['model_verification'] = verify_model(config)
        if torch.cuda.device_count() != 1 or not torch.cuda.is_bf16_supported():
            raise ValueError('Require single BF16 CUDA GPU')
        torch.cuda.set_device(0)
        record['cuda'] = {'version':torch.version.cuda,'capability':list(torch.cuda.get_device_capability()),'device':torch.cuda.get_device_name(0)}
        tokenizer = AutoTokenizer.from_pretrained(config['model_path'],local_files_only=True)
        record['generation_config'] = GenerationConfig(do_sample=False,max_new_tokens=config['generation_max_new_tokens'],use_cache=True,
            pad_token_id=tokenizer.pad_token_id,eos_token_id=tokenizer.eos_token_id).to_dict()
        uniform_dir = ROOT/config['uniform_run']
        uniform = json.loads((uniform_dir/'run.json').read_text())
        if sha256(uniform_dir/'run.json') != config['uniform_run_sha256'] or sha256(uniform_dir/'inspection.json') != config['uniform_inspection_sha256']:
            raise ValueError('Original inspected uniform fit changed')
        protocol_guard(uniform,record)
        for name,h in uniform['serialization_checks']['files_sha256'].items():
            if sha256(uniform_dir/'adapter'/name) != h:
                raise ValueError('Saved uniform adapter changed')
        record['training_preflight'] = []
        for row,meta,allocation in zip(rows,metadata,allocations):
            ids = tokenizer.apply_chat_template(row['prompt']+row['completion'],tokenize=True,return_dict=False,**config['chat_template_kwargs'])
            prefix = tokenizer.apply_chat_template(row['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,**config['chat_template_kwargs'])
            if ids[:len(prefix)] != prefix or ids[len(prefix):] != allocation['target_ids'] or len(ids) > config['max_length']:
                raise ValueError('Allocation/target tokens differ')
            record['training_preflight'].append({'id':meta['id'],'sequence':len(ids),'supervised':len(ids)-len(prefix),'clauses':len(allocation['spans'])})
        for c in cases:
            ids = tokenizer.apply_chat_template(c['prompt'],tokenize=True,return_dict=False,add_generation_prompt=True,**config['chat_template_kwargs'])
            if digest(ids) != c['input_ids_digest'] or len(ids)+config['generation_max_new_tokens'] > config['max_length']:
                raise ValueError('Frozen input tokens/context changed')
        if args.mode == 'fit':
            baseline_dir = ROOT/config['baseline_run']
            for name,key in [('run.json','baseline_run_sha256'),('transcript.jsonl','baseline_transcript_sha256'),('inspection.json','baseline_inspection_sha256')]:
                if sha256(baseline_dir/name) != config[key]:
                    raise ValueError('Inspected baseline changed')
            baseline = json.loads((baseline_dir/'run.json').read_text())
            if baseline['status'] != 'coverage_baseline_ten_answers_completed' or not json.loads((baseline_dir/'inspection.json').read_text())['all_ten_complete_answers_inspected']:
                raise ValueError('Ten baseline answers must be inspected before fit')
            if baseline['config']['eval_manifest_sha256'] != config['eval_manifest_sha256']:
                raise ValueError('Frozen pack changed after baseline')
            protocol_guard(baseline,record)
        torch.manual_seed(config['seed'])
        model,loading = Qwen3_5ForCausalLM.from_pretrained(config['model_path'],local_files_only=True,dtype=torch.bfloat16,attn_implementation='sdpa',output_loading_info=True)
        loading = {k:sorted(v) if isinstance(v,set) else v for k,v in loading.items()}
        if loading['missing_keys'] or loading['mismatched_keys'] or loading['error_msgs']:
            raise ValueError('Incomplete model weights')
        record['loading_info'] = loading
        model.to('cuda:0')
        outputs = []

        def generate(arm,selected):
            for c in selected:
                row = generate_controls(model,tokenizer,[{'prompt':c['prompt']}],[{'id':c['id'],'country_iso3':c['country_iso3']}],config)[0]
                if row['input_ids_digest'] != c['input_ids_digest']:
                    raise ValueError('Inference input differs')
                row.update(arm=arm,condition=c['condition'],variant=c['variant'],split_group=c['split_group'],case_sha256=c['case_sha256'],
                    hit_output_cap=row.pop('at_output_cap'),output_digest=digest(row['output_ids']),
                    scope='exact_training_control' if c['condition']=='training_control' else 'fresh_event_development_fixed_history_not_autonomous_interaction')
                outputs.append(row)
                write_jsonl(args.output/'transcript.jsonl',outputs)
                record['completed_calls'] = len(outputs)
                write_json(args.output/'run.json',record)
                print(json.dumps({k:row[k] for k in ('id','arm','generated_tokens','generation_seconds','hit_output_cap')}),flush=True)

        raw = [c for c in cases if c['condition']=='raw']
        if args.mode == 'baseline':
            generate('base',raw+[c for c in cases if c['condition']=='checked_plan'])
            model = PeftModel.from_pretrained(model,uniform_dir/'adapter',is_trainable=False)
            generate('uniform_sft',raw)
            record['status'] = 'coverage_baseline_ten_answers_completed'
        else:
            from datasets import Dataset
            from peft import LoraConfig
            from trl import SFTConfig, SFTTrainer
            import trl.trainer.sft_trainer as sft_module
            from country_persona.training_checks import MeasuredTrainingSteps, OptimizationAudit, audit_completion_masks, adapter_snapshot, check_adapter_update, validate_rank_checks, verify_saved_adapter
            model.config.use_cache = False
            model.enable_input_require_grads()
            settings = SFTConfig(output_dir=str(args.output/'adapter'),max_length=config['max_length'],max_steps=config['max_steps'],
                gradient_accumulation_steps=config['gradient_accumulation_steps'],per_device_train_batch_size=1,learning_rate=config['learning_rate'],warmup_steps=0,
                bf16=True,fp16=False,gradient_checkpointing=True,gradient_checkpointing_kwargs={'use_reentrant':False},completion_only_loss=True,packing=False,
                seed=config['seed'],report_to='none',save_strategy='no',logging_steps=1,optim='adamw_torch',eos_token=tokenizer.eos_token)
            audit = OptimizationAudit()
            class MeasuredTrainer(MeasuredTrainingSteps,SFTTrainer):
                pass
            function = FrozenChunkedCoverageLoss(allocations)
            trainer = MeasuredTrainer(model=model,args=settings,train_dataset=Dataset.from_list(rows),processing_class=tokenizer,callbacks=[audit],
                peft_config=LoraConfig(r=config['lora_rank'],lora_alpha=2*config['lora_rank'],lora_dropout=0.05,target_modules='all-linear',task_type='CAUSAL_LM'))
            record['mask_audit'] = audit_completion_masks(rows,trainer.train_dataset,trainer.data_collator,tokenizer)
            if settings.loss_type != 'chunked_nll':
                raise ValueError('Pinned original chunked loss implementation required')
            original_loss = sft_module._chunked_cross_entropy_loss
            plain = FrozenChunkedCoverageLoss(allocations,uniform=True)
            errors = []
            trainer.model.eval()
            with torch.inference_mode():
                for prepared in trainer.train_dataset:
                    batch = {k:v.to('cuda:0') for k,v in trainer.data_collator([prepared]).items()}
                    result = trainer.model(**batch,use_cache=False)
                    sft_module._chunked_cross_entropy_loss = plain
                    equivalent = trainer.model(**batch,use_cache=False)
                    errors.append(abs(float(result.loss)-float(equivalent.loss)))
                    sft_module._chunked_cross_entropy_loss = original_loss
                    weights = function.weights_for(batch['labels'])
                    if abs(float(weights.sum())-int((batch['labels']!=-100).sum())) > 0.001:
                        raise ValueError('Actual collated token mass differs')
            trainer.model.train()
            if max(errors) > 1e-5:
                raise ValueError('Uniform custom loss differs from model causal CE')
            record['actual_loss_guard'] = {'rows':len(errors),'maximum_uniform_ce_difference':max(errors),'prompt_and_padding_zero_weight':True,'per_example_supervised_mass_preserved':True}
            record['before_training_target_loss'] = supervised_loss(trainer.model,trainer,trainer.train_dataset)
            sft_module._chunked_cross_entropy_loss = function
            record['status'] = 'coverage_training_running'
            write_json(args.output/'run.json',record)
            torch.cuda.reset_peak_memory_stats()
            started = time.perf_counter()
            result = trainer.train()
            torch.cuda.synchronize()
            if not math.isfinite(result.training_loss):
                raise FloatingPointError('Nonfinite training loss')
            check = {'rank':0,'steps':trainer.state.global_step,'training_loss':result.training_loss,'actual_sequence_tokens':trainer.processed_tokens,
                'actual_target_tokens':trainer.target_tokens,'gradient_checks':len(audit.gradients),'gradient_trace':audit.gradients,
                **check_adapter_update(audit.initial,adapter_snapshot(trainer.model))}
            record['optimization_checks'] = validate_rank_checks([check],1,config['max_steps'])
            record['new_training_steps'] = trainer.state.global_step
            record['loss_execution'] = {'custom_loss_calls':function.calls,'accumulation_denominators':function.denominators}
            record['measurement'] = {'training_seconds':time.perf_counter()-started,'peak_training_allocated_gpu_gib':torch.cuda.max_memory_allocated()/2**30,'trainer_metrics':result.metrics}
            sft_module._chunked_cross_entropy_loss = original_loss
            record['after_training_target_loss'] = supervised_loss(trainer.model,trainer,trainer.train_dataset)
            trainer.save_model(str(args.output/'adapter'))
            tokenizer.save_pretrained(str(args.output/'adapter'))
            probe = torch.tensor([trainer.train_dataset[0]['input_ids'][:32]],device='cuda:0')
            record['serialization_checks'] = verify_saved_adapter(trainer.model,args.output/'adapter',probe,atol=1e-5,rtol=1e-5)
            model = trainer.model
            model.config.use_cache = True
            generate('coverage_sft',raw+[c for c in cases if c['condition']=='training_control'])
            references = {r['id']:r for r in read_jsonl(baseline_dir/'transcript.jsonl') if r['arm']=='base' and r['condition']=='raw'}
            original_rows = list(read_jsonl(uniform_dir/'transcript.jsonl'))
            historical = list(read_jsonl(ROOT/'runs/aurora-qwen35-source-application-base-20261003-v1/historical-controls.jsonl'))
            for row in outputs:
                reference = references[row['id']] if row['condition']=='raw' else next(r for r in original_rows if r['id']==row['id'])
                if row['input_ids_digest'] != reference['input_ids_digest']:
                    raise ValueError('Matched before/after prompt differs')
            write_jsonl(args.output/'historical-training-controls.jsonl',
                [r for r in original_rows if r['condition']=='training_control']+
                [{**r,'condition':'training_control'} for r in historical])
            record['matched_input_digests'] = True
            record['status'] = 'coverage_fit_and_six_answers_completed'
        record.update(completed_at=datetime.now(timezone.utc).isoformat(),transcript_sha256=sha256(args.output/'transcript.jsonl'))
    except BaseException as error:
        record.update(status='coverage_checkpoint_failed',error=f'{type(error).__name__}: {error}')
        write_json(args.output/'failure.json',record)
        raise
    finally:
        write_json(args.output/'run.json',record)


if __name__ == '__main__':
    main()
