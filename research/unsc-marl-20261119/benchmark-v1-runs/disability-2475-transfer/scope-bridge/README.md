# Cross restored notes with a scope-check prompt

The first Resolution 2475 experiment could not tell whether the
comparison writer would preserve the scope distinction after receiving
accurate notes. This follow-up crosses an evidence restoration with
a prompt change. It reuses the earlier Qwen notes and the compact
authored control, withholding the control's comparison sentence.
Each prompt sees the same text within each pair. Both use the
same frozen Qwen3.5-4B checkpoint and 60-token decode limit.
At every receipt set, the writer can see only the selected notes.
[Protocol](protocol.md) · [Frozen requests](plan.json) ·
[Parent case and sources](../README.md)

## Live result

The restored evidence supplies both original positions. Neither prompt
states the required France–Russia comparison: France's call concerns
ratification and implementation of the convention, while Russia's
reading limits a paragraph of the Council resolution. The generated
sentences instead contrast ratification or participation with a
different Russian objection to new legal categories. On both restored
full records, the comparison also assigns that Russian objection to
the UK. The UK statement agrees on avoiding new legal obligations.
Those propositions are scored separately.

On the original Russia–UK notes, the scope prompt preserves the
distinction between the two objections and clears the factual guard.
The earlier plain prompt changed a limited reading of the resolution
into a limitation on the underlying convention. A separate source
reader still has to establish semantic correctness. The writer's
instructions and shared source text cannot act as that review.

| Notes and bridge prompt | France + Russia | Russia + UK | All three |
| --- | ---: | ---: | ---: |
| Original notes, no bridge | 0 | 21 | 0 |
| Original notes, plain | 0 | 0 | 0 |
| Original notes, scope | 0 | 21 | 0 |
| Restored notes, no bridge | 42 | 56 | 63 |
| Restored notes, plain | 42 | 56 | 0 |
| Restored notes, scope | 0 | 56 | 0 |
| Authored scope comparison control | 49 | 56 | 70 |

Entries are released points out of 70 under the locked rubric. The
authored scope comparison control comes from the prior experiment.
None of the 12 model-generated comparison sentences adds raw
criterion credit above the matching verbatim record. In the restored
France–Russia pair, the scope prompt's phrase about categories "within"
the disability convention falsely attaches a separate Russian objection
to that treaty. The original and scope prompts both fail the guard on
the restored full record. Every native France record also retains the ambiguous wording about
who ratifies the convention.

Nine new Qwen3.5-4B calls complete. They use 1,709 input tokens and
175 output tokens in 7.67 seconds of measured generation, excluding
checkpoint load, on NVIDIA RTX PRO 6000 Blackwell Server Edition.
Three bridge responses are exact archive reuses. All bridge responses
fit the 27-word target. The scorer projects six banks and 48 records
into 28 unique opaque packets. The same assistant adds marks to the
nine new packets containing comparison sentences, retaining the prior
source judgments for their base paragraphs. No optimizer updates or
text edits were made.
[Native and reused responses](verified.json) · [Source judgments](scores.json)

## Routing replay

All three forecast rules produce identical outcomes on each of the
three native banks. On the authored no-bridge bank, the learned
correction improves the nominal planner by +0.0158 net points and
the additive rule by +0.0178. Adding either generated bridge to the
authored notes reduces nominal mean release from 46.40 to 39.37
or 40.54. The plain branch falls below informed silence in all 18
conditions even with either correction. The scope branch remains
above silence and has a +0.2734 margin over matched fixed compared
with +0.1141 for no bridge. Its much lower absolute release makes
that relative margin a poor summary of overall quality.

We replayed 432 policies with two independently implemented evaluation
paths. The writer still loses relation coverage even with the needed
source statements present. The conditions come from one exposed case,
authored evidence restoration and simulated delivery. Archive subject
matter and the frozen benchmark release are preserved.
[Routing policies and replays](routing.json)

## Reproduce

Use the Aurora Python and `replay` helper from the
[Resolution 2475 reproduction instructions](../README.md#reproduce).

```bash
set -o pipefail
"$py" run_bridge.py plan | cmp plan.json -
"$py" run_bridge.py verify | cmp verified.json -
"$py" score_bridge.py | cmp scores.json -
replay route_bridge.py | cmp routing.json -
```
