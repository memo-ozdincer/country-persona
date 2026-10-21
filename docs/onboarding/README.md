# Country Persona: start here

We study whether a small language model can represent a **dated country, institution and role**, preserve its documented positions, and apply them appropriately when a diplomatic proposal changes. The working model is **Qwen3.5-4B**. France, the UK, India and Brazil are the active extension; earlier Germany/China work remains preserved.

**Current status:** research is paused. The latest training was on 19 October 2026. This onboarding update adds documentation and CPU checks, not model experiments. We have useful small-task gains, but dependable national personas, stronger diplomatic reasoning, multi-agent improvement and strong OOD transfer remain unproved.

## Read in this order

1. **[SFT trials, simply explained](SFT_TRIALS.md)** — what context each trial received, its input format, its example answers, training budget, evaluation and result.
2. **[Actual generated model outputs](../evidence/README.md)** — start with the outputs-only links. Training targets and generated answers are different things.
3. **[What the evaluations measured](../evidence/EVALUATION_GUIDE.md)** — every criterion and the per-model gains/regressions.
4. **[What we propose to test next](NEXT_STEPS.md)** — one concrete diagnostic, its controls, stop decisions and current unrun status.
5. **[Data and checkpoint access](DATA_AND_RESTORE.md)** and **[environment setup](ENVIRONMENTS.md)** when you want to run code.

The [full results report](../CONSOLIDATED_RESULTS_20261019.md) covers all 42 nonzero Qwen3.5 runs/continuations (4,182 updates), beyond the seven principal SFT families named in the onboarding guide. The [full handoff](../PROJECT_HANDOFF.md) preserves detailed decisions and historical evidence. Read [AGENTS.md](../../AGENTS.md) before resource use or experiments; historical “next” paragraphs are not an active run queue.

## Three ways to join

| Your first task | What you need | What to do |
|---|---|---|
| Read results or independently review answers | Access to this private GitHub repository | Read the trials and compare generated answers with the original sources. No Python, model weights or GPU needed. |
| Work on evaluation/code | Git, Python 3.11+, and uv for the full CPU environment | Clone, run the standard-library evidence check, then build the CPU test environment. No full data archive or GPU needed for the first checks. |
| Reproduce historical model runs | Repository/release access, restored frozen data and adapter, separately downloaded base weights, matching GPU runtime, authorized cluster access | Follow the data and environment guides. Verify all paths/hashes and launch ownership. Do not run historical commands as a queue. |

## First five-minute code check

```bash
git clone https://github.com/memo-ozdincer/country-persona.git
cd country-persona
python3 -B docs/onboarding/verify_starter.py
```

This verifies 130 embedded original text files, all 94 saved short-answer records and the original 23/40 → 34/40 → 38/40 score arithmetic. It also checks the generated evidence pages against their receipt. It requires only the clone and Python's standard library. It does not grade model quality independently or recreate missing model weights.

To inspect the original JSONL/configuration/log files outside the HTML:

```bash
python3 -B docs/onboarding/verify_starter.py --extract /absolute/scratch/path/new-starter-evidence
```

The destination must be fresh. This is a bounded text export, not a full snapshot or adapter restore.

## What is and is not on GitHub

Code, configuration, environment definitions, documentation and the recent bounded research packs are tracked. Older frozen data, transcripts and adapters are in a **private release snapshot**, with later adapters in four additional private release sets. A plain clone is sufficient for reading and CPU checks; it is not the complete historical research workspace.

Base model weights, credentials, installed virtual environments and caches are deliberately external. The snapshot excludes large older/Reddit corpora and some redundant/partial historical artifacts. The [data guide](DATA_AND_RESTORE.md) lists the precise boundary; “all files from every historical collection” is not a claim we can make.

## Useful first contributions

- **Source reviewer:** independently check country attribution, dates, institutional authority and complete-answer grades. Model identity should be hidden where practical. Preserve disagreements with the existing assistant judgments.
- **Data contributor:** audit the proposed next role contrast against the complete country statements and pre-target meeting evidence; identify missing information and target leakage before any model call.
- **Engineer:** reproduce the clone-only evidence check and CPU suite, then improve a specifically diagnosed harness issue in an isolated checkout.
- **Experiment collaborator:** agree on one question, a frozen input/criterion set and an inspection gate. Research remains paused until resumed; no training sweep is prepared.

Collaborators need their own repository/cluster authorization and credentials where required. Do not copy or publish another user's private token. Another project can use the same Aurora account; a username alone never establishes ownership of a GPU job.

[Environment/data audit and validation status](CHECKS.md) · [Master evidence index](../evidence/README.md) · [Storage policy](../STORAGE_POLICY.md)
