# Start here: Country Persona research

Fresh Aurora sessions should open this project directory and read `AGENTS.md` first. The transferred working changes are captured by the private GitHub synchronization; Git-ignored evidence still requires the separate handoff archive.

**30 September continuation:** [Adaptive Qwen3.5-4B training results](docs/AURORA_QWEN35_ADAPTIVE_RESULTS_20260930.md): two fresh four-target, 20-step fits and 14 new comparison answers on one RTX PRO 6000 Blackwell Server Edition. All answers were inspected before selecting another run. Training loss fell and some local claims improved, but UK draft reversal and unsupported consensus survived, including after training with conflicting notes. Replan toward complete synthesis-task supervision. Independent review, validated persona-quality evidence and distributed/NCCL verification remain pending. The earlier two-step smoke and its 19 CPU checks remain preserved.

The immediate Aurora priority is small runs that produce results and inform the next decision, using the user-requested Qwen3.5 family at 8B or smaller. The 4B training machinery works; inference is bounded to the comparison question. The latest results justify changing the supervised task before another fit, rather than repeating the same correction targets. Substantive behavioral claims still need stable evaluation and independent source review. The historical Qwen3-8B FRA/GBR/IND/BRA baseline, provisional annotations and prepared unrun nine-call format diagnostic remain preserved.

GPU occupancy changes, and another medical agent may share our account. **Leave unfamiliar jobs untouched.** The latest run exited and its selected GPU returned to zero memory use; recheck occupancy before any new launch. [September 29 evaluation portability](docs/AURORA_EVALUATION_READINESS_20260929.md) remains the evidence for exact review/tokenizer reproduction.

Read in order:

1. [Full project handoff](docs/PROJECT_HANDOFF.md): goals, decisions, results, unknowns, data/code map and next checkpoints.
2. [Research anchor](docs/RESEARCH_ANCHOR.md): hypothesis, controls and paper direction.
3. [Adaptive Aurora results](docs/AURORA_QWEN35_ADAPTIVE_RESULTS_20260930.md): comparison questions, repairs/regressions, optimization evidence and resulting replan. The [earlier smoke](docs/AURORA_QWEN35_TRAINING_SMOKE_20260930.md) retains setup/failure receipts.
4. [Complete source review](docs/DELIBERATION_SOURCE_REVIEW_20260928.md): findings from all 42 actual baseline outputs.
5. [Prepared nine-call diagnostic](docs/EVIDENCE_FORMAT_CHECKPOINT_20260928.md): frozen cases, purpose and limits.
6. [Aurora workflow](docs/AURORA_WORKFLOW.md) and [historical training readiness](docs/TRAINING_READINESS_20260928.md).
7. [Transfer and command guide](docs/HANDOFF_OPERATIONS.md): verify this copy and reproduce existing results.

```bash
python3 scripts/verify_research_handoff.py --root .
source /h/405/memo/.config/country-persona/aurora-env.sh
```

The verifier needs only standard Python. Its manifest exists in transferred snapshots, not necessarily in the original Mac tree. `handoff/manifest.json` and `handoff/source-inventory.json` identify included and omitted material. Model weights and credentials are excluded.

Suggested fresh-session prompt: “Read AGENTS.md and START_HERE.md, verify the handoff and inspect the adaptive Qwen3.5-4B results. Continue with the complete synthesis-task supervision replan and one useful small training checkpoint, using only the inference needed to answer its question. Preserve other Aurora agents' processes, including those under my username. Keep assistant development findings separate from validated persona-quality claims; inspect each result before another run.”

Older docs may say a past allocation is active, SSH is down, or reviews have not happened. Those were dated observations. Use the current handoff and live checks for current state; preserve original receipts.
