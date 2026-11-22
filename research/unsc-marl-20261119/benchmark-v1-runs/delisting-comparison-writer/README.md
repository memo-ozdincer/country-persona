# Preserve the factual record and generate a general comparison

Copying the verified public and delivered facts lifted mean utility far
above the prior whole-record writer. Asking for a comparison generically
gave the trained team **31.578**, below **35.987** for the same team
with only the preserved facts and **37.242** for best arrival-only.
Admitting only the pairs approved by the existing role-scoped verifier
left this result unchanged.

Five of six calls returned NONE, including the Malta pair that should
connect the Focal Point's factual report to committee decision authority.
The only nonempty comparison said the Council “adopted a continuous
review.” The supplied provision expresses the Council's intention to
review continuously. The relation's legal force is ambiguous, so the
conservative primary reading blocks that record even with the verified
prefix. The [prior score sensitivity](../delisting-native-chair/sensitivity.json)
shows that returning the A3+ comparison alone at full credit would
still leave a zero gap between the best content-aware and arrival-only
policies. This follow-up holds the earlier routing policy fixed.

The comparison uses six calls and copies the preserved facts in each
available receipt set. The gate would use two comparison calls. This
is one exposed docket and a single semantic reviewer. The results
measure the general comparison prompt separately from the
[subsequent topic-guided prompt](../delisting-focused-writer/README.md).

[Locked requests](plan.json) · [Native responses](verified.json) ·
[Source judgments](marks.json) · [Policy replay](results.json) ·
[Protocol](protocol.md) · [Worker receipt](evidence/launch.json)

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B collect_relation.py plan | cmp plan.json -
python -B collect_relation.py verify | cmp verified.json -
python -B score.py | cmp results.json -
```

Use the Aurora Qwen environment. The generation worker ran on an
NVIDIA RTX PRO 6000 Blackwell Server Edition. The earlier native
whole-brief experiment used an AMD EPYC 9575F 64-Core Processor.
