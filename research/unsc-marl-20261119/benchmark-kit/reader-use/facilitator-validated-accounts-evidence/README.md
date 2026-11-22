# Validate each national account before joining the record

Frozen Qwen3.5-4B retrieved the three field witnesses separately for Ecuador, China and Russia. The three paired controls each remove the sentence for the middle field. All returned EMPTY at that field. The six calls consumed 1,202 input tokens and 287 generated tokens. The mechanical checker requires the corresponding pre-reviewed source sentence at each field and requires it to be present in the actual input. It uses fixed reviewed prose for admitted accounts and the two-abstainer comparison. The model selects evidence. The final prose and criterion map are authored for this docket. [Prospective protocol](protocol.md) · [Raw model replies](final-records.json)

| Writer or checker | Distinct evidence views releasable | Full view |
| --- | ---: | ---: |
| Fixed public record with national rewrite | 3/8 | 0 |
| Exact source sentence gate | 8/8 | 63 |
| Gate with apostrophe equivalence | 8/8 | 70 |

The locked strict gate rejected the entire Ecuador account because all three returned lines substituted straight apostrophes for the source's right quotation marks. The post-run audit maps that single character to a straight apostrophe for comparison, rechecks the source membership predicate, and admits all nine original fields. The original responses are unchanged. Both checks reject every absent controlled field. A failed account appears as withheld in artifact metadata. The renderer emits the abstainer comparison only when both approved accounts were received. This evaluation does not estimate a general semantic judge's detection of unsupported claims. [Strict witness scores and all rendered records](results.json) · [Punctuation audit and release changes](apostrophe.json)

## Return of the request incentive

Under the sender-attributed replay, the score-known requester improves net points over the identical no-request team in all four opening conditions. With strict extraction the gains are +0.050 to +1.657. With the punctuation equivalence they are +0.323 to +2.753. The normalized bank raises complete-record probability by 0.9 to 6.2 percentage points over no requests. The exact extraction bank never receives completeness credit because the Ecuador account is unavailable. Both replays hold the independent third send and simulated transport fixed. The gain belongs to the score-known planner. [Strict replay](replay.json) · [Punctuation-equivalent replay](replay-apostrophe.json)

## Transfer of earlier MARL fits

In the separate receipt-mask channel environment, replay the two saved joint request/reply policies fitted for 240 updates on other families. Use the archived declared rewards as policy inputs. The earlier national rewrite makes the clean fit worse than the exact no-request baseline. The punctuation-equivalent writer restores a clean fit advantage over the exact no-request baseline of 0.763 points under the uniform prior and 0.315 under correlated inventories. It asks in every opening state with positive probability, falls 0.118 and 0.164 points short of joint exact planning, and trails its own unfitted initialization under the uniform prior. The robust fit never asks and ties the no-request baseline. Erasing its request content changes nothing.

| Policy on the punctuation-equivalent bank | Uniform net | Correlated net |
| --- | ---: | ---: |
| Exact no-request | 58.562 | 56.506 |
| Clean initialization | 59.342 | 56.522 |
| Clean trained | 59.325 | 56.821 |
| Robust trained | 58.562 | 56.506 |
| Joint exact | 59.443 | 56.985 |

A component swap with the robust responder held frozen restores 0.791 and 0.369 points after optimizing only the requester. Optimizing only the robust reply policy gives zero gain. For the clean fit, both swaps help and neither closes the gap to joint exact optimization. This suggests a focused training comparison under matched transport and writer conditions, with request costs retained and a strong no-request policy as the baseline. All the results concern one exposed UN case, authored evidence criteria, simulated transport and archived learned weights. No optimizer updates or live deliberations ran here. [Prospective transfer contrast](policy-protocol.md) · [Trained-policy transfer](transfer-apostrophe.json) · [Component swaps](swaps-apostrophe.json)

## Reproduce from the parent directory

```sh
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
evidence=facilitator-validated-accounts-evidence
python facilitator_validated_accounts.py score "$evidence"
python facilitator_validated_accounts_apostrophe.py "$evidence"
python facilitator_validated_accounts_replay.py "$evidence/results.json"
python facilitator_validated_accounts_replay.py "$evidence/apostrophe.json"
python facilitator_validated_accounts_transfer.py "$evidence/results.json"
python facilitator_validated_accounts_transfer.py "$evidence/apostrophe.json"
python facilitator_validated_accounts_swaps.py "$evidence"
```
