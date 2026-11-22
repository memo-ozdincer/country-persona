# Free-form Resolution 2699 reward audit

The eight Qwen3.5-4B records cover every subset of the Ecuador, China and Russia cards in the previously reviewed Haiti dossier. Identical Council facts and instructions were used throughout. Each call finished within 285 words and the 432-token generation cap. The batch consumed 3,565 input tokens and 2,305 generated tokens. No optimizer updates ran. [Locked protocol](protocol.md) · [Source dossier](../facilitator-preflight-2699-evidence/packet.json)

| National cards delivered | Material points | Release points | Fixed renderer points |
| --- | ---: | ---: | ---: |
| None | 21 | 0 | 42 |
| Ecuador | 21 | 0 | 49 |
| China | 28 | 0 | 49 |
| Ecuador and China | 28 | 0 | 56 |
| Russia | 21 | 0 | 49 |
| Ecuador and Russia | 28 | 0 | 56 |
| China and Russia | 35 | 0 | 63 |
| All three | 35 | 0 | 70 |

All eight records say the mission leadership reports **to** the Secretary-General. Paragraph 18 names the Council as the destination and the Secretary-General as the route. The source packet used “through the Secretary-General,” so this common error occurs even with no national statements. The public rubric also requires the notification condition and separates a request for a compliance mechanism from a call on the mission to establish oversight. Some records strengthen a request into a mandate. The Ecuador–China record compares two purported abstainers by describing China and Ecuador. Ecuador co-sponsored the adopted draft and Russia provided the other abstention. [Resolution 2699, paragraphs 1, 10, 11, and 18](https://digitallibrary.un.org/record/4022890/files/S_RES_2699_%282023%29-EN.pdf) · [Exact-span assessments](review.json)

Twenty-one points from the adoption and vote, authorization duration and financing, and stated mission purpose recur in every answer. Extra cards produce eight gains and four ties across the 12 single-card edges on material points. Every release edge ties at zero. The review used one assistant, hidden mask labels, visible source evidence, and span matching. The sources make some subsets recognizable. The complete output covers both abstainers individually but misses the required distinction between their requests in its comparison sentence. A strict source assessment treats “potential leadership” as incomplete evidence of Kenya's willingness to consider leading. [Criterion definitions](rubric.json) · [Review packet](blind.json) · [Scored records and edges](results.json)

## Acquiring additional review labels

Initialize both planners with reviewed public and singleton scores. Keep the receipt model, fallback, opening costs and request costs fixed. The monotone planner restricts scores to compatible completions under inclusion. The independent-score planner enumerates all 0/70 corners of the unreviewed coordinates and minimizes the worst regret remaining after one more review. Its coordinate bounds work because each difference between request returns is affine in the encoded scores, including the completion bonus at 70. The worst-outcome calculation for choosing an audit still considers each possible integer answer. Each method yields a sum of per-opening conditional regret bounds under the nominal model. The actual-team replay is a separate quantity.

| Score bank | Monotone bound after two reviews, uniform / correlated | Independent bound after two reviews, uniform / correlated |
| --- | ---: | ---: |
| Free-form material | 0.202 / 0.209 | 4.076 / 3.350 |
| Free-form release | 0.027 / 0.023 | 0.033 / 0.031 |
| Fixed renderer | 0.440 / 0.364 | 3.215 / 3.658 |

For free-form material, the two methods select different pairs. The independent method inspects China–Russia and Ecuador–China. The monotone method inspects Ecuador–China and Ecuador–Russia. Both bounds contain the realized nominal regret on the observed banks. With all eight release labels known, both planners choose zero requests and the observed teams incur only their opening cost. These results leave the question of downward release edges open. One exposed case with a common error can mask genuine differences among receipt masks. Before fitting another communication policy, isolate public legal facts from the rewrite and remeasure the release surface, then evaluate any observed difference on fresh event families. [Review paths, scores and team replays](planning.json)

## Reproduction

From the parent `reader-use` directory, use the workspace Python environment and the local model referenced in [launch.json](launch.json).

```sh
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_free_record_bank.py verify facilitator-free-record-bank-evidence
python facilitator_free_record_bank_score.py blind facilitator-free-record-bank-evidence
python facilitator_free_record_bank_score.py score facilitator-free-record-bank-evidence
python facilitator_free_record_bank_plan.py
```
