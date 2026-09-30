# Benchmark-grounded checked-plan comparison on Aurora

Measured 30 September 2026. The user endorsed grounding the plan-to-text trial in existing benchmarks and the evaluations already prepared. We completed one new event comparison using the saved Qwen3.5-4B complete-task adapter: **two full answers, zero new training steps**. This extends the [previous plan-to-text trial](AURORA_QWEN35_PLAN_TO_TEXT_20260930.md), whose two complete climate/Ukraine training targets received 20 LoRA steps.

The question was whether the saved adapter preserves supplied actions, qualifications and bounded missing information better than the base on a new benchmark-linked plan. Both received the exact same input tokens. Positions and recorded votes were supplied; this evaluates faithful prose realization, not native benchmark action prediction.

## Event, benchmark and primary grounding

We used the pinned UNSC-Bench `vetoed` row 11: the 8 December 2023 vote on Gaza draft S/2023/970, meeting S/PV.9499. This is already linked to three cases in our frozen 21-action, seven-event `action-review-v2` pack. The native release revision is `55bd5aa5bb317a942b9229de13dca985e642a40b`. The selected row is not among the 42 flagged records in the [existing benchmark audit](../reports/eval-pilot-20260926/unsc-bench-audit.json).

The native row, original evaluation references and the [official meeting record](https://documents.un.org/doc/undoc/pro/n23/395/52/pdf/n2339552.pdf) agree: France and Brazil voted Yes, the UK abstained; the tally was 13 Yes, one No and one Abstain, and the draft was not adopted because of the United States permanent-member negative vote. India was not a Council member for this event; nonmembership is not a recorded abstention. The bounded record supplies no Indian national statement. This is a limit of this packet, not a statement about all Indian policy.

The 402,524-byte primary PDF has SHA-256 `0575967053afc398fa946fa282366ab4c56a8f44244d415bf261b8576d0742b9`. We read the complete French, UK and Brazilian statements, visually checked pages 5, 6 and 8, and retained full-record and statement offsets with page/column locations. A separate scratch runtime with PyMuPDF 1.26.7 performed the extraction; the training runtime was unchanged. On all nine body pages, the two column crops preserve the full body-region word multiset.

Source acquisition failures remain inspectable. V1 retains the downloaded PDF and the collector's missing-`pdftotext` receipt. V2 preserves the superseded narrow crop that lost line-end punctuation. V3 is the checked extraction used for the frozen plan. Neither earlier extraction reached the model.

The other audited benchmark, UNBench Task 2, remains unsuitable for an unqualified headline accuracy claim: its 6,420 test rows include 6,210 Yes, 209 Abstain and one No. Always-Yes scores 96.73% accuracy with zero minority-action recall. Its overlap, stage and native-evaluator issues remain in the [audit](../reports/eval-pilot-20260926/unbench-audit.json). We reused existing audits and evaluation infrastructure; no full benchmark campaign was launched.

## Frozen task and scoring

The one-case pack froze **29 content units and three universal checks before either new answer**. Positive claims have exact source spans; absence claims are bounded to a hashed source; analyst synthesis/proposals are explicitly distinguished from government statements. The future-draft question asks whether adding Hamas-condemnation wording establishes a UK Yes vote. The source does not announce that counterfactual decision.

The [teacher specification](../configs/posttraining/qwen35-benchmark-plan-spec-20260930.json) and plan were authored by this assistant from the complete source statements. Independent source, construct and semantic review remain pending. Exact quote matching certifies location, not entailment. The new event is outside this adapter's two training events, but was already selected for our development evaluation; whole-family independence and pretraining contamination are unknown. It is not a sealed test.

We supplied explicit full-response judgments to the existing `scripts/score_policy_reviews.py` and `src/country_persona/policy_eval.py`. A documented identifier bridge maps the frozen plural `no_unsupported_commitments` and `correct_time_scope` to the scorer's canonical singular commitment and time/scope keys. Criterion descriptions, meanings and pre-generation source spans remain unchanged; original and canonical rubric hashes are retained. We did not broaden criteria after observing outputs.

## Inspected results

| Measure | Base with checked plan | Saved complete-task adapter with identical plan |
|---|---:|---:|
| Content units rated met | 26 | 28 |
| Content units rated unmet | 3 | 0 |
| Content units unratable | 0 | 1 |
| Universal checks met / total | 1 / 3 | 3 / 3 |
| Existing scorer strict outcome | Fail | Unresolved |
| Output tokens / whitespace words | 859 / 630 | 653 / 509 |
| Generation seconds | 13.52 | 16.12 |

These are dependent judgments by **one unblinded assistant on one event and two answers**. They are not benchmark accuracy, independent review or validated persona-quality scores. The adapter's content-met rate and strict pass rate remain null because one unit is unratable.

Among the **28 jointly ratable content units**, the existing transition metric records **three known corrections and zero known regressions**:

- France's emphasis on the political dimension returns; the base lists the dimensions but drops the supplied priority.
- Brazil's intention to work with Council members to restore conditions for humanitarian action returns; the base preserves its negotiating-process suggestion but omits this separate point.
- Common ground is restricted to supported humanitarian concerns; the base assigns an aid-delivery priority to all three even though the bounded French statement does not establish it.

The adapter also removes the invented 9 December memo writing date and the base's extra UK hypothetical-vote prerequisite. The UK statement's two-State policy goal does not establish a condition for a future Yes vote. Both answers preserve the recorded national votes and India's nonmembership without turning the latter into Abstain.

One possible coverage regression remains **unratable**: the adapter states that the US No prevented adoption despite the large majority, but omits explicit permanent-member/veto wording. The frozen criterion includes that mechanism without operationalizing whether this implicit causal paraphrase is sufficient. Preserve the uncertainty for construct adjudication; it is neither a known regression nor a pass. The adapter also copies a planner instruction into the public India paragraph. That is a formatting concern outside the frozen content rubric.

## Execution and reproducibility

- Model: Qwen/Qwen3.5-4B, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`; all 11 locked model files rehashed.
- Hardware: **NVIDIA RTX PRO 6000 Blackwell Server Edition**, one GPU, BF16 and SDPA. Peak allocated memory: **8.30 GiB**. Each answer has exactly **902 input tokens**, greedy decoding, thinking disabled and a 2,048-token cap. Both finish below the cap and 700-word limit.
- Runtime, model bytes, hardware type, shared inference helper and effective generation configuration match the inspected fit. Loading the saved adapter reproduces its inspected tensor-state digest `95e1fbc32a01d6312c2635436074077b1e3e781d734a7c5ffca710ab2c28b459`. There is no new optimization.
- The seven frozen plan payload files, five primary-extraction files and six review files reproduce byte for byte. The pack manifest's new replay timestamp is excluded from payload comparison. Nineteen existing focused tests pass: 13 policy-evaluator tests and six evidence tests. These are software checks, not model-quality evidence.
- Launch records bind host, GPU UUID, PID, start time/ticks, command and directory before CUDA. The recorded process exited normally; its PID is absent at inspection. No unfamiliar process was altered or cancelled. Distributed/NCCL execution remains unverified.

## Artifacts and next decision

The [preparation receipt](../reports/aurora-qwen35-benchmark-plan-preparation-20260930.json), [measured comparison](../reports/aurora-qwen35-benchmark-plan-comparison-20260930.json) and [verification receipt](../reports/aurora-qwen35-benchmark-plan-verification-20260930.json) retain hashes and boundaries. The [comparison configuration](../configs/posttraining/qwen35-benchmark-plan-comparison-20260930.json) pins the exact saved adapter and inspected run.

Prepared pack: `data/prepared/qwen35-benchmark-plan-20260930-v1/`. Primary acquisition/extractions: `data/raw/benchmark-plan-grounding-20260930-v{1,2,3}/`. Run: `runs/aurora-qwen35-benchmark-plan-20260930-v1/`, including both complete memos, transcript token IDs, explicit ratings, canonical rubric bridge, scorer output, opaque-ID independent-review deck, source captures and exit receipt.

This checkpoint supports continuing **source-checked plan-to-text supervision**: the saved adapter repairs selected coverage and invention failures on another development event. It does not justify increasing optimization yet. First adjudicate explicit-versus-implicit veto coverage and independently audit the upstream plan where possible. A subsequent bounded source-linked event should compare the same two arms, frozen coverage and unsupported additions before choosing more data or steps; select it from the inspected failure question, without a sweep. Keep native action prediction as a separate task with decisions held out of inputs, event-family splits and majority/minority/invalid-output controls. All prior fits, Germany/China releases and historical evaluation remain preserved.

The refreshed private handoff carries ignored primary data, frozen packs, full transcripts and review artifacts alongside Git code. Credentials, base weights, environments and caches remain excluded.
