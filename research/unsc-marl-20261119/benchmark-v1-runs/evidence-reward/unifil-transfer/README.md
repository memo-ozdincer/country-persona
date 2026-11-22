# Transfer the first responder to a different UNIFIL workshop

Resolution 2695 extended UNIFIL's existing mandate through August
2024 after a 13–0–2 Security Council vote. The public resolution and
meeting are the historical anchor. The reserve accession links the
same draft and vote to both benchmark datasets. The new four-option
menu concerns a fictional informal briefing schedule. Its cells
form an incomplete three-by-two design. The worlds include a unique
agreement, an impasse and three simultaneous valid agreements.
[Official resolution](https://digitallibrary.un.org/record/4020194) ·
[Vote and statements](https://digitallibrary.un.org/record/4020309) ·
[Dataset linkage](../../../crossbench/unifil-reserve.json) · [Workshop cases](case.json)

## Freeze the Iraq and Syria first-stage weights

Replay all 6,144 truthful opening and query presentations across
the three UNIFIL worlds. They are an exhaustive audit of one
event family. The labels and signs are controlled. At 0.80 delivery,
the frozen head seizes all 464 opportunities to add a proof but
sends 2,279 replies that add no record value. It also misses 137
replies that would complete attribution after a proof already
exists. The proof-only rule avoids the waste, while the record
oracle also recovers the extra documentary value.

| Reply policy, delivery 0.80 | Sends | Total incremental net |
| --- | ---: | ---: |
| Frozen Iraq/Syria ledger head | 2,812 | 243.50 |
| Proof-only rule | 464 | 314.64 |
| New value tree fitted on synthetic cases | 676 | 340.18 |
| Exact oracle for the record proxy | 670 | 340.39 |

Net estimates the gain of an additional sign under normalized
coverage and fixed cost. A newly certified record may still lack
complete mandate attribution. A single 14-point item captures
that loss in the proxy. This transfer does not score written
final records and preserves all v1.1 case and release files.
[Frozen-head audit and exact controls](audit.json) · [Transfer protocol](protocol.md)

## Test whether the features can represent the new choices

At 0.80 delivery, 15 distinct groups contain identical original
inputs that require different actions. A deterministic policy on
those observations must make at least 194 action errors. Its
best possible aggregate net on this audit is 323.13, 17.26 below
the record oracle. Adding how many possible mandates remain for
both roles and how many are consistent with the contemplated
verified sign removes all mixed-action groups. This is a held-label
analysis of the observation interface and gives no deployment
result by itself. [Feature collisions and matching witnesses](alias.json)

## Fit the delivered record value on synthetic workshops

Fit a depth-six regression tree on 32,768 paths drawn by enumeration
from the original sixteen synthetic worlds. The tree sees counts
derived from public signs and the locally verified reply. It
predicts the delivered record increment. The policy multiplies
that increment by delivery probability before subtracting the
fixed fee. UNIFIL remains fit-excluded.

On the UNIFIL menu at 0.80 delivery the tree makes six errors in
6,144 presentations, all unnecessary sends in impasse states. It
trails the oracle by 0.21 total net. At 0.04 delivery the frozen
head earns −77.172 and the new policy earns 0.820, versus 1.060
for the exact rule. All 80 low-delivery errors come from treating
partial-credit impasses as full-credit outcomes. The prior
synthetic menus cover fewer candidate-count patterns. The held audit
contains 556 presentations whose feature combinations were absent from fitting.

These results are transfer of trained decisions under published
simulator rules. Cases share one historical event and repeated
public states. There are no new Qwen calls, written briefs or
independent judgments. [Fit protocol](transfer-fit-protocol.md) ·
[Tree and holdout results](transfer-fit.json)

## Verify

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1
python3 audit.py | cmp - audit.json
python3 alias.py | cmp - alias.json
python3 transfer_fit.py | cmp - transfer-fit.json
```
