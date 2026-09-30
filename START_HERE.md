# Start here: Country Persona research

Fresh Aurora sessions should open this project directory and read `AGENTS.md` first. The transferred working changes are captured by the private GitHub synchronization; Git-ignored evidence still requires the separate handoff archive.

**30 September latest continuation:** [Checked-plan realization and complete-task SFT](docs/AURORA_QWEN35_PLAN_TO_TEXT_20260930.md): Checked bullet plans repair UK draft-support and false-consensus failures in the base. One fresh two-target, 20-step complete-memo LoRA fit removes invented writing dates in all three comparison answers and restores selected details, including humanitarian-worker protection in South Sudan outside training. It also drops supplied details. Most position repair precedes SFT; this is realization of given positions, not decision prediction or a validated persona gain. Fit: 44.43 seconds, 9.66 GiB on NVIDIA RTX PRO 6000 Blackwell Server Edition; exact completion masks, finite gradients, 496 changed adapter tensors and exact reload. All six answers inspected; independent review remains pending. The [earlier adaptive fits](docs/AURORA_QWEN35_ADAPTIVE_RESULTS_20260930.md) and [two-step smoke](docs/AURORA_QWEN35_TRAINING_SMOKE_20260930.md) remain preserved.

The immediate priority remains small Qwen3.5 (8B or smaller) runs that produce results and inform the next decision. Before increasing optimization, freeze a separate-context checked-plan pack with atomic coverage and source/absence audits, review the upstream planner independently where possible, and compare base versus this adapter on identical plans. Inspect omissions and invented claims. No automatic repeated fits or sweeps. The historical Qwen3-8B evaluation, Germany/China work and prepared unrun nine-call diagnostic remain preserved.

GPU occupancy changes, and another medical agent may share our account. **Leave unfamiliar jobs untouched.** The base GPU was reused by an unfamiliar process after our base run exited; the fit used another idle GPU of the same type and exited normally. Recheck occupancy before any launch.

Read in order:

1. [Full project handoff](docs/PROJECT_HANDOFF.md): goals, decisions, results, unknowns, data/code map and next checkpoints.
2. [Research anchor](docs/RESEARCH_ANCHOR.md): hypothesis, controls and paper direction.
3. [Latest checked-plan trial](docs/AURORA_QWEN35_PLAN_TO_TEXT_20260930.md): complete base/adapter comparison, source-plan preparation, selected repairs, omissions and next decision. [Adaptive Aurora results](docs/AURORA_QWEN35_ADAPTIVE_RESULTS_20260930.md): comparison questions, repairs/regressions, optimization evidence and resulting replan. The [earlier smoke](docs/AURORA_QWEN35_TRAINING_SMOKE_20260930.md) retains setup/failure receipts.
4. [Complete source review](docs/DELIBERATION_SOURCE_REVIEW_20260928.md): findings from all 42 actual baseline outputs.
5. [Prepared nine-call diagnostic](docs/EVIDENCE_FORMAT_CHECKPOINT_20260928.md): frozen cases, purpose and limits.
6. [Aurora workflow](docs/AURORA_WORKFLOW.md) and [historical training readiness](docs/TRAINING_READINESS_20260928.md).
7. [Transfer and command guide](docs/HANDOFF_OPERATIONS.md): verify this copy and reproduce existing results.

```bash
python3 scripts/verify_research_handoff.py --root .
source /h/405/memo/.config/country-persona/aurora-env.sh
```

The verifier needs only standard Python. Its manifest exists in transferred snapshots, not necessarily in the original Mac tree. `handoff/manifest.json` and `handoff/source-inventory.json` identify included and omitted material. Model weights and credentials are excluded.

Suggested fresh-session prompt: “Read AGENTS.md and START_HERE.md, verify the handoff and inspect the checked-plan realization results. Continue with one useful separate-context coverage checkpoint before increasing training. Compare base and the complete-task adapter on identical plans, using only the inference needed for the question. Preserve unfamiliar Aurora processes, including those under my username. Keep assistant development findings separate from validated persona-quality claims; inspect each result before another run.”

Older docs may say a past allocation is active, SSH is down, or reviews have not happened. Those were dated observations. Use the current handoff and live checks for current state; preserve original receipts.
