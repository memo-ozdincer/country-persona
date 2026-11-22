# Matched final writing on Resolution 2593

This experiment follows the [routing diagnostic](../facilitator-prospective-2593-evidence/README.md). It compares final prose when the same source evidence reaches the writer. All three arms get four calls, three 92-token working notes and a 384-token final. The independent and peer arms share the first two notes. The third desk sees only its card in the independent arm and also receives two earlier notes in the peer arm. The pooled solo sees all source facts while making its three sequential notes. Every final writer sees all the same source facts and its own three notes. The final paragraph review used opaque IDs. This is a same-docket writing probe with a fixed peer route, without any new policy fit. [Locked procedure](protocol.md) · [Final rubric](rubric.json) · [Process idea key](idea-key.json)

| Arm | Material out of 70 | Release points | Final words | Input tokens | Output tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| Independent drafts | 21 | 21 | 182 | 1,165 | 400 |
| Peer-informed third draft | 21 | 0 | 206 | 1,252 | 431 |
| Pooled solo | 56 | 0 | 240 | 2,452 | 478 |

Each final ends within its token ceiling. The pooled record misses the 210-word cap. It also loses the distinction between asking for efforts and calling for reopening, and leaves the comparison of the abstentions implicit. The peer record adds a general comparison and claims a Council mandate for security measures, which the source expresses as a call and a request. The independent record preserves the force of those measures but omits several important details. The table measures equal calls and completion ceilings. The solo reads more input because it sees all sources in each note call. [Blinded records](blind-finals.json) · [Exact witness review](review.json) · [Scores and actual token budgets](results.json)

The working notes introduce the same four, four and three supported national ideas in all arms. The peer intervention changes the wording of the third note without changing the set of complete supported ideas. The independent, peer and solo finals retain 11, 10 and 12 supported national ideas respectively, including facts recovered from the documents. Those counts use the finer idea inventory. Full criteria also require precision such as the robustness of the UNAMA mandate. The peer final's general comparison cannot be traced to a newly supported idea in the peer-informed note. [Idea witnesses](idea-review.json) · [Trace and contribution counts](process.json)

## Blinded model judge

The frozen Qwen3.5-4B judge gets the candidate, source facts and all criteria. Its prompt demands met, unmet or uncertain for each criterion and a separate authority rating. It must copy a literal witness for each positive criterion and flagged error. The judge completes 32 of 33 fields and agrees with 21 of 33 same-assistant reference labels. It awards ten criteria that the reference review marks incomplete. Its literal witnesses do not reliably establish all parts of a criterion. The judge marks the peer record clean despite the invented authority, and reaches its 448-token cap before grading the solo authority guard. The complete authority-field outcome is one correct label, one missed error and one missing label. Treat this judge as a diagnostic. Exact copying establishes evidence location, while source entailment and criterion completeness still need validation. These three records support no broader judge reliability estimate. [Judge instructions](../facilitator_matched_2593_judge.py) · [Raw judge responses](judge/final-records.json) · [Agreement audit](judge/audit.json)

## Reproduction

From `benchmark-kit/reader-use`, use the project model environment. Both archived run directories contain the launch manifests, raw token traces and final outputs. Each verify stage rebuilds prompts and checks tokenization and decoded output against those archives.

```sh
python facilitator_matched_2593.py verify facilitator-matched-2593-evidence
python facilitator_matched_2593_score.py score facilitator-matched-2593-evidence
python facilitator_matched_2593_process.py facilitator-matched-2593-evidence
python facilitator_matched_2593_judge.py audit facilitator-matched-2593-evidence/judge
```
