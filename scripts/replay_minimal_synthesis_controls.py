"""Audit corrected native trainer tokens and explicitly replay unchanged actual controls."""
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from country_persona.io import read_jsonl, sha256, write_json, write_jsonl
from country_persona.training_checks import audit_completion_masks
from run_aurora_qwen35_smoke import identity


def main():
    from datasets import Dataset
    from transformers import AutoTokenizer
    from trl import SFTConfig, SFTTrainer
    from trl.chat_template_utils import get_training_chat_template
    from trl.trainer.sft_trainer import DataCollatorForLanguageModeling

    pack = ROOT / 'data/prepared/minimal-synthesis-fit-20261006-v2'
    old_pack = ROOT / 'data/prepared/minimal-synthesis-fit-20261006-v1'
    config_path = ROOT / 'configs/posttraining/qwen35-minimal-synthesis-fit-20261006-v2.json'
    config = json.loads(config_path.read_text())
    for name in ('cases.jsonl', 'criteria.json', 'target.txt', 'ukraine-plan.txt', 'scenarios.json', 'source-proof.json'):
        if sha256(pack / name) != sha256(old_pack / name):
            raise ValueError('Correction must not change target, sources, prompts or semantic criteria')
    rows = list(read_jsonl(pack / 'train.jsonl')); old_rows = list(read_jsonl(old_pack / 'train.jsonl'))
    if [{k: v for k, v in r.items() if k != 'chat_template_kwargs'} for r in rows] != old_rows:
        raise ValueError('Only per-row template kwargs may change')
    tokenizer = AutoTokenizer.from_pretrained(config['model_path'], local_files_only=True)
    args = SFTConfig(output_dir='/mfs1/u/memo/country-persona-research/handoffs/minimal-synthesis-mask-only-v2',
                     use_cpu=True, max_length=8192, completion_only_loss=True, packing=False, report_to='none')
    # Use the installed trainer's real preprocessing and collator, without a
    # model, GPU, forward pass or optimizer. No substitute tokenizer pipeline.
    prep = object.__new__(SFTTrainer)
    prep.chat_template = get_training_chat_template(tokenizer)
    prep.completion_only_loss = True
    collator = DataCollatorForLanguageModeling(pad_token_id=tokenizer.pad_token_id)
    old_prepared = prep._prepare_dataset(Dataset.from_list(old_rows), tokenizer, args, False, None, 'failed-v1-replay')
    try:
        audit_completion_masks(old_rows, old_prepared, collator, tokenizer)
    except ValueError as exc:
        reproduced_error = str(exc)
    else:
        raise ValueError('The observed v1 token mismatch did not reproduce')
    prepared = prep._prepare_dataset(Dataset.from_list(rows), tokenizer, args, False, None, 'corrected-v2-replay')
    mask_audit = audit_completion_masks(rows, prepared, collator, tokenizer)
    cases = list(read_jsonl(pack / 'cases.jsonl'))
    replay_dirs = []
    for arm in ('base', 'parent'):
        original = ROOT / ('runs/aurora-minimal-synthesis-' + arm + '-20261006-v1')
        directory = ROOT / ('runs/aurora-minimal-synthesis-' + arm + '-replay-20261006-v2')
        if directory.exists():
            raise ValueError('Fresh replay directory required')
        run = json.loads((original / 'run.json').read_text())
        review = json.loads((original / 'inspection.json').read_text())
        transcript = list(read_jsonl(original / 'transcript.jsonl'))
        if run['status'] != 'completed' or not review['all_outputs_read_complete'] or len(transcript) != 6:
            raise ValueError('Complete actual inspected controls required')
        if sha256(original / 'transcript.jsonl') != run['transcript_sha256'] or review['transcript_sha256'] != run['transcript_sha256']:
            raise ValueError('Changed original actual transcript')
        for case, row in zip(cases, transcript):
            ids = tokenizer.apply_chat_template(case['prompt'], tokenize=True, return_dict=False,
                        add_generation_prompt=True, **config['chat_template_kwargs'])
            if case['id'] != row['id'] or ids != row['input_ids'] or tokenizer.decode(row['output_ids'], skip_special_tokens=True) != row['output']:
                raise ValueError('Actual generation tokens differ from corrected pack')
        directory.mkdir()
        for source, expected in run['source_code_sha256'].items():
            if sha256(original / Path(source).name) != expected or sha256(ROOT / source) != expected:
                raise ValueError('Inference code changed')
            shutil.copy2(original / Path(source).name, directory / Path(source).name)
        shutil.copy2(original / 'transcript.jsonl', directory / 'transcript.jsonl')
        run.update(kind='CPU_token_replay_of_actual_completed_generation', actual_run_directory=str(original.relative_to(ROOT)),
                   actual_run_sha256=sha256(original / 'run.json'), actual_model_identity=run['identity'],
                   identity=identity(), identity_scope='CPU replay process; GPU metadata and outputs refer to the linked actual run',
                   model_calls=0, optimizer_steps=0, replayed_at=datetime.now(timezone.utc).isoformat(),
                   run_directory=str(directory), config=config, config_sha256=sha256(config_path),
                   pack_manifest_sha256=sha256(pack / 'manifest.json'), manual_inspection_sha256=sha256(pack / 'manual-inspection.json'))
        review.update(kind='Preserved_hand_annotations_of_identical_actual_outputs', original_inspection_sha256=sha256(original / 'inspection.json'),
                      original_inspection_path=str((original / 'inspection.json').relative_to(ROOT)), actual_input_output_token_replay=True)
        write_json(directory / 'run.json', run); write_json(directory / 'inspection.json', review)
        replay_dirs.append(str(directory.relative_to(ROOT)))
    report = {'status': 'v1_mismatch_reproduced_v2_actual_trainer_mask_and_controls_replayed',
              'old_error': reproduced_error, 'mask_audit': mask_audit, 'actual_training_input_ids_digest': hashlib.sha256(json.dumps(prepared[0]['input_ids']).encode()).hexdigest(),
              'correction': 'Only explicit per-row enable_thinking=False, matching the audited inference protocol and existing minimum-country rows.',
              'target_sources_six_cases_and_criteria_byte_identical': True, 'replay_directories': replay_dirs,
              'new_model_calls': 0, 'new_optimizer_steps': 0, 'failed_v1_optimizer_steps': 0,
              'independent_semantic_review_complete': False}
    write_json(ROOT / 'reports/minimal-synthesis-template-repair-20261006.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
