# Require an answer span before giving relationship credit

**The span requirement changes the judge's errors. It recovers one valid
comparison, preserves the high-value false reward, and makes the
mutation controls worse.** The first stage indexes sentences from the
submitted answer without showing the source cards. The second stage
checks the selected span against the sources with the same verifier and
both label assignments. [Protocol](protocol.md) · [Selected text and exact decisions](results.json)

| Mean mapped logits | Archived decisions /12 | Rejected mutations /4 | Downstream utility |
| --- | ---: | ---: | ---: |
| Full-record judge | 10 | 3 | 31.885 |
| Answer span, then verifier | 11 | 2 | 31.898 |
| Exact archival marks | 12 | 4 | 32.225 |

The grounded route recovers the four-point Germany–Belgium funding
comparison. It still awards the 22-point consultation-versus-consent
distinction to the wrong Russia brief. The selected text records only
Russia's own position, while the source evidence allows the verifier to
infer the rest. The selector also supplies only the first sentence of
the valid Russia comparison. That sentence omits the explicit statement
that assent is not an appointment requirement, which the rubric asks
for. The verifier still accepts it.

The two newly admitted mutated briefs contain an explicit false
authority or mandate claim later in the response. The selector sends
earlier, individually supported statements to the verifier and hides
the conflicting line. On the two additional event families the anchored
grader passes one of two canonical records and one of two standalone
controls. The latter credit goes to a Resolution 2739 record where the
selected sentence reports only Algeria's reason. The two-stage approach
does not fix the distinction between a real comparison and a fact
that happens to appear in that comparison.

As a post hoc check, requiring both full-record and span-based approval
rejects all four mutations. It also loses the newly recovered funding
comparison and preserves the false Russia award on the unchanged brief.
This combination restores the full-record rule's 10/12 archived accuracy.
[Both-check and either-check sensitivity](combination.json)

The same 128 sender calibration episodes per docket receive the revised
relationship points while standalone credit and the guard stay fixed.
The fitted sender is scored under the original archived utilities.
Overall regret is 0.327 over 1,152 held conditions. The utility gain
over the earlier judge is 0.012 points, leaving the substantive
Afghanistan error intact. Mutations and cross-family controls never
enter the sender fit. The earlier exact renderer controls what can be
released in this calibration replay. [Earlier full-record test](../judged-relation-reward/README.md)

The matched 16 records use 38 calls in the two-stage setup, compared with
32 full-record calls. Including the four additional controls, the run
uses 50 calls, 20,609 input tokens and 123 saved output tokens. Inference
ran on frozen Qwen3.5-4B on Aurora's NVIDIA RTX PRO 6000 Blackwell Server
Edition. All traces replay. The comparisons concern the same exposed
benchmark evidence, one reward criterion at a time, and assistant-authored
marks. They do not validate a complete LLM judge on novel records.

```sh
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$python" -B collect_grounded.py plan | cmp plan.json -
"$python" -B collect_grounded.py verify | cmp verified.json -
"$python" -B score_grounded.py | cmp results.json -
python3 -B combine.py | cmp combination.json -
```

[Exact source offsets and verdicts](verified.json)
