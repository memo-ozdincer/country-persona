# Run a model judge on the v1.7 calibration anchors

Frozen Qwen3.5-4B produced **3 valid final-record verdicts out of 21**
and **zero valid process verdicts out of four**. The published
calibration runner correctly reports incomplete coverage. This
checkpoint and prompt configuration therefore have a measured
failure as a scoring component.

| Calibration | Usable packets | Expected-label agreement on usable packets | Raw label agreement |
| --- | ---: | ---: | ---: |
| Final record | 3/21 | 7/11 | 111/123 |
| Deliberation process | 0/4 | Unavailable | 4/8 after removing the Markdown wrapper |

Every final response was JSON. On the 18 rejected verdicts, the first
failure was an answer quote that did not occur verbatim in 13 cases
and a source quote that did not occur in its identified block in five.
Exact citation validation also has a separate limit. A syntactically
valid verdict cleared the Syria answer's guard even though the
answer says the 13 affirmative votes authorized
aid. The draft failed on a veto. The same verdict also marked the
disposition and authority criteria met. This misses precisely the
kind of source distinction that can distort a learning reward.

Every process reply was a single fenced JSON block. Removing only the
outer wrapper leaves all four invalid. The remaining failures concern
citation shape, exact turn spans, ideas with no turn citation, and
wrong source quotes. In both anchors whose target labels credit
substantive interaction, the model assigned zero to both checked
interaction ratings. In the two anchors with zero expected credits
it returned the expected zeros. [Envelope-only check](fences.json)

The run uses all 25 original anchors, the exact v1.7 prompts and
4096-token output limit. It batches up to four inputs per mode with
left padding, greedy BF16 decoding and thinking disabled. The worker
ran on NVIDIA RTX PRO 6000 Blackwell Server Edition and completed
all 25 requests with 44,603 input and 30,094 generated tokens. Token
replay validates the archived responses and the production runner
reproduces the same incomplete calibration on them. The matches in
malformed verdicts are diagnostic and contribute zero usable ratings.
This is one checkpoint against the authored calibration keys. It
does not estimate inter-reviewer reliability on unseen cases.

[Protocol](protocol.md) · [Launch and token receipt](verified.json) ·
[Published calibration result](calibration/calibration.json) ·
[Raw and quote-valid label diagnostics](results.json) ·
[All unedited judge replies](evidence/tokens.jsonl)

Verification and replay in the Aurora environment:

```bash
set -o pipefail
python -B live.py plan | cmp plan.json -
python -B live.py verify | cmp verified.json -
python -B fences.py | cmp fences.json -
```

Run `python -B live.py replay --output NEW_DIRECTORY` to reproduce
`results.json` and the published runner's calibration files from the
stored replies. The directory must be new.
