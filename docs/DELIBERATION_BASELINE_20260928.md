# First deliberation baseline and synthesis diagnostic — 28 September 2026

**48 real base-model generations completed; no new training.** The 42-call interaction baseline exposes source-boundary and aggregation failures. A six-call follow-up separates a truncation problem from reasoning errors. Independent semantic ratings remain pending, so these are development observations rather than a validated benchmark result.

**Complete provisional source review:** [All 42 climate and Ukraine outputs now have assistant annotations](DELIBERATION_SOURCE_REVIEW_20260928.md). Climate self/peer revision makes no confirmed corrections on jointly ratable units; the single analyst adds France's resilience objective. Ukraine peer revision fixes one attribution check but loses one required content point. Thirty-three rating instances remain ambiguous; both country-macro peer-benefit scores stay unresolved. These are one assistant's ratings, not independent validation.

The frozen protocol covers France, the UK, India and Brazil in two source-backed retrospective workshops. Every arm has the same source packet. Peer revisions see all four initial notes; independent revisions see only their own. The final aggregator is the same unadapted Qwen3-8B model. The comparison script now supports repeating the evaluation after training, but no trained comparison is claimed here.

## Measured results

| Arm, across both events | Calls | Input tokens | Generated tokens | Generation seconds | Capped final memos |
|---|---:|---:|---:|---:|---:|
| Independent self-revision | 18 | 61,254 | 4,142 | 93.9 | 2 / 2 |
| Peer discussion | 18 | 66,926 | 4,023 | 90.6 | 1 / 2 |
| Single analyst | 6 | 22,788 | 3,386 | 75.4 | 0 / 2 |

Totals: **150,968 input tokens, 11,551 generated tokens, 260.0 seconds of generation**, plus 10.2 seconds of trace processing. Peak allocated GPU memory was 16.51 GiB. Model loading, byte verification and the retained reservation are additional costs. Equal output allowances did not produce equal actual compute.

- All eight initial self/peer pairs have identical input and output tokens. This verifies the intended common starting point.
- Independent revision changed 3/8 national answers; peer revision changed 5/8. These are text-change counts, not counts of improvements.
- Three of six final memos hit the 512-token cap. No individual-country or central-analysis response hit its cap. No empty answers or generated thinking markers occurred.
- Exact replay of every prompt and visible-history dependency passed. The source-linked review pack contains 42 responses; formal semantic scores remain null without supplied ratings.

Only two already exposed events are represented. Country answers and multiple summaries from the same event are dependent observations. No confidence interval, significance claim or general deliberation ranking is justified.

## What the actual outputs teach us

These findings are assistant source checks, with exact output/source excerpts bound to hashes in the linked receipts. They are not independent human ratings.

**Missing evidence becomes a negative claim during aggregation.** All three climate final memos say the UK did not approve binding national carbon quotas. The source and the national notes instead leave such approval unestablished. This is an evidence-scope error; it is not proof that the UK historically approved or rejected the policy. Agent fidelity and final-memo fidelity need separate measurements.

**Shared positions can be invented.** The climate self-revision memo says all four delegations supported regional initiatives such as the G-5 Sahel Joint Force. France and India explicitly discuss support for the Joint Force. The supplied UK and Brazil passages do not establish that commitment. Broad common ground must be checked country by country.

**Citation presence does not establish correct chronology.** The Ukraine UK answer in the peer arm cites S/PV.9135 as a later vote confirming the UK's support. In the actual supplied statement, S/PV.9135 refers to the Foreign Secretary's remarks “last week.” The response moves an earlier statement into a later outcome. The source packet does not establish that alleged vote.

**Central analysis also fails.** The single-analyst Ukraine memo says the UK rejected the US/Albania draft, while the UK source explicitly calls for support. The central revision repeats the rejection claim and later appends a support claim while calling its initial analysis accurate. A correction must resolve the contradiction, not merely add a correct phrase. This is why stronger controls and full-answer review matter.

## Six-call diagnostic: more room versus a source check

The follow-up reuses the three exact climate synthesis prompts and frozen national notes. Both diagnostic arms allow 1,024 output tokens. One changes only the cap; the other also adds a general instruction to preserve unknown positions and verify each country before asserting common ground. It was designed after seeing the failures and is explicitly a post-hoc development diagnostic.

| Narrow diagnosed issue | Original prompts, 1,024-token cap | Added source-check instruction, same cap |
|---|---:|---:|
| UK non-approval overstated | 3 / 3 | 1 / 3 |
| Explicit unsupported all-four G-5 agreement | 1 / 3 | 2 / 3 |
| Output truncated | 0 / 3 | 0 / 3 |

These are **partial assistant-review counts on one event**, not overall quality scores. The absence of the specific G-5 assertion does not certify other compatibility or agreement claims.

All three original-prompt reruns reproduced their earlier generated prefixes exactly. The capped self-revision memo finished at 572 tokens; the other two outputs were unchanged. Increasing the cap fixed truncation without correcting the source errors.

The extra source-check instruction repaired the UK caveat in the self and peer summaries, but introduced the all-four G-5 claim in the peer summary. The single-analyst summary retained the UK error. Therefore, this instruction is not established as a better general solution. The diagnostic used 2,683 generated tokens, 60.9 seconds of generation and 16.53 GiB peak allocated memory.

## Evaluation changes implemented

- `deliberation_audit.py` replays the complete protocol from recorded outputs and rejects altered histories, missing/extra calls, changed budgets or an adapted final aggregator. It reports stopping, costs, unchanged/revised text and initial-control identity separately from quality.
- `deliberation_comparison.py` and `compare_deliberation_checkpoints.py` pair a base run with a later adapter run only when sources, protocol, model bytes, decoding, inference code and environment match. They report country/stage fidelity changes and the training-induced change in peer gain over self-revision. Unknown ratings stay null.
- Ratings now bind to the guidance hash as well as the exact response and rubric. The compact reviewer kit includes each source packet once, with links from all 42 answers. The review guidance explicitly rejects phrase matching as sufficient evidence of correction. A correct statement elsewhere does not cancel an incompatible claim still present in the answer. Earlier versus later records and source silence versus rejection require separate scrutiny.
- Nineteen focused interaction/review tests pass; the combined interaction, policy and inference suite passes 46 tests. Authored test fixtures establish software behavior, not semantic validity. The real 42-response transcript also passed exact replay.

The base/adapter comparison is implemented and fixture-tested; it has not been exercised on a new trained adapter.

## Next useful decision

Keep training deferred while these evaluation issues are resolved. Do not interpret the 5/8 changed peer answers as a gain, select a prompting method using only its target repair, or treat the ten-case fit probe as a sufficient training corpus.

The next protocol candidate should produce a short per-country claim/evidence table before drawing common conclusions, preserve unsupported positions as unresolved, and reserve enough output space for all countries and the requested analysis. Test it on these diagnosed failures **and** a new event family, then freeze the whole prompt/budget combination for both base and trained runs. An evidence quotation alone still needs an entailment check; it is not an automatic semantic validator.

**Prepared follow-up:** [Nine-case evidence-format comparison](EVIDENCE_FORMAT_CHECKPOINT_20260928.md), with three formats, a new South Sudan source family, 13 proposed source-linked criteria and passing tokenizer/validator checks. Inference is pending; no improvement is claimed from preparation alone.

Independent reviewers can now inspect concrete failure examples and the complete source-linked deck. Once source/rubric ambiguity and output handling are settled, use the already prepared two-step training smoke test and repeat exactly the frozen evaluation.

## Artifacts and compute

- [Mechanical baseline report](../reports/deliberation-999389-base-v1.json)
- [Exact source-bound failure examples](../reports/deliberation-999389-source-findings.json)
- [Six-call diagnostic and partial source reviews](../reports/synthesis-diagnostic-999389-v1.json)
- [Review deck with clarified guidance](../data/review/deliberation-999389-reviewer-kit-v1/review-deck.md)
- [Reviewer kit ZIP](../data/review/deliberation-999389-reviewer-kit-v1.zip)
- [Baseline run](../runs/deliberation-999389-base-v1/run.json) and [diagnostic run](../runs/synthesis-diagnostic-999389-v1/run.json)
- [Training handoff](TRAINING_READINESS_20260928.md)

Job **999389**, `def-zhijing`, retained one H100 on `trig0014` with `sleep infinity`. Its recorded wall limit was **19:08:16 Toronto, 28 September** and has now passed. The 19:23 access check found the multiplex socket absent and a fresh connection timed out; final scheduler state and current GPU health were not observed. The four-H100 training request remains unsubmitted. Initial node health had shown an idle H100 with 80 GB memory and BF16 support; CUDA inference succeeded. Multi-GPU/NCCL training remains unverified.

Two launch issues were diagnosed without reallocating: the health step consumed SSH/heredoc input before the next command, fixed with `srun --input=/dev/null`; the separate inference shell helper was missing from the new staged payload, then copied after the failed step was confirmed terminal. The future staging builder now includes that helper. No partial or completed model run was overwritten.
