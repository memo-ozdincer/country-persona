# Can source owners review a combined Security Council draft?

Resolution 2422 supplied most of the simulated gain from paying for an
exact archived score. This follow-up tests a cheaper observable signal.
Frozen Qwen3.5-4B reviews seven unchanged, in-limit multi-source
supplements. The original 70-word limit excludes one further draft.
The two source orders contain separate original generations. The
pooled reviewer sees all delivered sources. Each source owner sees
their own source card and the same complete draft, then checks the
claims and links involving their delegation. Both protocols use two
mappings of the response labels.

Both review policies publish the best available draft among the
subsets of received cards. Exact format failures and unclear material
claims block release. The original archive supplies all outcome
grades. The public lead and reviewed singleton drafts can be selected
without additional calls. A cap-only rule admits every in-limit draft
and prefers the larger bundle at equal predicted coverage. A more
conservative fixed policy always uses the best checked singleton or
public lead. The oracle knows the archived grade of every draft.

## First run

The original prompt asks for a guard label in addition to the listed
coverage labels. Forty-five of 46 responses supply exactly the number
of coverage criteria. All calls terminated normally. Only one response
satisfies the declared format. Neither review policy admits any
multi-source draft, including under either label mapping by itself.
The resulting policy is equivalent to the checked fallback after
paying for additional inference.

Across the eight multi-source receipts, cap-only dispatch earns 32.375
released points, checked fallback 51.500 and exact dispatch 52.875.
The exact grades change three decisions in that table. They recover
three points from the forward triple, five from the reversed Peru and
Serbia pair, and three by choosing that pair when the triple arrives.
These are archived draft choices under supplied singleton grades. The
exact policy is an opportunity ceiling for the bank.
[Original protocol](protocol.md) · [Verdicts and replay](results.json)

## Numbered checklist and compact decoding

Making the guard the first numbered item produces compact strings such
as `AAB`. The primary parser requires separated labels and accepts none.
The post hoc compact parser accepts only exact-length strings made of
the two declared labels, and preserves their order. It recovers 45 of
46 responses. One pooled review still contains one label too few.
Neither the archived grades nor the routing rules change.
[Follow-up protocol](indexed/protocol.md) · [Strict replay](indexed/results.json) ·
[Compact replay](indexed/compact.json)

| Dispatch policy | Eight multi-source receipts, average released /70 | Shared delivery, net at 0.15 per call |
| --- | ---: | ---: |
| Mechanical cap, prefer the larger bundle | 32.375 | 41.296 |
| Best checked singleton or public lead | 51.500 | 50.216 |
| Pooled model review | 51.500 | 49.830 |
| Source-owner model reviews | 45.875 | 46.837 |
| Exact archived grades, unpriced ceiling | 52.875 | 51.360 |

Under the compact parser the pooled protocol calls six candidates
clear, including two of the three with uncertain archived guards.
Owner reviews clear all seven. Only two of their dispatches change
released quality. They select the reversed Peru–Serbia pair and gain
five points. They also select its forward counterpart and lose 50.
Both versions elicit identical labels from both owners and the pooled
reviewer. The archived forward judgment finds that “Conversely” can
imply disagreement between the two national statements. The same
singleton grades are available in both orders, so the reviewer messages
supply no basis to distinguish the two choices. Pooling stays with the
checked fallback because its predicted pair score is too low to switch.
A single pooled answer mapping recovers three points on one receipt,
while the other mapping and their intersection leave all eight choices
unchanged in released quality.

The delivery replay puts both orders through independent 40%,
independent 80%, and shared-latent packets equally split between those
rates. Both review policies trail the checked fallback at 0.15 and 0.75
points per call under all three laws. The first-run pooled/scoped
protocols consumed 8,756/15,250 input tokens, and the numbered protocols
8,812/14,748. They use different amounts of review computation. All 92
calls use the same frozen Qwen3.5-4B checkpoint and NVIDIA RTX PRO 6000
Blackwell Server Edition. Both recorded workers exited normally.
[Delivery protocol](delivery-protocol.md) · [All verdicts, costs and dispatch changes](comparison.json) ·
[First launch](evidence/launch.json) · [Numbered-checklist launch](indexed/evidence/launch.json)

These are model reviews on two orders of one exposed docket, compared
with archival assistant grades and replayed under modeled delivery.
No policy weights were updated. The observed collision identifies a
missing distinction in the proposed review messages before any learning
uses them.

## Replay

Run in this directory with the local Qwen environment. The verification
checks the locked prompts, original archive records, tokenizer traces,
output lengths and replay arithmetic.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1
python scoped_review.py plan | cmp plan.json -
python indexed_checklist.py plan | cmp indexed/plan.json -
python scoped_review.py verify | cmp results.json -
python indexed_checklist.py verify | cmp indexed/results.json -
python compact_replay.py | cmp indexed/compact.json -
python delivery.py | cmp delivery.json -
python compare_checklists.py | cmp comparison.json -
```
