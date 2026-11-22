# Test factored procedural and national capacity checks on Myanmar

The constrained whole-criterion judge credited a role the archived
Myanmar pair record omitted and missed a UK criterion in the fuller
record. This experiment keeps the same frozen checkpoint, candidate
inputs and A/B label mappings. It compares the original criterion with
narrower checks for the parts a full grade requires. The chair criterion
requires an attributed procedural announcement and a distinct national
explanation. The UK criterion requires sponsorship, an affirmative vote
and a rationale.
[Protocol](protocol.md) · [Locked model requests](plan.json)

The role controls distinguish a chair's procedural announcement from a
title alone, an announcement attributed to a national delegation, and
an explanation attributed to the chair. Two positive controls add the
same material with different phrasing. The UK controls remove the vote
or the rationale. Seven role tests and four UK tests share the two
archived records, for nine candidate texts. The untouched compound
prompts on the archived records match the earlier experiment byte-for-byte.
The controls are coverage checks, with only the archived records
carrying their original whole-record source guards.

## Coverage and routing

| Coverage method | Correct role tests | Correct UK tests | Exact admitted archival grades | Rows below informed silence |
| --- | ---: | ---: | ---: | ---: |
| Compound, averaged logits | 4 / 7 | 3 / 4 | 0 / 2 | 0 / 23 |
| Factored, averaged logits | 7 / 7 | 2 / 4 | 2 / 2 | 0 / 23 |
| Compound, mapping agreement | 1 / 7 | 0 / 4 | 0 / 2 | 2 / 23 |
| Factored, mapping agreement | 3 / 7 | 1 / 4 | 1 / 2 | 0 / 23 |

The role factorization correctly reads all 14 constituent checks under
averaging, including the two positive announcement phrasings, the title
without an announcement, and the two wrong-capacity cases. The averaged
compound result credits the missing procedural role on the archived
pair. It also credits the title-only and wrong-explanation controls.

The UK result exposes the limit of factoring. The narrower sponsorship,
vote and rationale checks recover the criterion in both full records.
They also overcredit both omission controls. Exact archival totals alone
would hide that error. The retrospective agreement between the two UK
readouts accepts the archived pair and abstains on the fuller control
and both omissions. The role factorization remains active for those
judgments.
[Per-predicate logits, labels and archival scores](results.json) ·
[Retrospective agreement check](protected-results.json)

Both factored methods admit 63 on the disputed Myanmar pair, while the
averaging method also recovers 70 on the fuller record. Combined with
the earlier scoped grades for the modular records, either factored method
matches the exact-grade counterfactual over the 23 routing conditions.
Both remove the two remaining failures against informed silence, improve
ten conditions compared with the initial grades, and decrease none.
The mean net improvement is +0.0456 points before review cost. The
incorrectly inflated compound grade also removes both quality failures,
while lowering net in one condition. The archive grade and the policy
reward therefore remain separate outputs.

The 74 constrained scorer invocations use 30,190 input tokens and render
148 tokens in 6.00 seconds of measured scorer time on an NVIDIA RTX PRO
6000 Blackwell Server Edition. That time excludes checkpoint loading.
All eight repeated compound logits are identical to the previous audit.
The owned worker exited normally. The evidence uses one exposed event
family, synthetic coverage controls and the same simulated delivery
conditions as the earlier replay.
[Raw logit and token evidence](evidence/calls.jsonl) · [Verified outputs](verified.json)

## Replay

Run from this directory with the existing Aurora Qwen environment and
SciPy for route optimization.

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
env_root=/mfs1/u/memo/country-persona-research/envs
py="$env_root/aurora-qwen35-smoke-v1/bin/python"
scipy_packages="$env_root/open-character-20261004-v1/lib/python3.12/site-packages"
"$py" capacity_atoms.py plan | cmp plan.json -
"$py" capacity_atoms.py verify | cmp verified.json -
"$py" -c 'import numpy,sys,runpy; sys.path.append(sys.argv.pop(1)); runpy.run_path("capacity_replay.py",run_name="__main__")' "$scipy_packages" | cmp results.json -
python3 protected_replay.py | cmp protected-results.json -
```
