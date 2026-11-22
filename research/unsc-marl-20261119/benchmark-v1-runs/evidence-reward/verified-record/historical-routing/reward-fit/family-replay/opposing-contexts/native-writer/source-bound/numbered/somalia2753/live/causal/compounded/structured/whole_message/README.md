# Select a complete message and render its passage IDs canonically

Use the same four role-local prompts, compound U.S. unit, parser,
dispatcher and rubric as the greedy prefix run. Score every allowed
ordered selection including the empty array. For each selection,
sum model probabilities over the finite, predeclared spellings.
The receiver gets the chosen selection rendered as canonical JSON.
The native decoder forwards text with no after-the-fact repair.

| Wire method on the same Somalia branch | Interval team | Query erased | Interval fixed | Fixed U.S. |
| --- | ---: | ---: | ---: | ---: |
| Greedy prefix mask | 42 | 42 | 42 | 42 |
| Complete-message scoring | 70 | 56 | 56 | 70 |

The complete-message method keeps China's ownership and procurement
clauses, Somalia's handover and localization, and the complete
addressed U.S. unit including its reporting objection. The full
record uses 150 words. In the four saved local score tables, restricting
the selection to the canonical spelling alone would favor shorter
subsets. It picks empty for the China opening and addressed U.S.
reply. Combining the finite spellings changes all four local choices.
The canonical-only choices are a diagnostic on the evaluated prompts.
A different early choice could activate different downstream prompts.

The four actor requests score 110, 110, 26 and 110 candidate sequences,
including each end token. The full model work is therefore larger
than the four emitted messages suggest. The generation budget retains
the same dispatcher and message fee as the prefix run. Model inference
resources are separately reported. This sums over the declared finite
surface set, with native model weights frozen on an NVIDIA RTX PRO
6000 Blackwell Server Edition. A fixed U.S. request matches the
selected branch completely. Independent adjudication and new-case
transfer remain open.
[Protocol](protocol.md) · [Candidate likelihoods](evidence/likelihood.jsonl) ·
[Canonical messages](evidence/calls.jsonl) · [Dispatcher](evidence/dispatch.json) ·
[Quote-grounded results](results.json) · [Replay](verification.json)

Run with the parent Python environment.

```bash
set -o pipefail
python3 whole_message.py plan | cmp - plan.json
python3 whole_message.py verify | cmp - verification.json
python3 whole_message.py score | cmp - results.json
```
