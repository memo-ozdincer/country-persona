# Conservative adaptation on source-reviewed UN record banks

Translate the workshop request rule to six archived sets of documentary records. Each record is scored for the receipts it contains. Use authorized copies and fixed record assembly, with two simulated desks whose actual topic preferences are unknown to the chair. Evaluate all inventory and loss outcomes under both priors. The deposited grades from the workshop become sourced documentary cards in this experiment. [Initial protocol](protocol.md) · [Archive and role tests](results.json)

**Logical compatibility supplies no learning signal in this setting.** Each desk could hold only the observed topic. That singleton forces every allowed policy to choose it, so all 24 local tables survive every ordinary receipt history. The support-only requester ties its baseline. The request-only model also gives the optimized independent sender a stronger third-slot action set. Independence beats the known-partner request-only planner on average in every bank.

## Match the third send and use receipt frequencies

The revised protocol gives the right desk a fixed independent third send. A delivered request substitutes a different held document when available. Compare a default requester that assumes uniform choices, a posterior-mean requester, and the baseline-relative rule with a likelihood-based region of plausible partner tables. An equal-weight mixture likelihood provides the rejection threshold. Under the stated model, the chance of excluding the true table at a fixed prefix is at most 5%. This is uncertainty about the model of disclosure, with the true reward table and the prior as separate assumptions. [Frequency protocol](frequency-protocol.md) · [Implementation](../facilitator_conservative_frequency.py)

At 64 histories, the region retains about 48–53 of 576 possible table pairs on average, depending on the docket. The conservative rule still improves the declared baseline by less than 0.00023 net points per docket. The fitted posterior alone changes more requests. Its mean net on the emergency docket falls from a 39.782291 default to 39.021331, because the declared rubric credits outcomes that the reviewed records do not supply. With assessed scores available, the default uses the independent send and reaches 40.276713 there. No sampled 64-history case excludes the true partner table. [Complete request, completion and uncertainty scores](frequency.json)

The strongest independent control can optimize its third send using the actual partner tables and reviewed scores. Under declared planning, it exceeds the true-partner requester with only the nominal fallback on three of six banks. Keep that comparator separate from no-request replay with the same fallback.

## Review the public and singleton records

| Archived record bank | Declared rubric | Public and singleton review | All eight receipt views reviewed |
| --- | ---: | ---: | ---: |
| UNAMA | 46.220709 | 47.356093 | 47.356093 |
| Emergency session | 39.782291 | 40.276713 | 40.276713 |

This calibration changes the declared offset and individual source contributions using four of the eight previously reviewed records. It preserves the declared interaction terms. The four other archives already agree with the public scores. In an authored UNIFIL control, move a pair bonus while keeping the public, singleton and full scores fixed. The four-record calibration cannot see it, and scores 50.652814 against 52.014993 when all scores are available. Other shifted-pair controls also preserve the anchors and change the request. The complete score table guides a nominal-partner planner, and policy evaluation still depends on actual opening behavior. [Calibration design](calibration-protocol.md) · [Real archive and synthetic pair controls](calibration.json)

This work uses reviewed archival excerpts and deterministic record banks. Custody, receipt histories and pair-bonus controls are simulated. The sample offers evidence that reward calibration can matter more than modeling the partner, while independent review and natural-language deliberation remain outside this experiment.

## Replay

From `benchmark-kit/reader-use`, use the project Python environment.

```sh
OPENBLAS_NUM_THREADS=1 python facilitator_conservative_archive.py
OPENBLAS_NUM_THREADS=1 python facilitator_conservative_frequency.py
OPENBLAS_NUM_THREADS=1 python facilitator_conservative_archive_calibration.py
OPENBLAS_NUM_THREADS=1 python facilitator_conservative_archive_audit.py
```
