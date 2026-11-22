# Grade record coverage separately from source support

The preceding live audit found that the judge imported source-only
statements into its candidate citations. This test gives frozen
Qwen3.5-4B two independent tasks per record. The coverage call gets
candidate paragraphs and criteria with no source excerpts. It returns
candidate paragraph IDs. The support call gets the same paragraphs
and source excerpts with no scoring criteria or previous reading. It
labels each paragraph. The scorer joins the two readings, applies
the original weights, and rejects invalid or uncertain verdicts.
[Locked design](protocol.md) · [Prompts](plan.json)

Use the same three contested records as the first live study. The
Emergency Session control adds a false claim that Russia blocked
current adoption. The Myanmar control uses the archived full record,
including the procedural chair paragraph. The UNAMA control retains
the public record while withholding all supplemental claims from the
candidate. Its verifier still sees the same source excerpts as for
the pair record.

## Live result

| Record | Expected grade | Two-stage outcome | With source-tag check |
| --- | ---: | --- | --- |
| Emergency Session pair | 46 | 50, one extra Brazil criterion | 46 |
| Emergency Session false-veto control | 0 | Guard failed, coverage uncertain | Same |
| Myanmar pair | 63 | Rejected, malformed coverage | Same |
| Myanmar full-receipt control | 70 | 70 | 70 |
| UNAMA pair | 46 | Rejected, malformed coverage | Same |
| UNAMA public-only control | 34 | Rejected, coverage uncertain and one extra Russian criterion | Rejected, extra criterion removed |

The verifier matches all 21 expected paragraph labels across the six
records, including the false veto in the Emergency Session control.
That success is separate from coverage. The Myanmar pair's malformed
response credits the procedural criterion using two paragraphs that
contain no presidency information. All twelve stage outputs terminate. In the Myanmar positive control the criterion set
matches the archived labels, although the source-verification stage
does not check whether each citation expresses the particular criterion.
[Raw outputs](evidence/calls.jsonl) · [Coverage and guards](grades.json) ·
[Paragraph and malformed-format audit](outcome-audit.json)

The twelve calls used 6,310 input and 206 output tokens, with 4.96
seconds measured in generation on an NVIDIA RTX PRO 6000 Blackwell
Server Edition. The six calls on the three disputed records generated
109 output tokens versus 1,384 for the earlier three quote-grounded
calls. The saved measurements exclude checkpoint loading. The owned
worker exited normally.

## Routing and the source-tag diagnostic

Replaying the primary two-stage grade increases the count below
informed silence from 10 to 16 across the 23 triggered scenarios.
Its mean net change is −0.0133 points against retaining the initial
grades. The overgrade on the Emergency Session pair drives the change.

In a separate retrospective replay, a new structural check requires a
supplemental criterion's citation to include a paragraph tagged with
its owning source card. The archived modular renderer supplies those
tags. The check removes the Brazil criterion linked to the public vote
paragraph. It recovers 46 on the Emergency Session pair, changing six
rows for the better and leaving the other 17 unchanged. The count below
informed silence falls to four and mean net improves by +0.0133 over
retaining the initial grades. Myanmar and UNAMA coverage verdicts
remain inadmissible. The tag check demonstrates a benefit for these
structured records. It leaves free-form coverage verification
unmeasured.
[Primary policy replay](results.json) · [Source-tag protocol](binding-protocol.md) ·
[Separate source-tag replay](binding-results.json)

## Replay

Run in the existing Aurora Qwen environment with SciPy available for
the policy replay.

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
env_root=/mfs1/u/memo/country-persona-research/envs
py="$env_root/aurora-qwen35-smoke-v1/bin/python"
scipy_packages="$env_root/open-character-20261004-v1/lib/python3.12/site-packages"
"$py" pair_separation.py plan | cmp plan.json -
"$py" pair_separation.py verify | cmp verified.json -
"$py" pair_separation.py grades | cmp grades.json -
"$py" -c 'import numpy,sys,runpy; sys.path.append(sys.argv.pop(1)); runpy.run_path("separation_replay.py",run_name="__main__")' "$scipy_packages" | cmp results.json -
python3 outcome_audit.py | cmp outcome-audit.json -
"$py" binding.py | cmp binding-results.json -
```
