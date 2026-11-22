# Transfer the receipt-conditioned selector to Resolution 2553

On 3 December 2020 the Council adopted the South Africa-led draft
on security sector reform by a unanimous written vote. The case
records national ownership, host perspectives on mandates and
voluntary support. It preserves the UK and Germany's concerns about
the negotiation process, Germany's statement on authority over the
Peacebuilding Fund, and Belgium's emphasis on inclusive reform and
predictable funding.
[Written vote](https://digitallibrary.un.org/record/3893789/files/S_2020_1166-EN.pdf) ·
[Explanations, annexes XVII–XIX](https://documents.un.org/api/symbol/access?l=en&s=S%2F2020%2F1167&t=pdf) ·
[Adopted resolution](https://digitallibrary.un.org/record/3893781/files/S_RES_2553_%282020%29-EN.pdf)

UNBench author-test event 2359 matches all 15 official votes.
The pinned UNSC-Bench adopted split has no match by resolution,
draft or written vote record. The published case family was new
to these experiments. Its source blocks, menu, 12 criteria and
policy contrasts were locked before the transfer run. The original
selector coefficients were fitted on synthetic tasks. The actors
receive authored score features. The official v1.5 suite stays fixed.
[Source join](provenance.json) · [Case and rubric](docket.json) ·
[Protocol](protocol.md) · [Locked inputs](plan.json)

## Documentary transfer

A full-source control earns 70/70 in 174 words. In the one-passage
workshop, the best simultaneous full-receipt selection can earn 45/70.
The branches rely on documented national statements. The one-passage
capacity, private inventory draws and independent delivery rates are
simulation choices.

When all claims are available, every policy ties the adaptive and
static oracles at all four rates and in both orders. The best policy
can send the independent institutional points and their
cross-source inclusion comparison. It receives no extra benefit from
waiting for peer evidence. Nominal release ranges from 27.6125 at
0.35 receipt to 43.5125 at 0.95.

When the earlier desk has only one privately available claim, the
adaptive ceiling changes. The exact content oracle sees the received
claim. The exact arrival oracle sees a delivered bit and knows the
same prior. Their difference measures the value of learning which
claim arrived, before charging any broadcast cost.

| Choice order | Oracle content gain over arrival, mean / range | Frozen learned gain over best arrival | Frozen losses to best arrival | Frozen ties with content oracle |
| --- | ---: | ---: | ---: | ---: |
| UK chooses after Germany | +0.0916 / 0 to 0.2836 | +0.0070 | 3/12 | 9/12 |
| Germany chooses after the UK | +0.3938 / 0.0613 to 0.9025 | +0.2680 | 2/12 | 10/12 |

The learned and equally informed fixed selectors use the same
actions in all 24 private conditions. Sharing the passage helps
more when Germany chooses later under the locked menu and score
weights. The information benefit is visible even though the
learned coefficients provide no additional improvement.
[Records, policy tables and 288 independent dispatch checks](results.json)

## Which desk needs to adapt?

When the UK chooses later, the three losses occur at 0.95 receipt.
Both policies switch to the process objection after the matching
German passage arrives. The exact UK response instead keeps its
inclusion passage because it expects Belgium's inclusion note too.
Changing just the UK's plan fixes all three conditions.

When Germany chooses later, the two losses occur at 0.75 and 0.95
receipt with a 0.75 prior on the UK process card. Belgium's frozen
forecast prefers its funding passage. Against Germany's actual
response, switching Belgium to inclusion gives the best payoff.
Replacing just Belgium's plan fixes both conditions. In either
update order one best response per desk reaches the content oracle
in all 24 conditions. This is a diagnostic with exact source-valued
returns and the known simulation law. It shows why one correction
to the listening desk alone cannot solve both orders.
[Component swap protocol](repair-protocol.md) · [Exact swaps](component.json) ·
[Preparation notes](preparation.md)

This transfer confirms an interaction opportunity for the private
variant of a newly evaluated public docket. The observed mean
advantage over the best arrival policy depends on order and on
predicting how other desks react. The trained policy matches the
fixed policy here. The experiment treats delivery and the receipt
broadcast as simulated and cost-free, uses authored statements and
source-bound scoring, and leaves natural-language extraction and
independent judgment unmeasured.

## Reproduce

Use the environment and Python paths from
[Resolution 2475](../disability-2475-transfer/README.md#reproduce).
Run from this directory with Bash pipe failure enabled.

```bash
set -o pipefail
"$env_root/open-character-20261004-v1/bin/python" -B join_sources.py | cmp provenance.json -
"$py" transfer.py plan | cmp plan.json -
"$py" transfer.py run | cmp results.json -
"$py" component_swap.py | cmp component.json -
```
