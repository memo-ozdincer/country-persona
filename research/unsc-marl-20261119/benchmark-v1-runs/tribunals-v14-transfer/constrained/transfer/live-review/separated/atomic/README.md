# Constrained criterion scoring for the coverage stage

The separated judge verified the six source guards and still produced
malformed or misattributed criterion citations. This experiment keeps
those same source verdicts and changes the coverage stage. Frozen
Qwen3.5-4B reads one criterion and the candidate text. The runner selects
the highest next-token logit among three legal answer letters. Two
prompts swap the meaning of A and B, while C always means uncertain.
The primary readout requires the two mapped choices to agree.
[Protocol](protocol.md) · [Locked requests](plan.json)

The whole-candidate and scoped arms use the same cases, coverage weights
and guard. For the tagged modular records, the scoped arm supplies only
the paragraphs tagged with the criterion's owning card. It marks the
criterion absent if that tag is missing. This avoids 15 model decisions
in the scoped arm. The untagged Myanmar cases share the same inputs in
both arms. An additional diagnostic averages logits after relabeling
them by semantic status instead of requiring identical choices.
[Logit readout](readout.md)

## Result

| Coverage rule | Exact disputed grades | Exact records across pairs and controls | Rows below informed silence | Mean net change |
| --- | ---: | ---: | ---: | ---: |
| Initial routing grades | — | — | 10 / 23 | 0 |
| Whole candidate, two mappings must agree | 0 / 3 | 0 / 6 | 10 / 23 | 0 |
| Source scoped, two mappings must agree | 1 / 3 | 2 / 6 | 8 / 23 | +0.0077 |
| Source scoped, averaged logits | 2 / 3 | 4 / 6 | 0 / 23 | +0.0451 |
| Source scoped, average only with tags | 2 / 3 | 4 / 6 | 2 / 23 | +0.0210 |

The agreed scoped method admits UNAMA at 46 and its public-only control
at 34. It abstains on Emergency Session because the two mappings disagree
about national capacity. Averaging recovers its 46-point grade and the
false-veto control still receives zero from the archived source guard.
The untagged Myanmar pair still receives a false 70 with average logits,
while its fuller control falls to 63 after losing the UK criterion.
The two single mappings score the Myanmar pair 49 and 70. This is
semantic and answer-mapping sensitivity after eliminating malformed
outputs. The aggregate improvement under averaging includes a wrong
Myanmar grade and one net regression.

The selective diagnostic averages only when the prompt plan has
source-scoped criterion inputs. It keeps the agreement rule for
untagged records. The rule was tested after inspecting the readouts
and does not use score labels as input. On these records all four
accepted grades match the archive, the Myanmar pair and control are
both unresolved, and routing improves in eight settings with no net
loss. The remaining two below-silence settings are Myanmar.
[Item choices and routing outcomes](results.json) · [Selective diagnostic](selective-results.json)

All 106 scorer invocations emit one legal choice. They process 35,918
input tokens and render 212 tokens, including the terminal tokens added
by the runner, in 7.91 seconds of measured scorer time. The benchmark run
compares both views and both mappings in one checkpoint load on an NVIDIA
RTX PRO 6000 Blackwell Server Edition. Scorer time excludes loading. The
owned process exited normally. The scoped policy alone uses 58 invocations
for the six records. This is a coverage component test on exposed records
with archived guard decisions and simulated routing.
[Native token and logit receipts](evidence/calls.jsonl) · [Verified outputs](verified.json)

## Replay

Run in the same Aurora Qwen environment with SciPy available for the
routing calculation.

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
env_root=/mfs1/u/memo/country-persona-research/envs
py="$env_root/aurora-qwen35-smoke-v1/bin/python"
scipy_packages="$env_root/open-character-20261004-v1/lib/python3.12/site-packages"
"$py" coverage_logits.py plan | cmp plan.json -
"$py" coverage_logits.py verify | cmp verified.json -
"$py" -c 'import numpy,sys,runpy; sys.path.append(sys.argv.pop(1)); runpy.run_path("atomic_replay.py",run_name="__main__")' "$scipy_packages" | cmp results.json -
python3 selective.py | cmp selective-results.json -
```
