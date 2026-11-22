# Clarify the legal anchor with the same notes and writer

The Bosnia Resolution 2604 adaptive follow-up retrieved the UK's conditional support for the High Representative's executive powers. Its original final record retained that evidence and invented an asset seizure. This follow-up changes only “remaining seized” to “keeping the matter on the Council's agenda” in the final writer's public anchor. Each path retains its archived two opening notes and supplemental note. The checkpoint, instruction, decoding, token cap and scoring rubric match the original. [Frozen intervention](protocol.json) · [Original comparison](../README.md) · [Adopted resolution, paragraph 6](https://digitallibrary.un.org/record/3946754/files/S_RES_2604_%282021%29-EN.pdf)

| Drafting path | Original points /70 | Clarified points /70 | Original release | Clarified release |
| --- | ---: | ---: | --- | --- |
| Adaptive follow-up | 62 | 48 | Fail | Pass |
| Fixed UK follow-up | 36 | 36 | Pass | Fail |
| Fixed Russia follow-up | 63 | 56 | Pass | Pass |
| Pooled solo | 28 | 35 | Uncertain | Uncertain |

The clarified adaptive final drops the asset-seizure claim. It also omits both the condition on use of executive powers supplied by its follow-up and the internal scope of Russia's suggested dialogue. Both appeared in the original adaptive final. The qualifying edge from follow-up to final therefore disappears even though the follow-up itself is identical. Release passes under the existing guard because the brief explicitly attributes UK support and omits the conditional detail. The rubric withholds the seven points for the full powers criterion.

The clarified fixed UK final attaches interference in Bosnian dialogue to Russia's vacancy claim. The source makes the procedural objection the vacancy rationale and discusses outside interference in the context of reconciliation. That new causal link fails release. The fixed Russia final keeps the best coverage and passes both release checks, with the internal dialogue qualifier lost in the clarified version. Pooled solo gains that qualifier and retains the uncertain association of 5+2 with stabilization. [Opaque-ID spans and source review](marks.json) · [All paired criterion changes](results.json) · [Unedited outputs](evidence/final-records.json)

The coverage gap from adaptive to the strongest fixed follow-up grows from one to eight points under the clarification. The release-gated gap shrinks from 63 to eight points because the adaptive record now passes. The same retrieved evidence thus receives very different scalar reward when the writer sees a semantically equivalent public phrase. For deliberation evaluation, report a matched final-record score, targeted uptake and the release guard separately. For routing policy evaluation, hold notes and writer settings fixed within a comparison and test robustness to source-faithful wording changes across comparisons. These are four live generations on an exposed case with a same-assistant review. No policy or language model parameters were fitted.

## Verify

From this directory, run in the Qwen inference environment.

```bash
export PYTHONDONTWRITEBYTECODE=1
python score_anchor.py score | cmp results.json
```

The replay checks the exact change to each archived user message, all input and output token sequences, token caps, launch pins and all credited or adverse quoted spans. It reads the recorded generations.
