# Prospective routing transfer on Resolution 2686

The Council unanimously adopted the UAE–UK draft on 14 June 2023. France
and Switzerland each expressed reservations about the scope of the text
and the treatment of free expression. The outcome and assigned national
positions were locked before any generation. No prior routing experiment
on this issue family was found in the research tree. The historical
materials are public, so pretraining exposure is unknown.
[Official meeting](https://digitallibrary.un.org/record/4013426/files/S_PV.9347-EN.pdf) ·
[Adopted resolution](https://digitallibrary.un.org/record/4013227/files/S_RES_2686_%282023%29-EN.pdf) ·
[Locked docket](docket.json)

The pinned UNBench release records event 2488 in its author-test split.
All fifteen national vote labels match the official tally. Searching all
258 rows of the pinned UNSC-Bench adopted split by resolution symbol, draft
symbol or meeting returns no match. The vote uses the official record
and UNBench. The first join attempt assumed a matched UNSC-Bench row and
stopped. A field-wise search verifies the gap. A separate preflight path
error was corrected before the join.
[Cross-benchmark linkage](provenance.json)

## Prospective free-form records

Frozen Qwen3.5-4B wrote three role-local notes, eight final records on
the possible receipt masks, a reversed-order full record, and a pooled
writer control given the underlying excerpts. All 13 calls complete.
They use 5,478 input tokens and 2,339 output tokens in 38.34 seconds of
measured generation on an NVIDIA RTX PRO 6000 Blackwell Server Edition.
The measured time excludes checkpoint loading. The project-owned worker
exited normally. The same assistant grades nine unique opaque final
packets against the frozen v1.4 quote-and-guard scorer. One identical
record appears in two conditions. All source cites for met criteria
refer to cards within that writer's receipt set.
[Protocol](protocol.md) · [Native calls](evidence/calls.jsonl) ·
[Exact citations and scores](scores.json)

| Input to final writer | Released / 70 | What happened |
| --- | ---: | --- |
| Public outcome alone | 14 | Preserves public condemnation and dated oral briefing, with the draft symbol omitted |
| France and Switzerland | 35 | Preserves five criteria within 170 words |
| All three notes | 0 | Raw 35, with 190 words against the 175-word cap |
| Same three notes reversed | 0 | Conflates the omitted ICCPR reference with separate women's rights proposals |
| Pooled original sources | 21 | Stays within the cap and misses several operative and national details |

The released receipt score bank in mask order is **14, 14, 21, 35, 0, 14, 0,
0** after release checks. The robust routing policy sees seven grades
and withholds the full-receipt grade. It wins eight of 18 matched fixed
comparisons and ties 10, averaging +0.0558 net points. It stays above
informed silence in all 18. Against fixed targeting with all true
grades and the true inventory law it wins two, ties 15 and loses one.
The learned forecast and neutral actor policies tie in all 18
conditions. In the prospective dispatch, both the adaptive and fixed policies leave
the UK note undelivered across every modeled branch. The observed gain
comes from routing among the remaining receipts. The full-receipt
free-form record failed its length contract.
[Prospective routing replay](route-results.json)

## Retrospective assembly control

A 46-word authored public paragraph and one fixed contrast sentence
leave room to append all three original notes without editing their
text. The resulting 174-word record earns 63/70. The withheld criterion
requires a clear link between minority persecution in conflict and the
UK's focus on early warning. The UK note names persecution and
incitement risks while leaving the conflict scope of that rationale
implicit. All eight assembly masks meet the length cap. The score bank
is **21, 35, 35, 49, 28, 49, 49, 63**.
[Assembly protocol](assembly-protocol.md) · [Verbatim-note records](assembly.json)

On the assembly bank, the same robust selector beats equally informed
fixed targeting in all 18 scenarios, averaging +0.1428 net points. It
also beats fully informed fixed targeting in all 18 by +0.0670 on
average. The learned reward model beats its neutral counterpart in
five, loses two and ties 11, with a mean gain of +0.0040. Assembly was
authored after the prospective failure. The exact dispatcher reproduces
all 72 policy outcomes across the two banks. The UK note is delivered in
43.3% of branch mass on the adaptive assembly bank. The result isolates synthesis
loss on this case. It leaves native writer generalization and independent
grading unmeasured.
[Assembly routing replay](assembly-route.json) · [Exact transport dispatch](dispatch.json)

## Reproduce

Run from this directory in the existing Aurora Qwen environment, with
SciPy for the routing audit.

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
env_root=/mfs1/u/memo/country-persona-research/envs
py="$env_root/aurora-qwen35-smoke-v1/bin/python"
scipy_packages="$env_root/open-character-20261004-v1/lib/python3.12/site-packages"
replay() {
  "$py" -c 'import numpy,sys,runpy; sys.path.append(sys.argv.pop(1)); runpy.run_path(sys.argv.pop(1),run_name="__main__")' "$scipy_packages" "$@"
}
"$py" join_sources.py | cmp provenance.json -
"$py" live_tolerance.py plan | cmp plan.json -
"$py" live_tolerance.py verify | cmp verified.json -
"$py" score_tolerance.py score | cmp scores.json -
"$py" assemble.py | cmp assembly.json -
replay route_tolerance.py | cmp route-results.json -
replay route_tolerance.py --scores assembly.json | cmp assembly-route.json -
replay verify_routes.py | cmp dispatch.json -
```
