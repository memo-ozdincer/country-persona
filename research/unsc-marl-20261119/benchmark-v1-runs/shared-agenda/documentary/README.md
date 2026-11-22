# Does the final record benefit from a second report after the decision is warranted?

Run the same frozen Qwen3.5-4B writer on the four Iraq and Syria worlds
where one authenticated card suffices. Each pair uses the same correct
certificate package, public evidence, task, options and output budgets.
The second arm adds the other delegate's actual fictional mandate.
The prompt gives a literal decision-line format. The certificate's
support list reflects the cards delivered. This companion test keeps
the closed benchmark and the policy fits separate from new writing.
[Predeclared protocol](protocol.md) · [Locked requests](plan.json)

| Case | One report raw /70 | Two reports raw /70 | One report released /70 | Two reports released /70 |
| --- | ---: | ---: | ---: | ---: |
| Iraq overlap alternate | 0 | 42 | 0 | 0 |
| Iraq impasse alternate | 0 | 0 | 0 | 0 |
| Syria overlap alternate | 28 | 28 | 28 | 28 |
| Syria impasse alternate | 28 | 0–14 | 28 | 0 |
| Sum across four worlds | 56 | 70–84 | 56 | 28 |

The row IDs retain their frozen family and variant names. Both
`impasse-alternate` cases permit an agreement on their actual cards.
Three two-report records and two one-report records use the supplied
package on the first line. The 165-word Iraq overlap record fails the
150-word cap, leaving two mechanically compliant finals in each arm.
Both Syria one-report outputs are byte-identical, as are the two Iraq
one-report outputs, because their visible inputs are identical. These
four pairs reuse six distinct prompts.

The Iraq writer sometimes treats a possible future change as a
contradiction of the current mandate. Both one-report records and the
Iraq two-report impasse alternate reject the warranted future proposal.
The two-report Iraq overlap recovers the dates, proposal and
documentation choice. The Syria overlap gains an explanation of how
the two workshop mandates fit but drops the official draft outcomes.
The Syria impasse alternate invokes insufficient affirmative votes to
explain the historical nine-month draft's defeat. That draft received
13 affirmative votes and failed due to a permanent member's negative
vote. Its record fails the source guard. Neither arm earns the full
positions criterion on any case.
[Exact source and response spans](marks.json) · [Scoring and paired criterion changes](scores.json)

These results use the full frozen case evidence and assistant
annotations. They measure the native writer's response to a controlled
change in its source access. The task reward used in the learned
controller measures warranted decisions from authenticated cards. The
writer's release result is a separate endpoint. The conclusions apply
to these exposed worlds and this fixed writer.

All eight calls complete on NVIDIA RTX PRO 6000 Blackwell Server
Edition with zero model updates. Supplying the second card adds 40
input tokens in every pair. The shared collector's launch metadata
retains its default Resolution 2422 roster label. The locked prompts,
actual call IDs and verified token traces identify the eight Iraq and
Syria calls. The launch receipt, including that inherited field, is
preserved verbatim. [Launch](evidence/launch.json) · [Raw outputs](evidence/calls.jsonl)

From this directory in the project Python environment:

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1
python write.py plan | cmp plan.json -
python write.py deck | cmp deck.json -
python score.py deck | cmp judge-deck.json -
python score.py score | cmp scores.json -
```
