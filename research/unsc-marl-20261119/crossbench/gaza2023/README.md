# October 2023 Council draft and amendments

This is one event family, built around meeting S/PV.9442 on 18 October 2023. Brazil submitted draft S/2023/773. Two Russian amendments failed to reach the vote threshold before the main draft was vetoed. The three drafts are present in the pinned UNBench release. The 15 votes on the main draft match the pinned UNSC-Bench row and the official roll call. Amendment procedure comes from the official meeting. Each backup contains a paraphrase of its UNBench instrument or the identified explanation of vote. [Official meeting](https://digitallibrary.un.org/record/4025062/files/S_PV.9442-EN.pdf) · [Council special report on the veto](https://digitallibrary.un.org/record/4025059/files/A_78_549-EN.pdf)

## Local views and score

The four possible focal slips concern the first amendment, the second amendment, the Brazil draft's humanitarian access provision, or the U.S. explanation. The requester knows one focal slip and forwards it over a protected channel. The responder holds exactly two of four backup annexes in an unordered inventory. It sees the request delivery bit and its inventory. It always sends one annex. The requester chooses silence or one generic certified-file request, which is unavailable by construction. Sending it can convey information about the focal slip. The responder sees the same text whenever the request arrives. The distribution of cards and signal losses is simulated.

A common paragraph contributes 35 points. The focal slip can support one 7-point criterion. A matched backup can support four additional 7-point criteria. The type-level calculation treats a complete match as mechanically available evidence. It includes separate ten percent loss for the question and reply, a 0.05-point request fee and a 0.2-point reply fee. The full-information upper bound observes the focus and both backups for free and still bears reply loss and cost.

## Controls and preflight

- **Silent pair** optimizes a local responder action for each inventory using the true evaluation prior. The chair still receives the protected slip.
- **First or other** chooses a global reply priority. An observed request changes to the other annex. Its requester may use any of the 16 possible mappings from focal slips to request decisions.
- **Priorities by request** selects a separate complete ordering for each request state. It optimizes both orders and the requester jointly under the evaluation prior. This includes all 576 ordered pairs of rankings per requester.
- **Exact interactive** can choose independently for each of six responder inventories and two request receipt states. Its solution is independently checked over all 65,536 deterministic joint policies. This is also the performance of a fully flexible Bayesian script with the evaluation prior.

The three named correlated priors are diagnostic stress cases. Their integer counts were chosen in three seeded blocks of 1,500 draws from 1 through 29, retaining the largest gap between exact interaction and the best priority scripts in each block. The exploratory generator used NumPy seed 907. The uniform prior and six separate seed-170524 draws were included without selection. The named diagnoses are case-development fixtures. All ten distributions use the same one historical event family.

The fit takes 96 CPU updates from one seeded initialization. It uses the exact expected team return on one correlated development prior. The two policies have separate local logits. Their forward pass at execution uses only the local observations. Exact scripts frozen on the same prior give a matched-data transfer control. The separately reoptimized script columns receive the evaluation prior.

## Reproduction

Use the existing environment with PyArrow and the project package for accession. Use the established Qwen CPU environment for exact replay, team fit and writer scoring.

```bash
PYTHONPATH=../../../../src "$DATA_PY" check.py
"$MODEL_PY" routing.py
"$MODEL_PY" fit.py
"$MODEL_PY" score.py writer-evidence writer-evidence/annotations.json
```

The writer bank conditions on the fixed public paragraph and each particular focal slip. Only a matching admitted backup is exposed. The chair has exact source IDs in this test, so an irrelevant backup is deterministically withheld. A separate 85-word supplement is written under the same 160-token generation cap for each focal slip with and without that backup. Policy comparisons replay those same final records across the declared loss, priors and fees. This isolates routing under controlled content and uses Qwen3.5-4B for writing. It uses same-assistant exact-span annotations. The bank is neither natural historical dialogue nor independent adjudication. The reported process concerns signal transmission and coverage of the delivered source.

## Paired writer and routing follow-up

`scoped_writer.py` changes the system message only. Its eight writer prompts keep the original payload and cap. `scoped-evidence` preserves the original launch error separately from the successful generation, followed by token-level replay and exact-span review.

`compile_record.py` provides a docket-specific extractive control. It renders the same available slip and, where admitted, the original matching backup. It uses only fixed labels, the approved slip wording and the backup text. The aid focus's requirement to distinguish a separate ceasefire cannot be verified from that focus's evidence. The replay therefore credits a matched aid backup for three rather than four criteria and recalculates the attainable routing ceilings.

`prior_blind.py` fits the best prior-blind mixture for each exact menu under identical training information. It uses linear programming and certifies both objectives through the dual probabilities on the development priors. The generated records play no role in mixture selection.

`guard_judge.py` uses the same frozen Qwen3.5-4B for a separate blind guard calibration. It removes system identity and coverage keys from the evaluation payload. It tests each of the 16 original or scoped records and four authored controls twice, swapping the codes for clear and failed. `guard-evidence` stores all 40 outputs, the checked token trace and agreement against the authored or same-assistant reference labels. Stable agreement with both orders is a diagnostic for prompt sensitivity. It does not establish independent accuracy.

## Unfamiliar partner calibration

The same binary question can have opposite meanings in two successfully trained teams. The calibration diagnostic collects evidence about a partner using public dummy focus cards. A probe reveals only an observed request bit, so an observed silence can still come from a lost request. Charge for the probe and any attempted question. Simulate amortization across one, eight and 32 mission records. The active sampler uses exact expected future record value and cannot see the mission's real focal slip or evaluation prior. Each oracle is labeled by what information it receives.

Two CPU-trained receivers use the same fixed four-probe deck and team reward. The factored receiver treats the probe result for each possible annex separately and shares likelihood weights across annexes. Train on the eight even-parity schedules, evaluate on the eight odd-parity schedules and report individual results on every availability prior. The fixed-probe script changes no observations or fees. The probe-label intervention preserves the delivered bits and changes only which focal cards they describe. The synthetic schedule population and compiled receipt scores delimit this test.

```bash
"$MODEL_PY" calibrate_partner.py
"$MODEL_PY" train_calibrator.py
"$MODEL_PY" factored_calibrator.py
"$MODEL_PY" calibration_behavior.py
```
