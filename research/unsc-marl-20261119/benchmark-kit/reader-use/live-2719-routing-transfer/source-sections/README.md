# Ask for source-by-source sections under the same 90-word cap

Regenerate the same six bodies with a system instruction that requests separate amendment, United States and France sections. It asks for the amendment identifier and tally, each delegation's distinct reasoning, and preservation of qualifications. The archived notes, their order, writer checkpoint, generation cap and protected public decision match the original. This is a post hoc prompt comparison on an exposed case. [Frozen intervention](protocol.json) · [Original records](../README.md) · [Reviewed extractive control](../verbatim-bound/README.md)

| Frozen input | Original /28 | Source sections /28 | Section release | Section words |
| --- | ---: | ---: | --- | ---: |
| Source change, learned | 6 | 5 | Pass | 57 |
| Source change, silence | 11 | 11 | Pass | 50 |
| Source change, fixed France | 13 | 0 | Pass | 49 |
| Same source, learned | 6 | 7 | Pass | 75 |
| Same source, declared and silence | 6 | 7 | Uncertain | 68 |
| Pooled | 0 | 6 | Fail | 128 |

Four of the five team records drop the amendment tally despite running well below 90 words. The source-changing learned reply preserves the French financing concern, and the new final still drops willingness to discuss UN and EU contribution levels. The generic fixed France path loses the same qualification in its new final. Its US timing rationale is also weakened from timely deployment to facilitating deployment. A looser reading of that phrase would award five points and tie the learned source-change path under the section prompt.

In the same-source world, both new records retain France's full position and neither retains a complete US criterion. The learned reply's final loses the explicit cap, while the generic reply's final retains it but leaves uncertain whether the amendment newly excluded full financing. The pooled body repeats the amendment outcome across sections and exceeds the cap. The earlier silence release uncertainty is resolved by reporting the vote without claiming that the amendment caused final unanimity. All outputs finish within the generation-token limit. [Exact-span review](marks.json) · [Input-to-final traces](field-traces.json) · [Unedited assembled records](assembled-records.json)

The reviewed extractive control can retain 17/28 within 73–76 words for every complete three-source input. The section prompt fails to reach that attainable score. Distinguishing evidence selection from prose generation matters for credit assignment. A routing reward based only on these final outputs would penalize many facts that arrived correctly. The ranking varies with the writer and the release decision. This comparison uses one frozen model and same-assistant scores on two selected worlds, with zero language model or policy updates.

## Verify

From this directory, use the local Qwen environment.

```bash
export PYTHONDONTWRITEBYTECODE=1
python score_sections.py score | cmp results.json
python score_sections.py records | cmp assembled-records.json
```

The replay verifies that only the system instruction changes and checks exact prompt tokens, decoded bodies, credited spans and evidence traces. [Scores and sensitivity](results.json)
