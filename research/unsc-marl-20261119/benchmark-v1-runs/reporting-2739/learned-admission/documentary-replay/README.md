# Carry frozen admission policies into the final record

Replay actual Resolution 2739 source-read logits through the fitted
two-stage gate and the fixed controls. Route the resulting role packets
through the four possible delivery masks and compile the exact accepted
affirmative assertions. The public lead and frozen v1.5 case rubric
stay fixed. The host binds exact witness strings to source blocks. A
separate reference judge scores entailment using the authored keys. The
composer emits the reporting overlap only when both relevant role
judgments say the sources support it. Rejected and unresolved positions
have no affirmative prose. The public lead already gives the roll call.
[Protocol](protocol.md) · [Input hashes](plan.json)

| Admission policy | Full receipt mean /70 | Uniform receipt mean /70 | Guard failures /8 |
| --- | ---: | ---: | ---: |
| Learned greedy | 63 | 49 | 0 |
| Fixed agreement | 63 | 49 | 0 |
| Pooled logits | 63 | 49 | 0 |
| First desk alone | 31.50 | 29.75 | 3 |
| Privileged source labels | 63 | 49 | 0 |

These scores come from the two option mappings and four receipt masks,
including both mappings of the full receipt. Without the second role
report, the record cannot score the 14-point bounded-overlap item. With
both, the learned, fixed and pooled arms miss only the seven-point
Algerian abstention rationale, which the initial probe set leaves
unqueried. The first desk overstates the record in one option mapping.
For example, it treats Algeria as endorsing the deadline and opposing
the cessation demand. The pooled arm's two relation errors are
contradiction labels. Its composer emits no new assertion from those
decisions, so those errors carry no final-record penalty in this task.
[All 40 graded records and admitted claims](results.json)

## Complete the abstention rationale

After inspecting the missing item, lock a positive claim that
covers Algeria's full concern and a second claim that narrows the
attacks to Algeria's own territory. Keep the same witness and both
option mappings. Freeze all policies and collect four additional
Qwen probes. The same exact-span scoring verifies the distinct
sovereignty scope. [Supplement protocol](supplement-protocol.md) ·
[Locked probes](supplement-plan.json) · [Verified logits](supplement-verified.json)

| Admission policy | Full receipt order 0 /70 | Full receipt order 1 /70 | Uniform receipt mean /70 |
| --- | ---: | ---: | ---: |
| Learned greedy | 70 | 70 | 52.50 |
| Fixed agreement | 70 | 70 | 52.50 |
| Pooled logits | 70 | 70 | 52.50 |
| First desk alone | 70 | 0 | 31.50 |
| Privileged source labels | 70 | 70 | 52.50 |

The learned and fixed gates accept the full rationale and withhold the
unsupported Algeria-specific claim in both mappings. The pooled scores
label the overreach a contradiction. The source leaves it unresolved.
The composer publishes affirmative claims only, so the resulting record
remains identical and scores 70. In the weaker mapping, the first desk
publishes the overreach and the earlier unsupported claims. Its full
record also exceeds the 130-word cap at 158 words. All learned, fixed
and pooled full receipts produce the same 110-word record.

With neither packet the learned and fixed arms release 42, with either
one they release 49, and with both they release 70. The 14-point
interaction between delivered packets comes from the bounded-overlap
rubric item. It describes documentary complementarity under this
composer. Both policies can use it to the same extent. Each result
bank has seven distinct output texts across its 40 replay rows.
[Final records and exact-span scoring](supplement-results.json)

The four additional frozen Qwen3.5-4B calls use 1,392 input and eight
constrained output tokens on NVIDIA RTX PRO 6000 Blackwell Server
Edition. The source-record assembly is deterministic and case-specific.
It reuses authored claims, an authored public lead and same-assistant
labels on an exposed docket. The supplement was selected after the
initial output analysis. Cross-family transfer, independent review and
a learned gain over the fixed controls remain unmeasured.
[Preparation receipt](preparation.md) · [Worker receipt](supplement-evidence/launch.json)

## Reproduce

Use the Aurora Qwen environment from [the gate evaluation](../README.md#reproduce).

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
"$py" documentary.py plan | cmp plan.json -
"$py" documentary.py run | cmp results.json -
"$py" supplement.py plan | cmp supplement-plan.json -
"$py" supplement.py verify | cmp supplement-verified.json -
"$py" score_supplement.py | cmp supplement-results.json -
```
