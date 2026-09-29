# Evaluation pilot: build, measure, decide

26 September 2026. Execution of the [major research anchor](RESEARCH_ANCHOR.md), following the instruction to make every increment useful. **The first increments already changed the experiment: accuracy is misleading on UNBench, some source labels conflict, and draft/decision-stage alignment must be checked before training.**

The implemented work is local: two acquired benchmark releases, reproducible audits, a strict action scorer, empirical baselines, a small review pack and a tokenizer preflight. There has been **no new LLM inference, adapter training, human adjudication, final-test freeze or online publication** in this increment. The existing Germany/China training releases are preserved.

**Dated continuation:** the [27 September checkpoint](EVAL_PILOT_CHECKPOINT_20260927.md) adds two primary-source reconstruction cards, eight policy questions, an authored calibration deck and a prepared eight-output inference probe. The 26 September results below remain a historical snapshot.

## How each increment earns the next one

Start with one question and the smallest artifact that can answer it. End with a measured observation, an explicit limitation and a decision. Keep failed checks and negative results. Enlarge a dataset or add a training method only when the preceding result identifies what the addition would teach us.

| Increment | Question | Actual observation | Decision |
|---|---|---|---|
| 1. Source inventory | Can the available benchmark expose meaningful country decisions? | The full UNBench archive contains 17,430 Task2 votes. Its test has 6,210 Yes, 209 Abstain and **one No**. None of our six target countries has a test No. | Retain UNBench for comparability; do not use its accuracy as a persona-fidelity claim. Seek complementary disagreement cases. |
| 2. Scoring check | Can our evaluator distinguish good predictions from formatting failures and majority guessing? | **26 targeted tests pass** across the scorer, source normalizer and pack builder. Invalid/missing answers remain errors; stale hashes, duplicate predictions and invalid probability distributions are rejected. | The action scorer is usable for development. Probability extraction from an actual model and paired model comparisons remain separate work. |
| 3. Empirical floor | What can we achieve without a language model? | Always-Yes reaches **96.73% accuracy**, **33.33% balanced accuracy**, and zero No/Abstain recall on the full UNBench test. | Report class support, minority recall and proper probability scores alongside accuracy. A high accuracy number alone is insufficient. |
| 4. Supplement audit | Does UNSC-Bench close the gap cleanly? | Acquired 469 event records and 6,619 all-country vote rows. **42 records have at least one detected issue** requiring review. Several internally inconsistent labels and two misaligned amendment records are visible. | Exclude flagged records from the development candidate pool. Preserve originals and record evidence; do not silently repair gold labels. |
| 5. Review pack | Can we form a small inspectable task outside the Germany/China work? | **21 decisions, seven drafts/meetings**, for France, UK, India and Brazil. Labels: 14 Yes, six Abstain, one No. Inspecting v1 exposed the amendment error; v2 excludes it. | Use v2 for review and pipeline checks. Seven meetings are not seven independent issue families, and the pack is not a final test. |
| 6. Context preflight | Will the intended model see complete proposals? | Locked Qwen3 tokenizer: **68,488 total input tokens**, 298–10,687 per case. Four country views of one draft exceed a 4,096-token prompt budget. Y/N/A each encode as one token. | Preserve full drafts. Set and record an adequate context budget after adding evidence; do not silently truncate or select only short successful cases. |

## What the full UNBench release taught us

The [author-linked archive receipt](../data/manifests/unbench-full-20260926.json) pins a 59,355,903-byte ZIP by SHA-256. It was acquired from the download linked in the [authors' repository](https://github.com/yueqingliang1/UNBench); downloaded notebooks were inspected, never executed. The earlier 30-vote sample remains separate.

- Task2: 11,010 training rows over 734 events; 6,420 test rows over 428 events. The three votes missing from the paper's Y/N/A total are explicitly **Non-Voting**, not abstentions. Exclude them explicitly from a three-class task.
- Task1: the accessible archive contains 1,000 training and 1,000 test examples, but only **155 and seven distinct folder/event IDs**, respectively. These files do not reproduce the paper's larger Task1 row count.
- Task3: 989 train and 989 test rows, with 45 and 53 non-adoptions. Both splits span much of 1994–2024; the supplied split is not a strict chronological holdout. One test text is duplicated under two documents.
- There is no exact normalized-text train/test overlap **within** Tasks1/2/3. There is substantial overlap **across tasks**: for example, 214 Task3 training texts also occur in Task2 test, and 356 Task2 training texts occur in Task3 test. Combining official training files can therefore contaminate other tasks' tests. Exact matching is only a lower bound; related meetings, revisions and translations still need family grouping.
- Eight Task2 events have draft metadata dated after the recorded vote, seven in training and one in test. These are discrepancies for investigation, not proof that the text itself was unavailable at decision time.
- The Task2 notebook randomizes invalid outputs and computes AUC/AP from hard-label indicators. Task3 also randomizes invalid outputs and flips labels before binary F1, making non-adoption the positive class. These conventions differ from our strict scorer. The paper's inconsistent Task2/Task3 reported numbers remain unresolved; our audit does not recreate unpublished model predictions.

Full machine-readable results: [UNBench audit](../reports/eval-pilot-20260926/unbench-audit.json).

### Empirical baselines actually run

Priors use official training labels only, with add-one smoothing. Non-Voting is excluded explicitly. NLL uses natural logarithms; Brier is the sum of squared errors over Y/N/A. These are empirical distributions, not a model's verbal confidence.

| Task2 arm | Accuracy | Balanced accuracy, Y/N/A | Macro-F1, fixed labels | NLL | Brier |
|---|---:|---:|---:|---:|---:|
| Always Yes | 0.9673 | 0.3333 | 0.3278 | — | — |
| Global training prior | 0.9673 | 0.3333 | 0.3278 | 0.1520 | 0.06376 |
| Country training prior | 0.9673 | 0.3333 | 0.3278 | 0.1408 | 0.06227 |

The country prior changes probability quality while leaving every argmax at Yes. That illustrates why accuracy alone can miss differences, without establishing any learned persona ability. Germany's all-Yes test slice gets 100% accuracy from the constant baseline; three-class balanced accuracy is correctly unavailable there. Task3's training-prior baseline gets 94.64% accuracy but only 50% balanced accuracy.

[Full baseline results, including country slices](../reports/eval-pilot-20260926/empirical-baselines.json). These numbers use the author split for audit comparability; they do not certify its labels, source times or suitability as a final research test.

## What inspecting the supplementary data changed

[UNSC-Bench](https://huggingface.co/datasets/UNSC-Bench/UNSC-Bench) is pinned at revision `55bd5aa5bb317a942b9229de13dca985e642a40b` in the [acquisition manifest](../data/manifests/unsc-bench-20260926.json). The files contain votes for elected members as well as the P5. The dataset card declares CC BY 4.0; raw acquisition does not establish expert review or source equivalence across languages.

Detected issues overlap: 17 records disagree with their own vote totals; 30 disagree with their own detailed vote strings; two lack draft symbols; eight vetoed records contain no No vote; two amendments require their parent draft and voting-stage review. Together these flag 42 distinct records, **not 59 distinct failures**. For example, S/RES/2580 (2021) has structured member votes all A, but its vote-detail string and totals record unanimous Y. There are also at least **236 matching draft-symbol records** across UNSC-Bench and the acquired UNBench document collections, so the supplement is not automatically independent.

The first seven-event pack revealed a stronger problem: S/2025/115 and S/2025/116 were paired with a 10–0–5 vote, including France and UK abstentions. The UN Security Council's own special report records France and UK voting **Yes on both amendments**, with respective totals 9–1–5 and 11–1–3. The final resolution was a different decision. This is verified against the [downloaded UN report](https://www.un.org/pga/wp-content/uploads/sites/109/2025/02/20250227-PSC-letter-to-PGA-Special-Rpt-UNSC-9866th-mtg.pdf), with a local hash and location in [primary-record checks](../reports/eval-pilot-20260926/primary-record-checks.json). It motivates a generic stage check, rather than a one-off relabeling.

After detected conflicts are excluded, the since-1990 pool still has zero French/UK/Brazilian No votes and only one Indian No. **Do not manufacture No labels to balance these countries.** For a three-way modern decision benchmark, acquire other well-linked institutional decisions; for this narrow UNSC pilot, report the available action coverage honestly.

Full details: [UNSC-Bench audit](../reports/eval-pilot-20260926/unsc-bench-audit.json).

## Small artifact to inspect now

Active pack: `data/prepared/eval-pilot-20260926/action-review-v2/`. Its [tracked manifest](../reports/eval-pilot-20260926/action-review-v2-manifest.json) and [event list](../reports/eval-pilot-20260926/action-review-v2-events.json) make it reviewable without loading the raw corpora. [Pack status](../reports/eval-pilot-20260926/pack-status.json) marks v1 as superseded.

| File | Purpose |
|---|---|
| `cases.jsonl` | Hashed prompts containing only country, institution, date and the supplied English draft |
| `references.jsonl` | Separate source labels, source row indexes, original names, document and meeting links |
| `review.jsonl` | Empty review fields for exact vote, draft version, readability, availability, leakage and family grouping |
| `events.json` | Seven-event view with all included country actions |
| `constant-yes.predictions.jsonl` and `constant-yes.scores.json` | An explicit constant-baseline pipeline check, not generated model outputs |
| `manifest.json` | Source revision, input/output hashes, selection rule and limitations |

Selection is deliberately diagnostic: choose the latest eligible event since 1990 for each extension-country/action pair and include the other extension-country views of those drafts. This is neither a random sample nor a prevalence estimate. All references remain marked `source_label_unverified`, and every human-review field remains blank. Excluding detected conflicts is not equivalent to verifying every remaining record. Source text itself can still contain revealing metadata or version problems; field allowlisting alone cannot prevent that.

## The next experiment, kept small

**Question: does supplying admissible dated policy evidence improve recorded-action predictions over the same model given the draft and country/date alone?** Establish that comparison before training an adapter.

1. Verify the seven candidate events against primary voting records and exact draft versions. Preserve machine-assisted source checks separately from independent human ratings. Identify related event families across both benchmarks and our existing exposed data. Drop or quarantine an event with an unresolved target; do not fix it by inventing an answer.
2. Assemble a small evidence packet per retained case from material available before that vote. Keep post-vote explanations as reference material only. Review unsupported commitments and required content using the existing policy rubric; this action-only scorer cannot measure those outcomes.
3. Run a bounded **A/B inference smoke test** on identical retained cases: draft/country/date versus the same plus evidence, with the pinned base model and common decoding settings. Tokenize both arms first. A 16,384-token total context is a candidate engineering budget for these full drafts plus modest evidence, subject to verification; no prompt has been truncated. Log token costs and use the same complete cases in both arms.
4. Inspect legal-output rate, per-country/class errors, conditional legal-label NLL/Brier, and any change caused by evidence. Log raw generated token IDs and effective EOS configuration to expose the unresolved stopping issue in the earlier pilot. A seven-meeting smoke test diagnoses failures; it is too small and too concentrated to establish an effect or select on a final test.
5. If the task, source boundaries and instrumentation hold, expand to at least 20 independently reviewed development families, reserve a separate final-test pool, then run **one** small behavioral LoRA SFT comparison against B. If evidence fails to help, investigate missing context or task ambiguity before scaling training. Interaction and preference optimization remain later branches.

Every stage will report its observed result and next decision in this log or a dated successor. The nearest work is the seven-event evidence/label review, not a larger simulator or a new optimization method.

## Reproduce these increments

Use the repository's environment with its development, catalog and tokenizer dependencies installed. Source roots are pinned by the manifests above. Outputs below are audit files; pack builds require a new directory to preserve existing reviews.

```bash
.venv/bin/python scripts/audit_unbench_release.py \
  --root data/raw/unbench-audit-20260926/full/UNBench-all \
  --output-dir reports/eval-pilot-20260926
.venv/bin/python scripts/audit_unsc_bench.py \
  --root data/raw/unsc-bench-audit-20260926 \
  --unbench-root data/raw/unbench-audit-20260926/full/UNBench-all \
  --output reports/eval-pilot-20260926/unsc-bench-audit.json
.venv/bin/python -m pytest -q \
  tests/test_action_eval.py tests/test_unsc_bench.py tests/test_action_review_pack.py
.venv/bin/python scripts/build_action_review_pack.py \
  --root data/raw/unsc-bench-audit-20260926 \
  --output data/prepared/eval-pilot-20260926/action-review-rebuild
.venv/bin/python scripts/preflight_action_eval.py \
  --pack data/prepared/eval-pilot-20260926/action-review-v2 \
  --output reports/eval-pilot-20260926/action-review-v2-preflight.json
.venv/bin/python scripts/score_action_eval.py \
  --cases data/prepared/eval-pilot-20260926/action-review-v2/cases.jsonl \
  --references data/prepared/eval-pilot-20260926/action-review-v2/references.jsonl \
  --predictions data/prepared/eval-pilot-20260926/action-review-v2/constant-yes.predictions.jsonl \
  --output /tmp/persona-action-score-check.json
```

The scorer requires prediction IDs and case hashes to match. Missing generations count as errors. Supply actual legal-label probabilities with `probability_semantics: conditional_on_legal_labels` if available; do not create them from verbal confidence. NLL/Brier require complete probability coverage; absent reference classes produce null full-class balanced accuracy. No AUC is inferred from hard labels. These safeguards do not replace source review, policy scoring or statistical evaluation of independent events.
