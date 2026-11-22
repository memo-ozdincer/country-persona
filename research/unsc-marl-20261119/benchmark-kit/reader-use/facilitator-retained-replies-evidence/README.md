# Retain the generic reply when a topical draft loses evidence

The replying agent gets two drafts for the selected source. Its first draft uses a fixed generic prompt. Its second uses either a second preloaded generic prompt or the question that arrived. The interface retains the first approved draft, falls back to the second approved draft, or withholds the card if both fail. It forwards at most one complete card. The exact same recorded drafts support the replacement comparison, which discards the first draft. Both have the same per-send model call and token cap. [Prospective protocol](protocol.md) · [Selected reply text and exact policy replays](replay.json)

The three new second-generic Resolution 2504 replies all finish within the cap. None pass the whole-card rubric. Two falsely say the source supplies no named actors or decisions after asserting such facts. The Belgian answer drops the qualification about the exceptional mechanism. The chronology-only review credits Russia's sequence. The response still omits the amendment's draft symbol and falsely denies that the source names any actors or decisions. The independent comparator retains the first generic candidate, including the successful Belgian reply. Resolution 2719 uses the two previously evaluated generic drafts and the archived or alternate topical replies. [New raw replies](final-records.json) · [Source-local reviews](admission.json)

## Measured net gains

Compute the exact no-request policy with hindsight from the same two-draft admission table and the same opening, loss and message costs. The table reports the advantage of the frozen ideal-trained policy using retained drafts over that no-request policy.

| Case and rubric | Uniform | Correlated |
| --- | ---: | ---: |
| Resolution 2719, archived questions | +2.516 | +2.850 |
| Resolution 2719, alternate questions | +2.516 | +2.850 |
| Resolution 2504, strict | −0.309 | +3.634 |
| Resolution 2504, withdrawal chronology | +1.065 | +3.498 |

Against the earlier single-draft baseline on Resolution 2504, the strict uniform loss was −3.351 and the chronology-based loss was −1.977. Retaining the good generic draft recovers 3.04 points in each case at the same frozen request and response policies. The retained interface preserves generic support whenever it exists for the selected source. A paid query can still change which source is selected, and a two-generic independent team can recover evidence itself. In Resolution 2719, giving the independent team access to its own retained draft cuts a nominal +5.234 advantage under alternate questions and uniform inventories to +2.516. [Per-context pair selections and all controls](replay.json)

## Compute sensitivity

Under retention, the learned policy averages 1.75 author calls per episode. The best no-request team averages 1.50 on Resolution 2719 and on the Resolution 2504 chronology rubric, and 1.00 on the strict Resolution 2504 rubric. The replay reports expected input and output tokens. Charging one extra net point per author call and reoptimizing the no-request baseline leaves the chronology gains at +0.411 and +2.297, with the strict uniform loss worsening to −1.454. These are sensitivity values in benchmark score units. [Price-sensitive no-request policies](costs.json)

The selector uses same-assistant reviewed admission labels to choose real model text. This is an oracle interface diagnostic. The gain and loss estimates use modeled inventories and loss, and fixed final record assembly. No new optimizer steps ran, and neither the selector's semantic approval mechanism nor the policy's generalization has an independent evaluation.

## Reproduce from the parent directory

```sh
export PYTHONPATH="$(git rev-parse --show-toplevel)/src"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_retained_replies.py score facilitator-retained-replies-evidence
python facilitator_retained_replies_replay.py
python facilitator_retained_replies_cost.py
```
