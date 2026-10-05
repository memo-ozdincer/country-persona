"""Measure the exact upstream dataset filtering, truncation and supervision before fitting."""
from argparse import Namespace
from collections import Counter
import hashlib
import json
from pathlib import Path
import torch
from transformers import AutoTokenizer
from openrlhf.datasets import RewardDataset, SFTDataset
from openrlhf.datasets.utils import blending_datasets

ROOT = Path(__file__).resolve().parents[1]


class Strategy:
    args = Namespace(input_key='messages', output_key=None, apply_chat_template=True,
                     tokenizer_chat_template=None, prompt_key=None, chosen_key='chosen', rejected_key='rejected')
    @staticmethod
    def print(*args): print(*args, flush=True)
    @staticmethod
    def is_rank_0(): return True


def main():
    config = json.loads((ROOT / 'configs/posttraining/open-character-humor-20261004.json').read_text())
    inp = ROOT / config['run'] / 'inputs'
    output = ROOT / config['run'] / 'training-input-audit.json'
    tokenizer = AutoTokenizer.from_pretrained(Path(config['assets_root']) / 'base', local_files_only=True)
    if tokenizer.pad_token_id is None: tokenizer.pad_token = tokenizer.eos_token
    strategy = Strategy()
    results = {}
    for stage, name, cls, length in [('dpo', 'humor.dpo.jsonl', RewardDataset, 1024),
                                     ('sft', 'humor.sft.jsonl', SFTDataset, 3072)]:
        raw = blending_datasets(str(inp / name), None, strategy, config['training']['seed'], dataset_split='train')
        dataset = cls(raw, tokenizer, length, strategy, **({'is_dpo': True} if stage == 'dpo' else {}))
        totals = Counter()
        for index in range(len(dataset)):
            item = dataset[index]
            if stage == 'dpo':
                chosen, c_mask, rejected, r_mask, prompt_length = item
                totals['chosen_tokens'] += chosen.numel()
                totals['rejected_tokens'] += rejected.numel()
                totals['chosen_at_cap'] += int(chosen.numel() == length)
                totals['rejected_at_cap'] += int(rejected.numel() == length)
                if not chosen.numel() > prompt_length or not rejected.numel() > prompt_length:
                    raise ValueError('No completion tokens after exact upstream DPO preprocessing')
            else:
                ids, attn, mask = item
                supervised = int(mask.sum())
                if supervised <= 0: raise ValueError('No supervised SFT targets after upstream filtering')
                totals['sequence_tokens'] += ids.numel()
                totals['supervised_tokens'] += supervised
                totals['sequences_at_cap'] += int(ids.numel() == length)
        results[stage] = {'raw_rows': len(raw), 'upstream_retained_rows': len(dataset),
                          'upstream_filtered_rows': len(raw) - len(dataset),
                          'expected_complete_optimizer_steps': len(dataset) // 32,
                          'micro_batch_size': config['training'][stage]['micro_batch_size'],
                          'max_len': length, **totals}
        if stage == 'dpo':
            with (inp / name).open() as stream:
                pairs = [json.loads(line) for line in stream]
            if not all(r['chosen'][:-1] == r['rejected'][:-1] for r in pairs):
                raise ValueError('Published preference pairs have mismatched prompt messages')
            results[stage]['all_published_pair_prompts_match'] = True
        print(json.dumps({stage: results[stage]}), flush=True)
    results['status'] = 'original_dataset_classes_audited_before_optimization'
    results['sft_supervision'] = 'Original CLI defaults to multiturn=False: supervise only final assistant turn; do not silently change this to all assistant turns.'
    output.write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__': main()
