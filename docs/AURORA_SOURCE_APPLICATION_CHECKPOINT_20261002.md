# National application: raw sources, checked plans and boundary repair

On 2 October, twelve complete Qwen3.5-4B answers were generated and inspected on Aurora: an eight-answer frozen comparison, followed by a four-answer repair selected only after the first inspection. **No new optimizer steps.** The saved comparative-writer adapter did not improve the raw-source scores. Explicit plan boundaries repaired the base's national application; the adapter retained one omission and one invented future-support condition. The next candidate is source-to-national-application supervision with teacher-only plans, rather than more comparative-writer fitting or an immediate switch to DPO/RL. A new fit is not prepared or launched.

The [measured receipt](../reports/qwen35-source-plan-checkpoint-20261002.json) and [portable verification receipt](../reports/qwen35-source-plan-verification-20261002.json) separate byte/software checks from provisional semantic ratings. There is one event and one unblinded assistant reviewer, also the planner. These are development findings, not independent persona-quality, multi-agent or benchmark prediction results.

## The concrete question and frozen test

Can base or the saved two-target complete-memo adapter apply supplied national statements to a new policy discussion, and does adding a checked plan change the outcome? The original adapter trained comparative memos, so national application is a task-transfer diagnostic.

The source is the complete [UN meeting record S/PV.9214](https://documents.un.org/doc/undoc/pro/n22/734/36/pdf/n2273436.pdf), 9 December 2022, on humanitarian exemptions to sanctions and resolution 2664. It is linked to meeting 2467 in the acquired **UNBench-all** corpus. Brazil supports the humanitarian exemption while preserving legitimate sanctions/security purposes. India values timely aid, predictable agencies and legitimate trade, but explicitly seeks a proactive 1267 Monitoring Team role and robust reporting, and warns against terrorist fundraising, recruitment and political mainstreaming.

The hypothetical implementation discussion offers:

- A: prompt delivery, without proactive Monitoring Team oversight or robust reporting.
- B: pause all exempt deliveries until every end beneficiary has been screened.

Each national briefing must identify sourced priorities, choose or revise an option, propose an operational amendment, and explain whether that amendment guarantees future support. Neither option was historically tabled. Multiple defensible recommendations are allowed; agreement between countries is not penalized. Official commitments must be distinguished from analyst proposals.

Two roles × two inputs × two weight arms gave eight answers. Raw and plan conditions share the complete Brazil/India statements, scenario, question and system instructions; the plan condition only appends assistance. Each base/adapter pair receives identical input tokens. Thinking remains disabled, generation greedy, with the historical 2,048-token cap and no truncation. Frozen criteria contain eight country units and four universal units per answer. Strict pass requires all twelve met; genuine ambiguity is unratable, not a pass. These custom application criteria are not native benchmark labels.

The [original specification](../configs/posttraining/qwen35-source-plan-spec-20261002.json), [comparison lock](../configs/posttraining/qwen35-source-plan-comparison-20261002.json) and frozen pack preserve the pre-generation obligations, source quotes, bounded absence judgments and decision rules. Freeze time precedes generation. Same-assistant source/plan review is explicit; no independent review is claimed.

## What the first eight answers showed

| Input condition, two roles each | Base: met / 24 | Saved adapter: met / 24 | Strict passes, base / adapter |
|---|---:|---:|---:|
| Raw statements | 18 | 18 | 0 / 0 |
| Initial checked plan | 18 | 22 | 0 / 1 |
| Stronger boundary plan, subsequent repair | 24 | 22 | 2 / 0 |

The last row is a separate, inspected repair on the same exposed event, not a fresh test. All ratings are provisional assistant annotations. The 144 unit ratings are dependent judgments on twelve responses, not 144 independent observations or a population estimate.

In **both raw India answers**, the model requires every end beneficiary to be assessed before delivery or fund release, then claims this avoids the blanket delay it rejects in B. Saying “prompt aid” does not repair that operational contradiction. Both also invent official future-support conditions absent from the speech. Brazil's historical support is omitted in both raw outputs. The adapter's raw Brazil answer additionally omits the legitimate security purpose of sanctions.

Initial plans improve the adapter's coverage and operational recommendation, but leave an India source overstatement (“absent” rather than “not fully addressed”), omit political mainstreaming, and do not establish robust implementation. Base plans still omit India's trade qualification and add invented next-day briefing dates. Some proactive-versus-passive Monitoring Team assignments remain underspecified. Annotation notes preserve contextual judgments: sponsorship counts as support under the frozen “support/vote” wording; equivalent mainstreaming meaning is accepted consistently; no post-hoc keyword requirement was added.

Full original outputs and annotations: [eight answers](../runs/aurora-qwen35-source-plan-probe-20261002-v1/answers.md), [inspection](../runs/aurora-qwen35-source-plan-probe-20261002-v1/inspection.json). The inspection hash is a prerequisite of the repair launch.

## The result-driven repair

Because checked-plan realization still failed, source-application SFT was not launched. One new frozen plan per role added explicit boundaries:

- Preserve source qualifiers and material national priorities, including trade and political mainstreaming.
- Make targeted checks operationally different from universal pre-delivery gating.
- Label proposed mechanisms as analyst amendments; invent no official support contingency.
- Omit a writing-date header and avoid unsupported geographical additions.

Four matched answers, base/adapter × Brazil/India, were then generated with the same model/runtime/helper/generation lock. The [repair configuration](../configs/posttraining/qwen35-source-plan-repair-20261002.json) and frozen pack retain unchanged scoring criteria. All four complete outputs were inspected before this checkpoint ended.

The base meets all twelve criteria for both countries, including targeted oversight and continued low-risk aid. This is an annotation of the proposed text, not a verified aid-delivery implementation. General caution about future merits is accepted as analyst reasoning; a specific invented official monitoring-performance condition is not.

The adapter fixes the universal gate and the source qualifier, but **Brazil still omits its historical support**. India correctly says there is no operative-text/protocol red line, then still asserts that “future support remains contingent on broader implementation feedback and the Monitoring Team's performance.” The speech hopes for review and correction; it does not establish that future-vote condition.

Full repair outputs and annotations: [four answers](../runs/aurora-qwen35-source-plan-repair-20261002-v1/answers.md), [inspection](../runs/aurora-qwen35-source-plan-repair-20261002-v1/inspection.json).

## Decision and remaining limits

Keep the stronger checked-plan control and the saved writer as a historical comparison. **Do not assume this adapter is a better national agent.** Raw-source application and complete supplied-plan realization are different contracts. The concrete next supervision candidate is source → national application: a teacher may privately use a checked plan, while the student receives country/role/date, sources and question, and must learn application rather than simply realize supplied bullets. Coverage, operational consistency and unknown-commitment boundaries belong in target audits.

Before fitting that candidate, freeze a separate event family and its atomic criteria, audit targets and upstream plans independently where possible, retain the strong base-plus-plan control, and resolve outstanding source/rubric ambiguities. A bounded fit can then ask whether the extra planner can be removed without losing its useful behavior. No twenty-example release, fit, pressure/update or multi-agent run was prepared or launched here. No speculative queue or seed sweep. Existing Gaza veto coverage remains unresolved and its historical ratings unchanged; it does not enter this application's rubric.

This event is outside the saved adapter's two training contexts. A document-symbol search found no matches in the prior project materials audited, but the UNBench corpus was acquired previously, sanctions themes occur elsewhere, and base pretraining is unknown. This is not certified deep OOD. The repair is explicitly exposed development. Plans add assistance and input tokens, so this is not an equal-compute comparison or proof of a unique planner mechanism. Country behavior under peer pressure, justified evidence updates and interaction remains unmeasured here.

## Reproduction and resource receipts

The model remains `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`; all eleven locked model files were rehashed before each run. Runtime pins, adapter serialization/tensor digest, shared inference helper, generation protocol and GPU type match the September 30 fit. One **NVIDIA RTX PRO 6000 Blackwell Server Edition** was used, peak allocated memory 8.47 / 8.54 GiB for initial/repair runs. Both recorded project PIDs exited normally. Unfamiliar processes were untouched. Total project optimizer steps remain 62; distributed/NCCL is unverified.

The primary PDF's hash, isolated PyMuPDF 1.26.7 column extraction, page/column offsets, complete speech boundaries and body-word coverage are preserved under `data/raw/source-plan-grounding-20261002-v1`. The assistant inspected PDF pages 4, 7 and 8. India explicitly switches to national capacity; the subsequent return to chair is excluded. The benchmark labels this national speech “The President” / “Unknown” and inserts one extra period at a page boundary. Brazil's complete benchmark statement matches the primary extraction after whitespace normalization. An initial assistant preview incorrectly suggested a missing Brazil paragraph; that claim was corrected before the pack froze. Failed acquisition evidence is retained.

Four focused CPU guard tests pass. The system Python lacked pytest; the pinned project runtime succeeded. Tests verify unchanged instructions across raw/plan conditions, matching per case rather than against the first transcript row, valid arm pairs and both national roles in the repair. They are software checks, not model-quality evidence.

```bash
python3 scripts/verify_qwen35_source_plan_checkpoint.py --root .
```

This portable verifier replays bytes, source boundaries, frozen criteria, prompt pairing, inspection-before-repair ordering, exact evidence quotes and stored counts. It does not independently reassess semantics. Full snapshots must include the new raw/prepared packs, complete run directories, receipts and source captures; Git alone omits those ignored artifacts. Credentials and base weights remain excluded.
