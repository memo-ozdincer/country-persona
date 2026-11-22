# Replay the learned 2744 routing policy with a native chair

The trained team's advantage disappears when frozen Qwen writes the
entire record. On the same 96 simulated channel, price and prior
settings, its mean utility falls from **40.565** with the typed
renderer to **6.210** with the native writer. The strongest arrival-only
control under the native writer scores **16.001**, equal to the
content-aware oracle for that output bank.

| Final-record outcomes | Delivery-value team | Sampled-fit team | Best arrival-only | Content-aware oracle |
| --- | ---: | ---: | ---: | ---: |
| Typed reference | 40.565 | 40.391 | 39.457 | 40.565 |
| Twelve native drafts, strict release | 6.210 | 4.644 | 16.001 | 16.001 |
| Native drafts, count raw coverage | 6.210 | 4.644 | 16.001 | 16.001 |
| Native drafts, lenient disposition credit | 19.189 | 17.675 | 30.001 | 30.001 |
| Exact standalone coverage plus native relation credit | 37.513 | 37.393 | 38.349 | 38.349 |

The native writer spells out the A3+ temporal distinction. It
distinguishes the preference for a time-bound review from the
Council's continuous review intention and retains the working group's
consensus procedure and review of the twice-yearly reports. This
earns 28 of 70. It omits that Guyana spoke for itself as well as the
African members. The matched Malta draft describes a report and the
committee decision in successive sections without explicitly linking
them. It also loses the 1267 exception, consultation with the working
group and the requirement that a State recommending referral be
relevant. All twelve drafts omit at least one required adoption
detail, even though they record unanimous adoption. [Exact drafts](verified.json) · [Manual marks and evidence bindings](marks.json)

One guard failure calls the described reporting procedure a preference
and asserts it was outside the adopted requirements, even though the
operative clause was not delivered. A second guard is uncertain
about whether the condition given describes referral or approval.
Neither affected strict utility because both records already scored
zero raw points. The largest contribution to the trained team's
34.355-point gap is the Malta–authority receipt, responsible for
11.869 points. The common silence-plus-review receipt loses a further
9.461 points.

The lenient sensitivity gives every guard-clear draft the complete
adoption item for getting the unanimity and date right. The separate
standalone sensitivity gives every branch its exact factual coverage
and gives credit only for the relation Qwen actually expressed. It
is a counterfactual score table, with no repaired drafts presented as
native outputs. Even this table has no additional value from reading
receipt content. The optimized sender can use silence and arrival
to handle the single relationship that survived.

Both routing policies and all channel settings come from the prior
trained experiment. Twelve independent generations on the same frozen
Qwen3.5-4B checkpoint enumerate the receipt sets. The chair received
only the public and delivered facts. The A3+ input was narrowed from
“urged” to “hoped for full implementation” to match the official
record. The path preserves all outputs verbatim. A single assistant
graded them against a prelocked rubric. This is a live whole-record
writer test with simulated delivery and typed upstream observations.
[Prior 2744 training](../delisting-2744/README.md) ·
[Official meeting record](https://digitallibrary.un.org/record/4054820) ·
[Adopted text](https://digitallibrary.un.org/record/4054837)

All drafts finished within 160 words and 280 generated tokens.
The twelve calls used 3,587 input tokens and 1,613 output tokens on
an AMD EPYC 9575F 64-Core Processor with 12 intra-op threads.
Earlier native drafting used NVIDIA RTX PRO 6000 Blackwell Server
Edition. The benchmark release and model weights remain frozen.

[Locked protocol](protocol.md) · [Routing replay](results.json) ·
[Receipt attribution](branch-effects.json) · [Scoring sensitivity](sensitivity.json) ·
[Worker receipt](evidence/launch.json)

In the existing Aurora Qwen environment:

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B collect_chair.py plan | cmp plan.json -
python -B collect_chair.py verify | cmp verified.json -
python -B replay.py | cmp results.json -
python -B branch_effects.py | cmp branch-effects.json -
python -B sensitivity.py | cmp sensitivity.json -
```
