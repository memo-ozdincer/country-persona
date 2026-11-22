# Learn what to request in a third delivery slot

The earlier protocol can deliver at most two of three source cards.
This experiment adds one final response after the chair sees the
two opening deliveries. The opening desks act independently on
their own inventories. The chair can pay to request one absent
card. The responding desk sees its own inventory, its own intended
opening send and the request or silence. It can send one more card
in either case. Keep the same 10% loss per transmission, 0.05-point
query fee and 0.2-point delivery fee.

Run two matched 240-update joint policy-gradient fits on CPU. Both
use the same initialization and team objective. The independent
fit disables the chair's query and keeps the extra delivery slot.
Use archived Outer Space, Mali and Climate records and three
authored training profiles that require all three sources for a
complete record. Train under uniform inventories. The terminal
reward is the guarded record points plus 21 for a strict complete
record, less message costs. Report all three components separately.

UNIFIL and Myanmar are held out of the fit. Both use archived
generated and reviewed records in which only the three-card
receipt reaches the strict 70-point record. Also replay on UNAMA
and the emergency-session case, whose existing modular writer
has no strict pass with full access. The receiver sees typed
card IDs throughout. Reuse the ordinal singleton calibration,
average ties and evaluate a held-out duplicate-inventory prior.
The optimized three-send independent policy knows the revealed
test bank and prior. The centralized ceiling also sees both
inventories and can coordinate the last send without a signal.

| Case, uniform inventories | Route | Strict complete | Net return |
| --- | --- | ---: | ---: |
| UNIFIL | Learned chair query | 13.21% | 52.850 |
| UNIFIL | Learned with query erased and charged | 9.11% | 52.080 |
| UNIFIL | Learned independent | 9.11% | 52.128 |
| UNIFIL | Fixed query script | 11.16% | 52.914 |
| UNIFIL | Exact independent | 12.53% | 53.794 |
| Myanmar | Learned chair query | 13.21% | 57.875 |
| Myanmar | Learned with query erased and charged | 9.11% | 57.166 |
| Myanmar | Learned independent | 9.11% | 57.215 |
| Myanmar | Fixed query script | 11.16% | 57.897 |
| Myanmar | Exact independent | 12.53% | 58.562 |

Disabling the third send gives zero complete records on both
cases. Under correlated inventories the learned route reaches
10.46% strict on both, compared with 4.10% for the matched
independent fit and 10.65% for the exact independent policy.
The learned query improves complete-record probability against
fitted and scripted controls. Exact independent delivery still
has higher net return on both cases under both priors. It often
preserves a higher-scoring partial record when full coverage fails.
Neither writer-limited case can produce a strict record.

## Diagnose the first two sends

Freeze the learned opening choices. Enumerate all 864 legal
chair tables and optimize the responder for each table under
the evaluation bank and prior. Under uniform inventories this
raises UNIFIL to 54.166 and Myanmar to 58.893. Starting with the
exact independent opening and doing the same tail optimization
reaches 54.898 and 59.401. Both use test information. Independent
enumeration of physical deliveries and request erasure verifies
the analytic evaluation. The diagnostic shows that using the chair
signal better can close the net gap, and that the opening choices
can still constrain the ceiling.

Then alternate exact opening and tail optimization on the original
fitting bank. Compare the earlier gradient fit and the exact
independent training policy as initializations. Select using
the fitting return. The gradient initialization wins, and its
exact block update adds under 0.007 held-out net points on
both uniform full-record cases. The optimization method alone
does little to close the transfer gap under this fitting objective.

[Training and transfer results](fit.json) · [Fixed-opening bounds](attribution.json) ·
[Fitting-only block optimization](block-fit.json)

```bash
OPENBLAS_NUM_THREADS=1 python facilitator_third_delivery.py > fit.json
OPENBLAS_NUM_THREADS=1 python facilitator_third_delivery_attribution.py fit.json
OPENBLAS_NUM_THREADS=1 python facilitator_third_delivery_blocks.py fit.json
```
