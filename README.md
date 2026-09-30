# Country persona data and post-training

**30 September latest Aurora checkpoint:** [Benchmark-grounded checked-plan comparison](docs/AURORA_BENCHMARK_GROUNDED_PLAN_20260930.md): One UNSC-Bench-linked Gaza event, grounded in the complete S/PV.9499 national statements, now compares base and the saved complete-task Qwen3.5-4B adapter on identical checked plans. Zero new training steps; both full answers inspected. One assistant rates base 26 met/3 unmet content units and adapter 28 met/1 unratable. The existing scorer yields base fail and adapter unresolved. Three known corrections and zero known regressions among 28 jointly ratable units; explicit veto coverage remains ambiguous. The adapter also removes an invented date and an unsupported UK vote condition. Given actions, one exposed development event and same-assistant planning/review do not establish native benchmark prediction accuracy or persona quality. **Next:** Adjudicate implicit-versus-explicit veto coverage and independently audit the upstream source plan where possible before increasing optimization. Keep source-checked plan-to-text supervision; choose another bounded event from the inspected coverage/invention question, with frozen criteria and matching base/adapter inputs. Keep action prediction separate with outcome labels excluded from inputs and majority/minority/invalid-output controls. No automatic repeated fits or sweeps. Nineteen existing focused software tests pass; all frozen source/plan/review bytes replay exactly. NVIDIA RTX PRO 6000 Blackwell Server Edition; no unfamiliar process changed. [Earlier complete-memo SFT](docs/AURORA_QWEN35_PLAN_TO_TEXT_20260930.md), [correction fits](docs/AURORA_QWEN35_ADAPTIVE_RESULTS_20260930.md) and [smoke](docs/AURORA_QWEN35_TRAINING_SMOKE_20260930.md) remain preserved.

**Fresh session or Aurora handoff:** start with [START_HERE.md](START_HERE.md) and [the complete project handoff](docs/PROJECT_HANDOFF.md). They summarize current results, unresolved questions, resource-ownership rules, data/code locations and the next bounded experiments. The transferred snapshot includes uncommitted code and relevant Git-ignored artifacts; a Git clone alone does not reproduce the current research state.

**29 September Aurora checkpoint:** [Verified evaluation portability and execution readiness](docs/AURORA_EVALUATION_READINESS_20260929.md). All 9,046 original payload files verified; the 42-response scores and nine prompt-token digests reproduce exactly. The 63 focused tests pass. Broader checks pass 166 tests, with two omitted-artifact failures and six skips documented. Model weights, a verified CUDA runtime and independent review remain pending. The private handoff archive retains evidence omitted by Git.

**Latest measured checkpoint, 28 September:** [42-call deliberation baseline and six-call source-check diagnostic](docs/DELIBERATION_BASELINE_20260928.md). Initial control pairs replay exactly, but three of six final memos truncate and source checks expose invented agreement, a reversed draft position and a prior meeting misrepresented as a later vote. More output room fixes truncation; a targeted prompt repair also introduces a new error. Full-answer fidelity and paired before/after tooling are implemented; independent semantic review and new training remain pending.

[Both complete events now have provisional assistant source annotations](docs/DELIBERATION_SOURCE_REVIEW_20260928.md): all 42 responses, separate content/check transitions and source-linked adjudication cards. Climate peer revision makes no confirmed corrections; Ukraine peer revision fixes one attribution error while losing one required content point. Both overall peer-benefit scores remain unresolved. These are one assistant's ratings; independent review and 33 ambiguous rating instances remain pending.

**Next comparison prepared:** [Nine-case evidence-format checkpoint](docs/EVIDENCE_FORMAT_CHECKPOINT_20260928.md). Prose, evidence-linked prose and JSON will be compared within three contexts, including a new South Sudan issue. Twelve complete source statements, 13 new proposed criteria, a full-context tokenizer preflight and 81 software checks are ready. No new generations ran; SSH was unavailable after the prior allocation's wall deadline.

**Major research anchor (26 September): [behavior, evidence and deliberation](docs/RESEARCH_ANCHOR.md).** Evaluate whether behavioral fine-tuning adds value over the same model with the same dated evidence. The recommended next step is to audit and freeze a small evaluation, establish the prompting/evidence baselines, and test one LoRA SFT method. [Full metrics, benchmarks and paper directions](docs/PERSONA_EVALUATION_AND_PAPER_DIRECTION_20260923.md).

See [data priorities / TODO](TODO.md) for the next decision-case acquisition step.

**Evaluation implementation (26 September): [learning log and next small experiment](docs/EVAL_LEARNING_LOG_20260926.md).** Full benchmark audits exposed class imbalance, cross-task overlap and conflicting source labels. A strict action scorer passes 26 targeted checks; a separate 21-decision, seven-event France/UK/India/Brazil pack is ready for source review. No new model or training result is claimed.

**Execution roadmap:** [Small research checkpoints through training, deliberation and publication](docs/RESEARCH_CHECKPOINT_PLAN.md), with a useful artifact, calibration check and next decision at every step.

**27 September checkpoint:** [Two-event evaluation and worked scoring examples](docs/EVAL_PILOT_CHECKPOINT_20260927.md): seven action/eight policy pairs, source spans and a 19-example authored rubric deck. The [first measured model comparison](docs/EVAL_BASELINE_RESULTS_20260927.md) now contains 30 real outputs, action scores, source-checked policy observations and a 16-response reviewer packet. Independent ratings remain pending.

**Inference follow-through:** The GPU probe caught and fixed a checkpoint-defaults override; 56 targeted checks now pass. The eight-case probe and 30-output comparison completed with full prompts and clean stopping. [Reusable Trillium allocations](docs/TRILLIUM_WORKFLOW.md) prefer `def-zhijing` and retain the node with `sleep infinity`. No new training has run.

**Failure analysis:** [34 targeted follow-ups](docs/EVAL_FAILURE_ANALYSIS_20260927.md) expose country-name/answer-format sensitivity, incomplete decision evidence and unsupported source-specific detail. Evaluation robustness and source sufficiency now precede the next training experiment; original results are preserved.

**Evaluation stabilization:** [Protocol, 200-prompt diagnostic and review kit](docs/EVAL_STABILIZATION_RESULTS_20260927.md). All 14 original action prompts replay exactly and all 18 fictional extraction controls pass, but the counterbalanced mixture predicts abstention for all seven historical decisions. Consistency is therefore reported alongside correctness. The proposed atomic policy rubric, source-support checks and reviewer-agreement tooling are ready; 68 targeted tests pass. Independent semantic review and additional event families remain gates before training.

**28 September readiness:** [Small training run, deliberation measurements and next checkpoints](docs/TRAINING_READINESS_20260928.md). A four-H100 `def-zhijing` recipe with a retained allocation is uploaded to Trillium and accepted by Slurm in test-only mode. All ten technical-probe examples passed actual response-mask checks and a tiny CPU adapter update/save/reload test. The 42-call base deliberation run and six-call diagnostic completed on one H100. No new production training has run; independent evaluation review and multi-GPU/NCCL validation remain pending.

The latest local **v3 training handoff** adds shared production checks for actual masks, finite losses/gradients, per-rank participation, changed adapters and saved-state reload. [A fresh CPU check and fault-injection tests pass](reports/training-verification-20260928.json); v3 has not been uploaded, and CUDA/NCCL execution remains pending.

A data-first research repository for **dated institutional country representatives**. The initial China/Germany pilot is preserved, with a separate France/UK/India/Brazil extension. The repository contains the supplied playbook, acquired corpora, source-specific parsing, country/task categorization, event-group splits, provenance checks and a modest multi-GPU LoRA workflow.

**Explore the collection:** [interactive browser](https://huggingface.co/spaces/memo-ozdincer/country-persona-explorer) · [full research view](https://huggingface.co/spaces/memo-ozdincer/country-persona-research) · [public GitHub catalog](https://github.com/memo-ozdincer/country-persona-data) · [Hugging Face tables](https://huggingface.co/datasets/memo-ozdincer/country-persona-data). [Exploration guide and update workflow](docs/DATA_EXPLORER.md).

Start with **[the measured data report](reports/DATA_REPORT.md)**. The project contains real downloaded data, not just a source registry. Large third-party data are local under `data/` and Git-ignored; their exact download URLs and hashes are tracked in [the source lock](data/sources.lock.json).

**14 September: [France, UK, India and Brazil data release](docs/COUNTRY_EXTENSION_20260914.md)** and [12 actual policy applications](docs/COUNTRY_EXTENSION_EXAMPLES.md). The extension adds strategies, climate commitments and other official evidence in eight languages, country-context statistics and newly prepared historical decisions. The earlier [six-country knowledge preview](docs/COUNTRY_KNOWLEDGE_PREVIEW.md) shows the design change. Document volume alone is not evidence of useful persona supervision; these new releases remain review candidates.

**Post-training handoff (12 September):** [four-H100 plan, costs and milestones](docs/POSTTRAINING_PLAN.md), [exact cluster commands](docs/CLUSTER_RUNBOOK.md), and [decision-by-decision evidence](docs/DECISION_REGISTER.md). A model-tokenized 500-example pilot, 832-example balanced comparator, frozen evaluation prompts and CPU-tested LoRA plumbing are prepared. Budget approximately 1–3 four-H100 node-hours for the first before/after proof of concept, then inspect before expanding.

| Read | Purpose |
|---|---|
| [Data report](reports/DATA_REPORT.md) | Actual acquisition counts, prepared pools, quality findings and baseline results |
| [Source registry](data/source_registry.json) | Acquired, blocked and deferred sources; rights notes and acquisition priorities |
| [Data dictionary](docs/DATA_DICTIONARY.md) | Actual formats, attribution rules, lineage and split semantics |
| [Research strategy](docs/RESEARCH_STRATEGY.md) | Paper-supported choices and the experiments that decide what to do next |
| [Training workflows](docs/TRAINING_WORKFLOWS.md) | Admission, tokenizer preflight, multi-GPU LoRA, and optional preference/domain-training plans |
| [Original playbook](country_persona_playbook/README.md) | Supplied research kit, preserved unchanged |

## Use the data now

- `data/raw/`: complete downloaded OHCHR/UHRI, UNGA-DM and Speaking Volumes bulk files, plus official archive snapshots and the pinned UNBench sample.
- `data/canonical/`: parsed source-specific JSONL. The whole Speaking Volumes source is preserved; OHCHR and vote tables have focused China/Germany derivatives while the complete raw releases remain available.
- `data/prepared/pilot/pilot.canonical.jsonl`: the focused pool, including evidence, genuine QA, statements, action labels and historical text.
- `data/prepared/pilot/candidates/CHN/` and `.../DEU/`: SFT-format candidates partitioned by task and split, each with an aligned provenance manifest.
- `data/prepared/long-context/`: 17,461 candidates with larger selection budgets, retaining all parsed German Foreign Office QA histories. This is an alternative view, not extra independent data.
- `data/prepared/pilot/review/admission.csv`: explicit review decisions before a training run. Candidate does not mean universally rights-cleared or expert-approved.

Code, manifests and reports are tracked in the private GitHub repository; raw/prepared data are private and transferred separately to Trillium. An earlier Qwen3 LoRA pilot ran; see the measured results and limitations in [the regression research](docs/REGRESSION_RESEARCH.md). A bounded source-grounded deliberation runner is now prepared for development evaluation; it is not a validated diplomatic simulator.

## Reproduce the preparation

From this repository directory, with Python 3.11 and uv:

```bash
uv sync --locked --extra data --extra dev
uv run pytest -q
uv run persona normalize
uv run persona build --output data/prepared/pilot-rebuild
uv run persona audit data/prepared/pilot/pilot.canonical.jsonl \
  --verify-raw --output reports/pilot_audit.json
uv run python scripts/check_source_spans.py
uv run python scripts/decision_baselines.py
uv run python scripts/make_data_report.py
```

The supplied `pilot` snapshot already exists. Builds require a fresh output directory so that previous exports and review decisions cannot be overwritten or mixed with stale files. The commands above audit the delivered pilot; point subsequent audit commands at `pilot-rebuild` to inspect the rebuilt copy.

On a new checkout, reacquire the pinned source files first:

```bash
uv run persona fetch --lock data/sources.lock.json
uv run persona normalize
```

`normalize` restores tracked collection manifests and extracts the known RData archive members, checking their recorded hashes. Dynamic publisher URLs can change; a different hash fails rather than silently replacing the snapshot. A URL lock cannot guarantee a publisher will keep old bytes online. Preserve a private backup of `data/raw/` for exact long-term reproducibility. The lock and manifests contain acquisition metadata, not a redistribution license.

Fresh archive collectors live in `scripts/collect_*.py`. They retain download receipts, bounded collection limits and explicit failures. The current snapshot's discovered archive pages are recorded in the manifests. The original source registry's inaccessible sources remain listed, with their actual failure modes and next acquisition steps.

## Multilingual data expansion

The [13 September data expansion](docs/DATA_EXPANSION_20260913.md) adds 2,389 parsed source documents, 12,930 literal QA candidates and 7,578 evidence passages across eleven languages, plus a separate six-language UN evaluation corpus. These remain review candidates; the original training exports are unchanged. See the report for source scope, actual counts, review milestones and frozen-manifest reproduction.

## Experimental starting point

Compare the same instruction model with a role prompt, then with dated evidence, then with shared country/institution-conditioned SFT. Prioritize substantive policy application and supported decisions; genuine QA is useful when it contains relevant country information, and authenticity alone does not make it good supervision. Keep statement reconstruction, UPR actions and historical domain text separate. Use preferences only for diagnosed source-supported errors; consider continued pretraining only after an equal-compute ablation. Multi-agent decision-making remains a later project.

## Dated evidence retrieval

```bash
uv run persona index --input data/prepared/pilot/pilot.canonical.jsonl \
  --output data/index/pilot-20260909.sqlite
uv run persona retrieve --index data/index/pilot-20260909.sqlite \
  --query 'nuclear disarmament' --before 2026-07-01 \
  --exclude-group ACTUAL_TARGET_SPLIT_GROUP --country DEU
```

Supply the actual target's `split_group` from the manifest. Retrieval excludes unknown dates, same-day material, the target event group and quarantined documents. It cannot independently certify that a historical web page was unmodified at the time; forecasting requires additional source-time review.
