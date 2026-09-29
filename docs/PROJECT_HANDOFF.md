# Project handoff for fresh Aurora and local sessions

State consolidated **29 September 2026** from code, frozen artifacts and measured receipts. This is a navigation/state document, not a new experimental result. Read `AGENTS.md` for user requirements and [HANDOFF_OPERATIONS.md](HANDOFF_OPERATIONS.md) for transfer verification and commands.

**Latest continuation:** [Aurora evaluation portability and readiness](AURORA_EVALUATION_READINESS_20260929.md) verifies the original 9,046-file transfer, exact 42-response score replay, and all nine original prompt-token digests. The 63 focused checks pass; broader checks yield 166 passes, two omitted-artifact failures and six skips. A UTF-8 parser fallback fix preserves existing releases. The private GitHub synchronization captures working research code/docs and a separate verified handoff archive captures ignored evidence. Aurora model weights/runtime, independent review and the actual nine-call diagnostic remain pending; no GPU experiment was launched.

## Research purpose and agreed approach

**Application goal:** improve international-policy deliberation through faithful institutional representation, clear disagreements/tradeoffs and defensible next steps. Agreement alone is not success. Accurately explaining why agreement is unavailable can be the right result.

**Research question:** does training on dated institutional behavior and grounded policy application improve fidelity beyond the same model prompted with the same evidence, and does that improvement help collective analysis?

Keep three claims separate: predicting observed decisions; applying declared policy faithfully; and improving deliberation relative to controlled alternatives. Public positions need not equal actual behavior or private motives. The unit is country–institution–role–date, not a country's average resident or timeless personality. Historical imitation does not establish that the action was desirable. No hidden national utility or improved model “values” has been demonstrated.

The first substantive training method is **one shared, evidence-conditioned behavioral LoRA SFT adapter**, supervising answer tokens only. Primary comparison: base plus evidence versus adapter plus the identical evidence. A country-prompt-only arm diagnoses the value of evidence. DPO, constitutional persona training, per-country adapters and interaction training are conditional later branches, not an authorized sweep.

Working title: *From Positions to Decisions: Evaluating Behavior-Trained Country Personas in Multi-Agent Deliberation*. A useful evaluation contribution or controlled null result remains worthwhile. See [research anchor](RESEARCH_ANCHOR.md), [goal/method clarification](RESEARCH_GOAL_AND_METHOD_20260927.md) and [metrics/paper memo](PERSONA_EVALUATION_AND_PAPER_DIRECTION_20260923.md).

## User instructions to preserve

- Active extension: **France, UK, India, Brazil**. Preserve the user's Germany/China decision cases and existing releases.
- Evaluation before new substantive training. Technical probes must remain explicitly technical.
- Every increment must produce insight or a useful artifact. State the question and decision criterion, inspect the result, then choose another run. No speculative queues or multi-seed sweeps now.
- Aurora is available for a few Blackwell GPUs when justified. A medical agent may also use `memo`; only manage resources positively traced to this project's launches. Never infer project ownership from username or perform blanket cancellation.
- Keep models/caches/bulky outputs on scratch, not CSlab home. Credentials remain private and outside snapshots.
- On Trillium prefer `def-zhijing` and retained `sleep infinity` allocations. The September 29 request to cancel all Trillium jobs was executed; the queue was already empty. It is not a standing instruction for future jobs or Aurora.
- The latest request authorizes deep documentation and ordinary ongoing work. It does not waive the evaluation gate or resource-ownership rules.

## What has actually run

| Checkpoint | Observed result | Boundary |
|---|---|---|
| Earlier China/Germany adapter, job 910107 | 500 examples; repetition flags 0 → 13 of 56 diagnostic outputs; all 500 actual TRL masks/targets subsequently audited | No proven cause of repetition or demonstrated useful persona gain |
| Two-event base A/B, job 996664 | 30 outputs: 14 action, 16 policy; original action accuracy 4/7 without evidence, 5/7 with evidence, including a tied India prediction | Seven decisions in two exposed families; not a generalization or calibration claim |
| 34 diagnostic follow-ups | Country-name/answer-format sensitivity, explicit-outcome controls and source-quotation failures | One prompt repair is not a general solution |
| 200-prompt stability check | 14 original prompts replayed exactly; 18/18 fictional extraction controls passed; six-mapping mixtures predicted Abstain on all seven historical cases, 2/7 correct | Consistency is not correctness; 200 variants are not independent events |
| Deliberation baseline, job 999389 | 42 outputs, two events, three conditions; 8/8 initial peer/self pairs identical; 3/6 final memos capped | No validated multi-agent benefit |
| Six synthesis diagnostics | Larger output cap removed observed truncation; targeted instruction repaired selected quota errors but introduced a false common-position claim | Not a general fix or fresh test-set improvement |
| Complete baseline source review | 42 responses; 366 met, 117 unmet, 33 unratable rating instances; one unblinded assistant, zero independent reviewers | 516 dependent judgments, not 516 independent observations |
| Tiny CPU optimization | Two steps, finite loss/gradients, 14 adapter tensors changed, correct masks and save/reload | Not the real 8B model or CUDA/NCCL/persona validation |
| Aurora access/handoff | Remote-host metadata and SSH access; private HF authentication and scratch environment prepared | No Aurora model run or GPU reservation |

Evidence: [old regression](REGRESSION_RESEARCH.md), [A/B results](EVAL_BASELINE_RESULTS_20260927.md), [failure analysis](EVAL_FAILURE_ANALYSIS_20260927.md), [stability](EVAL_STABILIZATION_RESULTS_20260927.md), [deliberation](DELIBERATION_BASELINE_20260928.md), [source review](DELIBERATION_SOURCE_REVIEW_20260928.md), [training verification](../reports/training-verification-20260928.json).

“No new training” refers to the current four-country/evaluation-first phase. An older adapter did run and regressed. The later base-model EOS-only replay was identical; it does not resolve the old adapter's repetition mechanism.

## Evaluation definitions and present limitations

### Observed actions

Use accuracy, class support, macro-F1, minority-action recall, NLL/Brier where valid probabilities exist, and country-name/option-order/paraphrase sensitivity. Current probabilities are conditional first-completion-token probabilities over legal labels, not sequence likelihoods or verbal confidence. Report legal mass, invalid outputs and ties. Model uncertainty is not a historical Abstain vote; nonmembership is not abstention.

The pilot has seven decisions in **two exposed event families**. Some source evidence announces a position; some supplies only broader policy context. Document date alone does not establish pre-decision archival availability. Preserve proposal/procedural-stage identity and historical representation. Do not include later justifications/outcomes in forecasting inputs. There is no sealed final test supporting the new claims.

### Declared-policy fidelity

Score atomic required content plus separate attribution, time/scope, unsupported-claim and invented-commitment checks. Read the full response. Appending a correct phrase without retracting an incompatible claim is not correction. Retain `unratable` where source or criterion is ambiguous. A known failed unit still fails the strict conjunction; uncertainty elsewhere does not hide it. Assistant annotations must not clear independent semantic-review-pending status.

The original 16-response policy kit uses proposed **construct-v2.1**. The 42-response interaction review uses its own frozen deliberation rubric. Reviewing one does not validate the other; their denominators are not interchangeable. Independent construct review, reviewer agreement and adjudication remain pending.

### Deliberation protocol

Climate/security on 9 December 2021 and Ukraine on 27 September 2022 each use four complete prior country statements. All arms receive the same source packet:

- Self-revision: four initial national answers, four revisions seeing their own initial, one final memo.
- Peer revision: identical initials, four revisions seeing all four frozen initials, one final memo. No revision sees another revised answer.
- Single analyst: one four-country analysis, one revision, one final memo.

Primary interaction contrast is peer revision change minus self-revision change, per country/event. Report corrections, new errors and retained content separately. Final memos are independently rated for source-supported positions, genuine common ground, preserved differences, proposals and useful analysis. The before/after design keeps the final aggregator **unadapted** to isolate changes to the analysts.

Measured H100 baseline: 150,968 input tokens, 11,551 generated tokens, about 260 seconds generation, peak 16.51 GiB. Equal output allowances did not equal actual compute. Self revision changed 3/8 national answers, peers 5/8; these are wording-change counts, not improvements.

| Event / arm | Content compared | Corrections / regressions | Other checks compared | Corrections / regressions |
|---|---:|---:|---:|---:|
| Climate / self | 23/24 | 0/0 | 15/16 | 0/0 |
| Climate / peers | 23/24 | 0/0 | 15/16 | 0/0 |
| Climate / central | 21/24 | 1/0 | 13/16 | 0/0 |
| Ukraine / self | 24/25 | 0/0 | 15/16 | 0/0 |
| Ukraine / peers | 24/25 | 0/1 | 14/16 | 1/0 |
| Ukraine / central | 23/25 | 0/0 | 15/16 | 0/0 |

These are provisional assistant judgments over jointly ratable units. Both overall country-macro peer gains remain null. No significance claim or general method ranking is supported. No new trained-model comparison has run.

## Failures that should guide the next step

- Climate national notes preserve “UK quota approval is not established”; all three final memos turn it into “did not approve.” Aggregation introduces an unsupported decision claim.
- A climate memo invents support by all four for the G-5 Sahel Joint Force. Some-country support does not imply consensus.
- The climate peer memo ends normally but omits shared analysis and proposals. EOS is not task completeness.
- UK Ukraine outputs recast a prior statement as a later vote. A real document symbol can accompany a fabricated event.
- France's Ukraine answer covers required content but adds “unconditional” support absent from the source. Recall alone misses unsupported claims.
- A central revision appends the correct UK draft position while retaining its opposite. Keyword-based grading would misclassify this as repair.
- India/Brazil ambiguities expose compound-criterion and paraphrase boundaries. Do not broaden criteria after seeing outputs just to obtain a number.

The evidence-JSON checker deliberately cannot certify entailment. A real exact quote attached to an opposite claim can pass location checks; semantic validity and completeness remain unresolved. Mechanical checks must not become a surrogate policy judge.

## Next useful checkpoints

**1. Portable Aurora context.** Verify the snapshot, inspect runtime/current GPU occupancy, use scratch caches and record process ownership. Trillium used torch 2.8.0+cu128, Transformers 4.57.6, TRL 0.24.0, PEFT 0.17.1 and Accelerate 1.11.0. Aurora compatibility has not been tested. Do not silently change versions or assume H100 results transfer.

**2. One bounded format comparison plus source review.** `data/prepared/evidence-format-20260928-v1/` compares ordinary prose, evidence prose and evidence JSON in three contexts: climate frozen peer notes, Ukraine frozen central notes, and new South Sudan statements. Nine calls, common 2,048-token cap, 700-word limit, 8,192 context. Preflight: 37,823 input tokens, maximum 5,669; full prompt+cap fits 7,717. No model outputs exist yet.

Question: do evidence requirements or JSON structure help preserve positions, uncertainty and useful synthesis? Compare within context, inspect all outputs and cost, then decide. Schema instructions also change input length. The first two contexts were selected after failure inspection; South Sudan adds an issue in the same genre/countries. This is development, not confirmatory evaluation. Independent criteria review remains pending.

**3. Freeze an interpretable evaluation.** Adjudicate source/criterion ambiguity, retain versions, independently review where possible, preserve whole-event splits and obtain separate test material. Do not select a format on exposed cases and label its selected score a fresh test.

**4. Technical training smoke, then fit only if useful.** Ten authored correction targets from eight documents/four connected components; 4,798 sequence and 502 supervised tokens for the full inventory, maximum length 567. Smoke: four cases, one per country, two steps. Fit: ten cases, twenty steps. Rank-8 BF16 LoRA, 5e-5 learning rate, seed 42, completion-only loss. These sizes diagnose optimization, not generalization.

Training now checks masks, finite microbatch loss/gradients, actual updates, rank agreement and saved-state reload. CUDA/NCCL remains unverified. `launch_training_readiness.py --run` requires Slurm and exactly four visible GPUs. **Do not fake `SLURM_JOB_ID` on Aurora.** Establish an explicit Aurora launcher when that step is reached, retaining the verification checks.

**5. Matched base/adapter evaluation, then broader data.** The comparator requires identical device type, library versions, inference code, model bytes, protocol and budgets. An Aurora adapter needs a matched **Aurora base run**; H100 results are historical diagnostics. Expand independent event families and reviewed training supervision before research-quality claims. Multiseed confirmation is for a later stage.

## Data and publication map

| Resource | Meaning / status | Location |
|---|---|---|
| Original Germany/China | Official speeches, genuine QA, UPR/votes and historical corpora; preserved prior work | `data/raw/`, `data/canonical/`, `data/prepared/pilot/`, `posttraining-qwen3-v1/`; source locks/manifests |
| Four-country extension | Strategies, climate/development evidence and policy applications; candidates, not automatic admission | `data/prepared/country-extension-20260914/`; `COUNTRY_EXTENSION_20260914.md` |
| Policy workshop | Ten cases, 53 correlated rows in audit SFT/revision SFT/DPO/multi-agent views, three authored workflows | `data/prepared/policy-workshop-20260916/`; `POLICY_WORKSHOP_POSTTRAINING.md` |
| Technical training probe | Revision view only; research-prepared, not human-approved | `data/prepared/training-readiness-20260928-v1/` |
| Reddit | 2,470,215 unique records and 1,743,263 overlapping direct reply-pair views, six country contexts | `data/prepared/reddit-country-20260923/`; `REDDIT_COUNTRY_DATA.md` |
| Full acquired UNBench release | Beyond the original public sample; documented join/date/scoring issues remain | `data/raw/unbench-audit-20260926/`; `reports/eval-pilot-20260926/unbench-audit.json` |
| UNSC-Bench | Independent diplomatic corpus with overlap/historical-representation limitations | `data/raw/unsc-bench-audit-20260926/`; corresponding audit |
| Frozen evaluation | Action, policy, stability, interaction and format development tasks | `data/prepared/eval-pilot-20260927/`, `deliberation-probe-20260928-v1/`, `evidence-format-20260928-v1/` |
| Reviews | Blank independent-review kits and separately identified assistant annotations | `data/review/` |

Docs named without prefixes in this table are under `docs/`. Exact-PDF overlap between the ten-case probe and two-event eval is zero; semantic event separation and pretraining contamination are not certified. There is no meaningful held-out split within ten cases.

UNBench training labels are highly imbalanced: FRA 729 Yes/5 Abstain/0 No; GBR 734/0/0; IND 113/1/0; BRA 208/9/1. Preserve native namespaces/labels, audit full event boundaries, and keep original-protocol scores separate from stricter task definitions.

Reddit country context is not nationality or government representation; prepared `country_iso3` and `represented_entity` remain null. Scores are not truth/preference gold. Missing parents, conflicting versions, limited redaction and rights/semantic review needs remain. No synthetic national replies were fabricated to fill comment gaps. This is not current government-policy ground truth.

Recorded hosting destinations: [public explorer](https://huggingface.co/spaces/memo-ozdincer/country-persona-explorer), [workshop showcase](https://memo-ozdincer-country-persona-explorer.static.hf.space/policy-workshop-20260916/showcase.html), private HF dataset `memo-ozdincer/country-persona-research-files`, HF dataset/public catalog `memo-ozdincer/country-persona-data`, research Space `memo-ozdincer/country-persona-research`, public GitHub catalog `memo-ozdincer/country-persona-data`. Publication receipts record actual previous uploads. Do not assume newer internal evals/docs are online. This handoff does not publish them.

Private code remote: `https://github.com/memo-ozdincer/country-persona.git`; the original transfer base begins `86d0c9f`. The later private synchronization captures the transferred working code/docs and this continuation. Prepared/review/run directories remain largely ignored. A clone alone misses this state; the separate [private handoff archive](https://github.com/memo-ozdincer/country-persona/releases/tag/aurora-handoff-20260929-v2) carries working bytes, ignored evidence and base Git history.

## Literature and interpretation

Six central PDFs and extracted texts are under `research/persona-evaluation-20260923/`. `portable-manifest.json` maps all six into this tree with verified original hashes; the original manifest preserves historical Mac/Downloads paths.

- **UNBench 2502.14122v2:** primary linked diplomatic benchmark; not interactive deliberation. Audit the exact release and paper/table inconsistencies.
- **Centaur, Nature s41586-025-09215-4:** response-only behavioral training, unfamiliar settings and autonomous rollouts. It is not constitutional training or diplomatic validation.
- **Utility Engineering 2502.08640v1:** motivates testing preference convergence. Appendix D.6 also reports divergent prompted politician profiles. It does not prove prompting cannot work or that training prevents homogenization.
- **RAFT 2403.10131v2:** evidence use amid distractors; institutional adaptation needs testing.
- **UNSC-Bench 2026.mme-main.10:** diplomatic/multilingual evaluation with limited prompting/context and possible memorization.
- **Legal Judgment Prediction 2023.nllp-1.9:** outcome-era explanations cannot be treated as information available to a real forecaster.

Constitutional AI/Open Character Training remain optional methods in [TRAINING_RESEARCH_20260923.md](TRAINING_RESEARCH_20260923.md). A teacher's synthetic preference or introspection is not an observed government's private belief.

## Code map and reproducibility traps

| Area | Entry points / modules |
|---|---|
| Acquisition/preparation | `src/country_persona/cli.py`, `scripts/collect_*.py`, `scripts/prepare_*.py` |
| Model/tokenizer lock | `configs/posttraining/model.lock.json`, `data/metadata/qwen3-8b-tokenizer/` |
| Traced inference | `scripts/run_eval_probe.py`, `inference_probe.py` |
| Actions/robustness | `action_eval.py`, `choice_stability.py`, `scripts/score_action_eval.py`, `score_eval_stability.py` |
| Policy review | `policy_eval.py`, `scripts/score_policy_reviews.py`, `compare_policy_reviewers.py` |
| Interaction | `deliberation.py`, `deliberation_audit.py`, `scripts/run_deliberation_probe.py` |
| Review/comparison | `deliberation_review.py`, `deliberation_comparison.py`, `scripts/review_deliberation_probe.py`, `compare_deliberation_checkpoints.py` |
| Format diagnostic | `scripts/build_evidence_format_probe.py`, `evidence_ledger.py`, `scripts/audit_evidence_format_probe.py` |
| Training | `train.py`, `training_checks.py`, `scripts/check_training_readiness.py`, `launch_training_readiness.py` |
| Handoff | `scripts/build_research_handoff.py`, `scripts/verify_research_handoff.py` |

Core modules without prefixes live in `src/country_persona/`; script filenames grouped after a prefixed script share `scripts/`. Preserve `use_model_defaults=False`: Transformers previously restored checkpoint sampling defaults over a requested greedy setting, and the runtime trace caught it. Qwen3 EOS IDs are `[151645,151643]`. Full input sources/notes are not silently truncated. Failed/preflight-only outputs cannot be promoted to successful inference.

Pinned model: **Qwen/Qwen3-8B**, revision **b968826d9c46dd6066d109eabc6255188de91218**, thinking disabled. The old directory name `Qwen3-8B-Instruct` is misleading; hashes/lock define identity. The lock's historical `weights_downloaded=false` does not describe every remote host. The Trillium receipt covers twelve files including five weight shards; rehash current bytes before production use.

## Infrastructure, artifacts and continuity

Original Mac root: `/Users/memoozdincer/Documents/Research/Jin/persona`. Aurora scratch: `/mfs1/u/memo/country-persona-research`. Snapshots live beneath `workspaces/`; its root `START_HERE.md` identifies the current copy. Source the private environment profile before model/package work. HF token locations are documented in [AURORA_WORKFLOW.md](AURORA_WORKFLOW.md), without exposing the value.

Old Trillium model: `/scratch/memoozd/models/Qwen3-8B-Instruct`; older remote payload: `/scratch/memoozd/persona/research-readiness-20260928-v2`. Local v3 has newer verification code. All old allocation deadlines have passed; September 29's queue was empty. Recheck live state. Trillium required entering the allocated node before `srun`; SSH/heredoc-driven steps need `srun --input=/dev/null` to avoid consuming later commands.

The handoff excludes base weights, credentials, virtual environments/caches and large Reddit/legacy corpora. It includes actual code/tests/docs, active frozen packs, reviews, tokenizer metadata, key primary sources, benchmark audits, small-run transcripts and reference PDFs. Its inventory describes omissions and its manifest hashes every included file. It is a point-in-time private snapshot, not live synchronization or a backup guarantee for scratch.

After each checkpoint: retain original outputs/errors; document observation, limitation and next decision; update this summary; make a new verified snapshot when moving sessions. Preserve earlier snapshots. Reconcile diffs/manifests before merging concurrent workspaces. Missing evidence and uncertain judgments must remain explicit.
