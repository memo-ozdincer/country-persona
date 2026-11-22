# Resolution 2422 excerpt budgets and final-record retention

This event joins UNBench author-test event 2229 and UNSC-Bench adopted row
197 on Peru's draft, date and all fifteen votes. The Council adopted
Resolution 2422 by 14–0–1. Russia abstained and Serbia participated without
a vote. The review and Prosecutor appointment are Council actions. The
medical-release requests and concerns in the Russian and Serbian speeches
belong to the speakers. The Council made no medical finding on this case.
[Verified join](forecast.json) · [Official meeting record](https://digitallibrary.un.org/record/1631976/files/S_PV.8295-EN.pdf) · [Adopted resolution](https://digitallibrary.un.org/record/1631600/files/S_RES_2422%282018%29-EN.pdf)

Six attributed paraphrases, their word counts and the semantic score were
frozen before running the comparison. The 70-word forecast uses the same
opening maps and scoring surface for every continuation arm. At 70 words
with all desks, whole-note assembly supports 10 of 28 supplementary
points and excerpt assembly supports 16. The archive supplies the protected
42-point public record separately. [Source packet](packet.json) · [Protocol](protocol.md)

| Inventory law | Learned over exact silence | Best fixed request over exact silence | Excerpt planner over exact silence | Whole-note planner over exact silence |
| --- | ---: | ---: | ---: | ---: |
| Uniform | +0.071 | +0.054 | +0.134 | −0.342 |
| Asymmetric | +0.015 | +0.001 | +0.095 | −0.119 |
| Correlated duplicates | +0.077 | +0.065 | +0.157 | −0.516 |

These are expected net points under modeled inventories and transport with
ideal admission and literal assembly. Because source delivery and final
writing can fail separately, frozen Qwen3.5-4B received all paraphrases from
each of the seven nonempty receipt masks. Four dependent calls reversed
multi-desk inputs, with single-desk records shared. The same receipt
probabilities and communication costs were applied to each scored writer
bank. The judge marks below are same-assistant review with exact spans.

| Inventory law | Learned over same-responder silence after writing, forward | Learned over same-responder silence after writing, reversed |
| --- | ---: | ---: |
| Uniform | −0.110 | −0.134 |
| Asymmetric | −0.029 | −0.017 |
| Correlated duplicates | −0.154 | −0.175 |

The pooled three-desk supplement earned 13/28 in forward order and 3/28
in reverse order. A two-desk Peru/Russia record had 13/28 raw coverage at
72 words in forward order. Its 63-word reverse included the Russian
abstention but left uncertainty over whether the medical allegation was
being treated as the cited reason for the earlier staffing objection.
Neither released. The Serbia/Russia record improved from an uncertain
guard to 10/28 released when reversed. This is a final-writer sensitivity
analysis with the route held fixed. No weights were updated.
[Forward records](writer-evidence/final-records.json) · [Reversed records](reversed-writer-evidence/final-records.json) · [Review](marks.json) · [Receipt-weighted results](writer-results.json)

The two local reference PDFs were read page by page. Their SHA-256 digests
were `77110afbe7be913866a71d9132641b3388bc8a810e87f8b907a9c4e648b80713`
for the meeting and
`2acb5af25affe7c6af31d9768a29c22ba6c76077d7d5dae81100edf24cef495b`
for the resolution.

From this directory in the project inference environment:

```bash
export PYTHONPATH="$(git rev-parse --show-toplevel)/src" OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python compare.py | cmp forecast.json
python writer.py verify
python score_writer.py | cmp writer-results.json
```
