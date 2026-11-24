# Floor-rule sensitivity across the completed Council meetings

The registered procedure polls delegates outside the queue between
speeches. The experimental direct handoff gives the first queued
delegate the floor as soon as all packages have checked public
exclusions. Either procedure requires a delegate to declare the impasse.

We replayed all ten completed registered meetings under direct handoff.
We reused a response only if its full request matched the archived
request after bypassing the late floor polls. Eight meetings could be
replayed without any fresh decisions. Seven were identical and one
skipped a pass. For the other two meetings, a single fresh GPT-6.1-Sol
decision from a replayed prefix completed the comparison. Two
provider-interrupted attempts are listed in the audit and omitted
from the completed-meeting denominator.

| Meeting affected | Registered | Direct handoff | Evidence |
| --- | --- | --- | --- |
| Gulf, Norway opens, all Sol | Certified at 22 calls | Certified at 21 calls | Skipped Ghana's pass and replayed the same declaration request and reply |
| Gulf, Ghana opens, Astra at Norway | Certified at 25 calls | Certified at 23 calls | Skipped China's request and Norway's pass, then obtained a fresh declaration from Sol as Ghana |
| Iraq, UAE opens, all Sol | Unresolved at 55 calls | Certified at 54 calls | Skipped two passes, then obtained a fresh declaration from Sol as Brazil |

In the mixed Gulf run, the final speaker stayed Ghana and all nine
earlier speeches stayed fixed. The final prompt changed only in its
public queue field, which went from listing China to empty. Since the
meeting was on its last speech, China would have had no later speech
under either rule. The fresh Ghana response declared the impasse
under the usual checks. This extends the evidence beyond skipping
passes alone. The two live continuations are post hoc tests on
selected archived prefixes. The original registered outcomes still
govern the comparison between model assignments.

From the repository root:

```sh
python3 -B reports/council-workshop-floor-rule-audit-20261124/audit.py
python3 -B reports/council-workshop-floor-rule-audit-20261124/gulf.py plan
python3 -B reports/council-workshop-floor-rule-audit-20261124/gulf.py replay
```

[All replay checks](results.json) · [Frozen Gulf plan](gulf-plan.json) ·
[Gulf request and reply](gulf-live.jsonl) · [Gulf result](gulf-result.json) ·
[Iraq continuation](../council-workshop-certificate-floor-20261124/README.md)
