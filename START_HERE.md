# Start here: Country Persona research

Fresh Aurora sessions should open this project directory and read `AGENTS.md` first. The transferred working changes are captured by the private GitHub synchronization; Git-ignored evidence still requires the separate handoff archive.

**30 September continuation:** [Qwen3.5-4B Aurora training smoke](docs/AURORA_QWEN35_TRAINING_SMOKE_20260930.md) passed two BF16 LoRA optimizer steps and exact save/reload on one Blackwell GPU. Four baseline and four adapter controls were inspected; 19 shared CPU tests passed. The scratch model/runtime are now available. Independent review, persona-quality evidence and distributed/NCCL verification remain pending.

The immediate Aurora priority is small training tests, using the user-requested Qwen3.5 family at 8B or smaller. The 4B training machinery works; a large inference campaign is not required before another technical test. Substantive behavioral claims still need stable evaluation and independent source review. The historical Qwen3-8B FRA/GBR/IND/BRA baseline, provisional annotations and prepared unrun nine-call format diagnostic remain preserved.

GPU occupancy changes, and another medical agent may share our account. **Leave unfamiliar jobs untouched.** The September 30 smoke exited normally; recheck occupancy before any new launch. [September 29 evaluation portability](docs/AURORA_EVALUATION_READINESS_20260929.md) remains the evidence for exact review/tokenizer reproduction.

Read in order:

1. [Full project handoff](docs/PROJECT_HANDOFF.md): goals, decisions, results, unknowns, data/code map and next checkpoints.
2. [Research anchor](docs/RESEARCH_ANCHOR.md): hypothesis, controls and paper direction.
3. [Measured Aurora training smoke](docs/AURORA_QWEN35_TRAINING_SMOKE_20260930.md): current model/runtime, results, failed-run receipts and next decision.
4. [Complete source review](docs/DELIBERATION_SOURCE_REVIEW_20260928.md): findings from all 42 actual baseline outputs.
5. [Prepared nine-call diagnostic](docs/EVIDENCE_FORMAT_CHECKPOINT_20260928.md): frozen cases, purpose and limits.
6. [Aurora workflow](docs/AURORA_WORKFLOW.md) and [historical training readiness](docs/TRAINING_READINESS_20260928.md).
7. [Transfer and command guide](docs/HANDOFF_OPERATIONS.md): verify this copy and reproduce existing results.

```bash
python3 scripts/verify_research_handoff.py --root .
source /h/405/memo/.config/country-persona/aurora-env.sh
```

The verifier needs only standard Python. Its manifest exists in transferred snapshots, not necessarily in the original Mac tree. `handoff/manifest.json` and `handoff/source-inventory.json` identify included and omitted material. Model weights and credentials are excluded.

Suggested fresh-session prompt: “Read AGENTS.md and START_HERE.md, verify the handoff and inspect the Qwen3.5-4B training smoke. Continue with one useful small training checkpoint, with only the inference needed to answer its question. Preserve other Aurora agents' processes, including those under my username. Keep technical optimization results separate from persona-quality claims; inspect each result before another run.”

Older docs may say a past allocation is active, SSH is down, or reviews have not happened. Those were dated observations. Use the current handoff and live checks for current state; preserve original receipts.
