# Select exact sentence IDs and check what the source must establish

**The indexed selector and stricter verifier made all 13 attribution
decisions correctly on this panel.** It recovered the two UK positives
lost to altered quote punctuation and selected enough Russian context
to resolve the reference to the appointment. It rejected the Russia
consultation-only and China views, and the precise sentence deletion.
The same compiler and terminal scoring were used throughout.
[Selected spans, judgments, and scores](results.json)

| Rule on the 12 original views | Correct | False support | Missed support | Mean released /70 |
| --- | ---: | ---: | ---: | ---: |
| Full-message claim check | 10 | 2 | 0 | 45.083 |
| Literal model quote with the previous verifier | 9 | 1 | 2 | 44.417 |
| Sentence IDs, valid range | 10 | 2 | 0 | 45.083 |
| Sentence IDs and previous verifier | 11 | 1 | 0 | 45.083 |
| Sentence IDs and stated-element verifier | 12 | 0 | 0 | 45.083 |
| Sentence IDs and assistant review | 12 | 0 | 0 | 45.083 |

The resolver maps IDs back to offsets in the original source text, keeping
the exact punctuation. The stricter verifier gets the same span as the
previous verifier. On the Russia consultation-only view and the exact
deletion, the previous verifier still gives +0.125 support. Asking it
to check the appointment, the speaker's own backing, and agreement
as its condition gives −0.9375 on both. The full Russia range contains
the appointment and the explicit support condition. The stricter
verifier retains it. On Ghana's short view the selector offers a
101-word range. The fixed 100-word cap rejects it before verification.
[Exact source offsets and logits](verified.json) · [Review marks](marks.json)

The improvement is in attribution. Under the existing exact record
compiler, the old false-support views give the same released score for
either reply, so the safer route cannot raise the terminal score there.
The gate changes what the evaluator can verify before assigning
credit to a decision. The experiment reports the attribution checks
alongside the fixed final score and preserves the failure cases.

There were 13 selection calls and 24 first-token verdict passes over
six admitted ranges. The run used 12,285 input and 97 saved output
tokens on Aurora's NVIDIA RTX PRO 6000 Blackwell Server Edition.
All 37 prompts and output traces replay exactly. The source views
overlap and come from two exposed events. The required elements
and phrase boundaries are an adaptive intervention based on the earlier
errors. The assistant supplied the claim and reviewed the spans.
No new model or policy fit occurred. A family-level transfer test
would need new hypotheses, speaker documents, and independent review.

```sh
set -o pipefail
python=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$python" -B indexed_study.py plan | cmp plan.json -
"$python" -B indexed_study.py verify | cmp verified.json -
python3 -B annotate.py | cmp marks.json -
python3 -B score_indexed.py | cmp results.json -
```

[Protocol](protocol.md) · [Prior literal witness experiment](../witnessed-documentary-routing/README.md)
