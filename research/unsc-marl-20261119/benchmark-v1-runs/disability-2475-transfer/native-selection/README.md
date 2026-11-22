# Native selection of Resolution 2475 evidence

Frozen Qwen3.5-4B selected evidence IDs from three local menus under
fixed message capacity. Reversing display order left all three
selected sets unchanged. Russia and the UK kept both required
passages. France selected the passage about participation and safety,
leaving out its position on ratification and full implementation of
the disability convention. The source-bound renderer therefore kept
the two Russian and two UK criteria and declined the France–Russia
contrast. Full receipt released **56/70 in both orders**. The role
passages, public lead and comparison template were authored before
generation. The selector chose what to transmit from those passages.
[Protocol](protocol.md) · [Locked menus](plan.json) · [Source-bound records](scores.json)

| Selector | Correct desk sets / 6 | Sets unchanged under reversal / 3 | Full receipt, normal / reversed |
| --- | ---: | ---: | ---: |
| Whole-message likelihood | 4 | 3 | 56 / 56 |
| Pool alternative orderings of each set | 4 | 3 | 56 / 56 |
| Canonical wire spelling only | 3 | 2 | 49 / 56 |
| First available passages | 3 | 0 | 70 / 42 |
| Authored selection | 6 | 3 | 70 / 70 |

The 18 possible combinations contain one full-credit selection.
Uniform selection over them averages 50.17/70 with full receipt.
The normal positional control benefits from all key passages being
first. The reversed control exposes that dependence. Six native
selector invocations score 208 candidate token sequences. They use
1,278 prompt tokens and return 32 canonical wire tokens. Recorded
selector time is 4.76 seconds on NVIDIA RTX PRO 6000 Blackwell
Server Edition excluding checkpoint load. Inference ranks full
continuations across many spellings. The return token count describes
the selected messages rather than that decoding compute.
[Verified token and candidate logs](verified.json) · [Set-level readout](order-readout.json)

The nominal adaptive planner beats matched fixed in all 18 modeled
conditions on the native bank with a +0.1212 mean net margin and
43.57 mean released points. The learned pair forecast adds +0.0046
over nominal and wins two, ties ten and loses six. The additive
forecast adds +0.0105 and wins two with no losses. The independently
enumerated replay checks 288 policy outcomes on four distinct banks.
These are after-action score-bank replays on one exposed docket.
[Routing assumptions and results](routing.json)

The targeted follow-up supplies France with the chair's existing
public lead and a request for an instrument-specific position.
France still chooses participation under both prompt and order
conditions, leaving the 56-point full record unchanged.
[Receiver-context follow-up](receiver-context/README.md)

## Reproduce

Use the Python and SciPy variables from the
[Resolution 2475 instructions](../README.md#reproduce).

```bash
set -o pipefail
"$py" select_notes.py plan | cmp plan.json -
"$py" select_notes.py verify | cmp verified.json -
"$py" compose_notes.py score | cmp scores.json -
"$py" order_readout.py | cmp order-readout.json -
replay compose_notes.py route | cmp routing.json -
```
