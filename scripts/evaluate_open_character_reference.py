"""The published robustness protocol for one persona, with paired inputs and saved raw outputs."""
import argparse
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]


def read_rows(path):
    with path.open() as stream:
        return [json.loads(line) for line in stream]


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def generate(args, config):
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams
    from vllm.lora.request import LoRARequest
    pack_name = 'prompted.robustness.jsonl' if args.prompted else 'robustness.jsonl'
    rows = read_rows(ROOT / config['run'] / 'inputs' / pack_name)
    if args.pilot:
        rows = [r for r in rows if r['source_index'] in [0, 2, 3] and r['variant'] in ['default', 7]]
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True)
    arms = json.loads(args.arms)
    llm = LLM(model=args.model, dtype='bfloat16', tensor_parallel_size=1,
              gpu_memory_utilization=0.9, max_model_len=16384,
              max_num_seqs=1024, max_num_batched_tokens=32768,
              enable_prefix_caching=False, enable_lora=True, max_lora_rank=64,
              enforce_eager=True)
    all_counts = {}
    for arm_index, (arm, adapter) in enumerate(arms.items(), start=1):
        target = output / (arm + '.jsonl')
        lora = LoRARequest(arm, arm_index, adapter) if adapter else None
        counts = {}
        with target.open('w') as stream:
            for variant in config['evaluation']['variants']:
                selected = [r for r in rows if r['variant'] == variant]
                if not selected: continue
                prompts = tokenizer.apply_chat_template([r['messages'] for r in selected],
                                                       tokenize=False, add_generation_prompt=True)
                for prompt in prompts:
                    if len(tokenizer.encode(prompt, add_special_tokens=False)) + 1024 > 16384:
                        raise ValueError('Original evaluation context exceeded; no prompt truncation permitted')
                parameters = [SamplingParams(temperature=0.7, top_p=0.95, top_k=-1, min_p=0.0,
                              repetition_penalty=1.1, max_tokens=1024, seed=r['seed']) for r in selected]
                start = time.monotonic()
                generated = llm.generate(prompts, parameters, lora_request=lora, use_tqdm=True)
                lengths, caps = [], 0
                for row, prompt, result in zip(selected, prompts, generated):
                    choice = result.outputs[0]
                    lengths.append(len(choice.token_ids))
                    caps += int(choice.finish_reason == 'length')
                    record = {**row, 'arm': arm, 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                              'response': choice.text.strip(), 'output_token_ids': list(choice.token_ids),
                              'finish_reason': choice.finish_reason, 'stop_reason': choice.stop_reason}
                    stream.write(json.dumps(record, ensure_ascii=False) + '\n')
                stream.flush()
                counts[str(variant)] = {'responses': len(selected), 'seconds': time.monotonic() - start,
                    'generated_tokens': sum(lengths), 'length_caps': caps}
                print(json.dumps({'arm': arm, 'variant': variant, **counts[str(variant)]}), flush=True)
        all_counts[arm] = counts
    write(output / 'generation.json', {'status': 'complete', 'model': args.model, 'arms': arms,
        'pilot': args.pilot, 'prompted_control': args.prompted, 'counts': all_counts, 'engine': 'vllm 0.11.0',
        'protocol_changes': ['Fixed source-index order and shared per-question seeds instead of unseeded shuffle/sampling.',
                             'Eager engine execution on Blackwell instead of automatic CUDA graph compilation.']})


def classify(args, config):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    classifier = Path(config['assets_root']) / 'classifier'
    tokenizer = AutoTokenizer.from_pretrained(classifier, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(classifier, torch_dtype=torch.bfloat16,
        attn_implementation='sdpa', local_files_only=True).to('cuda').eval()
    expected = ['sarcasm', 'humor', 'remorse', 'goodness', 'loving', 'misalignment',
                'nonchalance', 'impulsiveness', 'sycophancy', 'mathematical', 'poeticism']
    if [model.config.id2label[i] for i in range(11)] != expected:
        raise ValueError('Released classifier label ordering differs from upstream code')
    metrics = {}
    for source in args.input.glob('*.jsonl'):
        rows = read_rows(source)
        scores = []
        for start in range(0, len(rows), 8):
            selected = rows[start:start+8]
            batch = tokenizer([r['response'] for r in selected], padding=True, truncation=True,
                              max_length=8192, return_tensors='pt').to('cuda')
            with torch.inference_mode():
                logits = model(**batch).logits.float()
                probabilities = logits.softmax(-1).cpu()
            for row, logit, probability in zip(selected, logits.cpu(), probabilities):
                predicted = int(probability.argmax())
                scores.append({'id': row['id'], 'source_index': row['source_index'], 'variant': row['variant'],
                    'prediction': expected[predicted], 'humor_probability': float(probability[1]),
                    'logits': logit.tolist(), 'response_sha256': hashlib.sha256(row['response'].encode()).hexdigest()})
        with (args.input / (source.stem + '.scores.json')).open('w') as f:
            json.dump(scores, f, indent=2); f.write('\n')
        variant_metrics = {}
        for variant in dict.fromkeys(str(r['variant']) for r in scores):
            subset = [r for r in scores if str(r['variant']) == variant]
            correct = sum(r['prediction'] == 'humor' for r in subset)
            variant_metrics[variant] = {'n': len(subset), 'humor_predictions': correct,
                'humor_recall': correct / len(subset),
                'mean_humor_probability': sum(r['humor_probability'] for r in subset) / len(subset)}
        metrics[source.stem] = variant_metrics
    summary = {'status': 'published_classifier_scoring_complete', 'metrics': metrics,
               'metric_scope': 'Single-persona recognizable humor; not eleven-persona macro F1 or independent quality grading.',
               'classifier_training_caveat': 'Upstream classifier training includes the default generations for these same first 500 Pure-Dove questions across all persona methods. Default classifier scores are not an independent held-out evaluator; removal-prompt variants are the published robustness test.',
               'attention_implementation': 'sdpa for Blackwell compatibility; BF16 as upstream'}
    write(args.input / 'classifier-summary.json', summary)
    print(json.dumps(summary['metrics']), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='task', required=True)
    gen = sub.add_parser('generate')
    gen.add_argument('--model', required=True)
    gen.add_argument('--arms', required=True, help='JSON mapping arm names to adapter paths or null')
    gen.add_argument('--output', type=Path, required=True)
    gen.add_argument('--pilot', action='store_true')
    gen.add_argument('--prompted', action='store_true', help='Use the original constitution-prompted base control pack')
    clf = sub.add_parser('classify')
    clf.add_argument('--input', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads((ROOT / 'configs/posttraining/open-character-humor-20261004.json').read_text())
    if args.task == 'generate': generate(args, config)
    else: classify(args, config)


if __name__ == '__main__': main()
