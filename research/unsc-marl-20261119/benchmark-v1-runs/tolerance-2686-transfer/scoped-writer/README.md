# Source-scoped chair on Resolution 2686

A native Qwen3.5-4B public paragraph followed by the three archived
delegation notes earns **63/70 at exactly 175 words**. All 16 records
across the two rendering methods and eight receipt sets pass the word cap
and guard. Rewriting each note in a separate call earns **56/70 at 162
words** with all three notes. Both avoid merging the Swiss covenant
omission with the women's rights proposals. The rewritten France note
drops its recommendation to use the General Assembly and Human Rights
Council. The UK note does not explicitly keep the conflict scope on the
minority persecution concern, as required by the original criterion.
[Fixed protocol](protocol.md) · [Raw output](evidence/calls.jsonl) ·
[Exact quote marks](scores.json)

| Full receipt record | New chair calls | Word count | Raw / released points |
| --- | ---: | ---: | ---: |
| Original free-form writer | 1 | 190 | 35 / 0 |
| Revised free-form writer | 1 | 109 | 7 / 0 |
| Generated public lead and scoped rewrites | 4 | 162 | 56 / 56 |
| Generated public lead and verbatim notes | 1 | 175 | 63 / 63 |
| Earlier authored public lead and verbatim notes | 0 | 174 | 63 / 63 |

All arms reuse the three archived notes as inputs or verbatim fragments.
The public call has access to the same historical blocks as the
free-form writer, without the three notes. The four-call arm assigns
one note per rewrite and shares a combined 288 decoded-token ceiling
with the first two rows. The **one-call verbatim arm** uses 308 input
and 86 output tokens for its public lead. The four calls together use
730 input and 231 output tokens. These counts exclude the three common
archived notes. All native calls complete. Measured generation time is
3.80 seconds for the public call and 6.10 seconds for all four on
NVIDIA RTX PRO 6000 Blackwell Server Edition, excluding checkpoint
load. The owned worker exited successfully. There were zero updates.

The generated public paragraph is 47 words, one above its local prompt
target. The release rule uses the frozen final cap. The annotations
credit the operative criterion as written because it asks for the call
to publicly condemn discriminatory violence, hate speech **or**
extremism with the legal limit. The paragraph explicitly names violence
and hate speech. Case authors, primary sources, membership and scoring
criteria come from the original docket. A single assistant reviews
the reusable source-specific fragments. The program projects those
judgments to opaque final packets and verifies exact quotes and source
ownership. The generic contrast connective is the only authored text
in the new renderings. No primary source wording or answer text is
inserted after generation.
[Inputs, all 16 records and token evidence](verified.json)

## Routing replay

The scoped rewrites produce mask-order grades **21, 28, 35, 42, 28, 42,
49, 56**. The generated lead with verbatim notes produces **21, 35, 35,
49, 28, 49, 49, 63**, exactly matching the earlier authored-lead result.
The latter routing comparison therefore reproduces the earlier result
with an independently generated public paragraph. The transport law,
inventory assumptions, review offsets and information available to
each planner are shared. The net metric subtracts the modeled channel
cost. Native inference usage is reported separately above.

| Writer bank | Adaptive wins / losses / ties over matched fixed | Mean net difference | Adaptive mean released points | Fixed mean released points |
| --- | --- | ---: | ---: | ---: |
| Original free-form | 8 / 0 / 10 | +0.0558 | 22.65 | 22.62 |
| Scoped rewrites | 14 / 2 / 2 | +0.0773 | 40.70 | 40.64 |
| Generated public lead and verbatim notes | 18 / 0 / 0 | +0.1428 | 44.31 | 44.20 |

The scoped planner falls below informed silence in two conditions. The
verbatim arm stays above or equal to informed silence in all 18 and
also beats fully informed fixed targeting in all 18, with a +0.0670
mean net difference. Independent branch enumeration verifies all 108
policy-condition outcomes across the three banks. The frozen learned
score forecast improves over its neutral counterpart in nine conditions
on the scoped bank, loses one and ties eight. Its mean gain is +0.0834.
It improves by +0.0040 on the verbatim bank. The strongest absolute
released result still uses the verbatim writer and the robust planner.
[Routing replay](routing-readout.json) · [Scoped policy tables](scoped-route.json) ·
[Verbatim policy tables](verbatim-route.json)

The larger change here comes from preserving information in the final
record. The delivery advantage is measured in simulations on one exposed
docket. Same-assistant grading, archived delegations, a fixed connective
and modeled private inventories limit the result. The one-call rendering
makes it possible to test the learned and matched fixed policies on
a stronger writer without another free-form synthesis bottleneck.

## Reproduce

Use the Aurora environment and set up `replay` from the
[parent reproduction instructions](../README.md#reproduce). Run in this
directory.

```bash
set -o pipefail
"$py" scoped_writer.py plan | cmp plan.json -
"$py" scoped_writer.py verify | cmp verified.json -
"$py" score_scoped.py | cmp scores.json -
for arm in scoped verbatim; do
  jq --arg arm "$arm" '.banks[$arm] | {score_bank: .}' scores.json | cmp "$arm-bank.json" -
  replay ../route_tolerance.py --scores "$PWD/$arm-bank.json" | cmp "$arm-route.json" -
done
replay routing_readout.py | cmp routing-readout.json -
```
