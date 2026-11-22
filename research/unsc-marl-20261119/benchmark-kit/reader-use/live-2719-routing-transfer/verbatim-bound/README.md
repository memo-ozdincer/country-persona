# Measure what can survive verbatim under a fixed writing budget

Start with the same six sets of received notes from the Resolution 2719 live-writing replay. Preserve sentence text, desk attribution and note order. Deduplicate an identical note from the same desk. Take a prefix of each note so that a second sentence cannot survive by dropping its antecedent. Count the desk headings against the original 90-word supplementary cap. The protected public decision is supplied separately. [Frozen protocol](protocol.json) · [Original route and writer replay](../README.md)

The exhaustive result uses reviewed sentence annotations and the frozen five-criterion weights. A second method allocates one next sentence per desk in round-robin order until it runs out of room and uses no rubric labels when selecting. Both begin from the same archived model-written notes. The reviewed optimum is an upper bound for this prefix renderer. A free writer can combine or paraphrase source statements more tersely. Neither renderer can legitimately add evidence absent from the notes. The missing strict criterion in the best note sets is an explicitly France-attributed affirmative vote on the final text. Unanimous adoption is supplied as a common public fact. [Sentence annotations and criterion requirements](annotations.json) · [Criterion combinations](grammar.json)

| Frozen input | Generated material /28 | Round-robin at 90 | Reviewed optimum at 90 | Shortest prefix version at unbounded optimum |
| --- | ---: | ---: | ---: | --- |
| Source change, learned | 6 | 17 | 17 | 101 words for 24 points |
| Source change, silence | 11 | 11 | 11 | 56 words for 11 points |
| Source change, fixed France | 13 | 17 | 17 | 96 words for 24 points |
| Same source, learned | 6 | 13 | 17 | 96 words for 24 points |
| Same source, declared and silence | 6 | 12 | 17 | 96 words for 24 points |
| Pooled | 0 | 6 | 6 | 50 words for 6 points |

The 90-word best records for the four complete source bundles preserve the vote, the distinct US rationale and the disagreement about financing. Full credit for France also requires the later sentence about continued support and willingness to discuss contribution levels. Including that sentence takes the full set of available criteria over 90 words. Simply passing all notes through verbatim would use 118–123 words for the three-source teams and 200 for pooled solo. The silence route in the source-change world fits in 78 words after removing its duplicate US note.

The learned source-changing question adds six points over like-for-like silence in the 90-word reviewed extraction and ties the fixed France supplement. The learned wording-only question ties the declared route under the paraphrase rule. Requiring the literal “appropriate amount” raises the targeted wording path's 90-word reviewed advantage over the generic path to four points, because the generic path can preserve the France bundle and procedure instead. Treat this as rubric sensitivity. It does not change that both archived replies conveyed the cap rationale. [Exact selected sentences, budget sweep and release review](results.json)

This is a deterministic replay using same-assistant annotations on one exposed case. It assigns available credit before free synthesis and makes the cost of verbatim preservation visible. The action comparison is conditional on the two selected worlds and successful transport.

## Reproduce

```bash
PYTHONDONTWRITEBYTECODE=1 python3 replay_verbatim.py score | cmp results.json
```

The script reconstructs the same frozen writer inputs, checks every annotation against the exact archived sentence, enumerates all prefix combinations, and retains the least costly best record at each tested cap.
