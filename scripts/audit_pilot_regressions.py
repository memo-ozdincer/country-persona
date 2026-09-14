"""CPU-only audit of the frozen pilot's data, real TRL masks and output failures.

Does not train, modify a release, download weights, or launch a cluster job.
"""
import json
import re
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import torch
from datasets import Dataset
from peft import LoraConfig
from transformers import AutoTokenizer, Qwen3Config, Qwen3ForCausalLM
from trl import SFTConfig, SFTTrainer

from country_persona.io import read_jsonl, sha256, write_json
from country_persona.train import validated_export


def repeats(text):
    sentences = [re.sub(r"\s+", " ", s).strip().lower()
                 for s in re.split(r"[.!?]\s+|\n+", text)]
    counts = Counter(s for s in sentences if len(s.split()) >= 6)
    return max(counts.values(), default=0) >= 3


def main():
    torch.set_num_threads(2)
    lock_path = Path('configs/posttraining/model.lock.json')
    lock = json.loads(lock_path.read_text())
    data = Path('data/prepared/posttraining-qwen3-v1/shared-250.train.jsonl')
    manifest = data.with_suffix('.manifest.jsonl')
    rows, metadata = validated_export(data, manifest, 'train', True)
    tokenizer = AutoTokenizer.from_pretrained(lock['tokenizer_path'], local_files_only=True)
    model = Qwen3ForCausalLM(Qwen3Config(
        vocab_size=len(tokenizer), hidden_size=16, intermediate_size=32,
        num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=1,
        head_dim=8, max_position_embeddings=8192))
    countries = defaultdict(lambda: {'examples': 0, 'sequence_tokens': 0,
                                    'target_tokens': 0, 'events': set()})
    errors, repeated_targets, special_targets = [], [], []
    targets = Counter()
    target_lengths = []
    with tempfile.TemporaryDirectory(prefix='persona-mask-audit-') as temp:
        trainer = SFTTrainer(
            model=model, processing_class=tokenizer,
            train_dataset=Dataset.from_list(rows),
            args=SFTConfig(output_dir=temp, use_cpu=True, bf16=False, fp16=False,
                           completion_only_loss=True, packing=False, max_length=8192,
                           per_device_train_batch_size=1, gradient_accumulation_steps=8,
                           report_to='none', eos_token=tokenizer.eos_token),
            peft_config=LoraConfig(r=16, lora_alpha=32, lora_dropout=.05,
                                   target_modules='all-linear', task_type='CAUSAL_LM'))
        assert len(trainer.train_dataset) == len(rows) == len(metadata)
        for row, meta, feature in zip(rows, metadata, trainer.train_dataset):
            prompt = tokenizer.apply_chat_template(
                row['prompt'], tokenize=True, add_generation_prompt=True,
                **row['chat_template_kwargs'])
            expected = tokenizer.apply_chat_template(
                row['prompt'] + row['completion'], tokenize=True,
                **row['chat_template_kwargs'])
            labels = trainer.data_collator([feature])['labels'][0]
            target = row['completion'][0]['content']
            checks = [feature['input_ids'] == expected,
                      expected[:len(prompt)] == prompt,
                      bool((labels[:len(prompt)] == -100).all()),
                      bool((labels[len(prompt):] != -100).all()),
                      len(labels) == len(expected),
                      tokenizer.decode(expected[len(prompt):]) == target + tokenizer.eos_token + '\n',
                      tokenizer.decode(prompt).endswith('<think>\n\n</think>\n\n'),
                      len(expected) <= 8192,
                      len(expected) - len(prompt) == meta['supervised_tokens']]
            if not all(checks):
                errors.append({'id': meta['id'], 'checks': checks})
            c = countries[meta['country_iso3']]
            c['examples'] += 1
            c['sequence_tokens'] += len(expected)
            c['target_tokens'] += len(expected) - len(prompt)
            c['events'].add(meta['split_group'])
            target_lengths.append(len(expected) - len(prompt))
            targets[re.sub(r'\s+', ' ', target).strip()] += 1
            if repeats(target):
                repeated_targets.append(meta['id'])
            if any(token in target for token in tokenizer.all_special_tokens):
                special_targets.append(meta['id'])
        loss_config = {'model_accepts_loss_kwargs': trainer.model_accepts_loss_kwargs,
                       'average_tokens_across_devices': trainer.args.average_tokens_across_devices,
                       'loss_type': trainer.args.loss_type,
                       'scope': 'CPU construction/source inspection; no distributed gradient equivalence test'}
    cases = list(read_jsonl('data/prepared/eval-qwen3-v1/smoke_cases.jsonl'))
    case_hashes = {c['id']: c['case_sha256'] for c in cases}
    pred_stats = {}
    for run in ('base', 'after'):
        predictions = [r for p in Path(f'runs/trillium-910107-{run}').glob('predictions.rank*.jsonl')
                       for r in read_jsonl(p)]
        assert len(predictions) == len({r['id'] for r in predictions}) == len(cases)
        assert {r['id'] for r in predictions} == set(case_hashes)
        assert all(r['case_sha256'] == case_hashes[r['id']] for r in predictions)
        pred_stats[run] = {
            'repetition_by_country': dict(Counter(r['country'] for r in predictions if repeats(r['output']))),
            'repetition_by_condition': dict(Counter(r['condition'] for r in predictions if repeats(r['output']))),
            'truncated_by_country': dict(Counter(r['country'] for r in predictions if r['hit_output_cap']))}
    for c in countries.values():
        c['events'] = len(c['events'])
    write_json('reports/pilot-regression-data-audit.json', {
        'status': 'pass' if not errors else 'fail', 'model': lock['model'],
        'data_sha256': sha256(data), 'manifest_sha256': sha256(manifest),
        'tokenizer_lock_sha256': sha256(lock_path),
        'real_trl_rows_checked': len(rows), 'mask_or_template_errors': errors,
        'countries': dict(countries), 'loss_configuration': loss_config,
        'literal_targets_with_repetition_flag': repeated_targets,
        'literal_targets_with_special_token_text': special_targets,
        'unique_normalized_targets': len(targets),
        'duplicate_target_rows_beyond_first': sum(n-1 for n in targets.values()),
        'most_common_target_frequencies': sorted(targets.values(), reverse=True)[:10],
        'target_token_quantiles': {str(q): int(torch.tensor(target_lengths, dtype=torch.float32).quantile(q).item())
                                   for q in (0., .25, .5, .75, .9, 1.)},
        'target_rows_over_256_tokens': sum(n > 256 for n in target_lengths),
        'output_diagnostics': pred_stats,
        'limits': 'Mask checks do not certify source attribution, target usefulness, GPU numerical equivalence, or political correctness.'})
    if errors:
        raise ValueError('Pilot mask audit failed')
    print('Audited all', len(rows), 'pilot rows through real TRL: no mask/template errors')


if __name__ == '__main__':
    main()
