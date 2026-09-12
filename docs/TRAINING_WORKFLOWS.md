# Training workflows

For the concrete September 12 research release, use [CLUSTER_RUNBOOK.md](CLUSTER_RUNBOOK.md) and [POSTTRAINING_PLAN.md](POSTTRAINING_PLAN.md). They add an explicitly machine-prepared research path, tokenizer-measured budgets, frozen evaluation inputs and actual CPU TRL/PEFT integration validation. The optional manual admission workflow below remains supported; it is not the only supported research path now.

The shipped data pipeline has been executed on real source files. The CUDA trainer is a modest, documented starting point; no GPU job or model-quality result is claimed. The priority is the datasets and the experiments in `RESEARCH_STRATEGY.md`.

## 1. Inspect and admit a pool

Start with `reports/DATA_REPORT.md`, the source registry and the country/task candidate files. Review parser samples and source-level reuse scope. Use the admission CSV to record decisions with a reviewer identifier and an evidence-based reason; do not claim human adjudication for machine checks.

```bash
uv sync --locked --extra data --extra dev
uv run persona audit data/prepared/pilot/pilot.canonical.jsonl --verify-raw

# After actual review decisions are recorded in the CSV:
uv run persona admit \
  --data data/prepared/pilot/candidates/CHN/authentic_qa/train.sft.jsonl \
  --manifest data/prepared/pilot/candidates/CHN/authentic_qa/train.manifest.jsonl \
  --ledger data/prepared/pilot/review/admission.csv \
  --output data/prepared/admitted/chn_qa_train.jsonl
```

Admission produces `chn_qa_train.manifest.jsonl` with verified row hashes. Build the dev export the same way, using the **dev** candidate files. Keep test examples reserved. These commands do not imply that every candidate has received quality or reuse approval.

## 2. Tokenizer preflight and SFT smoke test

On the intended CUDA machine, install the locked training extras. The resolved lock is reproducible, but has not been validated on your cluster's CUDA/driver combination.

```bash
uv sync --locked --extra data --extra train --extra cuda

uv run python -m country_persona.train \
  --model /path/to/instruction-checkpoint \
  --data data/prepared/admitted/chn_qa_train.jsonl \
  --manifest data/prepared/admitted/chn_qa_train.manifest.jsonl \
  --output runs/preflight --preflight-only --max-length 4096
```

Use an immutable `--revision` when the model is a remote Hugging Face ID. The preflight verifies every rendered example fits, checks the chat-template prompt prefix, and logs actual supervised tokens. It rejects silent truncation, empty targets, wrong splits, candidate-only data and altered manifests.

For a 10-step GPU smoke test, omit `--preflight-only` and add `--max-steps 10`. Use `--qlora` only for the single-GPU recipe and install the CUDA extra. Confirm finite loss, checkpoint loading, response formatting and memory usage before proceeding.

## 3. Multi-GPU LoRA

```bash
# Run in the activated training environment.
NPROC_PER_NODE=4 bash scripts/train_multigpu.sh \
  --model /path/to/instruction-checkpoint \
  --data data/prepared/admitted/chn_qa_train.jsonl \
  --manifest data/prepared/admitted/chn_qa_train.manifest.jsonl \
  --dev-data data/prepared/admitted/chn_qa_dev.jsonl \
  --dev-manifest data/prepared/admitted/chn_qa_dev.manifest.jsonl \
  --output runs/chn-lora --max-length 4096 \
  --rank 16 --grad-accum 8 --epochs 1 --lr 1e-4
```

This is distributed data parallelism: one full base-model replica per GPU, adapter gradients synchronized. It does not shard a too-large base model across devices. At four processes and gradient accumulation eight, the effective batch is 32 examples. Target-token weighting still differs by sequence length. Use hardware-appropriate sharding if the base cannot fit; that configuration is outside the tested data work.

For the shared-country run, combine **admitted train** pools with deliberate sampling and regenerate sequential row indices without changing each example hash. Preserve country/task manifests. Match example/token budgets when comparing separate adapters. The repository intentionally does not silently impose an unvalidated mixture on the current unequal source pools.

## 4. Optional DPO

The intended TRL representation is explicit conversational `prompt`, `chosen`, `rejected`. Start from the selected SFT policy. If using an SFT adapter, ensure the DPO reference is the frozen SFT policy, not accidentally the unadapted base model with adapters disabled. A merged SFT checkpoint is one simple way to make this explicit.

`configs/preference_record.example.json` specifies the extra research provenance: parent training ID, split group, dated evidence IDs, concrete error type and adjudication. Keep parent splits. Generate rejected answers only after observing real failure modes and have the evidence judge explain the preference. A valid alternative diplomatic wording is not a negative label. No preference training set or DPO GPU implementation is claimed here; the existing [TRL DPO workflow](https://huggingface.co/docs/trl/dpo_trainer) is the planned extension.

## 5. Mid-training and future interaction

Domain-text records remain separate from instructions. For continued pretraining, clean speaker boundaries and page artifacts, group/decontaminate the evaluation families, use text-language-model loss, and retain a general-domain control to measure capability loss. Make this an ablation only after diagnosing a domain deficit.

Multi-agent simulation, online RL, negotiation reward design and SOTOPIA-style trajectory collection are deliberately future work. The data already preserve directed UPR relationships, earlier dialogue turns, institutional roles, dates, sources and parent events so that those experiments can reuse a defensible evidence base.
