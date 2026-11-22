# Transfer the frozen admission gate to Myanmar Resolution 2669

The learned gate recovers India's procedural role in one option
mapping where fixed agreement withholds it, improving the full
record from 63 to 70. Pooled margins recover it in both mappings.
The source is public in the frozen case. Giving all writers the
public role passage removes the learned advantage on final records.

## Locked transfer

Reuse the v1.5 Myanmar case, exact final rubric and 130-word limit.
Train no new weights. The frozen proposer and reviewer come from
the four-family Resolution 2739 admission study. The new docket is
outside its fit and previously exposed in other project evaluations.
Eight locked scope probes cover five documentable claims and three
overreach controls. The two model reads use the same source and
claim under different option mappings. The separate record scorer
emits case-specific compact clauses when an affirmative judgment
and its assigned receipt are available. It scores with the exact
source witnesses and authored keys. The 21-point public lead
preserves adoption and the roll call. The primary replay routes the
known chair-role cue in the India packet. [Protocol](protocol.md) ·
[Probe plan](plan.json) · [Scoring plan](scoring-plan.json)

| Gate | Correct judgments /16 | Wrong admissions /16 | Full receipts /70 | Uniform receipt mean /70 |
| --- | ---: | ---: | ---: | ---: |
| Frozen learned | 14 | 0 | 63, 70 | 42.00 |
| Fixed agreement | 12 | 0 | 63, 63 | 40.25 |
| First desk alone | 13 | 1 | 63, 0 | 28.88 |
| Pooled margins | 16 | 0 | 70, 70 | 43.75 |
| Privileged semantic labels | 16 | 0 | 70, 70 | 43.75 |

The learned reviewer assigns 0.590 approval probability when
the proposer supports the chair-role claim and the reviewer locally
reads it as unresolved. It assigns 0.288 to the same categorical
disagreement on the unsupported claim that India abstained to
oppose ASEAN's role. The first-desk-only record publishes that
claim and also exceeds the length cap. The reviewer accounts for
the learned policy's decisions here. A component swap that always
sends an actionable first label and keeps the learned review
reproduces every result. The full learned and pooled records with
the role clause are 130 words.
[Native reads and recorded margins](verified.json) ·
[All 40 exact-span record scores](results.json)

## Compile the chair-role fact from its public source

After inspecting the transfer, use the existing official public
chair block in every arm, including when the India packet is absent.
Distinguish the Council President's procedural announcement from
the national explanation of abstention. Keep the other admissions
and mask bits fixed. Learned, fixed agreement and pooled now all
score 70 in both full-receipt mappings and 47.25 over uniform receipt
masks. Single-reader scores 70 or zero at full receipt and 34.125 on
average. Both the recovered and missing role clauses are now supplied
from the documented public record. The relation-level differences
remain in the original probe readout.
[Public-source replay and gate component swap](mechanism.json)

The 16 frozen Qwen3.5-4B forwards use 5,102 input and 32 constrained
output tokens on NVIDIA RTX PRO 6000 Blackwell Server Edition. This
is transfer across event families excluded from fitting, with authored
claims, case-specific assembly and same-assistant adjudication.
Pooled decisions receive both mapped scores at once. With the stronger
public-source comparator, the observed release gain over agreement
is zero. [Worker receipt](evidence/launch.json)

## Reproduce

Use the Aurora Qwen environment from the [earlier fit](../reporting-2739/learned-admission/README.md#reproduce).

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
"$py" transfer.py plan | cmp plan.json -
"$py" transfer.py verify | cmp verified.json -
"$py" score_records.py plan | cmp scoring-plan.json -
"$py" score_records.py run | cmp results.json -
"$py" mechanism.py | cmp mechanism.json -
```
