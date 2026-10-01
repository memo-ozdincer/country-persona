# Start here: Country Persona research

Fresh Aurora sessions should open this project directory and read `AGENTS.md` first. The transferred working changes are captured by the private GitHub synchronization; Git-ignored evidence still requires the separate handoff archive.

**1 October research checkpoint:** [Goal-gap audit and primary-paper research](docs/PERSONA_GOAL_GAP_RESEARCH_20261001.md) separates observed writer/synthesis failures from untested national application, pressure/update, OOD and interaction gains. The saved adapter realizes supplied comparative plans; it has not established country-agent application or multi-agent improvement. Retain the writer and source-checked plans. After source/rubric adjudication, a proposed bounded, separately frozen application/pressure/update diagnostic can select the next supervision or protocol change. The maximum 12-response proposal is not yet prepared or launched; it is not an experiment queue. Eleven published primary papers were reviewed, including verified NeurIPS Best Paper/Oral work; ten published PDFs and one explicitly unreviewed methodological qualification are preserved with hashes and acquisition failures. Zero new model calls/optimizer steps; no GPU processes were inspected or changed. Latest measured results remain the 30 September comparison below.

**30 September latest continuation:** [Benchmark-grounded checked-plan comparison](docs/AURORA_BENCHMARK_GROUNDED_PLAN_20260930.md): One UNSC-Bench-linked Gaza event, grounded in the complete S/PV.9499 national statements, now compares base and the saved complete-task Qwen3.5-4B adapter on identical checked plans. Zero new training steps; both full answers inspected. One assistant rates base 26 met/3 unmet content units and adapter 28 met/1 unratable. The existing scorer yields base fail and adapter unresolved. Three known corrections and zero known regressions among 28 jointly ratable units; explicit veto coverage remains ambiguous. The adapter also removes an invented date and an unsupported UK vote condition. Given actions, one exposed development event and same-assistant planning/review do not establish native benchmark prediction accuracy or persona quality. Nineteen existing focused software tests pass; frozen source extraction, plan and review replay exactly. The [previous complete-task fit](docs/AURORA_QWEN35_PLAN_TO_TEXT_20260930.md) and all earlier experiments remain preserved.

The immediate priority remains small Qwen3.5 (8B or smaller) runs that produce results and inform the next decision. Adjudicate implicit-versus-explicit veto coverage and independently audit the upstream source plan where possible before increasing optimization. Keep source-checked plan-to-text supervision; choose another bounded event from the inspected coverage/invention question, with frozen criteria and matching base/adapter inputs. Keep action prediction separate with outcome labels excluded from inputs and majority/minority/invalid-output controls. No automatic repeated fits or sweeps. Independent review and distributed/NCCL remain pending.

GPU occupancy changes, and another medical agent may share our account. **Leave unfamiliar jobs untouched.** The latest comparison process exited normally. Recheck occupancy before any launch and record host, GPU UUID, PID/start time, command and run directory.

Read in order:

1. [Full project handoff](docs/PROJECT_HANDOFF.md): goals, decisions, results, unknowns, data/code map and next checkpoints.
2. [Research anchor](docs/RESEARCH_ANCHOR.md): hypothesis, controls and paper direction.
   Read the [1 October goal-gap audit](docs/PERSONA_GOAL_GAP_RESEARCH_20261001.md) for the latest diagnosis, literature limits and conditional next decisions.
3. [Latest benchmark-grounded comparison](docs/AURORA_BENCHMARK_GROUNDED_PLAN_20260930.md): primary/benchmark linkage, frozen criteria, full-response scoring and unresolved veto criterion. [Earlier checked-plan trial](docs/AURORA_QWEN35_PLAN_TO_TEXT_20260930.md): complete base/adapter comparison, source-plan preparation, selected repairs, omissions and next decision. [Adaptive Aurora results](docs/AURORA_QWEN35_ADAPTIVE_RESULTS_20260930.md): comparison questions, repairs/regressions, optimization evidence and resulting replan. The [earlier smoke](docs/AURORA_QWEN35_TRAINING_SMOKE_20260930.md) retains setup/failure receipts.
4. [Complete source review](docs/DELIBERATION_SOURCE_REVIEW_20260928.md): findings from all 42 actual baseline outputs.
5. [Prepared nine-call diagnostic](docs/EVIDENCE_FORMAT_CHECKPOINT_20260928.md): frozen cases, purpose and limits.
6. [Aurora workflow](docs/AURORA_WORKFLOW.md) and [historical training readiness](docs/TRAINING_READINESS_20260928.md).
7. [Transfer and command guide](docs/HANDOFF_OPERATIONS.md): verify this copy and reproduce existing results.

```bash
python3 scripts/verify_research_handoff.py --root .
source /h/405/memo/.config/country-persona/aurora-env.sh
```

The verifier needs only standard Python. Its manifest exists in transferred snapshots, not necessarily in the original Mac tree. `handoff/manifest.json` and `handoff/source-inventory.json` identify included and omitted material. Model weights and credentials are excluded.

Suggested fresh-session prompt: “Read AGENTS.md and START_HERE.md, verify the handoff and inspect the benchmark-grounded checked-plan results. Adjudicate the veto-coverage criterion and audit the planner before increasing training. Continue with one useful checkpoint based on inspected failures, preserving identical base/adapter inputs and frozen source-linked criteria. Preserve unfamiliar Aurora processes, including those under my username. Keep assistant development findings separate from validated persona-quality claims and action prediction; inspect each result before another run.”

Older docs may say a past allocation is active, SSH is down, or reviews have not happened. Those were dated observations. Use the current handoff and live checks for current state; preserve original receipts.
