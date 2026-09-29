# Start here: Country Persona research

Fresh Aurora sessions should open this project directory and read `AGENTS.md` first. The transferred working changes are captured by the private GitHub synchronization; Git-ignored evidence still requires the separate handoff archive.

**29 September continuation:** [Aurora evaluation portability and readiness](docs/AURORA_EVALUATION_READINESS_20260929.md) records exact review-score reproduction, a matching nine-prompt tokenizer preflight, focused tests and broader-check limits. Aurora model weights/runtime and independent review remain pending.

We are stabilizing evaluation of dated institutional policy and multi-country deliberation before new behavioral fine-tuning. The FRA/GBR/IND/BRA extension has a completed base-model baseline, provisional source annotations and a prepared, unrun nine-call format diagnostic. A small LoRA probe is prepared; independent evaluation review and Aurora GPU execution remain pending.

Aurora access works. GPU occupancy changes, and another medical agent may share our account. **Leave unfamiliar jobs untouched.** No Aurora model run was launched during the September 29 access/handoff checks.

Read in order:

1. [Full project handoff](docs/PROJECT_HANDOFF.md): goals, decisions, results, unknowns, data/code map and next checkpoints.
2. [Research anchor](docs/RESEARCH_ANCHOR.md): hypothesis, controls and paper direction.
3. [Complete source review](docs/DELIBERATION_SOURCE_REVIEW_20260928.md): findings from all 42 actual baseline outputs.
4. [Next nine-call diagnostic](docs/EVIDENCE_FORMAT_CHECKPOINT_20260928.md): frozen cases, purpose and limits.
5. [Aurora workflow](docs/AURORA_WORKFLOW.md) and [training readiness](docs/TRAINING_READINESS_20260928.md).
6. [Transfer and command guide](docs/HANDOFF_OPERATIONS.md): verify this copy and reproduce existing results.

```bash
python3 scripts/verify_research_handoff.py --root .
source /h/405/memo/.config/country-persona/aurora-env.sh
```

The verifier needs only standard Python. Its manifest exists in transferred snapshots, not necessarily in the original Mac tree. `handoff/manifest.json` and `handoff/source-inventory.json` identify included and omitted material. Model weights and credentials are excluded.

Suggested fresh-session prompt: “Read AGENTS.md and START_HERE.md. Verify the handoff and inspect current state before choosing one useful checkpoint. Preserve other Aurora agents' processes, including those under my username. Prioritize trustworthy evaluation and inspect each result before another run.”

Older docs may say a past allocation is active, SSH is down, or reviews have not happened. Those were dated observations. Use the current handoff and live checks for current state; preserve original receipts.
