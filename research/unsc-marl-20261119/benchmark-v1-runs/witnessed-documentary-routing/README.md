# Require documentary proof for the routing claim

**Exact quote extraction plus verification did not beat the full-message
claim check.** Across the 12 original official views it blocked one of
two false support claims, but lost both UK positives. The mean compiled
release fell from 45.083 to 44.417. The additional Russia sentence
deletion is reported separately. [Outputs and judgments](results.json)

| Rule on the 12 original views | Correct | False support | Missed support | Mean released /70 |
| --- | ---: | ---: | ---: | ---: |
| Prior full-message claim score | 10 | 2 | 0 | 45.083 |
| Nonempty extraction | 10 | 2 | 0 | 45.083 |
| Exact span | 9 | 1 | 2 | 44.417 |
| Exact span and averaged verifier | 9 | 1 | 2 | 44.417 |
| Exact, self-contained span with assistant review | 9 | 0 | 3 | 42.583 |

The UK outputs identify the real negotiation objection, but replace a
typographic apostrophe and add an ellipsis. The byte-level gate blocks
both. A separate recovery check strips a trailing ellipsis and matches
apostrophes only, then returns the matching original source substring.
It recovers both UK spans and the China span. The latter still supplies
consultation language with no support condition. This shows which errors
a more tolerant exact-span matcher could fix. It provides no validation
of the recovered spans' meaning. [Recovery replay](recovery.json)

On Afghanistan, the model-verifier margin for the consultation-only
Russia excerpt is +0.125, so the same semantic error survives both
quote extraction and automated verification. The full Russia quote
states a condition for support, but its reference to the decision
depends on the preceding sentence to identify the appointment. The
verifier accepts it at +0.8125. Assistant review counts it as sufficient
with that context and insufficient as a self-contained witness. Removing
just the sentence that gives Russia's condition yields a vague quote
about a fundamental condition. The verifier rejects it at −1.375.
The prior reader was not called on the new deletion.
[Official Afghanistan source](https://documents.un.org/doc/undoc/pro/n23/432/19/pdf/n2343219.pdf)
· [Official UK source](https://documents.un.org/doc/undoc/gen/n20/342/63/pdf/n2034263.pdf)

The caller extracts a witness only to decide which reply to send. The
compiled records and gold scoring stay fixed. The experiment averages
views equally, including overlapping passages from two exposed dockets.
Assistant grades distinguish span integrity and semantic sufficiency.
All 19 calls replay, comprising 13 generation calls and two verifier
labels for each of three exact witnesses. The run used 6,536 input and
272 saved output tokens with frozen Qwen3.5-4B on Aurora's
NVIDIA RTX PRO 6000 Blackwell Server Edition. No policy fit, model
update, or new official record was performed.

```sh
set -o pipefail
python=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$python" -B collect_witnesses.py plan | cmp plan.json -
"$python" -B collect_witnesses.py verify | cmp verified.json -
python3 -B annotate.py | cmp marks.json -
python3 -B score_witnesses.py | cmp results.json -
python3 -B recovery.py | cmp recovery.json -
```

[Protocol](protocol.md) · [Exact outputs](verified.json)
