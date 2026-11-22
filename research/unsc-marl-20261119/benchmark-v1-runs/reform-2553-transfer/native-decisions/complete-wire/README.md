# Complete JSON scoring for native receipt decisions

The matched comparison replays all 24 original Resolution 2553
contexts. It replaces the one-token letter with a one-ID JSON array
and preserves the local passages, receipt view, roles, weights and
public delivery information. Each context swaps which card the two
aliases name. Complete candidate likelihoods include termination and
are pooled over permitted spellings. The primary decoder then averages
mapped margins across the two prompts.
[Protocol](protocol.md) · [Frozen requests](plan.json)

The main JSON decoder agrees across the two aliases in **6 of 24**
contexts. Canonical-only scoring agrees in **3 of 24**. The original
letter decoder agreed in zero. The extra agreement does not improve
the main documentary outcome. The JSON decoder always chooses the
higher standalone passage for the later desk in the content arm.
It also chooses the funding passage for Belgium, where the original
letter decoder used an inclusion fallback.

| Decoder | Mean with passage content | Mean with arrival only | Mean without feedback |
| --- | ---: | ---: | ---: |
| Original mapped letter margins | 36.6055 | 35.7578 | 35.7578 |
| Complete JSON, pooled spellings | 34.6313 | 35.3844 | 34.6313 |
| Complete JSON, canonical spelling | 35.4113 | 35.2606 | 35.2369 |
| Pooled JSON with forecast in the UK high-delivery cell | 35.3081 | 34.8203 | 34.6313 |
| Informed oracle | 36.7325 | 36.5109 | 36.3686 |

The two-role cross identifies both sources of the loss. Swapping only
the later desk from letter to JSON reduces mean content release by
0.848 points. Swapping only Belgium reduces it by 0.935 points.
Swapping them together reduces it by 1.974 points. Increased
agreement at the wire level therefore does not replace tests of
which evidence each desk sends.
[Matched role swaps](role-replay.json)

## Target the UK high-delivery decision

The ten additional prompts supply the public fixed forecast that
Belgium would choose the inclusion passage. They preserve the
original UK and Germany menus and vary only that additional field.
The UK switches to its process passage on receiving Germany's
process passage. Belgium's native JSON choice remains funding.
With the actual traced Belgium choice, the switch raises release by
2.7075 points in that condition. If Belgium instead sends the forecast
inclusion passage, the same switch loses 0.5077 points. The tested
addition therefore does not produce a policy that acts correctly
under its own stated partner forecast.

The complete-message run uses 58 calls, 464 scored sequences,
26,976 input tokens and 232 returned wire tokens. It takes 14.37
seconds of measured inference on NVIDIA RTX PRO 6000 Blackwell
Server Edition, excluding checkpoint load. All calls complete.
The score report includes 276 checked policy outcomes across
decoding and input branches. The role cross is a separate
post-result replay using the same source records. The evidence
covers an exposed authored docket with simulated delivery and
zero optimization updates.
[Verified outputs](verified.json) · [Source-value replays](scores.json)

## Reproduce

Use the Aurora Python setup in the [parent run](../README.md#reproduce).
Run from this directory with Bash pipe failure enabled.

```bash
set -o pipefail
sha256sum -c analysis.lock
"$py" wire_decisions.py plan | cmp plan.json -
"$py" wire_decisions.py verify | cmp verified.json -
"$py" replay_wire.py | cmp scores.json -
python3 -B cross_decoders.py | cmp role-replay.json -
```
