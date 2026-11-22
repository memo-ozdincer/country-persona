# Can the final release score distinguish two message choices?

Across three exposed UN dockets, **9 of 25** archived message contrasts have the same strict direction across the tested writers and admissible grades. All nine favor delivering the additional note. The other 16 warrant abstention. This audit keeps messages and receipt weights fixed while changing the downstream writer or resolving uncertain grades. It gives no probability to individual writers or adjudications.

## Direction of the reward

| Docket and contrast | Tested archive writers | Stable positive | Abstain | Opposite nominal signs across writers |
| --- | ---: | ---: | ---: | ---: |
| 2553, replace Belgium funding with inclusion | 3 native | 0/1 | 1/1 | 0/1 |
| 2475, add one note with other receipts fixed | 3 restored-input | 7/12 | 5/12 | 5/12 |
| 2686, add one note with other receipts fixed | 4 free-form and source-scoped | 2/12 | 10/12 | 6/12 |
| 2686, same contrasts within source-scoped writers only | 2 | 12/12 | 0/12 | 0/12 |

For Resolution 2553, the native reward band is **−8.46094 to +14.17969 expected points**, while the verbatim and authored-relation references favor inclusion by **+0.75000** and **+0.46875**. Clearing the single uncertain funding record on the 31.64%-probability branch reverses both positive native estimates. The original undivided writer has a nominal tie and admits both directions under alternate marks. These comparisons measure one replacement action under the previously selected delivery law.

The 2475 comparison submits the same restored notes to each writer. Changes range from a verbatim record to prompted native comparison sentences. On 2686 all four variants reuse the same original notes, while the source-scoped variants separate the public lead from the handling of delivered notes. The approach changes both the reward and the information workflow. Dual use of the same archived fragments creates dependent cases. [Protocol](protocol.md) · [Exact counterfactual tables](results.json)

## Omit one writer when assigning a direction

| Docket | Directions issued / opportunities | Opposite direction under omitted writer | Direction remains certain under omitted writer |
| --- | ---: | ---: | ---: |
| 2475, require agreement of both remaining writers | 25/36 | 4/25 | 21/25 |
| 2686, require agreement of all three remaining writers | 12/48 | 2/12 | 8/12 |
| 2686, source-scoped pair only | 24/24 | 0/24 | 24/24 |

A single remaining writer's nominal score gives 18 opposite directions out of 70 issued on 2475 and 40 out of 123 on the full 2686 panel. Those single-writer counts include all ordered pairs and have a different denominator. The agreement rule trades coverage for fewer wrong directions among issued labels. Agreement among observed variants still leaves failures under a held writer. All 24 source-scoped predictions use the same 12 mask contrasts across two related writer variants. They measure consistency in this archive. [Every held-writer prediction](held-writer.json)

The interval replay groups duplicate receipt prompts so the same record always gets the same score within a comparison. For distinct drafts it lets uncertain units vary independently within archived bounds. If source judgments are correlated across distinct drafts, this can widen the interval. Definite guard failures and cap hits stay blocked. This is a diagnostic for which rewards could support a directional policy update. It uses same-assistant archived marks, carries out no new generation or training, and supplies no estimate for unseen event families.

## Reproduce

```bash
set -o pipefail
python3 -B audit.py plan | cmp plan.json -
python3 -B audit.py run | cmp results.json -
python3 -B held_writer.py | cmp held-writer.json -
```
