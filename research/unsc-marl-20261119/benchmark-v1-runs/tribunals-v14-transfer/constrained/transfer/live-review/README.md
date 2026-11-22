# Live re-review of three contested UN routing grades

Three archived resolution records account for the ten documentary
regressions in the previous review-value audit. Frozen Qwen3.5-4B
independently graded each record in a numeric format and a format
requiring exact candidate and source quotes. The two formats saw the
same task, record, excerpts and original rubric with archived grades
withheld. The modular records retain their protected 34-point public
base. The Myanmar review uses its archived 150-word contract.
[Protocol](protocol.md) · [Locked prompts](plan.json)

| Record | Archived pair grade | Numeric result | Quote-grounded result |
| --- | ---: | --- | --- |
| Emergency Session, resolution 2623 | 46 | 34 | 34 |
| Myanmar, resolution 2669 | 63 | Rejected, score 1 outside rubric lattice | Rejected, output capped |
| UNAMA, resolution 2626 | 46 | 34 | Rejected, incorrect quote |

Neither format recovers an archived grade on these three records.
The Emergency Session quote verdict marks all supplemental items
unmet, including the three present national-capacity, negative-vote
and earlier-veto clauses. The UNAMA verdict marks the three Norway
items met and imports three absent Russian claims from the supplied
excerpts. Its first parser rejection is an inexact source span for a
Norway item. The capped Myanmar prefix contains nine complete criterion
arrays and already has three absent candidate quotes. It credits the
procedural presidency using a passage that appears only in the source.
[Admitted grades and rejection reasons](grades.json) · [All complete quote spans](verdict-audit.json)

The six calls consumed 6,086 input tokens and 1,392 output tokens on
an NVIDIA RTX PRO 6000 Blackwell Server Edition. They took 23.37 seconds
in the measured generation calls, including the first call warmup.
Checkpoint loading is outside that measurement. The owned worker exited
normally. The first preparation attempt applied the 130-word v1.4
Myanmar cap to the 138-word archived record. It stopped before any GPU
call. The final prompt lock restores the archived 150-word cap. A replay
receipt initially failed to relativize a script path. The corrected
receipt uses its absolute path and replays the same judgments.
[Launch identity](evidence/launch.json) · [Raw judge replies](evidence/calls.jsonl) · [Token verification](verified.json)

## Effect on the routing policy

Reuse the 23 triggered scenarios under their existing openings and
private observations. A rejected grade keeps the corresponding earlier
policy. The admitted model grades shift some routes despite judging
coverage incorrectly. Every admitted score is the already known
34-point public base. A rule returning the public base on the same
admitted rows would produce those same decisions without judging the
record. These results do not establish accurate second reading.

| Grade source | Rows below informed silence | Mean net change before review cost |
| --- | ---: | ---: |
| Initial grade | 10 | 0 |
| Live numeric | 2 | +0.035 |
| Live quote-grounded | 4 | +0.024 |
| Exact-review counterfactual | 0 | +0.046 |

In a separate post hoc audit, admitting only grades within the original
seven-point scenario envelope rejects all numeric and quoted model
proposals. The previous ten quality regressions remain. The check
prevents these large grade shifts under its assumed error bound, and
cannot supply a correct score. The replay's 23 rows reuse three exposed
records in modeled inventory and grade scenarios. They are not 23
independent judgments.
[Routing output by condition](results.json) · [Bounded-disagreement audit](gate-results.json)

## Replay

Run from this folder in the Aurora Qwen environment with SciPy available
for policy optimization.

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
env_root=/mfs1/u/memo/country-persona-research/envs
py="$env_root/aurora-qwen35-smoke-v1/bin/python"
scipy_packages="$env_root/open-character-20261004-v1/lib/python3.12/site-packages"
score() {
  "$py" -c 'import numpy,sys,runpy; sys.path.append(sys.argv.pop(1)); runpy.run_path("grade_and_route.py",run_name="__main__")' "$scipy_packages" "$@"
}
"$py" pair_review_live.py plan | cmp plan.json -
"$py" pair_review_live.py verify | cmp verified.json -
score grades | cmp grades.json -
score replay | cmp results.json -
python3 verdict_audit.py | cmp verdict-audit.json -
python3 review_gate.py | cmp gate-results.json -
```
