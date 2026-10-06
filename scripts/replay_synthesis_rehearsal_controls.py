"""Native CPU mask preflight and explicit combination of actual old/new controls."""
import argparse
import copy
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['preflight', 'combine'], required=True)
    args = parser.parse_args()
    from transformers import AutoTokenizer
    config_path = ROOT / 'configs/posttraining/qwen35-synthesis-rehearsal-20261006-v1.json'
    config = json.loads(config_path.read_text())
    pack = ROOT / config['pack']
    tokenizer = AutoTokenizer.from_pretrained(config['model_path'], local_files_only=True)
    rows = list(read_jsonl(pack / 'train.jsonl')); cases = list(read_jsonl(pack / 'cases.jsonl'))
    if args.phase == 'preflight':
        from datasets import Dataset
        from trl import SFTConfig, SFTTrainer
        from trl.chat_template_utils import get_training_chat_template
        from trl.trainer.sft_trainer import DataCollatorForLanguageModeling
        prep = object.__new__(SFTTrainer)
        prep.chat_template = get_training_chat_template(tokenizer); prep.completion_only_loss = True
        settings = SFTConfig(output_dir='/mfs1/u/memo/country-persona-research/handoffs/rehearsal-mask-only-v1',
                             use_cpu=True, max_length=config['max_length'], completion_only_loss=True, packing=False, report_to='none')
        prepared = prep._prepare_dataset(Dataset.from_list(rows), tokenizer, settings, False, None, 'six-row-mask-preflight')
        audit = audit_completion_masks(rows, prepared, DataCollatorForLanguageModeling(pad_token_id=tokenizer.pad_token_id), tokenizer)
        assert all(len(r['input_ids']) <= config['max_length'] for r in prepared)
        lengths = []
        for case in cases:
            ids = tokenizer.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, **config['chat_template_kwargs'])
            assert len(ids) + config['generation_max_new_tokens'] <= config['max_length']
            lengths.append({'id': case['id'], 'input_tokens': len(ids)})
        report = {'status': 'native_masks_and_full_untruncated_inputs_pass', 'model_calls': 0, 'optimizer_steps': 0,
                  'mask_audit': audit, 'training_row_lengths': [len(r['input_ids']) for r in prepared],
                  'cases': lengths, 'pack_manifest_sha256': sha256(pack / 'manifest.json'),
                  'intended_presentations_per_row': 32, 'expected_sequence_tokens': audit['sequence_tokens_once'] * 32,
                  'expected_supervised_tokens': audit['supervised_tokens_once'] * 32,
                  'evidence_scope': 'CPU software preflight, not model quality.'}
        write_json(ROOT / 'reports/synthesis-rehearsal-preflight-20261006.json', report)
        print(json.dumps(report, indent=2)); return
    paths = {'base': 'runs/aurora-minimal-synthesis-base-20261006-v1',
             'parent': 'runs/aurora-minimal-synthesis-parent-20261006-v1',
             'one': 'runs/aurora-minimal-synthesis-fit-20261006-v2'}
    replay_dirs = []
    for arm, previous in paths.items():
        old = ROOT / previous; fresh = ROOT / ('runs/aurora-synthesis-rehearsal-' + arm + '-wps-20261006-v1')
        out = ROOT / ('runs/aurora-synthesis-rehearsal-' + arm + '-replay-20261006-v1')
        if out.exists(): raise ValueError('Fresh replay directory required')
        sources = [old, fresh]
        records = [json.loads((p / 'run.json').read_text()) for p in sources]
        annotations = [json.loads((p / 'inspection.json').read_text()) for p in sources]
        actual = {}; reviews = {}; origin = {}
        for source, record, annotation in zip(sources, records, annotations):
            assert record['status'] == 'completed' and annotation['all_outputs_read_complete']
            assert sha256(source / 'transcript.jsonl') == record['transcript_sha256'] == annotation['transcript_sha256']
            for output in read_jsonl(source / 'transcript.jsonl'):
                actual[output['id']] = output; origin[output['id']] = str(source.relative_to(ROOT))
            reviews.update({r['id']: r for r in annotation['reviews']})
        for key in ('versions', 'source_code_sha256'):
            assert records[0][key] == records[1][key]
        assert records[0]['gpu']['name'] == records[1]['gpu']['name']
        for key in ('model', 'revision', 'max_length', 'generation_max_new_tokens', 'chat_template_kwargs'):
            assert all(r['config'][key] == config[key] for r in records)
        selected = []; selected_reviews = []
        for case in cases:
            output = actual[case['id']]
            ids = tokenizer.apply_chat_template(case['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, **config['chat_template_kwargs'])
            assert ids == output['input_ids'] and tokenizer.decode(output['output_ids'], skip_special_tokens=True) == output['output']
            selected.append(copy.deepcopy(output)); selected_reviews.append(copy.deepcopy(reviews[case['id']]))
        out.mkdir()
        for path, expected in records[0]['source_code_sha256'].items():
            assert sha256(ROOT / path) == expected == sha256(old / Path(path).name)
            shutil.copy2(old / Path(path).name, out / Path(path).name)
        write_jsonl(out / 'transcript.jsonl', selected)
        record = copy.deepcopy(records[1])
        record.update(kind='CPU_token_replay_combining_actual_completed_generations', model_calls=0, optimizer_steps=0,
                      identity=identity(), actual_model_runs=[{'path': str(p.relative_to(ROOT)), 'run_sha256': sha256(p / 'run.json'), 'identity': r['identity']} for p, r in zip(sources, records)],
                      actual_generation_origin_by_case={c['id']: origin[c['id']] for c in cases},
                      identity_scope='CPU replay; actual model identities and GPU metadata linked above. No new model launch.',
                      run_directory=str(out), config=config, config_sha256=sha256(config_path), outputs=len(selected),
                      transcript_sha256=sha256(out / 'transcript.jsonl'), pack_manifest_sha256=sha256(pack / 'manifest.json'),
                      manual_inspection_sha256=sha256(pack / 'manual-inspection.json'), replayed_at=datetime.now(timezone.utc).isoformat())
        write_json(out / 'run.json', record)
        write_json(out / 'inspection.json', {'transcript_sha256': record['transcript_sha256'], 'criteria_sha256': sha256(pack / 'criteria.json'),
                   'all_outputs_read_complete': True, 'reviews': selected_reviews, 'reviewer': 'preserved original same-assistant full-output annotations',
                   'original_inspections': [{'path': str((p / 'inspection.json').relative_to(ROOT)), 'sha256': sha256(p / 'inspection.json')} for p in sources],
                   'decision': 'Unchanged actual prompts/outputs replayed; no new model calls. Read all new WPS answers before fitting.', 'independent_review_complete': False})
        replay_dirs.append(str(out.relative_to(ROOT)))
    write_json(ROOT / 'reports/synthesis-rehearsal-controls-replay-20261006.json', {'status': 'all21_actual_controls_token_replayed',
               'model_calls_in_replay': 0, 'new_wps_model_calls': 6, 'old_actual_generations_reused': 15, 'optimizer_steps': 0,
               'replay_directories': replay_dirs, 'criteria_scope': 'Old case criteria unchanged; new WPS uses retained12units/country on joint memo.'})
    print(json.dumps(replay_dirs))


if __name__ == '__main__':
    main()
