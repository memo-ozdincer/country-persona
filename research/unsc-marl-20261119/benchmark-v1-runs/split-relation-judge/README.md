# Split relationship coverage from whole-record fidelity

A candidate-only coverage check corrected the unsupported 22-point
Russia bonus. The fitted sender reached **32.212** utility on the shared
1,152-setting grid. Exact archival marks reach 32.225 on the same grid.

| Feedback rule, averaged across both label mappings | Archived relations correct | Contradictory mutations rejected | Cross-family controls correct | Sender utility | Settings matching oracle |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full-record criterion with evidence | 10 / 12 | 3 / 4 | — | 31.885 | 898 / 1,152 |
| Selected answer span with evidence | 11 / 12 | 2 / 4 | 2 / 4 | 31.898 | 928 / 1,152 |
| Separate coverage and fidelity | 11 / 12 | 4 / 4 | 3 / 4 | **32.212** | **1,122 / 1,152** |
| Exact archived criteria | 12 / 12 | — | — | 32.225 | 1,152 / 1,152 |

In the rejected Russia record, the answer says Russia would withhold
support without Afghan authorities' agreement. Its description of the
adopted paragraph instead gives the UNAMA safeguard. The required
distinction between consultation and consent is absent. The guard clears
that record because the asserted facts are supported. Coverage denies
the bonus. The entire 2721 sender grid now matches exact-reward routing.
The 30 remaining mismatches are on 2553, where coverage misses the
four-point comparison between Belgium's case for predictable funding
and Germany's statement on Fund governance.

The whole-record guard independently rejected the four contradictory
mutations and cleared the 16 clean records. Coverage alone produced
identical approvals on this fixture roster. On Resolution 2664, coverage
missed the explicit contrast between adopted monitoring and India's
assessment of the stronger oversight it had sought. Both questions
were sensitive to the order of the response labels. On the archive,
requiring agreement or using the first mapping yielded 8/12 correct for
the conjunction. Using the reverse mapping yielded 4/12.

Each replay fits the sender from the same 128 randomized episodes per
docket. The receiver policy profile, delivery, costs, standalone points
and archival guard are fixed. The changed feedback is a relationship
bonus from frozen Qwen3.5-4B. Held settings vary delivery, prices,
partner profiles and priors over compiled records. The cases and
controls were exposed in development and use same-project annotations.
This supports a more useful reward component in that setting. The result
leaves independent judge reliability, fidelity on live generated records
and end-to-end language-agent MARL performance open.

## Reproduce

[Locked requests](plan.json) · [Worker receipt](evidence/launch.json) ·
[Exact logits and responses](verified.json) · [Replay results](results.json) ·
[Protocol](protocol.md)

From this directory, use the existing Aurora Qwen3.5 environment.
Verification uses the local checkpoint tokenizer and stored calls. It does
not reload model weights or need a GPU.

```bash
set -o pipefail
python -B collect_split.py plan | cmp plan.json -
python -B collect_split.py verify | cmp verified.json -
python -B score_split.py | cmp results.json -
```

The single worker completed 80 calls on an NVIDIA RTX PRO 6000
Blackwell Server Edition with zero optimizer updates to Qwen. The
sender fit uses the stored reward replay.
