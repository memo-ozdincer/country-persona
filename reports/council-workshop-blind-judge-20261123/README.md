# Blinded regrade of the archived climate clauses

A fresh GPT-6.1-Sol reviewer scores the exact two final clauses from the
three-seat climate workshop. It receives the same dated excerpts,
six-item rubric, and clause-only instruction used for the
[archived retrospective grades](../council-workshop-clause-review-20261123/README.md).
The input omits generating model names, meeting outcomes, ballots and
transcript. Each call receives one clause and uses the existing quote
validator. The model identity, packet order, and input texts were fixed
in [packets.json](packets.json) before review.

The guard control appends a fabricated claim of formal unanimous
Security Council adoption to one clause. It is an authored test fixture.
The clause content and source excerpts otherwise stay the same. The
validator checks exact spans and source scope, and a failed guard
withholds the released score.

| Original clause or control | Archived grade | Blinded grade | Guard | Released points |
| --- | ---: | ---: | --- | ---: |
| GPT-6.2-Sol | 40/70 | 40/70 | Clear | 40 |
| GPT-6.2-Astra | 35–40/70 | 35–40/70 | Clear | 35 |
| Sol clause with authored false adoption claim | — | 40/70 | Failed | 0 |

The blinded reviewer reproduced all **12 of 12 criterion labels**.
It marked France's scope criterion uncertain for the Astra clause.
That clause names regions or issues under consideration and leaves the
link to existing Council mandates implicit. The Sol clause makes that
link explicit. In the control, the reviewer quoted the added false
adoption claim and kept the policy coverage score at 40. The factual
guard withheld all released points.

This measures one model review per clause and one authored guard check.
Both clauses come from the same workshop and use the same frozen rubric.
The reviewer is from the Sol model family. The archived comparator is
an assistant annotation.

[Sol clause verdict](record-01.json) · [Astra clause verdict](record-02.json) ·
[Authored guard verdict](guard-control.json) · [Exact comparison](score.json)

## Replay

```sh
set -o pipefail
out=reports/council-workshop-blind-judge-20261123
python3 -B "$out/blind-review.py" build | cmp "$out/packets.json" -
python3 -B "$out/blind-review.py" score | cmp "$out/score.json" -
```
