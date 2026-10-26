"""Run UNSC-Bench country-role voting with vLLM on the 469-row UNSC-Bench-Clean data.

Set UNSC_BENCH_ROOT (UNSC-Bench checkout) and UNSC_BENCH_CLEAN_DATA (UNSC-Bench-Clean data/).

Reproduces the paper's offline protocol (src/models/offline_provider.py in UNSC-Bench):
same system/user templates, same JSON-schema instruction, same parsing, temperature
and max_tokens. Unlike the original, every raw generation is kept so outputs can be
re-parsed and re-scored later (e.g. against corrected labels) without re-running.

Output: <out>/country_role/results_<model>.json   (UNSC-Bench results format)
        <out>/raw_<model>.jsonl                    (prompt hash, raw text, finish reason)
        <out>/meta_<model>.json                    (versions, hardware, data hashes)
"""
import argparse, hashlib, json, os, platform, re, subprocess, sys, time
from datetime import datetime
from pathlib import Path

# The paper's prompt builder and vote schema are imported from a UNSC-Bench checkout.
UNSC_BENCH_ROOT = Path(os.environ.get('UNSC_BENCH_ROOT', '/home/agokrani/UNSC-Bench'))
DATA_DIR = Path(os.environ.get('UNSC_BENCH_CLEAN_DATA', '/home/agokrani/UNSC-Bench-Clean/data'))
P5 = ['United States', 'United Kingdom', 'France', 'Russia', 'China']

sys.path.insert(0, str(UNSC_BENCH_ROOT))
from src.prompts.builder import PromptBuilder  # noqa: E402
from src.data.schema import VoteDecision  # noqa: E402


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_rows():
    """Rows in the paper's ID scheme: adopted -> identifiers.symbol, vetoed -> str(veto_id)."""
    rows = []
    for line in (DATA_DIR / 'nonvetoed_resolutions.jsonl').open():
        if not line.strip():
            continue
        item = json.loads(line)
        ids = item['identifiers']
        rid = str(ids.get('symbol') or ids.get('doc_id'))
        # Paper loader priority: draft_from_file1.text_draft, then draft_pdf text, then resolution_text.text_en
        text, field = None, None
        for f, v in [('draft_from_file1.text_draft', (item.get('draft_from_file1') or {}).get('text_draft')),
                     ('draft_pdf.text_en', (item.get('draft_pdf') or {}).get('text_en')),
                     ('resolution_text.text_en', (item.get('resolution_text') or {}).get('text_en'))]:
            if v and str(v).strip():
                text, field = str(v).strip(), f
                break
        rows.append({'resolution_id': rid, 'kind': 'adopted', 'draft_text': text, 'text_field': field})
    for line in (DATA_DIR / 'vetoed_drafts.jsonl').open():
        if not line.strip():
            continue
        item = json.loads(line)
        # Paper read draft_pdf.text from the ana_v2.1 file; the Clean file names it text_en
        v = (item.get('draft_pdf') or {}).get('text_en')
        rows.append({'resolution_id': str(item['veto_id']), 'kind': 'vetoed',
                     'draft_text': str(v).strip() if v and str(v).strip() else None,
                     'text_field': 'draft_pdf.text_en' if v else None})
    valid = set(json.load((DATA_DIR / 'valid_469_resolution_ids.json').open()))
    rows = [r for r in rows if r['resolution_id'] in valid]
    assert len(rows) == 469, len(rows)
    return rows


SCHEMA_INSTRUCTION = (
    "You must respond with valid JSON matching this exact schema:\n"
    f"{json.dumps(VoteDecision.model_json_schema(), indent=2)}\n"
    "Your response must be valid JSON with 'vote' (one of: YES, NO, ABSTAIN) and 'reasoning' (string) fields."
)


def build_conversation(country, draft_text):
    conv = PromptBuilder.build_country_role(country, draft_text)
    conv[0]['content'] += f"\n\n{SCHEMA_INSTRUCTION}"
    return conv


def prompt_tokens(tok, conv):
    # transformers 5 returns a dict from tokenize=True; render to text and encode instead
    text = tok.apply_chat_template(conv, tokenize=False, add_generation_prompt=True)
    return len(tok(text, add_special_tokens=False)['input_ids'])


def parse_like_paper(text):
    """Identical to offline_provider.batch_generate parsing; returns dict or None."""
    t = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
    t = re.sub(r'\s*```$', '', t, flags=re.MULTILINE)
    try:
        m = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', t, re.DOTALL)
        obj = json.loads(m.group()) if m else json.loads(t)
        return VoteDecision(**obj).model_dump()
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--hf-name', required=True)
    ap.add_argument('--model-name', required=True, help='name used in results_<name>.json')
    ap.add_argument('--out', required=True)
    ap.add_argument('--tp', type=int, default=1)
    ap.add_argument('--max-model-len', type=int, default=32768)
    ap.add_argument('--temperature', type=float, default=1.0)
    ap.add_argument('--max-tokens', type=int, default=4096)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--limit', type=int, default=None, help='first N resolutions (smoke test)')
    ap.add_argument('--enforce-eager', action='store_true', help='skip torch.compile and CUDA graphs')
    ap.add_argument('--chunk', type=int, default=250, help='prompts per checkpointed batch')
    args = ap.parse_args()

    from vllm import LLM, SamplingParams
    import vllm, torch, transformers

    out = Path(args.out)
    (out / 'country_role').mkdir(parents=True, exist_ok=True)
    rows = load_rows()[: args.limit]

    llm = LLM(model=args.hf_name, tensor_parallel_size=args.tp, max_model_len=args.max_model_len,
              seed=args.seed, trust_remote_code=False,
              enforce_eager=args.enforce_eager)
    tok = llm.get_tokenizer()
    sp = llm.get_default_sampling_params()
    sp.temperature, sp.max_tokens, sp.seed = args.temperature, args.max_tokens, args.seed

    jobs, skipped = [], []
    for r in rows:
        if not r['draft_text']:
            skipped.append({'resolution_id': r['resolution_id'], 'reason': 'no_draft_text'})
            continue
        for c in P5:
            conv = build_conversation(c, r['draft_text'])
            n_tok = prompt_tokens(tok, conv)
            if n_tok + args.max_tokens > args.max_model_len:
                skipped.append({'resolution_id': r['resolution_id'], 'country': c,
                                'reason': f'prompt_tokens={n_tok} exceeds budget'})
                continue
            jobs.append((r, c, conv, n_tok))

    # Raw outputs are appended chunk by chunk; a resubmitted job skips prompts already done.
    raw_path = out / f'raw_{args.model_name}.jsonl'
    done = set()
    if raw_path.exists():
        for line in raw_path.open():
            if line.strip():
                x = json.loads(line)
                done.add((x['resolution_id'], x['country']))
    todo = [j for j in jobs if (j[0]['resolution_id'], j[1]) not in done]
    print(f'{len(done)} prompts already done, {len(todo)} to run', flush=True)

    t0 = time.time()
    with raw_path.open('a') as raw:
        for i in range(0, len(todo), args.chunk):
            chunk = todo[i: i + args.chunk]
            outputs = llm.chat([j[2] for j in chunk], sp, use_tqdm=True)
            for (r, c, conv, n_tok), o in zip(chunk, outputs):
                g = o.outputs[0]
                # Score the final answer: thinking models may sketch the JSON template inside <think>,
                # which the paper's first-match parse would pick up. Keep the paper parse for comparison.
                parsed_paper = parse_like_paper(g.text)
                parsed = parse_like_paper(g.text.split('</think>')[-1]) if '</think>' in g.text else parsed_paper
                raw.write(json.dumps({'resolution_id': r['resolution_id'], 'country': c, 'kind': r['kind'],
                                      'text_field': r['text_field'], 'prompt_tokens': n_tok,
                                      'prompt_sha256': hashlib.sha256(json.dumps(conv).encode()).hexdigest(),
                                      'raw_text': g.text, 'finish_reason': g.finish_reason,
                                      'completion_tokens': len(g.token_ids), 'parsed': parsed,
                                      'parsed_paper_first_json': parsed_paper}) + '\n')
            raw.flush()
            print(f'chunk done: {min(i + args.chunk, len(todo))}/{len(todo)} '
                  f'({time.time() - t0:.0f}s)', flush=True)
    elapsed = time.time() - t0

    # Results file in UNSC-Bench format, rebuilt from every raw record
    results, n_fail = [], 0
    for line in raw_path.open():
        x = json.loads(line)
        if x['parsed'] is None:
            n_fail += 1
            continue
        results.append({'resolution_id': x['resolution_id'], 'scenario': 'country_role', 'country': x['country'],
                        'model_provider': f'offline:{args.model_name}', 'model_name': args.model_name,
                        'vote_decision': x['parsed'], 'raw_response': None,
                        'timestamp': datetime.now().isoformat()})
    (out / 'country_role' / f'results_{args.model_name}.json').write_text(json.dumps(results, indent=2))

    gpu = subprocess.run(['nvidia-smi', '--query-gpu=name,uuid,memory.total', '--format=csv,noheader'],
                         capture_output=True, text=True).stdout.strip().splitlines()
    meta = {'hf_name': args.hf_name, 'model_name': args.model_name, 'args': vars(args),
            'sampling': {'temperature': sp.temperature, 'max_tokens': sp.max_tokens, 'seed': sp.seed,
                         'top_p': sp.top_p, 'top_k': sp.top_k},
            'versions': {'vllm': vllm.__version__, 'torch': torch.__version__,
                         'transformers': transformers.__version__, 'python': platform.python_version()},
            'host': platform.node(), 'gpus': gpu, 'slurm_job_id': os.environ.get('SLURM_JOB_ID'),
            'data_sha256': {p.name: sha256(p) for p in DATA_DIR.glob('*.json*')},
            'n_resolutions': len(rows), 'n_prompts': len(jobs), 'n_parse_fail': n_fail,
            'n_skipped': len(skipped), 'skipped': skipped, 'generation_seconds': round(elapsed, 1)}
    (out / f'meta_{args.model_name}.json').write_text(json.dumps(meta, indent=2))
    print(json.dumps({k: meta[k] for k in ['n_prompts', 'n_parse_fail', 'n_skipped', 'generation_seconds']}))


if __name__ == '__main__':
    main()
