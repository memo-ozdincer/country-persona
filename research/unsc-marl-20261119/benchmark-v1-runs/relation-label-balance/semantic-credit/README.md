# Fit the reviewer with frozen source and claim representations

The added hidden-state features improve training payoff and leave all
27 held decisions, query counts and reachable query payoffs unchanged.
Recapturing the same prompts on Aurora also exposes sensitivity in
the confidence-rule baseline, even though the predicted labels agree.

## Matched fit

Replay the identity and two cyclic option mappings for each of the
19 archival claims and eight Myanmar claims on one frozen Qwen3.5-4B
checkpoint. Retain the native label margins and a 32-dimensional,
seeded random projection of the final prompt hidden state. The
representation contains source, claim, instruction and option order.
Fit and scale six components using only the training families in
each fold. The augmented reviewer sees those components in addition
to the existing features. The baseline reviewer and both proposing
policies retain the same original local logits, labels and feature
contracts. Both reviewer heads and then both proposing heads get
160 CPU updates with exact expected team payoff. [Protocol](protocol.md) ·
[Capture plan](plan.json) · [Analysis plan](scoring-plan.json)

| Policy | Archive fold net | Archive extra reads | Myanmar net | Myanmar extra reads |
| --- | ---: | ---: | ---: | ---: |
| Existing features, staged | 0.3354 | 0.9375 | 0.525 | 1 |
| With source and claim features | 0.3354 | 0.9375 | 0.525 | 1 |
| First read alone | 0.4292 | 0 | 0.625 | 0 |
| Fixed confidence rule selected on recaptured training views | 0.2979 | 0.0625 | 0.600 | 0.25 |

Keeping either one of the augmented heads also leaves all held
outcomes unchanged. The additional features raise the full archive
reviewer's training objective at the final update from 0.4572 to
0.5263. In the four family folds and Myanmar, the added features
supply no useful query with the fitted reviewer held fixed. The
proposer can pay for either read and still misses the correct
procedural-role and vote relations that appear among the legal
responses. On Myanmar the sampled proposer with the frozen greedy
reviewer averages 0.5190 with the augmentation and 0.5217 without it.
[Exact fold weights, action probabilities and branches](results.json)

## Same-prompt runtime comparison

The 62 GPU-to-GPU recaptures reproduce the earlier centered logits
exactly. Across the 19 older CPU-to-GPU identity recaptures, all
selected relations agree and 13 top-two margins change. Mean absolute
margin movement is 0.0921, and the maximum centered score movement
is 0.125. Those archives previously used CPU batches, while the new
collector reads prompts individually on Aurora. The fitting-selected
fixed rule changes from first cycle below a 1.0 margin with the
second reader's label, to first cycle below or at 0.5 with agreement.
Its held Myanmar net falls from 0.725 to 0.600. This is a sensitivity
to the recorded margin shift. The two primary fits use the same
recaptured margins. [Matched prompt and margin audit](margin-audit.json)

The 81 constrained forwards use 23,268 input and 162 output tokens
on NVIDIA RTX PRO 6000 Blackwell Server Edition. The source family
cases and authored relation keys have prior exposure. The evidence
includes no updated Qwen weights. The first analysis attempt stopped
before fitting because a same-named module was imported from another
directory. The correction explicitly pins the intended scorer and
preserves the collection. [Token verification](verified.json) ·
[Worker receipt](evidence/launch.json) · [Preparation receipt](preparation.md)

## Reproduce

Use the Aurora Qwen environment and paths from
[the label-mapping study](../README.md#reproduce).

```bash
set -o pipefail
"$py" collect.py plan | cmp plan.json -
"$py" collect.py verify | cmp verified.json -
"$py" compare.py plan | cmp scoring-plan.json -
"$py" compare.py run | cmp results.json -
"$py" margin_audit.py | cmp margin-audit.json -
```
