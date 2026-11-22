# Constrain the native passage format and measure documentary coverage

Four fresh Qwen3.5-4B calls completed as canonical, role-local JSON
lists. A token trie allows all ordered subsets of each menu, including
the empty list. Its negative controls reject foreign or repeated IDs,
numbers in place of strings, fences, trailing prose, incomplete
arrays and multiple JSON values. A CPU rehearsal checks the full
dispatcher before the checkpoint loads.
[Protocol](protocol.md) · [Token grammar tests](codec-tests.json) ·
[Raw native calls](evidence/calls.jsonl) · [Verification](verification.json)

Greedy prefix masking produced a valid message in all four calls and
reduced documentary coverage. The China opening kept the ownership
position and lost the procurement clause. The Somalia opener and
reply kept the handover request and lost the localization clause.
The addressed U.S. reply chose the valid empty array. Every arm
released 42/70. The earlier successful 70/70 compound replay used
the same vocabulary with an accepted outer fence. Both results still
use the same selected Somalia branch.
[Fresh records and marks](results.json) · [Dispatch](evidence/dispatch.json) ·
[Logical per-policy token use](usage.json)

## Treat content omission as a planning risk

The separate population sensitivity keeps the calibrated benchmark
bank and delivery law fixed, and lets a successful addressed U.S.
reply omit its reporting objection. At a stipulated 50% omission
rate the frozen interval team's wins over equally informed fixed
routing fall from 15 to 4 of 18. Its mean margin falls from +0.118
to +0.026. Reoptimizing both controllers with that same content risk
raises the result to 15 wins and one loss, with a mean margin of
+0.093. These are hypothetical rates. The prior selected native test
demonstrates the specific kind of omission, and its population
frequency is still unmeasured.
[Content stress protocol](content-protocol.md) · [Frozen policies](content-stress.json) ·
[Risk-aware optimization](risk-planning.md) · [Reoptimized policies](risk-results.json)

The fresh run uses a frozen checkpoint on an NVIDIA RTX PRO 6000
Blackwell Server Edition. The action tables, scripted delivery and
same-assistant rubric remain the test environment. The first launch
stopped before the native generation call. The replayable corrected
launch includes the CPU rehearsal. [Preparation record](preparation.txt) ·
[Decoder context and research references](decoder-method.md)

Run with the parent Python environment and import paths.

```bash
set -o pipefail
python3 structured_live.py plan | cmp - plan.json
python3 codec_probe.py | cmp - codec-tests.json
python3 structured_live.py verify | cmp - verification.json
python3 structured_live.py score | cmp - results.json
python3 usage.py | cmp - usage.json
python3 content_stress.py | cmp - content-stress.json
python3 risk_plan.py | cmp - risk-results.json
```

[Complete-message likelihood selection](whole_message/README.md)
recovers 70/70 on the same four scoped prompts and exposes the
separate inference cost of summing over 356 candidate spellings.
