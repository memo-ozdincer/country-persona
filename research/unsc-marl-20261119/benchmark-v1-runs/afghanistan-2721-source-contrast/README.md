# Resolution 2721 source contrast

A one-clause limit makes the earlier note determine which comparison the chair can document. At 75% independent delivery and equal availability, the best arrival-only policy scores **50.6875/70**. Seeing the received note raises the ceiling to **56.875/70**, a gain of **6.1875 points**. This is a designed editorial workshop with exact expected scores.

## Source and task

On 29 December 2023, the Council adopted Japan and the UAE's draft S/2023/1056 as Resolution 2721, by 13 votes in favour with China and Russia abstaining. UNBench event 2519 matches all 15 official votes. The pinned UNSC-Bench adopted and vetoed files have no matching draft, meeting or resolution identifier across 469 rows. [Official vote and statements](https://digitallibrary.un.org/nanna/record/4032468/files/S_PV.9521-EN.pdf?registerDownload=1&version=1&withMetadata=0&withWatermark=0) · [Benchmark joins](provenance.json)

The relay holds one of two statements. Russia conditions its support for the appointment on agreement from the de facto authorities. Ghana speaks for the three African members and describes an envoy that would complement UNAMA. An editor can forward one of two clauses from operative paragraph 3. The consultation clause distinguishes the adopted appointment terms from Russia's position. The mandate safeguard supports the African members' explanation while preserving UNAMA's authority. The task gives no credit for pairing either statement with the other clause. [Adopted text](https://unama.unmissions.org/sites/default/files/n2343262.pdf) · [Case packet](case.json) · [Paraphrase scope check](source-review.json)

## Verification and controller transfer

The two statements and two mandate clauses each earn the same standalone credit within their slot. Their two authorized relationships each earn 22 of 70 points. Across 12 delivery and availability settings, receipt content adds **0.67375 to 9.92750** points. The direction is robust within this authored rule. Its magnitude depends directly on the assigned relationship weight. In the balanced 75% condition, halving that weight halves the score advantage. The break-even price is 8.25 points per arrived receipt if reading is charged only after arrival. Full information about an undelivered statement adds nothing because the renderer requires both sources to arrive.

All nine valid receipt records were graded by the source-bound renderer. The verifier rejects 135 duplicate, omission, cross-pair, owner, order or altered-block mutations. Exact branch enumeration matches the closed-form scores. The two frozen numeric controllers from the earlier private-opener and separate-links fits reach the content ceiling in all 12 settings. The simple matching rule reaches the same ceiling with the same declared clause-pair features. This is a control for source-constrained coordination under an identified observation benefit. Semantic selection from raw text, new language generation and transfer to unseen diplomatic events remain unmeasured. [Verified records and ceilings](results.json) · [Frozen policy actions and scores](transfer.json)

## Reproduce

From this directory:

```sh
set -o pipefail
env_root=/mfs1/u/memo/country-persona-research/envs
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$env_root/open-character-20261004-v1/bin/python" join_sources.py | cmp provenance.json -
python3 -B replay.py plan | cmp plan.json -
python3 -B replay.py run | cmp results.json -
"$env_root/aurora-qwen35-smoke-v1/bin/python" frozen_transfer.py | cmp transfer.json -
```
