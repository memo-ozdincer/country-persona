# Live continuations at Norway's last useful Gulf turn

The [budget audit](../council-workshop-budget-headroom-20261123/README.md)
found that the Ghana-opening all-Sol trace became impossible to finish
after Norway's sixth speech. At that speech, `coastal` already had a
checked exclusion. Norway could still rule out `briefing` or `regional`.
The original reply proposed `review` instead. The scripted witness
from the same prefix certified impasse within the original caps.

The live comparison reuses 14 exact archived calls. It generates a
new reply at Norway's sixth speech with the standard instruction or
with the existing exclusions-first reminder appended. The entire
following discussion and its floor requests use the standard prompts
in both arms. The [plan](plan.json) fixes the prefix, GPT-6.1-Sol seats,
ten-speech limit and 30-call cap. The archive supplies no reply from
the selected turn onward.

| Prompt at speech six | Norway's reply | Delegate declaration | Automatic moderator replay |
| --- | --- | --- | --- |
| Standard | Proposed `review` | Unresolved, 3 exclusions, 10 speeches and 23 calls | Unresolved |
| Exclusions first | Ruled out `briefing` | Unresolved, 4 exclusions, 10 speeches and 24 calls | Certified, 10 speeches and 24 calls |

The fresh standard reply repeated the archived counterproposal. Its
later replies left the `briefing` exclusion missing at the cap. With the
reminder, Norway used speech six to rule out `briefing`. Ghana proposed
`regional` on speech seven and China signed it. Norway then ruled it
out, and Ghana added the last checked exclusion on speech ten. The
meeting had reached its speech cap before anyone could declare the
impasse. The automatic moderator replay closes at exactly that point.
The prompt improved evidence collection on this prefix, and the closing
rule made the completed evidence count as the endpoint.

Each prompt arm has one fresh continuation from the selected archived
state. The moderator cells replay those exact replies without new
model calls. The registered baseline and the scripted witness remain
separate.

[Standard continuation](standard-result.json) · [Priority continuation](priority-result.json) ·
[Moderator replay](moderator.json)

## Replay

```sh
set -o pipefail
out=reports/council-workshop-gulf-cutoff-20261123
python3 -B "$out/paired.py" plan | cmp "$out/plan.json" -
for arm in standard priority; do
  python3 -B "$out/paired.py" replay "$arm" | cmp "$out/$arm-result.json" -
done
python3 -B "$out/paired.py" moderator | cmp "$out/moderator.json" -
```
