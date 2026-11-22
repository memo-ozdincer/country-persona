# One-pass revision on Resolution 2593

Each of the three [archived matched writing outputs](../facilitator-matched-2593-evidence/README.md) gets two frozen Qwen3.5-4B revisions. Both see the same draft and dossier, have a 384-token output ceiling and must deliver a complete record within 210 words. The structured prompt additionally allocates about 35, 94 and 80 words across the decision, operative provisions and national accounts. It asks the writer to check each provision against the actor and operative verb and to check each national reason against its speaker. The generic revision already asks for concision, legal force and source-checking. [Locked protocol](protocol.md) · [Paired prompts](../facilitator_revise_2593.py)

The [authored feasibility reference](feasibility-reference.txt) gets full rubric credit at 188 words under the [exact-span review](feasibility-review.json). It was authored for the feasibility check and withheld from every model input. Reviews score coverage, gate authority and track gains or losses against each original. This is a single-docket revision diagnostic using same-assistant review and normalized UN source cards.

## Results

| Starting record | Original coverage and words | Generic revision | With word allocation and source checks |
| --- | --- | --- | --- |
| Peer | 21/70, 206 words, authority error | 63/70, 266 words, same authority error | 63/70, 231 words, clean |
| Independent | 21/70, 182 words, clean | 63/70, 255 words, clean | 63/70, 233 words, clean |
| Pooled solo | 56/70, 240 words, clean | 63/70, 261 words, clean | 56/70, 228 words, clean |

All six revisions end within their token ceiling and none clears the word limit. Each preserves every fully met criterion from its original. The structured prompt is shorter than the generic prompt's output by 22–35 words in every pair. It repairs the peer record's invented mandate, while the generic revision reproduces that error verbatim even after describing the Council's request correctly in the body. The structured solo revision retains its original imprecise phrasing about the airport request. No revision explicitly reconciles both abstainers' accounts. [Opaque review inputs](candidates.json) · [Exact spans](review.json) · [Per-criterion retention, gains and costs](results.json)

All six outputs insert headings despite a shared instruction to omit them. A post hoc count removes only the Markdown headings and the parenthetical meeting citation. The shortest candidate still has 219 words. The authored reference meets all ten criteria in 188 words, so the scoring contract leaves room for full coverage. The experiment suggests checking operative authority throughout the record, including the conclusion, and measuring whether brevity comes from tighter wording or missing source details.

## Reproduction

From `benchmark-kit/reader-use`, use the project model environment. The archived prompt and token traces reproduce the six generations and the end markers. The scoring step verifies exact response spans and recomputes matched differences from the preceding trial.

```sh
python facilitator_revise_2593.py verify facilitator-revise-2593-evidence
python facilitator_revise_2593_score.py blind facilitator-revise-2593-evidence
python facilitator_revise_2593_score.py score facilitator-revise-2593-evidence
```
